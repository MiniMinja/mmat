"""
simply creates a folder called 'mlogs' in your home directory
and prints logs that you speficy, or timing of executions of functions
should print out where the files is stored when you use this

Constants:
logDir -> the directory of the mlogs 
name -> this can be changed, but it's set to whatever name you want to store your logs
MAXOUTPUTLENGTH -> sometimes text files can get hard to read when the error message gets
        too long. So I made a 500 character cap, and if you want to see the full output
        the message should tell you which file has the full message
"""
import time
import datetime
import os
import sys
import uuid
import traceback

global logDir, name
logDir = os.path.join(os.path.expanduser('~'), 'mlogs')
name = 'log'

MAXOUTPUTLENGTH = 500

def setName(newname):
    """
    sets the name of the log files
    """
    global name
    name = newname

def mdate():
    """
    for getting todays date
    """
    return datetime.datetime.now().strftime("%Y%m%d")

def mnow():
    """
    for getting the time    
    """
    return datetime.datetime.now().strftime("%H:%M:%S")

def mlogPath():
    """
    its the path to todays current log file
    """
    global name
    return os.path.join(logDir, '{}_{}.log'.format(name, mdate()))

def generateHelperFile():
    """
    this is for the case when a message exceeds the character limit
    """
    helperPath = os.path.join(logDir, '{}.log'.format(uuid.uuid4()))
    with open(helperPath, 'w', encoding='utf8') as f:
        pass
    return helperPath

def checkAndSetLog():
    """
    This is mostly for init. this should be called every single time
    when trying to log
    """
    global name
    path = mlogPath()
    if not os.path.exists(logDir):
        os.mkdir(logDir)
    if not os.path.exists(path):
        with open(path, 'w', encoding='utf8') as f:
            print('Starting {}! check logs at:\n\t{}'.format(name, path))
    return path

def logJob(func, *args, **kwargs):
    """
    you can pass a function and its arguments (both the regular
    arguments and the defaulted arguments) to try and print out
    what values it got. It also runs a try except in an attempt
    to avoid complete crashes whilst also printing out what happened
    """
    path = checkAndSetLog()
    retVal = "Failure...? -> check diagnoser.py > logJob()"
    try:
        retVal = func(*args, **kwargs)
    except Exception as e:
        retVal = 'An exception occured:\n{}'.format(traceback.format_exc())
    with open(path, 'a', encoding='utf8') as f:
        f.write('|{}|\tRan {}\n'.format(mnow(), func.__name__))
        retVal = repr(retVal)
        if len(retVal) > MAXOUTPUTLENGTH:
            toShow = retVal[:MAXOUTPUTLENGTH]
            f.write('\t\t-> {}\n'.format(toShow))
            helperPath = generateHelperFile()
            with open(helperPath, 'a', encoding='utf8') as hf:
                hf.write(retVal)
                hf.write('\n')
            f.write('...Output truncated. Full output at {}'.format(helperPath))
        else:
            f.write('\t\t-> {}\n'.format(retVal))

def logDuration(func, *args, **kwargs): 
    """
    it's a timed version of logJob() where it tries to 
    run a function (you can add any args or defaulted arguments)
    and it should run like logJob() (with the try catch as well
    making it move past errors, whilst outputting it)
    but also adds a time to the end of the job
    """
    path = checkAndSetLog()
    retVal = "Failure...? -> check diagnoser.py > logDuration() [retVal not set]"
    timeElapsed = -1
    try:
        startTime = time.time()
        retVal = func(*args, **kwargs)
        timeElapsed = time.time() - startTime
    except Exception as e:
        retVal = 'An exception occured:\n{}'.format(traceback.format_exc())
        #print(traceback.format_exc())
    with open(path, 'a', encoding='utf8') as f:
        f.write('|{}|\tRan {}\n'.format(mnow(), func.__name__))
        f.write('|{}|\tArgs=[{}]\n'.format(mnow(), args))
        f.write('|{}|\tKWArgs=[{}]\n'.format(mnow(), kwargs))
        retVal = repr(retVal)
        if len(retVal) > MAXOUTPUTLENGTH:
            toShow = retVal[:MAXOUTPUTLENGTH]
            f.write('\t\t-> {}\n'.format(toShow))
            helperPath = generateHelperFile()
            with open(helperPath, 'a', encoding='utf8') as hf:
                hf.write(retVal)
                hf.write('\n')
            f.write('...Output truncated. Full output at {}'.format(helperPath))
        else:
            f.write('\t\t-> {}\n'.format(retVal))
        if timeElapsed == -1:
            f.write('Failure...? -> check diagnoser.py > logDuration() [timeElapsed = -1?]\n')
        else:
            f.write('|{}|\t Process took {}s\n'.format(mnow(), timeElapsed))
            f.write('\t\t>> which is {}min\n'.format(timeElapsed/60))
            f.write('\t\t>> which is {}hrs\n'.format(timeElapsed/60/60))

def log(str_val):
    """
    Not all everything is a job, sometimes you may want to just
    log some state and see what happened in what order. so 
    that's what this is (it's a print)
    """
    path = checkAndSetLog()
    with open(path, 'a', encoding='utf8') as f:
        f.write('|{}|\t{}'.format(mnow(), str(str_val)))
        f.write('\n')

def CrashWithLog(textToShow):
    """
    this is whenever you want to quick the program, but in a way that it logs the file
    with hopefully as much information as possible as to which state the program was in before
    and traceback, etc
    """
    path = checkAndSetLog()
    with open(path, 'a', encoding='utf8') as f:
        f.write('|{}| We got a crash. here is the text\n'.format(mnow()))
        f.write('>>')
        f.write(textToShow)
        f.write('\n')
        f.write('---TRACEBACK---\n')
        f.write(traceback.format_exc())
    sys.exit(1)