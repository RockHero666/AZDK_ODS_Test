
import xml.etree.ElementTree as ET
from azdk.azdksocket import PDSServerCommands, AzdkServerCommands
from AzdkCommands import AzdkCommands




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
    
    #with open("user.xml","w") as f:
    #    f.write(xml)
    return xml

if __name__ == '__main__':
    str_to_xml("s")