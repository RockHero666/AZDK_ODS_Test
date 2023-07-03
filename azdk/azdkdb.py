from os import path
from threading import Thread, Lock
import time
import xml.etree.ElementTree as ET
import json
from datetime import datetime, timedelta
import struct
import numpy as np
import serial
try: from tqdm import tqdm
except ImportError: tqdm = None
from serial.serialutil import SerialException
from azdk.pgm import Pgm
from azdk.linalg import Vector, Quaternion

def jsonfy(obj):
    raise TypeError

def quatntime_from_bytes(d : bytes):
    if len(d) < 24: return (None, None)
    elif len(d) > 24: d = d[:24]
    s = struct.unpack('4iI2H', d)
    q = Quaternion(s[0], s[1], s[2], s[3])
    q.normalize()
    if s[6] == 0: t = None
    else: t = datetime(s[6], 1, 1) + timedelta(s[5]) + timedelta(milliseconds=s[4])
    return (q, t)

def angvelntime_from_bytes(d : bytes):
    if len(d) < 20: return (None, None)
    elif len(d) > 20: d = d[:20]
    s = struct.unpack('3iI2H', d)
    v = Vector(s[0], s[1], s[2])*(2**-30)
    #v.normalize()
    if s[5] == 0: t = None
    else: t = datetime(s[5], 1, 1) + timedelta(s[4]) + timedelta(milliseconds=s[3])
    return (v, t)

def azdk_curtime():
    t = datetime.now()
    ms = t.microsecond / 1000
    t = t.timetuple()
    ms += (t.tm_hour*3600 + t.tm_min*60 + t.tm_sec)*1000
    return (ms, t.tm_yday, t.tm_year)

class AzdkCRC:
    _Crc8Table = [
        0x00, 0x31, 0x62, 0x53, 0xC4, 0xF5, 0xA6, 0x97, 0xB9, 0x88, 0xDB, 0xEA, 0x7D, 0x4C, 0x1F, 0x2E,
        0x43, 0x72, 0x21, 0x10, 0x87, 0xB6, 0xE5, 0xD4, 0xFA, 0xCB, 0x98, 0xA9, 0x3E, 0x0F, 0x5C, 0x6D,
        0x86, 0xB7, 0xE4, 0xD5, 0x42, 0x73, 0x20, 0x11, 0x3F, 0x0E, 0x5D, 0x6C, 0xFB, 0xCA, 0x99, 0xA8,
        0xC5, 0xF4, 0xA7, 0x96, 0x01, 0x30, 0x63, 0x52, 0x7C, 0x4D, 0x1E, 0x2F, 0xB8, 0x89, 0xDA, 0xEB,
        0x3D, 0x0C, 0x5F, 0x6E, 0xF9, 0xC8, 0x9B, 0xAA, 0x84, 0xB5, 0xE6, 0xD7, 0x40, 0x71, 0x22, 0x13,
        0x7E, 0x4F, 0x1C, 0x2D, 0xBA, 0x8B, 0xD8, 0xE9, 0xC7, 0xF6, 0xA5, 0x94, 0x03, 0x32, 0x61, 0x50,
        0xBB, 0x8A, 0xD9, 0xE8, 0x7F, 0x4E, 0x1D, 0x2C, 0x02, 0x33, 0x60, 0x51, 0xC6, 0xF7, 0xA4, 0x95,
        0xF8, 0xC9, 0x9A, 0xAB, 0x3C, 0x0D, 0x5E, 0x6F, 0x41, 0x70, 0x23, 0x12, 0x85, 0xB4, 0xE7, 0xD6,
        0x7A, 0x4B, 0x18, 0x29, 0xBE, 0x8F, 0xDC, 0xED, 0xC3, 0xF2, 0xA1, 0x90, 0x07, 0x36, 0x65, 0x54,
        0x39, 0x08, 0x5B, 0x6A, 0xFD, 0xCC, 0x9F, 0xAE, 0x80, 0xB1, 0xE2, 0xD3, 0x44, 0x75, 0x26, 0x17,
        0xFC, 0xCD, 0x9E, 0xAF, 0x38, 0x09, 0x5A, 0x6B, 0x45, 0x74, 0x27, 0x16, 0x81, 0xB0, 0xE3, 0xD2,
        0xBF, 0x8E, 0xDD, 0xEC, 0x7B, 0x4A, 0x19, 0x28, 0x06, 0x37, 0x64, 0x55, 0xC2, 0xF3, 0xA0, 0x91,
        0x47, 0x76, 0x25, 0x14, 0x83, 0xB2, 0xE1, 0xD0, 0xFE, 0xCF, 0x9C, 0xAD, 0x3A, 0x0B, 0x58, 0x69,
        0x04, 0x35, 0x66, 0x57, 0xC0, 0xF1, 0xA2, 0x93, 0xBD, 0x8C, 0xDF, 0xEE, 0x79, 0x48, 0x1B, 0x2A,
        0xC1, 0xF0, 0xA3, 0x92, 0x05, 0x34, 0x67, 0x56, 0x78, 0x49, 0x1A, 0x2B, 0xBC, 0x8D, 0xDE, 0xEF,
        0x82, 0xB3, 0xE0, 0xD1, 0x46, 0x77, 0x24, 0x15, 0x3B, 0x0A, 0x59, 0x68, 0xFF, 0xCE, 0x9D, 0xAC]

    _Crc16Table = [
        0x0000, 0x1021, 0x2042, 0x3063, 0x4084, 0x50a5, 0x60c6, 0x70e7,
        0x8108, 0x9129, 0xa14a, 0xb16b, 0xc18c, 0xd1ad, 0xe1ce, 0xf1ef,
        0x1231, 0x0210, 0x3273, 0x2252, 0x52b5, 0x4294, 0x72f7, 0x62d6,
        0x9339, 0x8318, 0xb37b, 0xa35a, 0xd3bd, 0xc39c, 0xf3ff, 0xe3de,
        0x2462, 0x3443, 0x0420, 0x1401, 0x64e6, 0x74c7, 0x44a4, 0x5485,
        0xa56a, 0xb54b, 0x8528, 0x9509, 0xe5ee, 0xf5cf, 0xc5ac, 0xd58d,
        0x3653, 0x2672, 0x1611, 0x0630, 0x76d7, 0x66f6, 0x5695, 0x46b4,
        0xb75b, 0xa77a, 0x9719, 0x8738, 0xf7df, 0xe7fe, 0xd79d, 0xc7bc,
        0x48c4, 0x58e5, 0x6886, 0x78a7, 0x0840, 0x1861, 0x2802, 0x3823,
        0xc9cc, 0xd9ed, 0xe98e, 0xf9af, 0x8948, 0x9969, 0xa90a, 0xb92b,
        0x5af5, 0x4ad4, 0x7ab7, 0x6a96, 0x1a71, 0x0a50, 0x3a33, 0x2a12,
        0xdbfd, 0xcbdc, 0xfbbf, 0xeb9e, 0x9b79, 0x8b58, 0xbb3b, 0xab1a,
        0x6ca6, 0x7c87, 0x4ce4, 0x5cc5, 0x2c22, 0x3c03, 0x0c60, 0x1c41,
        0xedae, 0xfd8f, 0xcdec, 0xddcd, 0xad2a, 0xbd0b, 0x8d68, 0x9d49,
        0x7e97, 0x6eb6, 0x5ed5, 0x4ef4, 0x3e13, 0x2e32, 0x1e51, 0x0e70,
        0xff9f, 0xefbe, 0xdfdd, 0xcffc, 0xbf1b, 0xaf3a, 0x9f59, 0x8f78,
        0x9188, 0x81a9, 0xb1ca, 0xa1eb, 0xd10c, 0xc12d, 0xf14e, 0xe16f,
        0x1080, 0x00a1, 0x30c2, 0x20e3, 0x5004, 0x4025, 0x7046, 0x6067,
        0x83b9, 0x9398, 0xa3fb, 0xb3da, 0xc33d, 0xd31c, 0xe37f, 0xf35e,
        0x02b1, 0x1290, 0x22f3, 0x32d2, 0x4235, 0x5214, 0x6277, 0x7256,
        0xb5ea, 0xa5cb, 0x95a8, 0x8589, 0xf56e, 0xe54f, 0xd52c, 0xc50d,
        0x34e2, 0x24c3, 0x14a0, 0x0481, 0x7466, 0x6447, 0x5424, 0x4405,
        0xa7db, 0xb7fa, 0x8799, 0x97b8, 0xe75f, 0xf77e, 0xc71d, 0xd73c,
        0x26d3, 0x36f2, 0x0691, 0x16b0, 0x6657, 0x7676, 0x4615, 0x5634,
        0xd94c, 0xc96d, 0xf90e, 0xe92f, 0x99c8, 0x89e9, 0xb98a, 0xa9ab,
        0x5844, 0x4865, 0x7806, 0x6827, 0x18c0, 0x08e1, 0x3882, 0x28a3,
        0xcb7d, 0xdb5c, 0xeb3f, 0xfb1e, 0x8bf9, 0x9bd8, 0xabbb, 0xbb9a,
        0x4a75, 0x5a54, 0x6a37, 0x7a16, 0x0af1, 0x1ad0, 0x2ab3, 0x3a92,
        0xfd2e, 0xed0f, 0xdd6c, 0xcd4d, 0xbdaa, 0xad8b, 0x9de8, 0x8dc9,
        0x7c26, 0x6c07, 0x5c64, 0x4c45, 0x3ca2, 0x2c83, 0x1ce0, 0x0cc1,
        0xef1f, 0xff3e, 0xcf5d, 0xdf7c, 0xaf9b, 0xbfba, 0x8fd9, 0x9ff8,
        0x6e17, 0x7e36, 0x4e55, 0x5e74, 0x2e93, 0x3eb2, 0x0ed1, 0x1ef0]

    _Crc32Table = [
        0x00000000, 0x77073096, 0xee0e612c, 0x990951ba, 0x076dc419, 0x706af48f,
        0xe963a535, 0x9e6495a3, 0x0edb8832, 0x79dcb8a4, 0xe0d5e91e, 0x97d2d988,
        0x09b64c2b, 0x7eb17cbd, 0xe7b82d07, 0x90bf1d91, 0x1db71064, 0x6ab020f2,
        0xf3b97148, 0x84be41de, 0x1adad47d, 0x6ddde4eb, 0xf4d4b551, 0x83d385c7,
        0x136c9856, 0x646ba8c0, 0xfd62f97a, 0x8a65c9ec, 0x14015c4f, 0x63066cd9,
        0xfa0f3d63, 0x8d080df5, 0x3b6e20c8, 0x4c69105e, 0xd56041e4, 0xa2677172,
        0x3c03e4d1, 0x4b04d447, 0xd20d85fd, 0xa50ab56b, 0x35b5a8fa, 0x42b2986c,
        0xdbbbc9d6, 0xacbcf940, 0x32d86ce3, 0x45df5c75, 0xdcd60dcf, 0xabd13d59,
        0x26d930ac, 0x51de003a, 0xc8d75180, 0xbfd06116, 0x21b4f4b5, 0x56b3c423,
        0xcfba9599, 0xb8bda50f, 0x2802b89e, 0x5f058808, 0xc60cd9b2, 0xb10be924,
        0x2f6f7c87, 0x58684c11, 0xc1611dab, 0xb6662d3d, 0x76dc4190, 0x01db7106,
        0x98d220bc, 0xefd5102a, 0x71b18589, 0x06b6b51f, 0x9fbfe4a5, 0xe8b8d433,
        0x7807c9a2, 0x0f00f934, 0x9609a88e, 0xe10e9818, 0x7f6a0dbb, 0x086d3d2d,
        0x91646c97, 0xe6635c01, 0x6b6b51f4, 0x1c6c6162, 0x856530d8, 0xf262004e,
        0x6c0695ed, 0x1b01a57b, 0x8208f4c1, 0xf50fc457, 0x65b0d9c6, 0x12b7e950,
        0x8bbeb8ea, 0xfcb9887c, 0x62dd1ddf, 0x15da2d49, 0x8cd37cf3, 0xfbd44c65,
        0x4db26158, 0x3ab551ce, 0xa3bc0074, 0xd4bb30e2, 0x4adfa541, 0x3dd895d7,
        0xa4d1c46d, 0xd3d6f4fb, 0x4369e96a, 0x346ed9fc, 0xad678846, 0xda60b8d0,
        0x44042d73, 0x33031de5, 0xaa0a4c5f, 0xdd0d7cc9, 0x5005713c, 0x270241aa,
        0xbe0b1010, 0xc90c2086, 0x5768b525, 0x206f85b3, 0xb966d409, 0xce61e49f,
        0x5edef90e, 0x29d9c998, 0xb0d09822, 0xc7d7a8b4, 0x59b33d17, 0x2eb40d81,
        0xb7bd5c3b, 0xc0ba6cad, 0xedb88320, 0x9abfb3b6, 0x03b6e20c, 0x74b1d29a,
        0xead54739, 0x9dd277af, 0x04db2615, 0x73dc1683, 0xe3630b12, 0x94643b84,
        0x0d6d6a3e, 0x7a6a5aa8, 0xe40ecf0b, 0x9309ff9d, 0x0a00ae27, 0x7d079eb1,
        0xf00f9344, 0x8708a3d2, 0x1e01f268, 0x6906c2fe, 0xf762575d, 0x806567cb,
        0x196c3671, 0x6e6b06e7, 0xfed41b76, 0x89d32be0, 0x10da7a5a, 0x67dd4acc,
        0xf9b9df6f, 0x8ebeeff9, 0x17b7be43, 0x60b08ed5, 0xd6d6a3e8, 0xa1d1937e,
        0x38d8c2c4, 0x4fdff252, 0xd1bb67f1, 0xa6bc5767, 0x3fb506dd, 0x48b2364b,
        0xd80d2bda, 0xaf0a1b4c, 0x36034af6, 0x41047a60, 0xdf60efc3, 0xa867df55,
        0x316e8eef, 0x4669be79, 0xcb61b38c, 0xbc66831a, 0x256fd2a0, 0x5268e236,
        0xcc0c7795, 0xbb0b4703, 0x220216b9, 0x5505262f, 0xc5ba3bbe, 0xb2bd0b28,
        0x2bb45a92, 0x5cb36a04, 0xc2d7ffa7, 0xb5d0cf31, 0x2cd99e8b, 0x5bdeae1d,
        0x9b64c2b0, 0xec63f226, 0x756aa39c, 0x026d930a, 0x9c0906a9, 0xeb0e363f,
        0x72076785, 0x05005713, 0x95bf4a82, 0xe2b87a14, 0x7bb12bae, 0x0cb61b38,
        0x92d28e9b, 0xe5d5be0d, 0x7cdcefb7, 0x0bdbdf21, 0x86d3d2d4, 0xf1d4e242,
        0x68ddb3f8, 0x1fda836e, 0x81be16cd, 0xf6b9265b, 0x6fb077e1, 0x18b74777,
        0x88085ae6, 0xff0f6a70, 0x66063bca, 0x11010b5c, 0x8f659eff, 0xf862ae69,
        0x616bffd3, 0x166ccf45, 0xa00ae278, 0xd70dd2ee, 0x4e048354, 0x3903b3c2,
        0xa7672661, 0xd06016f7, 0x4969474d, 0x3e6e77db, 0xaed16a4a, 0xd9d65adc,
        0x40df0b66, 0x37d83bf0, 0xa9bcae53, 0xdebb9ec5, 0x47b2cf7f, 0x30b5ffe9,
        0xbdbdf21c, 0xcabac28a, 0x53b39330, 0x24b4a3a6, 0xbad03605, 0xcdd70693,
        0x54de5729, 0x23d967bf, 0xb3667a2e, 0xc4614ab8, 0x5d681b02, 0x2a6f2b94,
        0xb40bbe37, 0xc30c8ea1, 0x5a05df1b, 0x2d02ef8d]

    @classmethod
    def crc8(cls, d: bytearray, crc=0xFF):
        crc = np.uint8(crc)
        for x in d:
            crc ^= x
            crc = cls._Crc8Table[crc]
        return np.uint8(crc)

    @classmethod
    def crc16(cls, d: bytearray, crc=0xFFFF):
        crc = np.uint16(crc)
        for x in d:
            i = (crc >> 8) ^ x
            crc = cls._Crc16Table[i] ^ np.uint16(crc << 8)
        return np.uint16(crc)

    @classmethod
    def crc32(cls, d: bytearray, crc=0xFFFFFFFF):
        crc = np.uint32(crc)
        for x in d:
            crc = cls._Crc32Table[(crc ^ x) & 0xFF] ^ (crc >> 8)
        return np.uint32(crc ^ 0xFFFFFFFF)

class AzdkCmd:
    _idcounter = 0
    _codemask = 0x7F

    def __init__(self, _code=0, *, _timeout=0.1) -> None:
        self.code = np.uint8(_code)
        self.params = []
        self.answer = b''
        self._answersize = -1
        self.data = b''
        self._datasize = 0
        self._id = AzdkCmd._idcounter
        AzdkCmd._idcounter += 1
        self.error = 0
        self.updatetime = None
        self.sendtime = None
        self.crc = 0
        self.timeout = _timeout
        self.type = 0

    def __str__(self) -> str:
        code = self.code & self._codemask
        s = f'Id={self._id}, Code={code}'
        np = len(self.params)
        if np > 0:
            s += ' ['
            for kp in range(np):
                if kp: s += ', '
                s += str(self.params[kp])
            s += ']'
        answer = self.answer
        if not isinstance(answer, list | tuple):
            answer = [answer]
        for x in answer:
            if isinstance(x, bytes) and len(x) > 0:
                s += ', answer=' + self.answer.hex(' ').upper()
            else:
                x = str(x)
                if len(x) > 0: s += ', ' + x
        np = len(self.data)
        if np > 0:
            s += f', data of {np} bytes'
        return s

    def clear(self) -> None:
        self._answersize = -1
        self.answer = b''
        self._datasize = 0
        self.data = b''

    def setdata(self, k: int, d: int) -> bool:
        if k < 0 or k >= len(self.params):
            return False
        self.params[k] = type(self.params[k])(d)
        return True

    def isanwerready(self) -> bool:
        return self._answersize == len(self.answer)

    def isready(self) -> bool:
        if self.error > 0: return True
        return len(self.answer) >= self._answersize and len(self.data) >= self._datasize

    def istimeout(self) -> bool:
        tLast = self.updatetime or self.sendtime
        tCurrent = time.perf_counter()
        return tLast and tCurrent > tLast + self.timeout

    def issame(self, cmd, idcounter=False) -> bool:
        ok = cmd and (not idcounter or self._id == cmd._id)
        return ok and (self.code & AzdkCmd._codemask) == (cmd.code & AzdkCmd._codemask)

class AzdkDB:
    CTYPES, CTYPE, DTYPES, DTYPE = 'cmdtypes', 'ctype', 'datatypes', 'datatype'
    CMDS, CMD, PARS, PAR = 'commands', 'cmd', 'params', 'par'
    FLAGS, FLAG, REGS, REG = 'flags', 'flag', 'registers', 'reg'
    ERRS, ERR, MODES, MODE = 'errors', 'err', 'wmodes', 'wmode'
    TYPE, RTYPE, DESCR, NAME, SIZE, VAL, COLOR, CODE, BIT = \
        'type', 'rtype', 'descr', 'name', 'size', 'value', 'color', 'code', 'bit'

    BULK_READ_TYPE = 4

    def __init__(self, xmlpath: str = None):
        self.cmdtypes = {}
        self.datatypes = {}
        self.commands = {}
        self.registers = {}
        self.modes = {}
        self.errors = {}
        self.db = {
            self.CTYPES: self.cmdtypes,
            self.DTYPES: self.datatypes,
            self.CMDS: self.commands,
            self.REGS: self.registers,
            self.MODES: self.modes,
            self.ERRS: self.errors
            }
        if isinstance(xmlpath, str):
            self.loadxml(xmlpath)

    def _loadcommand(self, elem):
        _code = elem.get(self.CODE)
        _type = elem.get(self.TYPE) or '0'
        if not _type or not _code: return
        _code = int(_code)
        _type = int(_type)
        _pars = []
        for par in elem.iterfind(self.PAR):
            _psize = par.get(self.SIZE)
            _ptype = par.get(self.TYPE)
            if not _psize: continue
            try:
                match int(_ptype):
                    case 15: _ptype = float
                    case _: _ptype = int
            except (ValueError, TypeError):
                _ptype = int
            _psize = int(_psize)
            _val = par.get(self.VAL)
            _val = int(_val) if _val else 0
            _flags = []
            for flag in par.iterfind(self.FLAG):
                _bit = flag.get(self.BIT)
                if _bit is None: continue
                _bit = int(_bit) if _bit else 0
                _fval = flag.get(self.VAL)
                _fval = int(_fval) if _fval else 0
                FLAG = {\
                    self.NAME: flag.get(self.NAME), \
                    self.BIT: _bit}
                _flags.append(FLAG)
                _val += _fval << _bit
            param = { \
                self.NAME: par.get(self.NAME), \
                self.SIZE: _psize,
                self.TYPE: _ptype,
                self.VAL: _val}
            if len(_flags) > 0:
                param[self.FLAGS] = _flags
            _pars.append(param)

        _rtype = elem.get(self.RTYPE)
        _rtype = int(_rtype) if _rtype else -1

        _color = elem.get(self.COLOR)

        self.commands[_code] = {self.NAME: elem.get(self.NAME), self.TYPE: _type}
        _descr = elem.get(self.DESCR)
        if _color:
            self.commands[_code][self.COLOR] = _color
        #if RTYPE >= 0:
        self.commands[_code][self.RTYPE] = _rtype
        if _descr:
            self.commands[_code][self.DESCR] = _descr
        if len(_pars) > 0:
            self.commands[_code][self.PARS] = _pars

    def loadxml(self, filepath) -> bool:
        try:
            fl = open(filepath, 'rt', encoding='UTF-8')
        except FileNotFoundError:
            print(f'File {filepath} not found')
            return False
        _d = None
        tree = ET.parse(fl)
        subtree = './/'
        for elem in tree.iterfind(subtree + self.CTYPE):
            TYPE = elem.get(self.TYPE)
            if TYPE is None: continue
            self.cmdtypes[int(TYPE)] = {\
                self.DESCR: elem.get(self.DESCR), \
                self.COLOR: elem.get(self.COLOR)}
        for elem in tree.iterfind(subtree + self.DTYPE):
            TYPE = elem.get(self.TYPE)
            if TYPE is None: continue
            SIZE = elem.get(self.SIZE)
            self.datatypes[int(TYPE)] = {\
                self.NAME: elem.get(self.NAME), \
                self.SIZE: int(SIZE) if SIZE else 0}
        for elem in tree.iterfind(subtree + self.REG):
            CODE = elem.get(self.CODE)
            if CODE is None: continue
            FLAGS = elem.get(self.FLAGS)
            self.registers[int(CODE)] = {\
                self.NAME: elem.get(self.NAME), \
                self.DESCR: elem.get(self.DESCR), \
                self.FLAGS: int(FLAGS) if FLAGS else 0}
        for elem in tree.iterfind(subtree + self.CMD):
            self._loadcommand(elem)
        for elem in tree.iterfind(subtree + self.ERR):
            CODE = elem.get(self.CODE)
            if CODE is None: continue
            self.errors[int(CODE)] = {\
                self.NAME: elem.get(self.NAME), \
                self.DESCR: elem.get(self.DESCR)}
        for elem in tree.iterfind(subtree + self.MODE):
            TYPE = elem.get(self.TYPE)
            CODE = elem.get(self.CODE)
            if TYPE is None or CODE is None: continue
            self.modes[(int(TYPE), int(CODE))] = {\
                self.NAME: elem.get(self.NAME), \
                self.DESCR: elem.get(self.DESCR)}
        return True

    def dtype(self, _dtype: int):
        try: return self.datatypes[_dtype]
        except KeyError: return None

    def showcommands(self, jsonlike=False, verbose=False):
        if jsonlike:
            print(json.dumps(self.commands, indent=2, ensure_ascii=False))
        else:
            for k, v in self.commands.items():
                s = f'{k:02X}h: {v[self.NAME]}, type={v[self.TYPE]}'
                if verbose:
                    if self.RTYPE in v:
                        s += f', rtype={v[self.RTYPE]}'
                    if self.DESCR in v:
                        s += f', descr={v[self.DESCR]}'
                    if self.PARS in v:
                        for p in v[self.PARS]:
                            s += f'\n - {p[self.NAME]}, size={p[self.SIZE]}'
                print(s)

    def _showmodes(self, jsonlike=False):
        if jsonlike:
            _dict = {}
            for k, v in self.modes.items():
                _dict[f'{k[0], k[1]}'] = v
            return json.dumps(_dict, indent=2, ensure_ascii=False)
        else:
            for k, v in self.modes.items():
                print(f'{k}h: {v["name"]} ({v["descr"]})')

    def tojson(self, filepath: str):
        try: fl = open(filepath, 'wt', encoding='UTF-8')
        except IOError:
            print('Path does not exist or no write access')
            return
        MODES = {}
        for k1, k2 in self.modes:
            MODES[f'{k1}.{k2:02d}'] = self.modes[(k1, k2)]
        self.db[self.MODES] = MODES
        json.dump(self.db, fl, indent=2, ensure_ascii=False, default=jsonfy)

    def info(self) -> str:
        s = 'AZDK database'
        s += f': {len(self.commands)} commands'
        s += f', {len(self.datatypes)} data types'
        s += f', {len(self.registers)} registers'
        s += f', {len(self.modes)} modes'
        s += f', {len(self.errors)} error types'
        return s

    def _createcmd(self, code, vcmd, params, timeout):
        cmd = AzdkCmd()
        cmd.code = code
        if timeout: cmd.timeout = timeout
        rtype = vcmd[self.RTYPE] if self.RTYPE in vcmd else None
        if rtype in self.datatypes:
            sz = self.datatypes[rtype][self.SIZE]
            if sz: cmd._answersize = sz
        if self.PARS in vcmd:
            for pk, p in enumerate(vcmd[self.PARS]):
                sz = p[self.SIZE]
                pval = 0
                if isinstance(params, list) and len(params) > pk:
                    pval = int(params[pk])
                if sz == 1:
                    cmd.params.append(np.uint8(pval))
                elif sz == 2:
                    cmd.params.append(np.uint16(pval))
                elif sz == 4:
                    cmd.params.append(np.uint32(pval))
        cmd.type = vcmd[self.TYPE]
        return cmd

    def createcmd(self, codename : int, params: list = None, *, timeout=None) -> AzdkCmd:
        if params is not None and not isinstance(params, list):
            params = [params]
        if isinstance(codename, str):
            for code, cmd in self.commands.items():
                if cmd[self.NAME] == codename:
                    return self._createcmd(code, cmd, params, timeout)
        elif isinstance(codename, int):
            if codename in self.commands:
                return self._createcmd(codename, self.commands[codename], params, timeout)
        return None

    def answer(self, code : int, answer : bytes):
        code = code & AzdkCmd._codemask
        if not code in self.commands:
            return answer
        rtype = self.commands[code][self.RTYPE]
        match rtype:
            case  4: return struct.unpack('i', answer)[0]
            case  3: return struct.unpack('I', answer)[0]
            case  2: return struct.unpack('H', answer)[0]
            case  1: return struct.unpack('B', answer)[0]
            case 10: return quatntime_from_bytes(answer)
            case 16: return angvelntime_from_bytes(answer)
            case 12: return np.frombuffer(answer, np.int32)
            case  7:
                d = np.frombuffer(answer, np.int32)
                if len(d) == 4: return Quaternion(d*(2**-30))
            case 6:
                d = np.frombuffer(answer, np.int32)
                if len(d) == 3: return Vector(d*(2**-30))
        return answer

    def answer_str(self, cmd: AzdkCmd) -> str:
        answer = self.answer(cmd.code, cmd.answer)
        if isinstance(answer, tuple) or isinstance(answer, np.ndarray):
            return ', '.join(str(x) for x in answer)
        if isinstance(answer, bytes):
            return cmd.answer.hex(' ').upper()
        return str(answer)

    def cmdinfo(self, cmd: AzdkCmd) -> str:
        code = cmd.code & 0x7F
        if not code in self.commands:
            return None
        s = f'CMD({code}, id={cmd._id}), '
        s += self.commands[code][self.NAME]

        if len(cmd.params) > 0:
            s += ', p=['
            for p in cmd.params: s += str(p)
            s += ']'

        answ_str = self.answer_str(cmd)
        if isinstance(answ_str, str) and len(answ_str) > 0:
            s += ': ' + answ_str
        return s

    def cmdname(self, cmd: AzdkCmd) -> str:
        if not cmd.code in self.commands:
            return None
        return self.commands[cmd.code][self.NAME]

    def cmd(self, _code: int) -> AzdkCmd:
        return self.commands[_code]

    def findcmd(self, _name: str):
        for _, v in self.commands.items():
            if v[self.NAME] == _name:
                return v
        return None

    def error(self, _err: int) -> str:
        if _err in self.errors:
            return self.errors[_err]
        else:
            return ''

class WState:
    def __init__(self) -> None:
        self.wmode = 0
        self.rmode = 0
        self.specmode = False
        self.progress = 0.0
        self.werr = 0
        self.cmderr = 0
        self.cmdlast = 0
        self.temp = 0
        self.sflags = 0

        self.readstage = 0
        self.calerr = 0
        self.cmosflags = 0

        self.backgr = 0
        self.dark = 0

    def __str__(self) -> str:
        s = 'Azdk state: '
        s += f'wm={self.wmode}, rm={self.rmode}, sp={self.specmode}, pr={self.progress}'
        s += f', werr={self.werr}, cerr={self.cmderr}, lc={self.cmdlast}'
        s += f', T={self.temp}, sig={self.sflags}, cnt={self.calerr}'
        s += f', bgrd={self.backgr}, dark={self.dark}'
        return s

    def from_buffer(self, d: bytes):
        if len(d) != 16: return
        self.wmode = d[0] & 0x0F
        self.rmode = (d[0] >> 4) & 0x03
        self.specmode = d[0] > 127
        self.progress = float(d[1]) / 2.25
        self.werr = d[2]
        self.cmderr = d[3]
        self.cmdlast = d[4]
        self.temp = d[5] * 0.5 - 40.0
        self.sflags = np.uint16(d[6] + d[7]*256)
        self.readstage = d[8]
        self.calerr = d[9]
        self.cmosflags = np.uint16(d[10] + d[11]*256)
        self.backgr = np.uint16(d[12] + d[13]*256)
        self.dark = np.uint16(d[14] + d[15]*256)

    @classmethod
    def from_bytes(cls, d: bytes):
        if len(d) != 16: return None
        ws = cls()
        ws.from_buffer(d)
        return ws

class AzdkPort:
    def __init__(self, portname, baudrate) -> None:
        self.port = serial.Serial(portname, baudrate) if portname else None
        self.cmd = None
        self.buffer = b''
        self.cmdidcounter = False
        self.echo = False

    def open(self, portname=None, baudrate=None) -> bool:
        if not self.port:
            self.port = serial.Serial()
        elif self.port.isOpen():
            self.port.close()
        if portname: self.port.name = portname
        if baudrate: self.port.baudrate = baudrate
        try:
            self.port.open()
            return True
        except SerialException:
            return False

    def close(self):
        if self.port:
            self.port.close()

    def cmdtobytes(self, cmd: AzdkCmd):
        raise NotImplementedError()

    def readbuffer(self, expectedCmd: AzdkCmd = None) -> AzdkCmd:
        raise NotImplementedError()

    def isbusy(self) -> bool:
        return self.cmd is not None

class AzdkRS485(AzdkPort):
    _address = b'\xA0'

    def __init__(self, portname=None, baudrate=115200, parity='N', stopbits=1, databits=8) -> None:
        super().__init__(portname, baudrate)
        if databits: self.port.bytesize = databits
        if stopbits: self.port.stopbits = stopbits
        if parity: self.port.parity = parity

    def sendarray(self, d: bytes):
        if self.port and self.port.isOpen():
            #self.cmd = None
            self.port.write(d)
            self.port.flush()
            if self.echo:
                print('TX: ' + d.hex(' ').upper())

    def cmdtobytes(self, cmd: AzdkCmd):
        d = b''
        d += self._address
        d += np.uint8(cmd.code)
        if self.cmdidcounter:
            d += np.uint8(cmd._id)
        dd = b''
        for x in cmd.params:
            dd += x.tobytes()
        d += np.uint8(len(dd))
        d += dd
        d += AzdkCRC.crc8(d)
        return d

    def _readanswer(self) -> bool:
        sz = self.cmd._answersize
        self.cmd.answer = self.buffer[:sz]
        self.cmd.updatetime = time.perf_counter()
        self.cmd.crc = AzdkCRC.crc8(self.cmd.answer, self.cmd.crc)
        crc = self.buffer[sz]
        self.buffer = self.buffer[sz+1:]
        if self.cmd.crc != crc:
            return False
        if self.cmd.type == AzdkDB.BULK_READ_TYPE and len(self.cmd.answer) >= 4:
            self.cmd._datasize = int.from_bytes(self.cmd.answer[:4], 'little')
        return True

    def _readdata(self):
        ks = self.buffer.find(self._address)
        szBuf = len(self.buffer)
        # check header package size
        kk = ks + len(self._address)
        if ks < 0 or szBuf < kk + 4: return
        pkgSz = self.buffer[kk + 3]
        kn = kk + 5 + pkgSz
        # check full package size
        if szBuf < kn: return
        #TODO check package number
        #pkgNum = self.buffer[kk + 1] + self.buffer[kk + 2]*256
        # check command code and skip package
        if (self.cmd.code & AzdkCmd._codemask) != self.buffer[kk] or pkgSz < 1:
            self.buffer = self.buffer[kn:]
            return
        if self.buffer[kn-1] != AzdkCRC.crc8(self.buffer[ks:kn-1]):
            self.cmd.error = 255
        self.cmd.updatetime = time.perf_counter()
        self.cmd.data += self.buffer[kk+4:kn-1]
        self.buffer = self.buffer[kn:]

    def readbuffer(self, expectedCmd: AzdkCmd = None) -> AzdkCmd:
        self.buffer += self.port.read_all()
        if self.cmd is None:
            k = self.buffer.find(self._address)
            kp = k + (5 if self.cmdidcounter else 4)
            if k < 0 or len(self.buffer) < kp: return
            kk = k + len(self._address) + 1
            self.cmd = AzdkCmd()
            self.cmd.code = self.buffer[kk - 1]
            if self.cmdidcounter:
                self.cmd._id = self.buffer[kk]
                kk += 1
            if self.cmd.issame(expectedCmd, self.cmdidcounter):
                self.cmd = expectedCmd
            sz = self.buffer[kk]
            self.cmd.crc = AzdkCRC.crc8(self.buffer[k:kp-1])
            self.buffer = self.buffer[kp-1:]
            if sz > 0xF0 or sz == 0:
                self.cmd._answersize = 0
                self.cmd.error = sz
                crc = self.buffer[0]
                self.buffer = self.buffer[1:]
                cmd = self.cmd
                self.cmd = None
                return cmd if cmd.crc == crc else None
            self.cmd._answersize = sz
        else:
            sz = self.cmd._answersize
        if len(self.cmd.answer) == sz:
            self._readdata()
        elif len(self.buffer) > sz and len(self.cmd.answer) == 0:
            if not self._readanswer():
                self.cmd = None
                return None
        if self.cmd and self.cmd.isready():
            cmd = self.cmd
            self.cmd = None
            if self.echo:
                print('cmd ' + str(cmd) + ' received')
            return cmd

class AzdkConnect(Thread):
    _maxqueuesize = 16
    ParityEven = 'E'
    ParityOdd = 'O'
    ParityNone = 'N'

    def __init__(self, portname, baudrate, *, porttype=AzdkRS485, parity='E', stopbits=1, databits=8, idcounter=False, verbose=False) -> None:
        super().__init__()
        self.cmdqueue = []
        self.cmdsent = None
        self.cmdready = []
        self.portname = portname
        self.baudrate = baudrate
        self.parity = parity
        self.stopbits = stopbits
        self.databits = databits
        self._mutex = Lock()
        self._running = False
        self._stopped = False
        self._porttype = porttype
        self._idcmdcounter = idcounter
        self.verbose = verbose

    def _sendcmd(self, port: AzdkPort):
        if port.isbusy(): return False
        if self.cmdsent: return False
        if len(self.cmdqueue) == 0: return False
        if not self._mutex.acquire(False): return False
        self.cmdsent = self.cmdqueue[0]
        del self.cmdqueue[0]
        d = port.cmdtobytes(self.cmdsent)
        if self.verbose:
            print(f'cmd {self.cmdsent} sent')
        self._mutex.release()
        self.cmdsent.sendtime = time.perf_counter()
        self.cmdsent.updatetime = None
        port.sendarray(d)
        return True

    def _check_is_in_queue(self, cmd: AzdkCmd):
        self._mutex.acquire()
        ok = cmd in self.cmdqueue
        self._mutex.release()
        return ok

    def _check_is_sent(self, cmd: AzdkCmd):
        self._mutex.acquire()
        ok = self.cmdsent and (cmd == self.cmdsent)
        self._mutex.release()
        return ok

    def _check_cmd_isready(self, cmd: AzdkCmd):
        self._mutex.acquire()
        ok = (cmd in self.cmdready)
        self._mutex.release()
        return ok

    def _enqueueready(self, cmd: AzdkCmd):
        self._mutex.acquire()
        #replace notifications
        for kr, cmdr in enumerate(self.cmdready):
            if cmd.code == cmdr.code and cmd._id == cmdr._id:
                self.cmdready[kr] = cmd
                break
        else:
            self.cmdready.append(cmd)
        self._mutex.release()

    def run(self):
        self._running = True
        if self.verbose:
            print(f'Starting port {self._porttype} thread')
        if self._porttype == AzdkRS485:
            _port = AzdkRS485(self.portname, self.baudrate, self.parity, self.stopbits, self.databits)
            _port.cmdidcounter = self._idcmdcounter
        elif self._porttype is None:
            self._running = False
            self._stopped = True
            return False
        else:
            _port = self._porttype(self.portname, self.baudrate)
        if not _port.open(): return False

        _port.echo = self.verbose

        while self._running:
            if self._sendcmd(_port):
                time.sleep(0.02)
            cmd = _port.readbuffer(self.cmdsent)
            if self.cmdsent:
                if self.cmdsent.issame(cmd, self._idcmdcounter):
                    self.cmdsent.answer = cmd.answer
                    self.cmdsent.data = cmd.data
                    cmd = self.cmdsent
                    self.cmdsent = None
                elif self.cmdsent.istimeout():
                    if self.verbose:
                        print('cmd ' + str(self.cmdsent) + f' timeout ({self.cmdsent.timeout} sec)')
                    self.cmdsent = None
                    _port.cmd = None
            if cmd:
                self._enqueueready(cmd)
                cmd = None
            time.sleep(0.01)
        _port.close()
        self._stopped = True
        if self.verbose:
            print(f'Port {self._porttype} has been stopped')
        return True

    def stop(self):
        self._running = False
        self.join()

    def enqueuecmd(self, cmd: AzdkCmd):
        if not self.is_alive():
            return False
        if len(self.cmdqueue) < self._maxqueuesize and self._mutex.acquire():
            cmd.clear()
            self.cmdqueue.append(cmd)
            self._mutex.release()
            time.sleep(0.01)
            return True
        return False

    def waitforanswer(self, cmd: AzdkCmd):
        if not self.is_alive():
            return False
        while self._check_is_in_queue(cmd):
            time.sleep(0.01)
        ok = self._check_cmd_isready(cmd)
        if not self._check_is_sent(cmd) and not ok:
            return False
        while not ok:
            time.sleep(0.01)
            if cmd.istimeout():
                return False
            ok = self._check_cmd_isready(cmd)
        self._mutex.acquire()
        self.cmdready.remove(cmd)
        self._mutex.release()
        return True

    def get_notification(self, code: int = None) -> AzdkCmd | None:
        cmd = None
        self._mutex.acquire()
        for k, xcmd in enumerate(self.cmdready):
            if code is None or xcmd.code == code:
                cmd = self.cmdready[k]
                del self.cmdready[k]
                break
        self._mutex.release()
        return cmd

    def sendcmd(self, cmd: AzdkCmd, db: AzdkDB = None) -> bool:
        if not self.enqueuecmd(cmd):
            return False
        if not self.waitforanswer(cmd):
            return False
        if cmd.error > 0:
            if db and self.verbose:
                print(f'Error on cmd {db.cmdname(cmd)}: {db.error(cmd.error)}')
            return False
        return True

    def getframe(self, db: AzdkDB = None, *, showprogress=True, timeout=1, subframe: list = None) -> Pgm:
        if subframe:
            cmdGetFrame = db.createcmd(24, subframe, timeout=timeout)
        else:
            cmdGetFrame = db.createcmd(23, timeout=timeout)

        if not self.enqueuecmd(cmdGetFrame):
            return None
        while not cmdGetFrame.isanwerready():
            time.sleep(0.1)
            if cmdGetFrame.istimeout():
                return None

        hdr = np.frombuffer(cmdGetFrame.answer[4:], np.uint16)
        nsec = int(hdr[0]) * int(hdr[1]) * 12 / self.baudrate

        pbar = None
        if showprogress and tqdm and nsec > 3.0:
            pbar = tqdm(desc='Obtaining frame', bar_format='{l_bar}{bar}', total=cmdGetFrame._datasize)

        while not cmdGetFrame.isready():
            time.sleep(0.1)
            if pbar:
                pbar.n = len(cmdGetFrame.data)
                pbar.update(0)
            if cmdGetFrame.istimeout():
                return None

        if pbar: pbar.close()

        data = np.frombuffer(cmdGetFrame.data, np.uint16)
        pgm = Pgm(hdr[0], hdr[1], dtype=np.uint16, maxval=max(data), _d=data)
        if len(hdr) > 2:
            pgm._pars['id'] = hdr[2] + hdr[3]*65536
        if len(hdr) > 4:
            pgm._pars['dark'] = hdr[4]
        if len(hdr) > 5:
            pgm._pars['exp'] = hdr[5]
        if len(hdr) > 9:
            mses = hdr[6] + hdr[7]*65536
            pgm._pars['time'] = datetime(hdr[9], 1, 1) + timedelta(int(hdr[8]), seconds=mses*0.001)
        if len(hdr) > 15:
            x = hdr[10] + hdr[11]*65536
            y = hdr[12] + hdr[13]*65536
            z = hdr[14] + hdr[15]*65536
            pgm._pars['vel'] = Vector(x, y, z) * (2**-30 * 180/np.pi)
        return pgm

    def clearready(self):
        self._mutex.acquire()
        self.cmdready.clear()
        self._mutex.release()

def azdkdbtest1(xmlpath: str):
    db = AzdkDB(xmlpath)

    conn = AzdkConnect('COM3', 500000, idcounter=True)
    conn.start()

    while conn.is_alive():
        qcmd_notif = conn.get_notification()
        if qcmd_notif:
            print(db.cmdinfo(qcmd_notif))
        #cmd = db.createcmd(16)
        #cmd.timeout = 1.0
        #if conn.enqueuecmd(cmd):
        #    if conn.waitforanswer(cmd):
        #        print(db.cmdinfo(cmd))
        time.sleep(0.05)

def azdkdbtest2(xmlpath: str):
    db = AzdkDB(xmlpath)
    print(db.info())
    cmd = db.createcmd(16)
    cmd_d = AzdkRS485().cmdtobytes(cmd)
    print(cmd, 'cmd_data=' + cmd_d.hex(' ').upper(), sep=', ')

def azdkdbtest3(xmlpath: str):
    wdir, filename = path.split(xmlpath)
    db = AzdkDB(xmlpath)
    print(db.info())
    db.showcommands(verbose=True)
    db._showmodes()
    db.tojson(wdir + filename + '.json')

if __name__ == "__main__":
    db = AzdkDB('AZDKHost.xml')
    print(2)
