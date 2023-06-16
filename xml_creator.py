from enum import Enum
import xml.etree.ElementTree as ET
from azdk.azdksocket import PDSServerCommands, AzdkServerCommands

class AzdkCommands(Enum):
    RESTART                  = 1           
    RESET                    = 2          
    DATE                     = 3            
    REGISTR                  = 4 
    SET_FLAGS                = 5         
    CHANGE_FLAGS             = 32        
    ANGL_SPEED_KA            = 6    
    ANGL_SPEED               = 7       
    DURATION_OF_ACCUMULATION = 8   
    SCREEN_GEOMETRY          = 9   
    FPY_FLAGS                = 10        
    SET_PARAMS               = 11
    SET_SK_KA                = 13
    CURTAIN                  = 14
    PELTIER                  = 15
    STATE                    = 16
    AZDK_REGISTR             = 17
    REED_ANGLE_SPEED         = 18
    REED_ANGLE_SPEED_MODEL   = 19
    REED_LAST_QUAT           = 20
    REED_DATE_TIME           = 21
    REED_LIST_FOTO           = 22
    REED_FRAME               = 23
    REED_SUBSCREEN           = 24
    REED_WINDOWS             = 25
    STATISTICS               = 26
    REED_PARAMS              = 27
    REED_FOCUS_OBJECT        = 28
    REED_LIST_NON_STARS      = 29
    SET_SPEED_RS485          = 30
    SET_SPEED_CAN            = 31
    STANDBY_MODE             = 48
    AUTO_MODE                = 49
    COMMAND_MODE             = 50
    CALIB_DARK_CURRENT_MOD   = 51
    CALIB_MEMS_GIRO_MOD      = 52
    REED_RAW_FRAME_MODE      = 53
    FRAME_AVERAGE_MODE       = 57
    SAVE_ALL_DATA_FLASH      = 64
    SAVE_PROPERTIES_FLASH    = 67
    REED_DATA                = 68
    SAVE_DATA                = 69
    REED_SOFT_VERSION        = 70
    UPDATE_SOFT              = 71
    SET_NUMBER_AZDK          = 72
    OVERWRITING_SOFT         = 73
    RETURN_TO_LOADER         = 75
    PROPERTIES_NOTIFICATION  = 76

    
    @classmethod
    def getname(cls, code: int):
        for _name, _value in cls.__members__.items():
            if _value.value == code:
                return _name
        return None

    @classmethod
    def findname(cls, name: str):
        return cls.__members__[name].value



def str_to_xml(psevdocode):

    scenariofile = ET.Element("scenariofile")

    lines_text = psevdocode.splitlines()

    for elems in lines_text:

        if elems == "scenario":
            scen = ET.Element("scenario")
            scenariofile.append(scen)
            continue
            
        split_text = elems.split()

        while len(split_text) < 5: #создаем пустые ячейки что бы не багал аут оф ренж
            split_text.append(None)

        if split_text[3]:
            params = split_text[3].split(":")
            params_list = []
            for param in params:
                if split_text[0] == "azdkservercmd" and split_text[2] == "SET_LOG_TEMPLATE" :
                    param_element = ET.Element("par",attrib={'name': 'name'})
                    param_element.text = params[0]
                    params_list.append(param_element)
                    param_element = ET.Element("par",attrib={'type': 'type'})
                    param_element.text = params[1]
                    params_list.append(param_element)
                    break
                elif split_text[0] == "pdscmd":
                    param_element = ET.Element("par")
                    param_pack = ""
                    for pdsparam in params:
                        param_pack += str(pdsparam) + ", "
                    param_element.text = param_pack
                    params_list.append(param_element)
                    break
                    

                else:
                    param_element = ET.Element("par")
                    param_element.text = param
                    params_list.append(param_element)
        else:
            params_list = []
            param_element = ET.Element("none")
            param_element.text = "none"
            params_list.append(param_element)

        if not split_text[4]:
            split_text[4] = str(0.1)
        

        if split_text[0] == "azdkcmd":
            code = str(AzdkCommands.findname(split_text[2]))
        elif split_text[0] == "azdkservercmd":
            code = str(AzdkServerCommands.findname(split_text[2]))
        elif split_text[0] == "pdscmd":
            code = str(PDSServerCommands.findname(split_text[2]))
        else:
            print("error psevdo")
            return


        cmd_attrs = {"descr": split_text[1], "code": code, "timeout": split_text[4]}
        
        for elem in split_text:
            if elem == "non_crit":
                cmd_attrs["non_critical"] = "true"
        
        command = ET.Element(split_text[0], cmd_attrs)
        for param_element in params_list:
            command.append(param_element)

        scen.append(command)
    

    xml = ET.tostring(scenariofile, encoding="unicode")
    
    with open("user.xml","w") as f:
        f.write(xml)
    return xml

if __name__ == '__main__':
    str_to_xml("s")