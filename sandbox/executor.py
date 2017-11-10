#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Python [3.6]
#
#  Author: Coumes Quentin     Mail: qcoumes@etud.u-pem.fr
#  Created: 2017-07-30
#  Last Modified: 2017-09-30


import json, os, tarfile, uuid, timeout_decorator, time

from serverpl.settings import CREATE_self.docker



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
        self.docker = CREATE_self.docker()
        self.timeout = timeout
        self.timeout_feedback = TIMEOUT_FEEDBACK.replace('{X}', timeout)
    
    def __create_dir(self):
        """ Create the directory which will be sent to the docker """
        
        for key in ['environment.zip', 'grader.py', 'student.py']:
            if not key in self.files:
                raise KeyError('Key "'+key+'" not found in request.files')
        os.mkdir(self.dirname)
        for filename in self.files.keys():
            with open(self.dirname+"/"+filename, 'wb') as f:
                f.write(self.files[filename].read())
    
    
    def __move_to_docker(self):
        """ Send the directory to the Docker by taring the directory, using Docker.put_archive() and untaring it inside the Docker"""
        
        with tarfile.open(self.dirname+"/pl.tar", "w") as tar:
            for key in self.files.keys():
                tar.add(self.dirname+"/"+key, arcname=key)
        
        with open(self.dirname+"/pl.tar", 'rb') as tar_bytes:
            self.docker.put_archive("/home/docker/", tar_bytes.read())
        
        self.docker.exec_run("tar -xf /home/docker/")
    
    
    @timeout_decorator.timeout(use_class_attribute=True, use_signals=False)
    def __evaluate(self):
        """ Unzip environment.zip and execute grader.py, returning the result. """
        
        self.docker.exec_run("unzip -o /home/docker/environment.zip")
        result = self.docker.exec_run("python3 grader.py")
        return result
        
        
    def execute(self, retries=0):
        """ 
        Send the environnement to the docker and evaluate the student's code.
            - If the evaluation suceeded, return a json of this dic:
                {
                    "platform_error": [],
                    "grade": {
                        "success": [True/False] according to the evaluation.
                        "feedback": [feedback]
                    }
                }
            - If the evaluation timed out, return a json of this dic:
                {
                    "platform_error": [],
                    "grade": {
                        "success": False,
                        "feedback": [Error message]
                    }
                }
            - If the evaluation failed, return a json of this dic:
                {
                    "platform_error": [list of errors],
                    "grade": {
                        "success": False,
                        "feedback": [Error message]
                    }
                }
        """
        
        try:
            self.__create_dir()
            self.__move_to_docker()
            result = self.__evaluate()
            dico_response = {
                "platform_error": [],
                "grade": json.loads(result.decode("UTF-8")),
            }
            dico_response['path_files'] = self.dirname
        
        except timeout_decorator.TimeoutError as e: #Evaluation timed out
            error_message={
                'feedback': TIMEOUT_FEEDBACK,
                'success': False,
            }
            dico_response = {
                "platform_error": [str(e)],
                "grade":  error_message,
            }
        
        except Exception as e: #Unknown error
            if not retries:
                return self.execute(1)
            error_message={
                'feedback':"Erreur de la plateforme. Si le problème persiste, merci de contacter votre professeur.<br> "+str(type(e)).replace('<', '[').replace('>', ']')+": "+str(e),
                'success': False,
            }
            if "result" in locals():
                error_message["feedback"] += "<br><br>"+result.decode('UTF-8').replace('\n', '<br>')
            dico_response = {
                "platform_error": [str(e)],
                "grade":  error_message,
            
            }
        
        finally:
            self.docker.kill()
            
        return json.dumps(dico_response)
