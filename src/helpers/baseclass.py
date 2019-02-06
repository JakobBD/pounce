import sys

class BaseClass():
   classDefaults={}
   subclassDefaults={}

   def __init__(self,classDict): 
      self.ReadPrms(classDict)
      self.InitLoc()

   def InitLoc(self):
      pass

   def ReadPrms(self,inputPrms):

      # initialize attribute dict with default values
      attributes=self.classDefaults
      attributes.update(self.subclassDefaults)

      # overwrite defaults with custom input prms
      for inputPrmName,inputValue in inputPrms.items(): 
         if inputPrmName not in attributes:
            sys.exit("'"+inputPrmName+"' is not a valid input parameter name!")
         elif type(attributes[inputPrmName]) is not dict:
            attributes[inputPrmName]=inputValue
         # Nested dicts are assumed to be numbered lists, i.e. have keys 1,2,...
         # A range of these keys is stored in an "ind" item. 
         # For each item of the list, the default value is then copied into the attributes array.
         # Input valies are then compared against this array
         else:
            inputValue["ind"]=range(1,len(inputValue)+1)
            try:
               for ind in inputValue["ind"]:
                  attributes[ind]=attributes[1]
                  for prm in inputValue[ind]:
                     if prm not in attributes[inputPrmName][ind]:
                        sys.exit("'"+prm+"' is not a valid input parameter name for an item of '"+inputPrmName+"'!")
                     else:
                        attributes[inputPrmName][ind][prm]=inputValue[ind][prm]
            except KeyError: 
               sys.exit("Items of '"+inputPrmName+"' have to be acending integers: 1,2,...!")
         

      # check if all mandatory input prms are set
      CheckAllPrmsSet(attributes)

      # convert dict to class attributes
      [setattr(self,prmName,prmValue) for prmName,prmValue in attributes.items()]

   def CheckAllPrmsSet(self,attributes):
      for prmName,prmValue in attributes.items(): 
         if prmValue is "NODEFAULT": 
            sys.exit("'"+prmName+"' is not set in parameter file and has no default value!")
         elif type(prmValue) is dict:
            CheckAllPrmsSet(prmValue)

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

