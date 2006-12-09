from logging_mixin import LoggingMixin
from simple_api_mixin import SimpleAPIMixin

class ScriptInterface(SimpleAPIMixin, LoggingMixin):

    def __init__(self, devide_app):
        self._devide_app = devide_app

        # initialise logging mixin
        LoggingMixin.__init__(self)

        print "Initialising script interface..."
        
    def handler_post_app_init(self):
        """DeVIDE-required method for interfaces."""

        pass

    def quit(self):
        pass

    def start_main_loop(self):
        self.log_message('Starting to execute script.')
        sv = self._devide_app.main_config.script_name
        mod = __import__(self._devide_app.main_config.script_name)

        # call three methods in script
        mod.setup(self)
        mod.execute(self)
        mod.finalize(self)
            
        self.log_message('Shutting down.')
        self.quit()

    
