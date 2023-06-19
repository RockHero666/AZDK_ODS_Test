from PyQt5.QtCore import QThread
import xml.etree.ElementTree as ET
from azdk.azdksocket import AzdkServerCmd, PDSServerCmd, PDSServerCommands, AzdkServerCommands
from azdk.azdkdb import AzdkDB
from azdk.linalg import Quaternion, Vector
import numpy as np 
import os

def is_float(string):
    try:
        int(string)
        return False
    except:
        try:
            float(string)
            return True
        except ValueError:
            return False

class PressetCmd:

    def __init__(self, duration_cycle, count_cycle, type_p):
        self.type_p = type_p
        self.duration_cycle = duration_cycle
        self.count_cycle = count_cycle

class Scenario(QThread):
     all_commands = []
     commands = []

     def parse(self,xml_file=None):
        try:
            fl = open(xml_file, 'rt', encoding='UTF-8')
            tree = ET.parse(fl)
        except Exception:
            if xml_file:
                tree = ET.fromstring(xml_file)
            else:
                return False


        current_file = os.path.abspath(__file__)
        directory = os.path.dirname(current_file)
        db = AzdkDB(directory+'/AZDKHost.xml')

        for root in tree.iterfind("scenario"):

             for branch in root.iterfind("azdkservercmd"):
                 code = int(branch.get("code"))
                 timeout = float(branch.get("timeout"))
                 cmd = AzdkServerCmd(AzdkServerCommands(code), [], None, timeout)
                 cmd.name = branch.get("descr")
                 params = []

                 critical_cmd = True
                 critical_cmd = not bool(branch.get("non_critical"))

                 for leaf in branch.iterfind("par"):
                    params.append(leaf.text)

                 if(len(params) > 0):
                    cmd.setparams(params)

                 self.commands.append([cmd, critical_cmd])

             for branch in root.iterfind("pdscmd"):
                 code = int(branch.get("code"))
                 timeout = float(branch.get("timeout"))
                 cmd = PDSServerCmd(PDSServerCommands(code), [], None, timeout)
                 cmd.name = branch.get("descr")
                 params = []

                 critical_cmd = True
                 critical_cmd = not bool(branch.get("non_critical"))

                 for leaf in branch.iterfind("par"):
                    match code:
                        case PDSServerCommands.SET_RANDOM_MODE.value:
                            params.append(float(leaf.text))
                        case PDSServerCommands.SET_STATE.value:
                            params.append(int(leaf.text))
                        case PDSServerCommands.SET_ORIENT.value:
                            params.append(Quaternion.fromstr(leaf.text))
                        case PDSServerCommands.SET_POS.value:
                            params.append(Vector.fromstr(leaf.text))
                        case PDSServerCommands.SET_ANGVEL.value:
                            params.append(Vector.fromstr(leaf.text))
                        case PDSServerCommands.SET_POINT_SETTINGS.value:
                            arr = leaf.text.split(", ")
                            for num in arr:
                                params.append(float(num))

                 if(len(params) > 0):
                    cmd.setparams(params)

                 self.commands.append([cmd, critical_cmd])

             for branch in root.iterfind("azdkcmd"):
                 
                 params = []

                 critical_cmd = True
                 critical_cmd = not bool(branch.get("non_critical"))
                 code = int(branch.get("code"))
                 

                 for leaf in branch.iterfind("par"):
                     if code == 13 or code == 7:
                        if is_float(leaf.text) :
                            result = np.int32(float(leaf.text)*2**30)
                            params.append(result)
                        else:
                            params.append(np.int32(leaf.text)) 
                     else:    
                        params.append(leaf.text)



                 
                 timeout = float(branch.get("timeout"))
                 cmd = db.createcmd(code,params)
                 cmd.name = branch.get("descr")
                 cmd.timeout = timeout


                 
                 
                 self.commands.append([cmd, critical_cmd])

             for branch in root.iterfind("pressetcmd"):
                 cmd = PressetCmd(branch.get("duration_cycle"), branch.get("count_cycle"), int(branch.get("type")))
                 critical_cmd = True
                 critical_cmd = not bool(branch.get("non_critical"))

                 self.commands.append([cmd, critical_cmd])
             
             self.all_commands.append(self.commands)
             self.commands = []

        

        return True
