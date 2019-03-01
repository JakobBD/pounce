from helpers.baseclass import BaseClass

class StochVar(BaseClass):
    subclasses = {}
    class_defaults={
        'name' : 'NODEFAULT'
        }

    def __init__(self,input_prm_dict,*args):
        for arg in args:
            self.class_defaults.update(arg)
        super().__init__(input_prm_dict)

from . import *
