import sys,os
import inspect

from helpers.baseclass import BaseClass
from helpers.printtools import *

class Solver(BaseClass):
    defaults_ = {
        "exe_path": "NODEFAULT"
        }

    def check_finished(self):
        return True




class QoI(BaseClass):

    defaults_={
        "exe_paths": {"iteration_postproc": ""}
        }

    def check_finished(self):
        return True

    def prepare_iter_postproc(self,simulation):
        raise Exception("not yet implemented")

    def prepare_simu_postproc(self,simulation):
        raise Exception("not yet implemented")


from . import *

