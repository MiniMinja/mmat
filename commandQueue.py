import diagnoser
import killSwitch
import serverConnector

from collections import deque
import threading
import time


global commandQueue, queueMutex
commandQueue = deque()
queueMutex = threading.Lock()

COMMANDTIMER = 10
# idExistenceTime acts like a "cooldown"
# since serverConnector.pollRooms() will grab
# currently persisting commands, there is a
# risk that commandQueue list will grow with the 
# same ID, so we reduce the rate in which it grows
# by adding a "add this to our list"-cooldown
# then we will only have maybe 1 (at most 2) of
# of a unique query in commandQueue
idExistenceTime = {}

def getNextCommand():
    with queueMutex:
        if len(commandQueue) == 0:
            return None
        return commandQueue.popleft()

def pollJob():
    '''this is going to run a while loop of pollRooms'''
    while killSwitch.isOkay:
        time.sleep(1)
        # remove all items from the idExistenceTime that exceeded timer
        toRemove = []
        for key in idExistenceTime:
            elapsedTime = time.time() - idExistenceTime[key]
            if elapsedTime > COMMANDTIMER:
                toRemove.append(key)
        for key in toRemove:
            del idExistenceTime[key]

        currQueries = serverConnector.pollRooms()
        if not currQueries:
            # i.e. currQueries is empty
            continue
        #print("CURRENT QUERIES: {}".format(currQueries))
        #print("EXISTENCE TIMER: {}".format(idExistenceTime))
        # add the non-cooldown queries from the pollRooms
        for query in currQueries:
            if query['ID'] not in idExistenceTime:
                with queueMutex:
                    commandQueue.append(query)
                idExistenceTime[query['ID']] = time.time()

def start():
    '''this loads and starts the pollJob loop thread'''
    pollThread = threading.Thread(target = pollJob)
    pollThread.daemon = True
    pollThread.start()
    return pollThread

def reset():
    with queueMutex:
        commandQueue = deque()
        idExistenceTime = {}

if __name__=="__main__":
    print('''
This is a test for commandQueue. THIS IS A TEST
if you want to run the main application quit now
in 3 seconds... 
''')
    time.sleep(3)

    diagnoser.setName('commandQueue_test')
    diagnoser.log('===starting commandQueue Test===')

    serverConnector.start()

    start()

    while True:
        print('\'quit\' to quit')
        print('\'queue\' to show current commands')
        ui = input('>>')

        if ui == 'quit':
            break
        elif ui == 'queue':
            print('\nTHE CURRENT QUEUE IS:')
            with queueMutex:
                for query in commandQueue:
                    print('\t{}'.format(query))
            print()