from PyQt5.QtCore import QThread
import xml.etree.ElementTree as ET
from azdk.azdksocket import AzdkServerCmd, PDSServerCmd, PDSServerCommands, AzdkServerCommands
from azdk.azdkdb import AzdkDB
from azdk.linalg import Quaternion, Vector

class PressetCmd:

    def __init__(self, duration_cycle, count_cycle, type_p):
        self.type_p = type_p
        self.duration_cycle = duration_cycle
        self.count_cycle = count_cycle

class Scenario(QThread):
     commands = []

     def parse(self,filepath=""):
        try:
            fl = open(filepath, 'rt', encoding='UTF-8')
        except FileNotFoundError:
            print(f'File {filepath} not found')
            return False
        tree = ET.parse(fl)
        subtree = './/'
        db = AzdkDB('AZDKHost.xml')

        for root in tree.iterfind(subtree+"scenario"):

             for branch in root.iterfind(subtree+"azdkservercmd"):
                 code = int(branch.get("code"))
                 timeout = float(branch.get("timeout"))
                 cmd = AzdkServerCmd(AzdkServerCommands(code), [], None, timeout)
                 cmd.name = branch.get("descr")
                 params = []

                 critical_cmd = True
                 critical_cmd = not bool(branch.get("non_critical"))

                 for leaf in branch.iterfind(subtree+"par"):
                    params.append(leaf.text)

                 if(len(params) > 0):
                    cmd.setparams(params)

                 self.commands.append([cmd, critical_cmd])

             for branch in root.iterfind(subtree+"pdscmd"):
                 code = int(branch.get("code"))
                 timeout = float(branch.get("timeout"))
                 cmd = PDSServerCmd(PDSServerCommands(code), [], None, timeout)
                 cmd.name = branch.get("descr")
                 params = []

                 critical_cmd = True
                 critical_cmd = not bool(branch.get("non_critical"))

                 for leaf in branch.iterfind(subtree+"par"):
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

             for branch in root.iterfind(subtree+"azdkcmd"):
                 code = int(branch.get("code"))
                 timeout = float(branch.get("timeout"))
                 cmd = db.createcmd(code)
                 cmd.name = branch.get("descr")
                 cmd.timeout = timeout
                 params = []

                 critical_cmd = True
                 critical_cmd = not bool(branch.get("non_critical"))

                 for leaf in branch.iterfind(subtree+"par"):
                     params.append(leaf.text)

                 if(len(params) > 0):
                    cmd.params = params
                 
                 self.commands.append([cmd, critical_cmd])

             for branch in root.iterfind(subtree+"pressetcmd"):
                 cmd = PressetCmd(branch.get("duration_cycle"), branch.get("count_cycle"), int(branch.get("type")))
                 critical_cmd = True
                 critical_cmd = not bool(branch.get("non_critical"))

                 self.commands.append([cmd, critical_cmd])

        return True
