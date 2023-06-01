import socket
from enum import Enum
import struct
import time
import sys
from datetime import datetime
from threading import Thread, Lock
try: import keyboard
except ImportError: keyboard=None
import numpy as np
from azdk.linalg import Vector, Quaternion
from azdk.azdkdb import AzdkDB, AzdkCmd

sys.path.append("..")
from File_logger import logger

class Bitfield:
    def __init__(self, p: int | bytes):
        if isinstance(p, bytes):
            self.bytes = bytearray(p)
        if isinstance(p, int):
            self.bytes = bytearray((p + 7) // 8)

    def __getitem__(self, idx):
        return self.bytes[idx // 8] >> (idx % 8) & 1

    def __setitem__(self, idx, on: bool):
        mask = 1 << (idx % 8)
        if on: self.bytes[idx // 8] |= mask
        else: self.bytes[idx // 8] &= ~mask

class ServerCmd:
    _idcounter = 0

    def __init__(self, code = 0, params: list = None, cmdid = None, timeout=None) -> None:
        if isinstance(code, Enum):
            self.code = code.value
            self.name = code.name
        else:
            self.code = code
            self.name = None
        if isinstance(params, tuple):
            self.params = list(params)
        elif isinstance(params, list) or params is None:
            self.params = params
        else:
            self.params = [params]
        self.flags = Bitfield(16)
        if cmdid is None:
            ServerCmd._idcounter += 1
            self.id = ServerCmd._idcounter
        else: self.id = cmdid
        self.timeout = timeout
        self.time_ex = None

    def pack(self) -> bytes:
        su = struct.Struct('I')
        si = struct.Struct('i')
        sd = struct.Struct('d')
        sll = struct.Struct('q')

        # header
        hdr = bytearray(8)
        hdr[0] = np.uint8(self.code)
        hdr[2:4] = self.flags.bytes
        hdr[4:8] = su.pack(self.id)

        if self.params is None or len(self.params) == 0:
            return bytes(hdr)

        sdata = b''
        # data description
        nParams = 0

        for p in self.params:
            if isinstance(p, int):
                pdata = si.pack(p)
                ptype = 2
            elif isinstance(p, float):
                pdata = sd.pack(p)
                ptype = 6
            elif isinstance(p, np.uint32 | np.uint16 | np.uint8):
                pdata = su.pack(p)
                ptype = 3
            elif isinstance(p, str):
                pdata = p.encode('UTF-8')
                ptype = 10
            elif isinstance(p, Quaternion):
                pdata = sd.pack(p.w) + sd.pack(p.x) + sd.pack(p.y) + sd.pack(p.z)
                ptype = 129
            elif isinstance(p, Vector):
                pdata = sd.pack(p.x) + sd.pack(p.y) + sd.pack(p.z)
                ptype = 130
            else: continue

            pdescr = si.pack(ptype) + si.pack(len(pdata))
            hdr += pdescr
            sdata += pdata
            nParams += 1

        if isinstance(self.time_ex, datetime):
            pdata = np.int64(self.time_ex.timestamp()*1000)
            hdr += si.pack(ptype) + si.pack(8)
            sdata += sll.pack(pdata)
            nParams += 1

        hdr[1] = nParams
        return bytes(hdr) + sdata

    def setparams(self, d):
        if d is None or isinstance(d, list):
            self.params = d
        else:
            self.params = [d]

    def setquiet(self, on : bool):
        self.flags[2] = on

    @classmethod
    def getcmd(cls, s: bytes | socket.socket):
        sok = isinstance(s, socket.socket)
        if isinstance(s, bytes):
            if len(s) < 8: return None, None
            hdr = s[:8]
        elif sok: hdr = s.recv(8)
        else: return None, None

        su = struct.Struct('I')
        si = struct.Struct('i')
        sd = struct.Struct('d')
        sll = struct.Struct('q')
        sv = struct.Struct('3d')
        sq = struct.Struct('4d')

        code = hdr[0]
        nParams = hdr[1]
        flags = Bitfield(hdr[2:4])
        cmdid = su.unpack(hdr[4:8])[0]
        hIdx = 8 + nParams*8
        time_ex = None

        if sok: pdescr = s.recv(nParams*8)
        elif len(s) < hIdx: return None, None
        else: pdescr = s[8:hIdx]

        pdescr = np.frombuffer(pdescr, np.uint).reshape([nParams, 2])
        dSz = pdescr.sum(0)[1]

        if sok: data = s.recv(dSz)
        elif len(s) < hIdx + dSz: return None, None
        else: data = s[hIdx:hIdx+dSz]

        p = []
        dIdx = 0
        for ptype, psize in pdescr:
            packer = None
            pdata = data[dIdx:dIdx+psize]
            if ptype == 10: p.append(pdata.decode('UTF-8'))
            elif ptype == 11:
                pdata = pdata.decode('UTF-8').split('\0')
                if len(pdata[-1]) == 0:
                    del pdata[-1]
                p.append(pdata)
            elif ptype == 2: packer = si
            elif ptype == 6: packer = sd
            elif ptype == 3: packer = su
            elif ptype == 12: p.append(pdata)
            elif ptype == 129:
                p.append(Quaternion(*sq.unpack(pdata)))
            elif ptype == 130:
                p.append(Vector(*sv.unpack(pdata)))
            elif ptype == 133:
                time_ex = datetime.fromtimestamp(sll.unpack(pdata)[0]*0.001)
            if packer:
                p.append(packer.unpack(pdata)[0])
            dIdx += psize

        cmd = cls(code, p, cmdid)
        cmd.time_ex = time_ex
        cmd.flags = flags
        return cmd, hIdx + dIdx

    def __str__(self) -> str:
        s = f'{self.name} [id={self.id}]'
        for p in self.params:
            if isinstance(p, bytes):
                sp = p.hex(' ')
            else:
                sp = str(p)
            if len(sp) > 0:
                s += ', ' + sp
        if self.time_ex is not None:
            s += ', ' + str(self.time_ex)
        return s

class PDSServerCommands(Enum):
    SET_VERSION = 0         # Получить версию приложения
    GET_FRAME = 1           # Получить кадр буфера экрана
    SET_RANDOM_MODE = 2     # Установить случайных изменений ориентации и угловой скорости
    GET_STATE = 3           # Получить состояние
    SET_STATE = 4           # Установить состояние
    GET_ORIENT = 5          # Получить ориентацию (GCRS)
    SET_ORIENT = 6          # Установить ориентацию (GCRS)
    GET_POS = 7             # Получить положение аппарата (GCRS)
    SET_POS = 8             # Установить положение аппарата (GCRS)
    GET_ANGVEL = 9          # Получить угловую скорость (GCRS)
    SET_ANGVEL = 10         # Установить угловую скорость (GCRS)
    GET_POINT_SETTINGS = 11 # Получить настройки точек
    SET_POINT_SETTINGS = 12 # Задать настройки для точек
    GET_BACKGROUNDS = 13    # Получить описание фоновой засветки
    SET_BACKGROUND = 14     # Установить фоновую засветку
    GET_TEO_POS  = 15       # Получить описание фоновой засветки
    SET_TEO_POS  = 16       # Установить фоновую засветку
    GET_FOCUS  = 17         # Получить фокус (масштабный фактор)
    SET_FOCUS  = 18         # Установить фокус (масштабный фактор)
    SET_CONN_NAME = 0xF0    # Поименовать соединение

    @classmethod
    def getname(cls, code: int):
        for _name, _value in cls.__members__.items():
            if _value.value == code:
                return _name
        return None

    @classmethod
    def findname(cls, name: str):
        return cls.__members__[name].value

class AzdkServerCommands(Enum):
    SCMD_HELP = 1           # Cписок команд
    DEVICE_CMD = 3          # Отправка команды АЗДК-1 с параметрами
    SET_MODE = 4            # Переключает разные режимы отображения и рассылки информации
    GET_SERIALPORT_LIST = 7 # Получение списка последовательных портов
    GET_RS_PORT = 8         # Номер порта для RS485
    GET_CAN_PORT = 9        # Номер порта для CAN
    GET_TRACE_PARAM = 13    # Значение отслеживаемого параметра
    GET_TP_LIST = 14        # Список параметров отслеживания
    GET_DEVICE_INFO = 15    # Данные об устройстве
    SET_LOG_TEMPLATE = 22   # Изменение шаблона имени файла журнала
    GET_VERSION = 23        # Получить версию программы

    @classmethod
    def getname(cls, code: int):
        for _name, _value in cls.__members__.items():
            if _value.value == code:
                return _name
        return None

    @classmethod
    def findname(cls, name: str):
        return cls.__members__[name].value

class PDSServerCmd(ServerCmd):
    _pdscmdcounter = 0
    def __init__(self, code : PDSServerCommands, params: list = None, cmdid=None, timeout=None):
        if cmdid is None:
            PDSServerCmd._pdscmdcounter += 1
            self.id = PDSServerCmd._pdscmdcounter
        super().__init__(code, params, cmdid, timeout)

class AzdkServerCmd(ServerCmd):
    _azdkcmdcounter = 0

    def __init__(self, code : AzdkServerCommands, params: list = None, cmdid=None, timeout=None):
        if isinstance(code, AzdkCmd):
            if params is None:
                params = code.params
            params = [code.code] + params
            code = AzdkServerCommands.DEVICE_CMD
        if cmdid is None:
            AzdkServerCmd._azdkcmdcounter += 1
            self.id = AzdkServerCmd._azdkcmdcounter
        super().__init__(code, params, cmdid, timeout)

    @classmethod
    def devicecmd(cls, code : int, params : list = None):
        scmd = cls(AzdkServerCommands.DEVICE_CMD, [code] + params)
        return scmd

class PDSServerState:
    STARS = 0
    GRID = 1
    RND_POINTS = 2
    FIX_POINTS = 3
    GRAD_POINTS = 4
    def __init__(self, mode=0, show=False, rotate=False, notify=False) -> None:
        self.mode = mode
        self.rotating = rotate
        self.showing = show
        self.notifying = notify

    def unpack(self, d : np.uint32 | bytes):
        if isinstance(d, bytes):
            d = struct.unpack('I', d[:4])[0]
        self.mode = d & 0xFF
        self.rotating = bool(d & 256)
        self.showing = bool(d & 512)
        self.notifying = bool(d & 1024)

    def pack(self):
        d = self.mode
        if self.rotating: d |= 256
        if self.showing: d |= 512
        if self.notifying: d |= 1024
        return np.uint32(d)

    def cmd(self):
        fl = self.pack()
        return ServerCmd(PDSServerCommands.SET_STATE, [fl])

class AzdkSocket(Thread):
    def __init__(self, ip: str = None, port = 0, commandClass = PDSServerCommands,
                 verbose=False, threadName : str = None, _logger : logger = None) -> None:
        super().__init__()
        try: socket.inet_aton(ip)
        except TypeError: ip = '127.0.0.1'
        self._peer = (ip, port)
        self.cmdsent = None
        self.notifications = []
        self.cmdqueue = []
        self.cmdready = []
        self._mutex = Lock()
        self.running = False
        self.verbose = verbose
        self.cmdclass = commandClass
        self.logger = _logger
        if isinstance(threadName, str):
            self.name = threadName
        else:
            self.name = commandClass.__name__

    def __enter__(self):
        if self.verbose: print(f'Starting {self.name}')
        self.start()
        if not self.waitStarted():
            self.stop()
            return None
        return self

    def __exit__(self, exc_type, exc_value, exc_traceback):
        if self.verbose: print(f'Stopping {self.name}')
        self.stop()

    def _log(self, txt : str):
        if self.logger:
            _timestamp = datetime.now().strftime(r'%Y.%d.%m %H:%M:%S.%f')
            print(_timestamp + f'; {self.name}; ' + txt)
            self.logger.log(str(_timestamp + f'; {self.name}; ' + txt ))
        else:
            print(txt)
        

    def enqueue(self, cmd: ServerCmd):
        if not isinstance(cmd, ServerCmd): return
        cmd.time_ex = None
        self._mutex.acquire()
        self.cmdqueue.append(cmd)
        self._mutex.release()

    def isCmdSending(self, cmd : ServerCmd):
        self._mutex.acquire()
        ok = cmd == self.cmdsent or cmd in self.cmdqueue
        self._mutex.release()
        return ok

    def waitforanswer(self, cmdsent: ServerCmd = None, timeout: float = None) -> ServerCmd | None:
        if timeout:
            tStart = time.perf_counter()
        while self.running:
            time.sleep(0.05)
            cmdanswer = None
            if cmdsent is None:
                cmdanswer = self.getNotification()
            elif self.isCmdReady(cmdsent):
                cmdanswer = cmdsent
            elif not self.isCmdSending(cmdsent):
                return None
            if cmdanswer:
                return cmdanswer
            if timeout and time.perf_counter() > tStart + timeout:
                if self.verbose and cmdsent:
                    self._log('Command waiting timeout')
                return None

    def clearNotifications(self, code = -1):
        self._mutex.acquire()
        if code < 0:
            self.notifications.clear()
        else:
            self.notifications = [x for x in self.notifications if x.code == code]
        self._mutex.release()

    def isCmdReady(self, cmd : ServerCmd, removeready=True):
        if cmd not in self.cmdready: return False
        if removeready:
            self._mutex.acquire()
            self.cmdready.remove(cmd)
            self._mutex.release()
        return True

    def getNotificationByParam(self, pNum : int, pVal, codeCheck : int = None):
        self._mutex.acquire()
        for cmd in self.notifications:
            if codeCheck and cmd.code != codeCheck: continue
            if pNum > len(cmd.params): continue
            if cmd.params[pNum] != pVal: continue
            self.notifications.remove(cmd)
            break
        else:
            cmd = None
        self._mutex.release()
        return cmd

    def getNotification(self):
        if len(self.notifications) == 0: return None
        self._mutex.acquire()
        cmd = self.notifications.pop(0)
        self._mutex.release()
        return cmd

    def run(self) -> None:
        if self.verbose:
            self._log(f'open socket [{self.cmdclass}]')
        s = socket.socket()
        s.settimeout(1)
        try:
            s.connect(self._peer)
            s.settimeout(0.01)
        except TimeoutError:
            self._log(f'Error: cannot connect to server {self._peer}')
            return
        buf = b''

        clearBufTimeout = 1.0
        clearBufTimer = time.perf_counter() + clearBufTimeout

        self.running = True

        while self.running:
            cmd = None
            try:
                dBuf = s.recv(256)
                if len(dBuf) > 0:
                    buf += dBuf
                    clearBufTimer = time.perf_counter() + clearBufTimeout
            except ConnectionError:
                if self.verbose:
                    self._log('Error: remote connection was closed')
                break
            except TimeoutError:
                pass
            if len(buf) > 0:
                cmd, idx = ServerCmd.getcmd(buf)
                if cmd: buf = buf[idx:]
            bufTimer = time.perf_counter()
            if bufTimer > clearBufTimer:
                clearBufTimer = time.perf_counter() + clearBufTimeout
                buf = b''

            if self.cmdsent:
                if cmd and cmd.code == self.cmdsent.code and cmd.id == self.cmdsent.id:
                    self._mutex.acquire()
                    self.cmdsent.params = cmd.params
                    self.cmdsent.time_ex = cmd.time_ex
                    self.cmdsent, cmd = None, self.cmdsent
                    self.cmdready.append(cmd)
                    self._mutex.release()
                    if self.verbose:
                        #cmdid = cmd.name or f'CMD-{cmd.code}'
                        #self._log(f'{cmdid} [id={cmd.id}] answer received')
                        self._log(str(cmd) + ' answered')
                    cmd = None
                elif self.cmdsent.timeout:
                    if time.perf_counter() - self.cmdsent.senttime > self.cmdsent.timeout:
                        self.cmdsent.senttime = -1
                        self.cmdsent = None

            if cmd:
                cmd.name = self.cmdclass.getname(cmd.code)
                cmd.flags[15] = True
                self._mutex.acquire()
                self.notifications.append(cmd)
                self._mutex.release()
                cmd = None

            if len(self.cmdqueue) > 0 and self.cmdsent is None:
                self._mutex.acquire()
                self.cmdsent = self.cmdqueue.pop(0)
                self._mutex.release()
                try:
                    s.sendall(self.cmdsent.pack())
                    self.cmdsent.senttime = time.perf_counter()
                    if self.verbose:
                        self._log(str(self.cmdsent) + ' sent')
                        #cmdid = self.cmdsent.name or f'CMD-{self.cmdsent.code}'
                        #self._log(f'{cmdid} [id={self.cmdsent.id}] {self.cmdsent.params} sent')
                except ConnectionError:
                    if self.verbose:
                        self._log('Error: remote connection was closed')
                    break
        if self.verbose:
            self._log('socket was closed')
        self.running = False

    def stop(self):
        self.running = False
        self.join()

    def setConnectionName(self, name : str, timeout=None):
        cmd = ServerCmd(PDSServerCommands.SET_CONN_NAME, [name])
        self.enqueue(cmd)
        return self.waitforanswer(cmd, timeout) == cmd

    def setThreadName(self, name : str):
        self.name = name

    def waitStarted(self, timeout=1.0):
        time.sleep(0.1)
        ts = time.perf_counter()
        while not self.is_alive() or not self.running:
            if time.perf_counter() > ts + timeout:
                return False
        return True

    def waitUntilStart(self, timeout=1.0):
        self.start()
        return self.waitStarted(timeout)

    def execute(self, cmd : ServerCmd, timeout : float = None):
        self.enqueue(cmd)
        return self.waitforanswer(cmd, timeout) == cmd

def call_azdk_cmd(s : AzdkSocket, cmd : AzdkCmd, timeout=np.inf, clearNotif=True):
    scmd = AzdkServerCmd(cmd)
    if clearNotif: s.clearNotifications()
    s.enqueue(scmd)
    tStart = time.perf_counter()
    if timeout is None: timeout = np.inf
    while True:
        time.sleep(0.01)
        dt = time.perf_counter() - tStart
        if dt > timeout: return False
        if s.isCmdReady(scmd):
            cmd.answer = scmd.params[1]
            if s.verbose: s._log(f'request time: {dt}')
            return True
        if len(s.notifications) == 0: continue
        acmd = s.getNotificationByParam(0, cmd.code, AzdkServerCommands.DEVICE_CMD.value)
        if clearNotif: s.clearNotifications()
        if acmd is None: continue
        cmd.answer = acmd.params[1]
        if s.verbose: s._log(f'request time: {dt}')
        return True

def pdssocket_test():
    pds = AzdkSocket('127.0.0.1', 55555, PDSServerCommands)
    pds.verbose = True
    pds.start()
    if not pds.waitStarted(): return
    pds.setConnectionName('teo_testing')
    pdsSetStateCmd = ServerCmd(PDSServerCommands.SET_STATE, [np.uint32(512)])
    pds.enqueue(pdsSetStateCmd)
    pds.waitforanswer(pdsSetStateCmd)

    quatChangeTimeout = 1.0
    quatChangeTimer = time.perf_counter() + quatChangeTimeout

    while pds.is_alive():
        t = time.perf_counter()
        if t > quatChangeTimer:
            quatChangeTimer += quatChangeTimeout
            cmd = ServerCmd(PDSServerCommands.SET_ORIENT, [Quaternion.random()])
            pds.enqueue(cmd)
            pds.waitforanswer(cmd)
        cmdok = pds.getNotification()
        if cmdok:
            print(cmdok)
            #if cmdok.flags[15]: s.clear_notifications(cmdok.code)
        if keyboard and keyboard.is_pressed('q'):
            break

    pds.stop()

def pdssocket_test_q():
    s = AzdkSocket('127.0.0.1', 55513)
    s.start()

    cmdSetQuat = ServerCmd(PDSServerCommands.SET_ORIENT)
    qsTimer = time.perf_counter()
    qsTimeout = 3.0

    while s.is_alive():
        curTime = time.perf_counter()
        if curTime > qsTimer + qsTimeout:
            qsTimer += qsTimeout
            cmdSetQuat.setparams(Quaternion.random())
            s.enqueue(cmdSetQuat)
            print(cmdSetQuat)
        cmdok = s.waitforanswer(timeout=0.1)
        if cmdok:
            print(cmdok)
            #if cmdok.flags[15]: s.clear_notifications(cmdok.code)
        if keyboard and keyboard.is_pressed('q'):
            break

    s.stop()

def pdssocket_test_te_object():
    s = AzdkSocket('127.0.0.1', 55513)
    s.start()

    #cmdGetTeoPos = ServerCmd(PDSCmd.GET_TEO_POS)
    cmdSetTeoPos = ServerCmd(PDSServerCommands.SET_TEO_POS)
    qsTimer = time.perf_counter()
    qsTimeout = 0.1
    w = 0.05
    a = 0.2
    z = 3.0

    while s.is_alive():
        curTime = time.perf_counter()
        if curTime > qsTimer + qsTimeout:
            qsTimer += qsTimeout
            x = a * np.cos(w*curTime)
            y = a * np.sin(w*curTime)
            cmdSetTeoPos.params = [Vector(x, y, z)]
            s.enqueue(cmdSetTeoPos)
            print(cmdSetTeoPos)
        cmdok = s.waitforanswer(cmdSetTeoPos, timeout=0.1)
        if cmdok:
            print(cmdok)
            #if cmdok.flags[15]: s.clear_notifications(cmdok.code)
        if keyboard and keyboard.is_pressed('q'):
            break

    s.stop()

def azdksocket_test():
    if AzdkDB is None:
        raise ImportError('azdkdb module not installed')
    db = AzdkDB('d:/Users/Simae/Work/2019/PDStand/Win32/Release/AZDKHost.xml')
    s = AzdkSocket('127.0.0.1', 53512, AzdkServerCommands)
    s.start()

    #cmdGetAngVel = ServerCmd(AzdkServerCommands.DEVICE_CMD, [18])
    qsTimer = time.perf_counter()
    qsTimeout = 5.0

    while s.is_alive():
        curTime = time.perf_counter()
        if curTime > qsTimer + qsTimeout:
            qsTimer += qsTimeout
            #s.enqueue(cmdGetAngVel)
            #print(cmdGetAngVel)
        cmdok = s.waitforanswer(timeout=0.1)
        if cmdok:
            if cmdok.code == AzdkServerCommands.DEVICE_CMD:
                qcmd = db.createcmd(cmdok.params[0], cmdok.params[1:])
                print(db.cmdinfo(qcmd))
            else:
                print(cmdok)
            #if cmdok.flags[15]: s.clear_notifications(cmdok.code)
        if keyboard and keyboard.is_pressed('q'):
            break

if __name__ == "__main__":
    pdssocket_test()
    #azdksocket_test()
    #pdssocket_test_te_object()
