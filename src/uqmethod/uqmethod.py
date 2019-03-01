from helpers.baseclass import BaseClass


class UqMethod(BaseClass):

    subclasses={}
    stoch_var_defaults={}
    level_defaults={}

    def __init__(self,input_prm_dict):
        super().__init__(input_prm_dict)
        self.do_continue = True

    def setup_batches(self):
        pass




# import subclasses
from . import *
