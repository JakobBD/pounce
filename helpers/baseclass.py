
class BaseClass():
   subclasses = {}

   def __init__(self,classDict): 
      self.ReadPrms(classDict)
      self.InitLoc()

   def InitLoc(self):
      pass

   def ReadPrms(self,classDict):
      for key,value in classDict.items(): 
         setattr(self,key,value)

   @classmethod
   def RegisterSubclass(cls, subclassKey):
      def Decorator(subclass):
         cls.subclasses[subclassKey] = subclass
         return subclass
      return Decorator

   @classmethod
   def Create(cls,classDict):
      subclassKey=classDict["name"]
      del classDict["name"]
      if subclassKey not in cls.subclasses:
         raise ValueError("'{}' is not a valid {}".format(subclassKey,cls.__name__))
      return cls.subclasses[subclassKey](classDict)

