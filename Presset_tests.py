from threading import Thread

class Presset_switcher():

    def __init__(self):
        self.pressets = {}

    def add_presset(self, type_p, func_obj: Thread):
        self.pressets[type_p] = func_obj
    
    def stop(self):
        for key, value in self.pressets:
            value.stop()

    def exec_presset(self, type_p):
        func_obj = self.pressets[type_p] 
        if func_obj is None: 
            print ("error")
            return
        func_obj.start()














def exec_presset(self, duration_cycle, count_cycle, type_p, azdk_socket, pds_socket):
        func = self.pressets[type_p] 
        if func is None: 
            print ("error")
            return
        func(duration_cycle, count_cycle, azdk_socket, pds_socket)