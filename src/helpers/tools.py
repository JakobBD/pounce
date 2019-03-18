import numpy as np
import inspect
import copy
from parse import parse

from helpers.printtools import *


def safe_sqrt(arg):
    if arg >= 0.:
        return np.sqrt(arg)
    else:
        info=inspect.getouterframes( inspect.currentframe() )[1]
        p_print(red("Warning: ")+"Sqrt received invalid value "
                +str(arg)+". Is set to 0.")
        indent_in()
        p_print("line:     "+str(info.code_context[0])[:-1])
        p_print("function: "+str(info.function))
        p_print("file:     "+str(info.filename))
        p_print("line no:  "+str(info.lineno)+"\n")
        indent_out()
        return 0.

class Empty():
    pass

def deepmerge(*args): 
    out=args[0]
    for arg in args[1:]: 
        out.update(copy.deepcopy(arg))
    return out



def parse_time_to_seconds(arg): 
    if isvalidlist(arg):
        return 3600*arg[0] + 60*arg[1] + arg[2]
    if isinstance(arg,str):
        formats=["0h0m0s", "0:0:0", "(/0,0,0/)", "0,0,0", "(0,0,0)"]
        for f in formats:
            tmp = parse(f.replace("0","{:d}"),arg.lower())
            if tmp: 
                return parse_time_to_seconds(list(tmp))
    return arg

def isvalidlist(arg):
    if isinstance(arg,(list,tuple)):
        if len(arg) == 3:
            return True
        else:
            raise TypeError("List or tuple has to have length 3, "
                            +"but is {}.".format(len(arg)))
    else:
        return False

def sec_to_list(sec):
    list_=[0.,0.,0.]
    list_[0] = int(int(sec)/3600)
    list_[1] = int(int(sec)/60 - 60*list_[0])
    list_[2] = int(sec - 3600*list_[0]  - 60*list_[1])
    return list_

def time_to_str(sec): 
    list_=sec_to_list(sec)
    return ":".join("%02d"%(int(i)) for i in list_)

def time_to_str2(sec):
    list_=sec_to_list(sec)
    tmp=["%2d"%(int(i)) for i in list_]
    return "{}h {}m {}s".format(*tmp)
