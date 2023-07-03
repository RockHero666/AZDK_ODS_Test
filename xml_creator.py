
import re
import xml.etree.ElementTree as ET
from azdk.azdksocket import PDSServerCommands, AzdkServerCommands
from AzdkCommands import AzdkCommands , get_scenario_dict
import xml.dom.minidom

def parse_command_string(command_string):
    command_name = ""
    parameters = []
    timeout = 0
    critical = True
    
    # Извлекаем данные внутри фигурных скобок
    pattern = r"\{([^}]*)\}"  
    
    
    matches = re.search(pattern, command_string)
    
    if matches:
        parameters_str = matches.group(1)
        parameters = [x for x in parameters_str.split(",")] if "," in parameters_str else []
    
    
    timeout_match = re.search(r"timeout=([\d.]+)", command_string)
    if timeout_match:
        timeout = float(timeout_match.group(1))
    else:
        timeout = 0.1
        
    critical_match = re.search(r"critical=(\w+)", command_string)
    if critical_match:
        if critical_match.group(1).lower() == 'true' or critical_match.group(1).lower() == 'True':
            critical = True
        elif critical_match.group(1).lower() == 'false' or critical_match.group(1).lower() == 'False':
            critical = False
    
    
    # Извлекаем имя команды из строки
    command_name_match = re.search(r"([a-zA-Z_|a-zA-Z]+)\(", command_string)
    if command_name_match:
        command_name = command_name_match.group(1)
    
    return command_name, parameters, timeout, critical


def str_to_xml(psevdocode):

    scenariofile = xml.dom.minidom.Document()
    scen = scenariofile.createElement("scenariofile")
    scenariofile.appendChild(scen)

    _dict = get_scenario_dict()

    lines_text = psevdocode.splitlines()
    
    scen_elem = scenariofile.createElement("scenario")
    scen.appendChild(scen_elem)

    for elems in lines_text:

        command_name, parameters, timeout, critical = parse_command_string(elems)

        split_command_name = command_name.split("_")
        real_command_name = None

        if split_command_name[0] == "azs":
            real_command_name = "azdkservercmd"
        elif split_command_name[0] == "pds":
            real_command_name = "pdscmd"
        elif split_command_name[0] == "azdk":
            real_command_name = "azdkcmd"
        else:
            print("Неверный синтаксис команды")
            return

        

        code = str(_dict[command_name].code)

        cmd_attrs = {"descr": _dict[command_name].descr, "code": code, "timeout": str(timeout)}

        if critical:
            cmd_attrs["critical"] = "true"
        else:
            cmd_attrs["critical"] = "false"

        command = scenariofile.createElement(real_command_name)
        for attr_name, attr_value in cmd_attrs.items():
            command.setAttribute(attr_name, attr_value)

        if not real_command_name == "pdscmd":

            if parameters:
                for param in parameters:
                    param_element = scenariofile.createElement("par")
                    param_element.appendChild(scenariofile.createTextNode(str(param)))
                    command.appendChild(param_element)
            else:
                param_element = scenariofile.createElement("none")
                param_element.appendChild(scenariofile.createTextNode("none"))
                command.appendChild(param_element)
        else:
            par=""
            for index, param in enumerate(parameters):
                if index == 0:
                    par +=  param 
                else:
                    par += ", " + param 
            
            if parameters:
                
                param_element = scenariofile.createElement("par")
                param_element.appendChild(scenariofile.createTextNode(str(par)))
                command.appendChild(param_element)
            else:
                param_element = scenariofile.createElement("none")
                param_element.appendChild(scenariofile.createTextNode("none"))
                command.appendChild(param_element)
            



        scen_elem.appendChild(command)

    xml_str = scenariofile.toprettyxml(indent="\t")

    with open("last_create_scen.xml", "w", encoding="utf-8") as f:
        f.write(xml_str)

    return xml_str


if __name__ == '__main__':
    command_string = 'azs_set_log_template({azdk_test,7}, critical=false,timeout=5)'
    xml = str_to_xml("azs_set_log_template({azdk_test,7}, critical=false,timeout=5)\n azs_set_log_template({azdk_test,7}, critical=false,timeout=5)\n")
    print(xml)  