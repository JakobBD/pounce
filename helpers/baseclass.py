
class BaseClass():
   subclasses = {}

   @classmethod
   def RegisterSubclass(cls, subclassKey):
      def Decorator(subclass):
         cls.subclasses[subclassKey] = subclass
         return subclass
      return Decorator

   @classmethod
   def Create(cls, subclassKey):
      if subclassKey not in cls.subclasses:
         raise ValueError("'{}' is not a valid {}".format(subclassKey,cls.__name__))
      return cls.subclasses[subclassKey]()

