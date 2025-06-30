import diagnoser
import killSwitch
import progressBar
# import naverSearch - this should not be here. Put it in queryProcessor
import threading
import time
import requests
import json
import re

import pprint
import traceback
from collections import deque
import ast

gatewayURL = 'http://localhost:8000/'
requestRoomname = 'mmat'

def makeURL(request, room=requestRoomname, msg=None):
    extra = ''
    if msg is not None:
        extra = '&res={}'.format(msg)
    url = '{}{}/?r={}{}'.format(gatewayURL, request, room, extra)
    return url

def postResults(ID, msg, progressObj=None, resultVal=None):
    basicURL = makeURL('results')
    basicURL += '&ID={}'.format(ID)
    basicURL += '&res={}'.format(msg)
    #print('URL: {}'.format(basicURL))
    progressJSON = { 'checkpoint':-1, 'value':'STARTED'}
    if progressObj is not None:
        progressJSON = {
            'checkpoint': progressObj.currCheckpoint(),
            'value': progressObj.currProgress()
        }
    if resultVal is None:
        resultVal = {}
    body={
        'progress': progressJSON,
        'computedResult': resultVal
    }
    try:
        response = requests.post(basicURL, json=body).json()
    except Exception as e:
        diagnoser.log('requests got an error')
        diagnoser.log(traceback.format_exc())
    #diagnoser.log('serverResponse:\n{}'.format(pprint.pformat(response)))

global roomMade
roomMade = False
roomCheckMutex = threading.Lock()

def isOnline():
    global roomMade 
    with roomCheckMutex:
        return roomMade 

def updateServerRoomCondition():
    global roomMade
    url = makeURL('status')
    # we have to call request.post for pong
    try:
        diagnoser.log('[serverConnector.py/updateServerRoomCondition()]checking server')
        response = requests.get(url).json()
        diagnoser.log('serverResponse:\n{}'.format(pprint.pformat(response)))
        roomInServer = False
        serverResponses = response['res'].split('\n')
        for line in serverResponses:
            diagnoser.log('Line: {}'.format(line))
            diagnoser.log('conditions: {} {}'.format(line.startswith('room'), requestRoomname in line))
            if line.startswith('room') and requestRoomname in line:
                roomInServer = True
                break
        if roomInServer:
            diagnoser.log('Found room scraper_room')
            roomMade = True
        else:
            createRoom()
    except Exception as e:
        diagnoser.log('requests got an error')
        diagnoser.log(traceback.format_exc())

def serverStatusJob():
    global roomMade
    while killSwitch.isOkay():
        with roomCheckMutex:
            diagnoser.log('>>>[SERVER STATUS]roomMade before: {}'.format(roomMade))
        updateServerRoomCondition()
        with roomCheckMutex:
            diagnoser.log('>>>[SERVER STATUS]roomMade after: {}'.format(roomMade))

        pingKey = getPingKey()
        if pingKey is not None and len(pingKey) > 0:
            postResults(pingKey, 'pong')

        time.sleep(1)

def start():
    serverStatusThread = threading.Thread(target=serverStatusJob)
    serverStatusThread.daemon = True
    serverStatusThread.start()
    return serverStatusThread

def reset():
    with roomCheckMutex:
        roomMade = False

'''
The format is:
{
    'query': <query>, 
    'ID': <ID>,
    
    # vvv deprecated
    # 'progress': <progressObj>
}
'''
# this will start the rooms necessary for this application
def createRoom():
    global roomMade
    url = makeURL('room')
    try:
        diagnoser.log('[serverConnector.py/createRoom()]Making room:\n{}'.format(url))
        response = requests.post(url).json()
        diagnoser.log('serverResponse:\n{}'.format(pprint.pformat(response)))
    except Exception as e:
        diagnoser.log('Cannot create room')
        diagnoser.log(traceback.format_exc())

    #print("Locking in createRoom")
    with roomCheckMutex:
        roomMade = True
    #print("releasing in createRoom")
    
def getPingKey():
    #print("Locking in getPingKey()")
    with roomCheckMutex:
        global roomMade
        if not roomMade:
            diagnoser.log('[serverConnector.py/getPingKey()]Room is not made yet!')
            #print("releasing in getPingKey()")
            return None
    #print("releasing in getPingKey()")

    diagnoser.log("[serverConnector.py/getPingKey()]is there ping?")
    url = makeURL('broadcast')
    #print("getting: {}".format(url))

    '''
    note that the form is something like
    {'room': 'scraper_requests', 'res': {'results': {}}}
    '''
    retVal = ''
    try:
        diagnoser.log('[serverConnector.py/getPingKey()]Room broadcast:\n{}'.format(url))
        response = requests.get(url).json() #['res']
        diagnoser.log('serverResponse:\n{}'.format(pprint.pformat(response)))
        #print('Response is: {}'.format(response))
        #diagnoser.log('trying to convert: {{{}}} (type:{})'.format(response['res'], type(response['res'])))
        # response['res'] = ast.literal_eval(response['res'])
        for key in response['res']:
            if key == 'results':
                continue
            elif response['res'][key] == 'ping':
                retVal = key 
                break
    except Exception as e:
        diagnoser.log('request got error!')
        diagnoser.log(traceback.format_exc())

    return retVal

# this will read the queries from room
# and simply return all requests and their IDs (to post responses)
def pollRooms():
    #print("locking in pollRooms()")
    with roomCheckMutex:
        global roomMade
        if not roomMade:
            diagnoser.log('[serverConnector.py/pollRooms()]Room is not made yet!')
            #print("releasing in pollRooms()")
            return None
    #print("releasing in pollRooms()")

    url = makeURL('broadcast')
    #print("getting: {}".format(url))
    '''
    note that the form is something like
    {'room': 'mmat', 'res': {...}}
    '''
    response = None
    try:
        diagnoser.log('[serverConnector.py/pollRooms()]Room broadcast:\n{}'.format(url))
        response = requests.get(url).json()#['res']
        diagnoser.log('serverResponse:\n{}'.format(pprint.pformat(response)))
    except Exception as e:
        diagnoser.log('error in request')
        diagnoser.log(traceback.format_exc())
        return None
    #print('RESPONSE:',response)

    if response is None:
        # negative space, it should go to exception right?
        #print("[serverConnector.py/pollRooms()]NEGATIVE SPACE")
        diagnoser.CrashWithLog("NEGATIVE SPACE")
        sys.exit(1)

    inRooms = []
    for key in response['res']:
        if key == 'results':
            continue
        if isinstance(response['res'], str):
            print('You got a response:', response['res'])
        elif response['res'][key] == 'ping':
            # responseWithPong() needs to be called in a different thread
            # for decouple's sake
            #respondWithPong(key)
            pass
        else:
            query = {
                'query': response['res'][key],
                'ID': key
                #'progress': progressBar.Progress()
            }
            inRooms.append(query)
    return inRooms


    #print("Query: ", awaitingQuery)

# turns out we can keep resolving a broadcast 
# on the server. 
# this function just calls the results api
# and updates the progress value
def updateProgress(ID, progressObj):
    postResults(ID, 'PROGRESS', progressObj = progressObj)

if __name__ == "__main__":
    print("THIS IS NOT THE MAIN APPLICATION")
    print('Running tester just for the server connector.')
    print('QUIT THIS NOW IF YOU ARE NOT TESTING')
    time.sleep(3)

    diagnoser.setName('serverConnector_test')
    diagnoser.log('===Starting test===')

    start() # starts serverStatusJob()

    while True:
        res = input('Just chill here or type \'quit\' to leave')
        if res == 'quit':
            break