from helpers.printtools import *
from helpers.time import Time

class BaseClass():
   """
   Skeleton for most classes to inherit from.
   Provides methods for user input and to choose subclasses from a user input string
   """
   classDefaults={}
   subclassDefaults={}

   def __init__(self,classDict):
      self.ReadPrms(classDict)

   def ReadPrms(self,inputPrmDict):
      """
      Gets user input for own class as a dictionary.
      Compares user input against defaults for parent class and subclass.
      Throws errors for invali input, else converts input dict to class attributes
      """

      Print("  Setup class "+yellow(self.__class__.__name__))
      # initialize attribute dict with default values
      attributes={}
      attributes.update(self.classDefaults)
      attributes.update(self.subclassDefaults)

      # overwrite defaults with custom input prms
      for inputPrmName,inputValue in inputPrmDict.items():
         if inputPrmName not in attributes:
            raise Exception("'"+inputPrmName+"' is not a valid input parameter name!")
         else:
            attributes[inputPrmName]=inputValue

      # check if all mandatory input prms are set
      for prmName,prmValue in attributes.items():
         if prmValue is "NODEFAULT":
            raise Exception("'"+prmName+"' is not set in parameter file and has no default value!")

      # convert dict to class attributes
      for prmName,prmValue in attributes.items():
         if "time" in prmName or "Time" in prmName: 
            prmValue=Time(prmValue).sec
         setattr(self,prmName,prmValue)
      # [setattr(self,prmName,prmValue) for prmName,prmValue in attributes.items()]

   @classmethod
   def RegisterSubclass(cls, subclassKey):
      """
      this is called before defining a cubclass of a parent class.
      It adds each subclass to a dict, so that the subclass can be chosen via a user input string.
      """
      def Decorator(subclass):
         cls.subclasses[subclassKey] = subclass
         return subclass
      return Decorator

   @classmethod
   def Create(cls,classDict,*args):
      """
      Choose subclass via a input string and init.
      The further user input for this class is passed to init as a dict
      """
      subclassKey=classDict["_type"]
      del classDict["_type"]
      if subclassKey not in cls.subclasses:
         raise ValueError("'{}' is not a valid {}".format(subclassKey,cls.__name__))
      Print("Chosen subclass of "+yellow(cls.__name__)+" is "+yellow(subclassKey)+".")
      return cls.subclasses[subclassKey](classDict,*args)

