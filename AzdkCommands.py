import os
from enum import Enum
from azdk.azdksocket import AzdkServerCommands, PDSServerCommands
from azdk.azdkdb import AzdkDB

class AzdkCommands(Enum):
    RESTART = 1
    RESET_SETTINGS = 2
    SET_DATETIME = 3
    SET_REGISTER = 4
    SET_CTRL_FLAGS = 5
    SET_SAT_VEL = 6
    SET_ANGVEL = 7
    SET_EXP_TIME = 8
    SET_FRAME_RECT = 9
    SET_SENSOR_FLAGS = 10
    SET_SETTINGS = 11
    SET_SAT_REF = 13
    TOGGLE_SHUTTER = 14
    TOGGLE_PELTIER = 15

    GET_STATE = 16
    GET_REGISTER = 17
    GET_ANGVEL = 18
    GET_ANGVEL_MODEL = 19
    GET_ATTITUDE = 20
    GET_DATETIME = 21
    GET_PHC_LIST = 22
    GET_FRAME = 23
    GET_SUBFRAME = 24
    #GET_WINDOWS = 25
    GET_STATISTICS = 26
    GET_SETTINGS = 27
    #GET_TARGET = 28
    #GET_OBJECT_LIST = 29
    SET_RS485_SPEED = 30
    SET_CAN_SPEED = 31

    SET_IDLE_MODE = 48
    SET_AUTO_MODE = 49
    #SET_SYNC_MODE = 50
    #SET_DARK_CALIBRATION_MODE = 51
    SET_AVC_CALIBRATION_MODE = 52
    SET_RAW_FRAME_MODE = 53
    SET_FRAME_AVG_MODE = 57

    WRITE_ROM_DATA = 64
    SAVE_SETTINGS = 65
    READ_RAM_DATA = 68
    UPLOAD_RAM_DATA = 69
    GET_FW_VERSION = 70
    UPDATE_FW = 71
    SET_DEVICE_ID = 72

    UPLOAD_FW_PART = 73
    BOOTLOAD_MODE = 75
    SETUP_NOTIFICATIONS = 76

    #NOTIF_RESTART = 112
    #NOTIF_STATE = 113
    #NOTIF_QUAT = 114
    #NOTIF_ANGVEL = 115
    #NOTIF_TARGET = 117
    #NOTIF_PHCS = 118

    @property
    def code(self) -> int:
        return super().value

    @property
    def descr(self, db : AzdkDB) -> str:
        return db.commands[self.value]['name']
    
    @classmethod
    def getname(cls, code: int):
        for _name, _value in cls.__members__.items():
            if _value.value == code:
                return _name
        return None

    @classmethod
    def findname(cls, name: str):
        return cls.__members__[name].value

class AzdkCmdStruct:
    def __init__(self, code, descr):
        self.code = code
        self.descr = descr

def get_scenario_dict():
    d = dict()
    db = AzdkDB('AZDKHost.xml')

    for name, cmd in AzdkServerCommands.__members__.items():
        name = 'azs_' + name.lower()
        d[name] = cmd

    for name, cmd in PDSServerCommands.__members__.items():
        name = name.lower()
        if name.endswith('_on'): continue
        d['pds_' + name] = cmd

    for name, code in AzdkCommands.__members__.items():
        name = 'azdk_' + name.lower()
        try: d[name] = AzdkCmdStruct(code.value, db.commands[code.value]['name'])
        except KeyError: pass

    return d

def scenario_dict_test():
    _dict = get_scenario_dict()
    for cmd, info in _dict.items():
        print(f'{cmd}: {info.code}, {info.descr}')


   