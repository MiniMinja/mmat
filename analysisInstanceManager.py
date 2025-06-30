# <Imports>
import diagnoser
import threading
from analyzer import analyzeWithAllTaggers
from commandQueue import commandQueue
import serverConnector
from typing import List, Dict, Optional
import json

# <Constants – ALL_CAPS>
MAX_THREADS = 10

# <Classes – CamelCasingAllClasses>
class JobMail:
    def __init__(self):
        self.textInputs: List[Optional[str]] = [None] * MAX_THREADS
        self.inputLocks: List[threading.Lock] = [threading.Lock() for _ in range(MAX_THREADS)]

        self.outputs: List[Optional[Dict[str, List[str]]]] = [None] * MAX_THREADS
        self.isFinished: List[bool] = [False] * MAX_THREADS
        self.outputLocks: List[threading.Lock] = [threading.Lock() for _ in range(MAX_THREADS)]

        # Launch thread pool
        for i in range(MAX_THREADS):
            thread = threading.Thread(target=self._analyzerThread, args=(i,), daemon=True)
            thread.start()

    def _analyzerThread(self, index: int):
        while True:
            with self.inputLocks[index]:
                text = self.textInputs[index]

            if text is not None:
                try:
                    result = analyzeWithAllTaggers(text)
                except Exception as e:
                    result = {"error": [str(e)]}

                with self.outputLocks[index]:
                    self.outputs[index] = result
                    self.isFinished[index] = True

                with self.inputLocks[index]:
                    self.textInputs[index] = None

            threading.Event().wait(0.05)

    def submitTextJob(self, text: str) -> int:
        for i in range(MAX_THREADS):
            with self.inputLocks[i]:
                if self.textInputs[i] is None:
                    self.textInputs[i] = text
                    with self.outputLocks[i]:
                        self.outputs[i] = None
                        self.isFinished[i] = False
                    return i
        raise RuntimeError("All analyzer threads are busy.")

    def getJobOutput(self, index: int) -> Optional[Dict[str, List[str]]]:
        with self.outputLocks[index]:
            return self.outputs[index] if self.isFinished[index] else None

    def isJobFinished(self, index: int) -> bool:
        with self.outputLocks[index]:
            return self.isFinished[index]


# <Functions – camelCasingAllNames>
def extractMessageFromCommand(rawCommand: str) -> str:
    if "@body@" in rawCommand:
        try:
            _, bodyJson = rawCommand.split("@body@", 1)
            data = json.loads(bodyJson)
            return data.get("computedResult", {}).get("message", "")
        except Exception as e:
            diagnoser.log(f"[ERROR] Failed to parse JSON in command: {e}")
            return ""
    return rawCommand  # fallback: treat it as plain text

def instanceJob(jobMail: JobMail):
    """
    Continuously pulls text from commandQueue and sends to open slot in jobMail.
    Waits for analysis and submits the result back to the server.
    """
    while True:
        if commandQueue:
            try:
                item = commandQueue.popleft()
                rawCommand = item['query']
                requestID = item['ID']

                diagnoser.log('[INFO] GOT FULL TEXT: {}'.format(rawCommand))
                print('[O o O] !! Got some input. processing...')
                print('>> {}'.format(rawCommand))
                text = extractMessageFromCommand(rawCommand)
                print('--> {}'.format(text))

                jobIndex = jobMail.submitTextJob(text)
                diagnoser.log(f"[INFO] Job submitted at slot {jobIndex} for text: {text}")

                # Poll until job is done
                while not jobMail.isJobFinished(jobIndex):
                    threading.Event().wait(0.1)

                print('[- o -] ~~ finished process. exporting...')
                result = jobMail.getJobOutput(jobIndex)
                diagnoser.log('>>>> Output of job is: {}'.format(result))
                if result:
                    serverConnector.postResults(requestID, 'RESULTS', resultVal=result)
                    diagnoser.log(f"[INFO] Posted results for job ID {requestID}")
                    print['[* v *] ~! check your output']
                else:
                    diagnoser.log(f"[WARN] No result for job ID {requestID}")
                    print('[X ^ X] !! error')
            except RuntimeError:
                threading.Event().wait(0.1)
            except Exception as e:
                diagnoser.log(f"[ERROR] Failed job execution: {e}")
        else:
            threading.Event().wait(0.05)

# <main function>
def main():
    jobMail = JobMail()

    # Start job feeder thread
    managerThread = threading.Thread(target=instanceJob, args=(jobMail,), daemon=True)
    managerThread.start()

    diagnoser.log("[MMAT Manager] System initialized and awaiting commands...")

    # Demo polling (remove or replace in production)
    import time
    while True:
        for i in range(MAX_THREADS):
            if jobMail.isJobFinished(i):
                output = jobMail.getJobOutput(i)
                diagnoser.log(f"[Slot {i} Completed] → {output}")
        time.sleep(1)

if __name__ == "__main__":
    main()