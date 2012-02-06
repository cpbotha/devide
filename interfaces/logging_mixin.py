# logging mixin for use by DeVIDE interfaces

import logging
import sys

class LoggingMixin:

    def __init__(self):
        # this sets things up for logging to stderr
        logging.basicConfig(level=logging.DEBUG,
                            format='%(asctime)s %(levelname)s %(message)s',
                            stream=sys.stdout)

        file_handler = logging.FileHandler('devide.log', 'w')
        file_handler.setLevel(logging.DEBUG)
        formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
        file_handler.setFormatter(formatter)
        # add file handler to root logger
        logging.getLogger('').addHandler(file_handler)
        
    def log_error_list(self, msgs):
        """Log a list of strings as error.

        This method must be supplied by all interfaces.
        """

        for msg in msgs:
            logging.error(msg)

    def log_error(self, message):
        """Log a single string as error.

        This method must be supplied by all interfaces.
        """

        logging.error(message)

    def log_info(self, message, timeStamp=True):
        """Log information.

        This will simply go into the log window.
        """

        # we'll always follow the format set by the logger setup in the ctor
        logging.info(message)

    def log_message(self, message, timeStamp=True):
        """Use this to log a message that has to be shown to the user in
        for example a message box.
        """

        logging.info('MESSAGE: %s' % (message,))

    def log_warning(self, message, timeStamp=True):
        logging.warning(message)

    def set_progress(self, progress, message, noTime=False):
        # we also output an informative message to standard out
        # in cases where DeVIDE is very busy, this is quite
        # handy.
        logging.info( "PROGRESS: %s: %.2f" % (message, progress) )
        
        
