try: import keyboard
except ImportError: keyboard=None
import time
import numpy as np
import matplotlib.pyplot as pp
from azdk.azdksocket import AzdkSocket, ServerCmd, PDSServerCmd, AzdkServerCmd, call_azdk_cmd, PDSServerState , PDSServerCommands, AzdkServerCommands
from azdk.azdkdb import AzdkDB, quatntime_from_bytes , AzdkCmd,WState
from threading import Thread, Lock

class Test(Thread):


    def run(self):
        pds_find_focus_s()



def pds_find_focus_s():
    # AZDK Database
    db = AzdkDB('./AZDKHost.xml')

    #azdkserver = ('127.0.0.1', 53512)
    #pdsserver = ('127.0.0.1', 55555)

    azdkserver = ('25.22.111.12', 56001)
    pdsserver = ('25.22.111.12', 55555)

    conn_name = 'bogdan-pds_find_focus.py'

    # PDSServer connection
    pds = AzdkSocket(pdsserver[0], pdsserver[1], PDSServerCommands)
    pds.verbose = True
    pds.start()
    if not pds.waitStarted(): return
    pds.setName(conn_name)
    pcmdSetState = PDSServerState(PDSServerState.STARS, True).cmd()
    pds.enqueue(pcmdSetState)
    pds.waitforanswer(pcmdSetState)

    # PDS commands
    pcmdSetFocus = ServerCmd(PDSServerCommands.SET_FOCUS)
    pcmdSetFocus.params = [0]

    # AzdkServer connection
    azs = AzdkSocket(azdkserver[0], azdkserver[1], AzdkServerCommands)
    azs.verbose = True
    azs.start()
    if not azs.waitStarted():
        pds.stop()
        return
    azs.setName(conn_name)

    # Azdk commands
    cmdSetIdleMode = db.createcmd(48)
    cmdSetAutoMode = db.createcmd(49)
    cmdChangeFlags = db.createcmd(32, [0, 1<<5, 0, 0])

    ws = WState()

    getStateTimeout = 2.0
    focusIterator = iter(np.arange(33.5, 34.5, 0.05))
    focusTimeout = 3.0

    focusTimer = 0
    getStateTimer = 0

    cmdTimeout = 0.25
    # AZDK set notifications
    cmdSetupNotif = db.createcmd(76, [1, (1<<0)|(1<<1)|(1<<6), 500, 0])
    while not call_azdk_cmd(azs, cmdSetupNotif, cmdTimeout): pass
    # AZDK set idle mode
    while not call_azdk_cmd(azs, cmdSetIdleMode, cmdTimeout): pass
    # AZDK change flag
    while not call_azdk_cmd(azs, cmdChangeFlags, cmdTimeout): pass
    # AZDK set auto mode
    call_azdk_cmd(azs, cmdSetAutoMode, cmdTimeout)

    focuses = []
    idcounts = []
    focus = None

    while pds.is_alive() and azs.is_alive():
        curTime = time.perf_counter()
        if curTime > focusTimer:
            try:
                focus = next(focusIterator)
            except StopIteration:
                break
            pcmdSetFocus.params[0] = focus
            pds.enqueue(pcmdSetFocus)
            print(f'PDS focus set to {focus:.2f}')
            focusTimer = curTime + focusTimeout
            getStateTimer = curTime + getStateTimeout
        cmd = azs.waitforanswer()
        if cmd:
            if cmd.code == AzdkServerCommands.DEVICE_CMD.value:
                match cmd.params[0] & 0x7F:
                    case 113 | 16:
                        ws.from_buffer(cmd.params[1])
                        if curTime > getStateTimer:
                            if focus:
                                print(f'focus={focus}, idcnt={ws.calerr}')
                                focuses.append(focus)
                                idcounts.append(ws.calerr)
                                focusTimer = curTime
                                focus = None
            else:
                print(cmd)
        if keyboard and keyboard.is_pressed('q'):
            break

    pds.stop()
    azs.stop()

    pp.scatter(focuses, idcounts, linewidths=0.1)
    pp.show()

if __name__ == "__main__":
    pds_find_focus_s()
