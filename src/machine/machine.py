from helpers.baseclass import BaseClass

class Machine(BaseClass):

    subclasses = {}
    stoch_var_defaults={}
    level_defaults={}

    def allocate_resources_postproc(self,batches):
        pass

    def allocate_resources_simu_postproc(self,batch):
        pass

from . import *
