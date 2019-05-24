from . import Tasks
import os
import logging
import sys

_carol_levels = dict(
    NOTSET="NOTSET",
    DEBUG='DEBUG',
    INFO="INFO",
    WARNING="WARN",
    WARN="WARN",
    ERROR="ERROR",
    CRITICAL="ERROR",
    FATAL="ERROR",
)


class CarolHandler(logging.StreamHandler):

    def __init__(self, carol):
        """

        Carol logger handler.

        This class can be used to log informatio in long tasks in Carol.

        :param carol: Carol object
            Carol object.

        """
        super().__init__(stream=sys.stdout)
        self.carol = carol
        self._task = Tasks(self.carol)
        self.task_id = os.getenv('LONGTASKID', None)
        self._task.task_id = self.task_id

    def _log_carol(self, record):
        msg = self.format(record)
        log_level = _carol_levels.get(record.levelname)
        self._task.add_log(msg, log_level=log_level)

    def emit(self, record):
        if self.task_id is None:
            super().emit(record)
        else:
            self._log_carol(record)
