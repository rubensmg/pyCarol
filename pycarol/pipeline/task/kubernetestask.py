import logging
import time
import uuid
from datetime import datetime
import os

import luigi
from .dockertask import EasyDockerTask, Task
from ...compute import Compute
from ...carol import Carol

logger = logging.getLogger('luigi-interface')


class EasyKubernetesTask(EasyDockerTask):

    """
    Need to define the following in each task:
    easy_run(self,inputs)
    image
    job_namespace
    """

    __POLL_TIME = 5  # see __track_job
    _kubernetes_config = None  # Needs to be loaded at runtime

    def _init_kubernetes(self):
        self.__logger = logger
        self.job_uuid = str(uuid.uuid4().hex)
        now = datetime.utcnow()
        namespace = self.get_task_namespace()
        file_id = luigi.task.task_id_str(self.get_task_family(), self.to_str_params(only_significant=True))
        file_id += "-" + self.job_uuid[:5]
        self.uu_name = file_id.split(namespace+'.')[-1]

    @property
    def name(self):
        """
        A name for this job. This task will automatically append a UUID to the
        name before to submit to Kubernetes.
        """
        #Name cannot have '.', also have to be less de 63 characters
        #TODO: Is this the best way? this will be the name of the task+package it is in.

        return '-'.join(self.__class__.__name__.lower().split('.'))
        #return '-'.join(self.get_task_family().lower().split('.')[-2:])


    @property
    def job_namespace(self):
        return os.environ['CAROLTENANT']

    @property
    def job_env_variables(self):

        env_var = dict(CAROLCONNECTORID=os.environ['CAROLCONNECTORID'],
                       CAROLORGANIZATION=os.environ['CAROLORGANIZATION'],
                       CAROLAPPOAUTH=os.environ['CAROLAPPOAUTH'],
                       LONGTASKID=os.environ.get('LONGTASKID', ''),
                       CAROLTENANT=os.environ['CAROLTENANT'],
                       CAROLAPPNAME=os.environ['CAROLAPPNAME'],
                       IMAGE_NAME=os.environ['DOCKER_IMAGE'],
                       CDMLINE=self.command,
                    )

        return env_var

    @property
    def delete_on_success(self):
        """
        Delete the Kubernetes workload if the job has ended successfully.
        """
        return True

    @property
    def print_pod_logs_on_exit(self):
        """
        Fetch and print the pod logs once the job is completed.
        """
        return True

    @property
    def active_deadline_seconds(self):
        """
        Time allowed to successfully schedule pods.
        See: https://kubernetes.io/docs/concepts/workloads/controllers/jobs-run-to-completion/#job-termination-and-cleanup
        """
        return None

    def __get_job_status(self, uri):
        status = self.job.track_process(uri)
        return status['status']

    def __track_job(self, job):
        """Poll job status while active"""

        uri = job['status_url']
        status = self.__get_job_status(uri)

        while status in ['Creating', 'ContainerCreating', 'Starting', 'Pending']:
            time.sleep(self.__POLL_TIME)
            self.__logger.debug("Waiting for Kubernetes job " + self.uu_name + " to start")
            status = self.__get_job_status(uri)

        status = self.__get_job_status(uri)
        while status == "Running":
            self.__logger.debug("Kubernetes job " + self.uu_name + " is running")
            time.sleep(self.__POLL_TIME)
            status = self.__get_job_status(uri)

        assert status not in ["Failed","ImagePullBackOff","ErrImagePull","CrashLoopBackOff",
                              "Error","Unknown","Job has reached the specified backoff limit"], \
            "Kubernetes job " + self.uu_name + " failed"

        self.__logger.info("Kubernetes job " + self.uu_name + " succeeded")
        self.signal_complete()

    def signal_complete(self):
        """Signal job completion for scheduler and dependent tasks.

         Touching a system file is an easy way to signal completion. example::
         .. code-block:: python

         with self.output().open('w') as output_file:
             output_file.write('')
        """
        pass


    def run(self):
        if self.runlocal:
            Task.run(self)
        else:
            # KubernetesJobTask.run()
            self._init_kubernetes()
            # Render job
            job_json = self._create_job_json()

            self.__logger.info("Submitting Kubernetes Job: " + self.uu_name)
            self.job = Compute(Carol())
            job = self.job.create_job(**job_json)
            # Track the Job (wait while active)
            self.__logger.info("Start tracking Kubernetes Job: " + self.uu_name)
            self.__track_job(job)

    def _create_job_json(self):

        job_json = {
            "env": self.job_env_variables,
            "image": self.DOCKER_IMAGE,
            "labels": {
                    "spawned_by": "luigi",
                    "luigi_task_id": self.job_uuid
                },
            "name": self.uu_name,
            "preemptible": False,
            "tenant": self.job_namespace,
            "type": "c1.micro"
        }

        return job_json
