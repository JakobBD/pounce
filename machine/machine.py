from helpers.baseclass import BaseClass

class Machine(BaseClass): 
   # dictionary of default input values; 
   # serves as check of correct input format and for default prm file printing
   classDefaults = {}
   subclasses = {}

from . import *
