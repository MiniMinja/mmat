import sys
import time
import threading


class Progress:
    def __init__(self, checkpoints = [], parent=None):
        self.checkpoints = checkpoints[:]
        self.p = 0
        self.c = 0
        self.start = False
        self.mutex = threading.Lock()

        self.subProgress = None
        self.parent = parent
    
    def addCheckpoint(self, name):
        with self.mutex:
            self.checkpoints.append(name)

    def currCheckpoint(self):
        with self.mutex:
            if not self.start:
                return "NOT STARTED"
            if self.subProgress is not None:
                return '{} [{}]'.format(
                    self.checkpoints[self.p],
                    self.subProgress.currCheckpoint()
                )

            if self.p == len(self.checkpoints):
                return 'COMPLETE'
            return self.checkpoints[self.p]
        
    def addSubProgress(self, subprogress):
        with self.mutex:
            self.subProgress = subprogress

    def startIt(self):
        with self.mutex:
            self.start = True
    
    def increment(self):
        with self.mutex:
            if self.start == False:
                self.start = True

            if self.subProgress is not None:
                self.subProgress.increment()
                if self.subProgress.isComplete():
                    self.subProgress = None
                else:
                    return

            if len(self.checkpoints) == 0:
                print("Please estimate total first")
                raise RuntimeError("Call addCheckpoint() first")
            
            if self.p >= len(self.checkpoints):
                print("progressed too many times")
                raise RuntimeError("Recalculate total")
            
            self.p += 1
            if (self.parent is not None and 
                (self.c == 1 or self.p == len(self.checkpoints))
                ):
                self.parent.registerFinishedSubprogress()

    def registerFinishedSubprogress(self):
        self.subProgress = None

        if len(self.checkpoints) == 0:
                print("Please estimate total first")
                raise RuntimeError("Call addCheckpoint() first")
            
        if self.p >= len(self.checkpoints):
            print("progressed too many times")
            raise RuntimeError("Recalculate total")
        
        self.p += 1

        if (self.parent is not None and 
                (self.c == 1 or self.p == len(self.checkpoints))
            ):
            self.parent.registerFinishedSubprogress()
            
    
    # a shortcut in case you miscalculated
    # not to be used often
    # - use complete if possible instead 
    def finish(self):
        with self.mutex:
            self.p = len(self.checkpoints) 
    
    def currProgress(self):
        with self.mutex:
            if not self.start:
                return 0
            elif self.c == 1 or self.p == len(self.checkpoints):
                return 100
            else:
                subProgressVal = 0
                if self.subProgress is not None:
                    # it should be the progress of the subprogress 
                    # and then scaled down to a single increment of 
                    # the current progress which is 1 / # currProgress
                    subProgressVal = self.subProgress.currProgress()/100 / len(self.checkpoints)
                return int((self.p / len(self.checkpoints) + subProgressVal) * 100)
    
    def started(self):
        with self.mutex:
            return self.start

    def complete(self):
        with self.mutex:
            self.c = 1

            if (self.parent is not None and 
                (self.c == 1 or self.p == len(self.checkpoints))
            ):
                self.parent.registerFinishedSubprogress()
    
    def isComplete(self):
        with self.mutex:
            if not self.start:
                return False
            return self.c == 1 or self.p == len(self.checkpoints)

    def reset(self):
        with self.mutex:
            self.p = 0
            self.c = 0
            self.checkpoints.clear()
            self.subProgress = None

def getProgressBarFormatStr(p):
    return '{}:\n[{:>100s}] {}%'.format(p.currCheckpoint(), '#' * p.currProgress(), p.currProgress())

def getProgressBarTree(p, level=1):
    outputList = ['Tree:']
    outputList = ['{}{}\n'.format('\t'*(level-1), str(p))]
    for checkpoint in p.checkpoints:
        if checkpoint == p.checkpoints[p.p]:
            outputList.append('\n{}[{}]'.format('\t'*level, checkpoint))
            if p.subProgress is not None:
                outputList.append(getProgressBarTree(p.subProgress, level=level+1))
        else:
            outputList.append('\n{}{}'.format('\t'*level, checkpoint))
    return ''.join(outputList)

def printProgressBar(p):
    print('{}:\n[{:>100s}] {}%'.format(p.currCheckpoint(), '#' * p.currProgress(), p.currProgress()))