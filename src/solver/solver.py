import sys,os

from helpers.baseclass import BaseClass
from helpers.printtools import *

class Solver(BaseClass):
    subclasses = {}
    class_defaults = {
        "project_name":"NODEFAULT",
        "exe_path": "NODEFAULT"
        }

    def check_all_finished(self,batches):
        finished = [self.check_finished(batch) for batch in batches]
        if all(finished): 
                p_print("All jobs finished.")
        else:
            tmp=[batch.name for batch,is_finished in zip(batches,finished) if not is_finished]
            raise Exception("not all jobs finished. Problems with batch(es) "+", ".join(tmp)+".")



class QoI(BaseClass):

    subclasses = {}
    class_defaults={
        "exe_paths": {"iteration_postproc": ""}
        }

    # def __init__(self,class_dict,*args):
        # super().__init__(class_dict)

    # def copy(self,class_dict):
        # super().__init__(class_dict)
        # #copy input prm dict to be able to create instances of this class later on
        # self.prms=class_dict

    # @classmethod
    # def register_subclass(cls, subclass_key):
        # """
        # this is called before defining a cubclass of a parent class.
        # It adds each subclass to a dict, so that the subclass can be chosen via a user input string.
        # """
        # def decorator(subclass):
            # cls.subclasses[subclass_key] = subclass
            # return subclass
        # return decorator

    # @classmethod
    # def create(cls,class_dict,*args):
        # """
        # Choose subclass via a input string and init.
        # The further user input for this class is passed to init as a dict
        # """
        # subclass_key=class_dict["_type"]
        # # del class_dict["_type"]
        # if subclass_key not in cls.subclasses:
            # raise ValueError("'{}' is not a valid {}".format(subclass_key,cls.__name__))
        # p_print("Chosen subclass of "+yellow(cls.__name__)+" is "+yellow(subclass_key)+".")
        # return cls.subclasses[subclass_key](class_dict,*args)


from . import *

