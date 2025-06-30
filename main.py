# <Imports>
import threading
import time
import diagnoser
import killSwitch
import serverConnector
import commandQueue
from analysisInstanceManager import JobMail, instanceJob

# <Constants – ALL_CAPS>
CHECK_INTERVAL = 2  # seconds between health checks
THREAD_LABELS = ["server", "commandQueue", "analyzer"]

# <Functions – camelCasingAllNames>
def safeThreadStart(targetFn, name: str, *args):
    def threadWrapper():
        try:
            targetFn(*args)
        except Exception as e:
            diagnoser.log(f"[FATAL] {name} thread crashed:\n{e}")
            killSwitch._main_kill_switch.kill()
    thread = threading.Thread(target=threadWrapper, name=name)
    thread.daemon = True
    thread.start()
    return thread

def restartIfDead(threadRef, label, restartFn):
    if not threadRef.is_alive():
        diagnoser.log(f"[WARN] {label} thread died. Restarting...")
        return safeThreadStart(restartFn, label)
    return threadRef

def monitorThreads(threadRefs, jobMail):
    while killSwitch.isOkay():
        time.sleep(CHECK_INTERVAL)
        threadRefs['server'] = restartIfDead(threadRefs['server'], 'server', serverConnector.serverStatusJob)
        threadRefs['commandQueue'] = restartIfDead(threadRefs['commandQueue'], 'commandQueue', commandQueue.pollJob)
        threadRefs['analyzer'] = restartIfDead(threadRefs['analyzer'], 'analyzer', instanceJob)

# <main function>
def main():
    diagnoser.setName("mmat_main")
    diagnoser.log("=== MMAT SYSTEM START ===")

    # Start components
    serverThread = safeThreadStart(serverConnector.serverStatusJob, "server")
    commandQueueThread = safeThreadStart(commandQueue.pollJob, "commandQueue")

    jobMail = JobMail()
    analyzerThread = safeThreadStart(instanceJob, "analyzer", jobMail)

    # Monitor and recover
    threads = {
        'server': serverThread,
        'commandQueue': commandQueueThread,
        'analyzer': analyzerThread
    }
    monitorThreads(threads, jobMail)

if __name__ == "__main__":
    main()