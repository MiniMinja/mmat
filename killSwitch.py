import threading
class _KillSwitch:
    def __init__(self):
        self.mutex = threading.Lock()

        self.isOkay = True
    
    def isKilled(self):
        with self.mutex:
            return not self.isOkay
    
    def kill(self):
        with self.mutex:
            self.isOkay = False
    
    def reset(self):
        with self.mutex:
            self.isOkay = True

global _main_kill_switch
_main_kill_switch = _KillSwitch()
def isOkay():
    return not _main_kill_switch.isKilled()