import numpy as np
import inspect

from helpers.printtools import *


def safe_sqrt(arg):
    if arg >= 0.:
        return np.sqrt(arg)
    else:
        info=inspect.getouterframes( inspect.currentframe() )[1]
        p_print(red("Warning: ")+"Sqrt received invalid value "+str(arg)+". Is set to 0.")
        indent_in()
        p_print("line:     "+str(info.code_context[0])[:-1])
        p_print("function: "+str(info.function))
        p_print("file:     "+str(info.filename))
        p_print("line no:  "+str(info.lineno)+"\n")
        indent_out()
        return 0.

class Empty():
    pass

class ListAndArrays():

    def __init__(self,list_in):
        self._list=list_in

    def __getattr__(self,key):
        return [getattr(e,key) for e in self._list]

    def __getitem__(self,index):
        return self._list[index]

    def __len__(self):
        return len(self._list)




