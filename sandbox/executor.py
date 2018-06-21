#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Python [3.6]
#
#  Author: Coumes Quentin     Mail: qcoumes@etud.u-pem.fr
#  Created: 2017-07-30
#  Last Modified: 2017-09-30


import json, os, tarfile, uuid, timeout_decorator, time, logging, traceback

from django.conf import settings

from sandbox.exceptions import MissingGradeError, GraderError

logger = logging.getLogger(__name__)


TIMEOUT_FEEDBACK = """
L'éxecution de votre programme prends trop de temps (maximum {X} secondes autorisées).
<br><br>Cette erreur peut être dû:
<ul>
    <li>À une boucle infinie. Pensez à vérifier les conditions d'arrêts de vos boucles <strong>while</strong> ainsi que de vos fonctions récursives.</li>
    <li>À un algorithme trop gourmand. Certains algorithmes sont meilleurs que d'autres pour effectuer certaines actions.</li>
</ul>
"""


class Executor:
    """ This class provide an interface to execute student's code inside a docker. """
    
    def __init__(self, request, timeout=3):
        self.files = request.FILES
        self.dirname = os.path.join(settings.MEDIA_ROOT, str(uuid.uuid4()))
        self.docker = settings.CREATE_DOCKER()
        self.timeout = timeout
        
    
    def _create_dir(self):
        """ Create the tar which will be sent to the docker """
        
        if not 'environment.tgz' in self.files:
            raise KeyError('environment.tgz not found in request.files')
        os.mkdir(self.dirname)
        for filename in self.files:
            with open(self.dirname+"/"+filename, 'wb') as f:
                f.write(self.files[filename].read())
    
    
    def _move_to_docker(self):
        """ Send the tar to the Docker, using Docker.put_archive() and untaring it inside the Docker"""
        with open(self.dirname+"/environment.tgz", 'rb') as tar_bytes:
            self.docker.put_archive("/home/docker/", tar_bytes.read())
        self.docker.exec_run("tar -xzf /home/docker/")
    
    
    @timeout_decorator.timeout(use_class_attribute=True, use_signals=False)
    def _evaluate(self):
        """Execute grader.py, returning the result. """
        
        return self.docker.exec_run("python3 grader.py")
        
        
    def execute(self):
        """ 
        Send the environnement to the docker and evaluate the student's code.
        """
        try:
            self._create_dir()
            self._move_to_docker()
            cwd = os.getcwd()
            exit_code, output = self._evaluate()
            output = output.decode("UTF-8")
            if exit_code:
                if exit_code > 1000 or exit_code < 0:
                    raise GraderError("Grader exit code should be "
                            + "[0, 999] (received '"
                            + str(exit_code)+"').")
                response = {
                    'feedback': "Erreur lors de l'évaluation de votre "\
                        + "réponse, merci de contacter votre professeur.",
                    'error': output,
                    'grade': -exit_code,
                    'other': [],
                }
            
            else:
                output = json.loads(output)
                if not 'grade' in output and not 'success' in output:
                    raise MissingGradeError
                if 'success' in output:
                    output['grade'] = 100 if output['success'] else 0
                response = {
                    'feedback': ("No feedback provided by the grader"
                                 if 'feedback' not in output 
                                 else output['feedback']),
                    'error': "" if 'error' not in output else output['error'],
                    'other': [] if 'other' not in output else output['other'],
                    'grade': output['grade'],
                }
        
        except timeout_decorator.TimeoutError as e:
            response = {
                'feedback': TIMEOUT_FEEDBACK.replace('{X}', str(self.timeout)),
                'grade' : 0
            }
        
        except MissingGradeError as e:
            response = {
                'feedback': ("Erreur lors de l'évaluation de votre "
                    + "réponse, merci de contacter votre professeur."),
                'error': str(e),
                'grade': -3,
                'other': [],
            }
        
        except GraderError as e:
            response = {
                'feedback': ("Erreur lors de l'évaluation de votre "
                    + "réponse, merci de contacter votre professeur."),
                'error': str(e),
                'grade': -4,
                'other': [],
            }

        except Exception as e: #Unknown error
            response = {
                'feedback': ("Erreur lors de l'évaluation de votre "
                    + "réponse, merci de contacter votre professeur."),
                'error': traceback.format_exc(),
                'grade': -5,
                'other': [],
            }
            logger.error(
                "Couldn't kill docker <"
               + str(self.docker.id) + " - " + str(self.docker.name) + "> :\n"
               + traceback.format_exc()
            )
        
        finally:
            try:
                self.docker.kill()
            except:
                logger.error(
                    "Couldn't kill docker <"
                   + str(self.docker.id) + " - " + str(self.docker.name) + "> :\n"
                   + traceback.format_exc()
                )
                   
            
        return json.dumps(response)
