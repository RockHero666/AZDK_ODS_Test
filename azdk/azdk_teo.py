import time
try: import keyboard
except ImportError: keyboard=None
import struct
from threading import Thread, Lock
from datetime import datetime
from enum import Enum
import numpy as np
from azdk.linalg import Quaternion, Vector
from azdk.azdksocket import AzdkSocket, ServerCmd, PDSServerCmd, AzdkServerCmd, AzdkCmd, call_azdk_cmd
from azdk.azdkdb import AzdkDB, quatntime_from_bytes

R2D = 180.0 / np.pi

class FramePos:
    def __init__(self, x=0.0, y=0.0) -> None:
        self.x = x
        self.y = y

    def __str__(self) -> str:
        return f'[{self.x:.2f}, {self.y:.2f}]'

    def todir(self, fparams : tuple):
        if fparams is None or np.isnan(self.x):
            return Vector()
        p = Vector(
            fparams[1] - self.x,
            fparams[2] - self.y,
            fparams[0]
        ).normalized()
        return p

    @classmethod
    def fromdir(cls, vdir : Vector, fparams : tuple):
        if fparams is None or vdir.z < 0.5:
            return cls(np.nan, np.nan)
        px = fparams[1] - vdir.x / vdir.z * fparams[0]
        py = fparams[2] - vdir.y / vdir.z * fparams[0]
        if px < 0 or px > fparams[3] or py < 0 or py > fparams[4]:
            return cls(np.nan, np.nan)
        return cls(px, py)

class DirAngles:
    def __init__(self, vdir : Vector) -> None:
        vdir = vdir.normalized()
        self.ra = np.arctan2(vdir.x, vdir.z) * R2D
        self.de = np.arcsin(vdir.y) * R2D

    def __str__(self) -> str:
        return f'({self.ra:.6f}, {self.de:.6f})'

    def todir(self):
        z = np.cos(self.de / R2D)
        x = np.cos(self.ra / R2D)*z
        y = np.sin(self.ra / R2D)*z
        z = np.sin(self.de / R2D)
        return Vector(x, y, z)

class TargetObject:
    class POS_TYPE(Enum):
        NONE = 0
        DIR = 1         # direction vector
        ANGLES = 2      # direction angles
        FRAME = 3       # frame coordinates

    ptype = POS_TYPE.ANGLES

    def __init__(self):
        self.signal = 0
        self.xFWHM = 0.0
        self.yFWHM = 0.0
        self.quat = Quaternion()
        self.time = datetime.now()
        self.vdir = Vector()
        self.fpos = FramePos()
        self.fparams = None
        self.rect = None

    def from_bytes(self, d : bytes):
        if len(d) < 20: return False
        s = struct.unpack('I2H3i', d[:20])
        quat, time = quatntime_from_bytes(d[20:])
        if time:
            self.quat, self.time = quat, time
        if s[0] == 0: return False
        self.signal = s[0]
        self.xFWHM = s[1]
        self.yFWHM = s[2]
        self.vdir = Vector(s[3], s[4], s[5]).normalized()
        self.calcframepos()
        self.calcrect()
        return True

    def __str__(self) -> str:
        s = 'TEO: '
        s += f'f={self.signal}, pos=' + str(self.pos())
        if self.time is not None:
            s += ', quat=' + str(self.quat)
            s += ', time=' + str(self.time)
        return s

    def set_fparams(self, focus : float, xcenter : float, ycenter : float,
                    width : int, height : int):
        self.fparams = (focus, xcenter, ycenter, width, height)

    def calcframepos(self, fparams : tuple = None):
        self.fparams = fparams = fparams or self.fparams
        if fparams is None: return None
        self.fpos = FramePos.fromdir(self.vdir, self.fparams)
        return self.fpos

    def calcdirection(self, fparams : tuple = None):
        self.fparams = fparams = fparams or self.fparams
        if fparams is None: return None
        self.vdir = self.fpos.todir(self.fparams)
        return self.vdir

    def calcrect(self, width : float = None, height : float = None):
        if np.isnan(self.fpos.x): return None
        if self.fparams is None: return None
        width = width or self.xFWHM*3
        height = height or width
        if self.xFWHM > 0 and width < self.xFWHM*3:
            width = self.xFWHM*3
        if self.yFWHM > 0 and height < self.yFWHM*3:
            height = self.yFWHM*3
        width //= 2
        height //= 2
        if self.fpos.x - width < 0: return None
        if self.fpos.x + width > self.fparams[3]: return None
        if self.fpos.y - height < 0: return None
        if self.fpos.y + height > self.fparams[4]: return None
        if width > 0 and height > 0:
            rect = (self.fpos.x, self.fpos.y, width*2 + 1, height*2 + 1)
        else:
            rect = (self.fpos.x, self.fpos.y)
        self.rect = [np.uint16(x) for x in rect]
        return True

    def pos(self, ptype = None):
        ptype = ptype or self.ptype or self.POS_TYPE.DIR
        match ptype:
            case self.POS_TYPE.DIR:
                return self.vdir
            case self.POS_TYPE.ANGLES:
                return DirAngles(self.vdir)
            case self.POS_TYPE.FRAME:
                if np.isnan(self.fpos.y):
                    self.calcframepos()
                return self.fpos
        return None

    @classmethod
    def from_teo_bytes(cls, d : bytes):
        if len(d) < 44: return None
        teo = cls()
        teo.from_bytes(d)
        return teo

    @classmethod
    def from_phc_list(cls, d : bytes):
        if len(d) < 12: return None
        s = struct.unpack('I4H', d[:12])
        teo = cls()
        teo.fpos = FramePos(s[1]/64.0, s[2]/64.0)
        teo.signal = s[3]
        if (s[0] & (1<<30)) and len(d) > (24+12):
            teo.quat, teo.time = quatntime_from_bytes(d[-24:])
        else:
            teo.time = None
        return teo

class TargetObjectDriver(Thread):
    atol = 5e-6
    def __init__(self, start_pos : Vector = None) -> None:
        super().__init__()
        self.t_start = time.perf_counter()
        self.pos_start = start_pos if start_pos else Vector()
        self.pos = self.pos_start
        self.angvelDir = Vector(0, 0, 1)
        self.angvelSpeed = 0.0
        self.isglobal = False
        self.pds = None
        self.port = 55513
        self._mutex = Lock()

    def rotationPosCmd(self, isglobal=False, restart=False):
        t = time.perf_counter()

        if not self._mutex.acquire(): return None
        if restart: self.t_start = t
        t -= self.t_start
        q = Quaternion(self.angvelDir, self.angvelSpeed*t)
        self._mutex.release()

        pos = q.rotate(self.pos_start)

        a = pos.dot(self.pos) / pos.length / self.pos.length
        a = np.arccos(a)
        if a < self.atol: return None
        self.pos = pos

        cmdSetTeoPos = ServerCmd(PDSServerCmd.SET_TEO_POS)
        cmdSetTeoPos.params = [pos]
        cmdSetTeoPos.flags[4] = isglobal
        cmdSetTeoPos.flags[2] = True        # Тихая команда
        return cmdSetTeoPos

    def run(self):
        teoSetTimer = time.perf_counter()
        teoSetTimout = 0.01

        # PDSServer connection
        pds = AzdkSocket('25.33.41.224', self.port, PDSServerCmd)
        pds.start()
        pds.setName('teo_testing')
        if not pds.waitStarted(): return
        pds.enqueue(ServerCmd(PDSServerCmd.SET_STATE, [np.uint32(512)]))

        print('Target object driver started')

        cmd = self.rotationPosCmd(restart=True)
        pds.enqueue(cmd)
        pds.waitforanswer(cmd)
        self.pds = pds

        while pds.is_alive():
            time.sleep(0.01)
            curTime = time.perf_counter()
            if curTime > teoSetTimer + teoSetTimout:
                cmd = self.rotationPosCmd()
                teoSetTimer = curTime + teoSetTimout
                if cmd:
                    pds.enqueue(cmd)
                    pds.waitforanswer(cmd, 0.01)
                #print('TEO_SET: ' + str(cmd.params[0].normalized()))
            cmdok = pds.waitforanswer(timeout=0.1)
            if cmdok: print('PDS - ' + str(cmdok))

        pds.stop()

    def stop(self):
        if self.pds and self.pds.is_alive():
            self.pds.stop()
        if self.is_alive():
            self.join()
        print('Target object driver stopped')

    def waitStarted(self, timeout=1.0):
        time.sleep(0.1)
        ts = time.perf_counter()
        while not self.is_alive() or self.pds is None:
            if time.perf_counter() > ts + timeout:
                return False
        return True

    def setRotation(self, angvel : Vector):
        if not self._mutex.acquire(): return None
        self.angvelSpeed = angvel.normalize()
        self.angvelDir = angvel
        self.t_start = time.perf_counter()
        self._mutex.release()

def waitForAzdkNotification(azs : AzdkSocket, cmd : AzdkCmd, db : AzdkDB, timeout=1e300):
    endTime = time.perf_counter() + timeout
    while time.perf_counter() < endTime:
        scmd = azs.waitforanswer(None, timeout)
        if scmd and scmd.code == AzdkServerCmd.DEVICE_CMD.value:
            nparams = len(scmd.params)
            if nparams == 0: continue
            if scmd.params[0] != cmd.code: continue
            cmd.answer = db.answer(scmd.params[0], scmd.params[1])
            return True
        time.sleep(0.01)
    return False

def teo_test2():
    teoRequest = False

    # AZDK Database
    db = AzdkDB('C:/temp/AZDKHost.xml')

    # Target Object Driver (with starting position and angular velocity vector)
    teoSetDriver = TargetObjectDriver(Vector(0.0, 1.0, 10.0))
    teoSetDriver.start()
    teoSetDriver.waitStarted()
    # Set output position type: DIR, ANGLES, FRAME
    TargetObject.ptype = TargetObject.POS_TYPE.FRAME

    # Azdk device connection
    azs = AzdkSocket('25.33.41.224', 52349, AzdkServerCmd)
    azs.setName('teo_testing')
    azs.start()
    if not azs.waitStarted():
        teoSetDriver.stop()
        return

    # AZDK setup notifications
    #           RESTART|  QUAT| RS485
    notifFlags = (1<<0)|(0<<1)|(1<<6)
    # set teo notification if not using requests
    if not teoRequest: notifFlags |= (1<<8)
    cmdAzdkSetupNotif = db.createcmd(76, [1, notifFlags, 0, 0])
    while not call_azdk_cmd(azs, cmdAzdkSetupNotif, 1.0): pass
    # AZDK restart auto mode
    call_azdk_cmd(azs, db.createcmd(49), 1.0)

    # AZDK target object commands
    cmdAzdkGetTeo = db.createcmd(28) if teoRequest else None
    cmdAzdkNonStarList = db.createcmd(29)

    teo = None

    teoTimeout = 0.1
    teoTimer = time.perf_counter() + teoTimeout

    # Frame parameters [pixels]: focus, xcenter, ycenter, width, height
    fparams = (20250/21.6, 128.0, 128.0, 256, 256)

    azs.clearNotifications()

    teoSetDriver.setRotation(Vector(0, 0, 0.01))

    while teoSetDriver.is_alive() and azs.is_alive():
        scmd = azs.waitforanswer(None, 0.05)
        if scmd and scmd.code == AzdkServerCmd.DEVICE_CMD.value:
            if scmd.params[0]  == 117:
                if teo:
                    teo.from_bytes(scmd.params[1])
                    print(f'** from notification ** {teo}')
                else:
                    teo = TargetObject.from_teo_bytes(scmd.params[1])
                    if teo: teo.calcframepos(fparams)
                    print(f'** INIT from notification ** {teo}')
        if teo is None:
            if call_azdk_cmd(azs, cmdAzdkNonStarList, 0.1):
                teo = TargetObject.from_phc_list(cmdAzdkNonStarList.answer)
                if teo:
                    teo.calcdirection(fparams)
                    print(f'-- INIT from PhcList -- {teo}')
            teoTimer = time.perf_counter() + teoTimeout
        else:
            curTime = time.perf_counter()
            if cmdAzdkGetTeo and curTime > teoTimer and teo.calcrect(15):
                teoTimer = curTime + teoTimeout
                cmdAzdkGetTeo.params = teo.rect
                if call_azdk_cmd(azs, cmdAzdkGetTeo, 0.1):
                    if teo.from_bytes(cmdAzdkGetTeo.answer):
                        print(f'++ from request ++ {teo}')
                    else:
                        teo = None
        if keyboard and keyboard.is_pressed('q'):
            break

    teoSetDriver.stop()
    azs.stop()


def azdk_test():
    db = AzdkDB('C:/temp/AZDKHost.xml')

    azdkserver = ('25.33.41.224', 52349)
    pdsserver = ('25.33.41.224', 55513)

    azs = AzdkSocket(azdkserver[0], azdkserver[1], AzdkServerCmd)
    azs.start()
    if not azs.waitStarted():
        return
    azs.setName('comm_testing')

    pds = AzdkSocket(pdsserver[0], pdsserver[1], PDSServerCmd)
    pds.start()
    if not pds.waitStarted():
        return
    pds.setName('comm_testing')

    

    while azs.is_alive() and pds.is_alive():
        cmd = pds.waitforanswer(timeout=0.1)
        if cmd:
            print(cmd)
        cmd = azs.waitforanswer(timeout=0.1)
        if cmd:
            if cmd.code == AzdkServerCmd.DEVICE_CMD.value:
                code, answer = cmd.params[0], cmd.params[1]
                cmd = db.createcmd(code)
                cmd.answer = answer
                answer = db.answer(code, answer)
            print(cmd)
        time.sleep(0.01)
    
if __name__ == "__main__":
    azdk_test()
