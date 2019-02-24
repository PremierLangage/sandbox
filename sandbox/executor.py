import json
import logging
import os
import tarfile
import time
import traceback

import timeout_decorator
from django.conf import settings

from sandbox.enums import SandboxErrCode
from sandbox.exceptions import ContextNotFoundError, GraderError


logger = logging.getLogger(__name__)

BUILD_TIMEOUT = 8
EVAL_TIMEOUT = 8

CONTEXT_FILE = "pl.json"
PROCESSED_CONTEXT_FILE = "processed.json"
STDOUT_FILE = "stdout.log"
STDERR_FILE = "stderr.log"
FEEDBACK_FILE = "feedback.html"
ANSWERS_FILE = "answers.json"

TIMEOUT_FEEDBACK = """
L'éxecution de votre programme prends trop de temps (maximum %d secondes autorisées).
<br><br>Cette erreur peut être dû:
<ul>
    <li>
        À une boucle infinie. Pensez à vérifier les conditions d'arrêts de vos boucles
       <strong>while</strong> ainsi que de vos fonctions récursives.
    </li>
    <li>
        À un algorithme trop gourmand. Certains algorithmes sont meilleurs que d'autres pour
        effectuer certaines actions.
    </li>
</ul>
"""



class Executor:
    """This class provide an interface to execute PL scripts."""
    
    
    def __init__(self, cw, envpath, timeout=0):
        self.envpath = envpath
        self.envid = os.path.splitext(os.path.basename(envpath))[0]
        self.cw = cw
        self.docker = cw.container
        self.timeout = timeout
    
    
    def move_env_to_docker(self):
        """Send the tar to the Docker and untar it inside the Docker"""
        start = time.time()
        with tarfile.open(self.envpath, "r:gz") as tar:
            tar.extractall(self.cw.envpath)
            tar.close()
        
        processed = os.path.join(self.cw.envpath, PROCESSED_CONTEXT_FILE)
        old = os.path.join(self.cw.envpath, CONTEXT_FILE)
        if os.path.isfile(processed):
            os.remove(old)
            os.rename(processed, old)
        
        logger.debug("move_env_to_docker() took " + str(time.time() - start))
    
    
    def get_file(self, path):
        """Return the content of /home/docker/<path> if found, an empty string otherwise."""
        start = time.time()
        with open(os.path.join(self.cw.envpath, path)) as f:
            content = f.read()
        logger.debug("get_file() took " + str(time.time() - start))
        return content
    
    
    def get_stdout(self):
        """Return content of /home/docker/STDOUT_FILE if found, an empty string otherwise."""
        return self.get_file(STDOUT_FILE)
    
    
    def get_stderr(self):
        """Return content of /home/docker/STDERR_FILE if found, an empty string otherwise."""
        return self.get_file(STDERR_FILE)
    
    
    def get_feedback(self):
        """Return content of /home/docker/FEEDBACK_FILE if found, an empty string otherwise."""
        return self.get_file(FEEDBACK_FILE)



class Builder(Executor):
    """Used to build an exercise."""
    
    
    def __init__(self, cw, envpath, timeout=BUILD_TIMEOUT):
        super().__init__(cw, envpath, timeout)
    
    
    def get_context(self):
        """Return content of PROCESSED_CONTEXT_FILE as a dictionnary (file must be a valid json).
        Raises ContextNotFoundError if the file could not be found."""
        start = time.time()
        
        try:
            with open(os.path.join(self.cw.envpath, PROCESSED_CONTEXT_FILE)) as f:
                j = json.load(f)
        except FileNotFoundError:
            logger.debug("get_context() took " + str(time.time() - start))
            raise ContextNotFoundError
        
        logger.debug("get_context() took " + str(time.time() - start))
        return j
    
    
    @timeout_decorator.timeout(BUILD_TIMEOUT, use_signals=False)
    def build(self):
        """Execute builder.py."""
        start = time.time()
        
        ret = self.docker.exec_run('./builder.sh')
        msg = ("Execution of build with parameters "
               + "DOCKER_MEM_LIMIT=" + str(settings.DOCKER_MEM_LIMIT) + " and "
               + "DOCKER_CPUSET_CPUS=" + str(settings.DOCKER_CPUSET_CPUS)
               + " took " + str(time.time() - start) + " secondes.")
        logger.debug(msg)
        return ret
    
    
    def execute(self):
        """Execute the class command and return a valid response dictionnary."""
        try:
            self.move_env_to_docker()
            exit_code, _ = self.build()
            response = {
                "id":         self.envid,
                "status":     exit_code,
                "stderr":     self.get_stderr(),
                "context":    self.get_context() if not exit_code else {},
                "sandboxerr": ""
            }
        except timeout_decorator.TimeoutError:
            response = {
                "id":         self.envid,
                "status":     SandboxErrCode.TIMEOUT,
                "stderr":     self.get_stderr(),
                "context":    {},
                "sandboxerr": ("Execution of the script build/before timed out after "
                               + str(self.timeout) + " seconds.")
            }
        except ContextNotFoundError:
            response = {
                "id":         self.envid,
                "status":     SandboxErrCode.CONTEXT_NOT_FOUND,
                "stderr":     self.get_stderr(),
                "context":    {},
                "sandboxerr": (
                    "File '" + PROCESSED_CONTEXT_FILE + "' and '" + CONTEXT_FILE + "' were "
                    + "not found in the environment after the execution of the "
                    + "build/before script.")
            }
        except Exception:  # Unknown error
            response = {
                "id":         self.envid,
                "status":     SandboxErrCode.UNKNOWN,
                "stderr":     self.get_stderr(),
                "context":    {},
                "sandboxerr": "An unknown error occured:\n" + traceback.format_exc()
            }
            logger.exception("An unknown exception occured during build of env %s:" % self.envid)
        
        return response



class Evaluator(Executor):
    """Use to grade an exercise."""
    
    
    def __init__(self, cw, envpath, answers, timeout=EVAL_TIMEOUT):
        super().__init__(cw, envpath, timeout)
        self.answers = answers
    
    
    def add_answer_to_env(self):
        """Add the answers in self.answers tp the environment."""
        start = time.time()
        with open(os.path.join(self.cw.envpath, ANSWERS_FILE), "w+") as f:
            json.dump(self.answers, f)
        logger.debug("add_answer_to_env() took " + str(time.time() - start))
    
    
    def get_context(self):
        """Return content of PROCESSED_CONTEXT_FILE as a dictionnary (file must be a valid json).
        Raises ContextNotFoundError if the file could not be found."""
        start = time.time()
        
        try:
            with open(os.path.join(self.cw.envpath, PROCESSED_CONTEXT_FILE)) as f:
                j = json.load(f)
        except FileNotFoundError:
            return {}
        
        logger.debug("get_context() took " + str(time.time() - start))
        return j
    
    
    @timeout_decorator.timeout(EVAL_TIMEOUT, use_signals=False)
    def evaluate(self):
        """Execute grader.py, returning the result. """
        start = time.time()
        ret = self.docker.exec_run("./grader.sh")
        msg = ("Execution of evaluate with parameters "
               + "DOCKER_MEM_LIMIT=" + str(settings.DOCKER_MEM_LIMIT) + " and "
               + "DOCKER_CPUSET_CPUS=" + str(settings.DOCKER_CPUSET_CPUS)
               + " took " + str(time.time() - start) + " secondes.")
        logger.debug(msg)
        return ret
    
    
    def execute(self):
        """
        Send the environnement to the docker and evaluate the student's code.
        """
        stdout = None
        try:
            self.move_env_to_docker()
            self.add_answer_to_env()
            exit_code, stdout = self.evaluate()
            stdout = stdout.decode()
            try:
                if not exit_code:
                    stdout = int(stdout)
            except ValueError:
                raise GraderError()
            feedback = self.get_feedback()
            if feedback == '\n':
                feedback = ""
            response = {
                "id":         self.envid,
                "status":     exit_code,
                "grade":      stdout if not exit_code else (-1),
                "stderr":     self.get_stderr(),
                "feedback":   feedback if feedback else str(stdout if not exit_code else -1),
                "context":    self.get_context() if not exit_code else {},
                "sandboxerr": "",
            }
        except timeout_decorator.TimeoutError:
            response = {
                "id":         self.envid,
                "status":     SandboxErrCode.TIMEOUT,
                "grade":      (-1),
                "stderr":     self.get_stderr(),
                "feedback":   TIMEOUT_FEEDBACK % self.timeout,
                "context":    {},
                "sandboxerr": ("Execution of the grader timed out after "
                               + str(self.timeout)
                               + " seconds.\nThe RAM of the sandbox is currently"
                               + " limited to "
                               + settings.DOCKER_MEM_LIMIT
                               + ", using more will "
                               + "considerably slow the execution of your grader.\n"
                               + "Do not forget to close every open file or to use 'with' "
                               + "statement.")
            }
        except GraderError:
            response = {
                "id":         self.envid,
                "status":     SandboxErrCode.GRADER_NOT_INT,
                "grade":      (-1),
                "stderr":     self.get_stderr(),
                "feedback":   ("Execution of the evaluating script returned an invalid value."
                               + " Please contact your teacher."),
                "context":    {},
                "sandboxerr": (
                    "Grader script did not return a valid integer on stdout, received:\n"
                    + ("'" + str(stdout) + "'" if str(stdout) else "[NOTHING]"))
            }
        except Exception:  # Unknown error
            response = {
                "id":         self.envid,
                "status":     SandboxErrCode.UNKNOWN,
                "grade":      (-1),
                "stderr":     self.get_stderr(),
                "feedback":   ("Execution of the evaluating script failed due to an unkwown error."
                               + " Please contact your teacher."),
                "context":    {},
                "sandboxerr": "An unknown error occured:\n" + traceback.format_exc()
            }
            logger.exception("An unknown exception occured during eval of env %s:" % self.envid)
        
        return response
