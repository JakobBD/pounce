import numpy as np
import inspect
import copy
from parse import parse

from helpers.printtools import *



def safe_sqrt(arg,silent=False):
    """
    for sqrt of negative values, print a warning instead of crashing.
    """
    if np.all(arg >= 0.):
        return np.sqrt(arg)
    elif np.any(abs(arg)>1.E-13):
        info=inspect.getouterframes( inspect.currentframe() )[1]
        p_print(red("Warning: ")+"Sqrt received invalid value(s) "
                +str(arg)+". Invalid values are set to 0.")
        indent_in()
        p_print("line:     "+str(info.code_context[0])[:-1])
        p_print("function: "+str(info.function))
        p_print("file:     "+str(info.filename))
        p_print("line no:  "+str(info.lineno)+"\n")
        indent_out()
    return np.sqrt(np.maximum(0.,arg))

class Empty():
    pass


def parse_time_to_seconds(arg): 
    """
    parse different formats to give time in the yml parameter file.
    """
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
    """
    time lists have three entries h,m,s
    """
    if isinstance(arg,(list,tuple)):
        if len(arg) == 3:
            return True
    else:
        return False

def sec_to_list(sec):
    """
    helper for time_sto_str
    """
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

class InputPrmError(Exception): 
    pass
