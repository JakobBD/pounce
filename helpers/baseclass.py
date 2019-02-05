import sys

class BaseClass():
   classDefaults={}
   subclassDefaults={}

   def __init__(self,classDict): 
      self.ReadPrms(classDict)
      self.InitLoc()

   def InitLoc(self):
      pass

   def ReadPrms(self,classDict):
      attrDict=self.classDefaults
      attrDict.update(self.subclassDefaults)
      for key,value in classDict.items(): 
         if key in attrDict:
            attrDict[key]=value
         else:
            sys.exit(key+" is not a valid input parameter name!")
      for key,value in attrDict.items(): 
         if value is "NODEFAULT": 
            sys.exit(key+" is not set in parameter file and has no default value!")
         setattr(self,key,value)
      # TODO: check if there are still prms with NODEFAULT

   @classmethod
   def RegisterSubclass(cls, subclassKey):
      def Decorator(subclass):
         cls.subclasses[subclassKey] = subclass
         return subclass
      return Decorator

   @classmethod
   def Create(cls,classDict):
      subclassKey=classDict["_type"]
      del classDict["_type"]
      if subclassKey not in cls.subclasses:
         raise ValueError("'{}' is not a valid {}".format(subclassKey,cls.__name__))
      return cls.subclasses[subclassKey](classDict)

