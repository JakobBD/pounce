from helpers.baseclass import BaseClass
from simulation.simulation import Stage

class Machine(Stage,BaseClass):
    """
    defines the machine that an external job is run on. 
    We call the processing of an external job (i.e. allocating 
    resouces, preparation, and running) as a stage. 
    Each stage can (theoretically) be run on a different machine.
    E.g., post-processing can be doen locally.
    Therefore, the different stages are instances of machine 
    subclasses.
    """

    defaults_ = {
        "name" : "default"
        }



from . import *
