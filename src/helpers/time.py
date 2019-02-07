import operator
import logging

class Time():
   """
   A Time object stores time data both in [h, m, s] and in sec format.
   It can be initialized with instance=helpers.Time(input), where input can either be a scalar
   or a tuple or list of length 3.
   Its value can be retrieved with time_in_sec = instance.sec() and time_as_list = instance.list().
   Mathematical operations can be carried out with an instance of the class and either another
   instance of the class, a scalar or a list / tuple.
   """

   sec_attr=0.
   list_attr=[0.,0.,0.]

   def __init__(self,*args):
      if len(args) == 1:
         self.set(args[0])
      elif args:
         raise TypeError("__init__() takes at most one argument. {} given".format(len(args)))

   def sec(self):
      return(self.sec_attr)
   def list(self):
      return(self.list_attr)
   def __call__(self):
      return(self.sec_attr)

   def set(self,*args):
      if len(args) != 1:
         raise TypeError("set() takes exactly one argument. {} given".format(len(args)))
      if self.islist(args[0]):
         self.list_attr = list(args[0])
         self.sec_attr = 3600*args[0][0] + 60*args[0][1] + args[0][2]
      else:
         self.sec_attr = args[0]
         self.list_attr[0] = int(args[0])/3600
         self.list_attr[1] = int(args[0])/60 - 60*self.list_attr[0]
         self.list_attr[2] = args[0] - 3600*self.list_attr[0]  - 60*self.list_attr[1]

   def islist(self, obj):
      if type(obj) in (list,tuple):
         if len(obj) == 3:
            return True
         else:
            raise TypeError("List or tuple has to have length 3, but is {}.".format(len(obj)))
      else:
         return False

   def checkinstance(self, other, op):
      if isinstance(other,Time):
         return Time(op(self.sec_attr,other.sec_attr))
      elif self.islist(other):
         return Time([op(a,b) for a,b in zip(self.list_attr,list(other))])
      else:
         return Time(op(self.sec_attr,other))

   def __neg__(self):
      return Time(-self.sec_attr)
   def __add__(self, other):
      return self.checkinstance(other,operator.add)
   def __radd__(self, other):
      return self.checkinstance(other,operator.add)
   def __sub__(self, other):
      return self.checkinstance(other,operator.sub)
   def __rsub__(self, other):
      return -self.checkinstance(other,operator.sub)
   def __mul__(self, other):
      return Time(self.sec_attr*other)
   def __rmul__(self, other):
      return Time(self.sec_attr*other)
   def __div__(self, other):
      if isinstance(other,Time):
         return float(self.sec_attr)/other.sec_attr
      else:
         return Time(float(self.sec_attr)/other)
   def __rdiv__(self, other):
      return float(other.sec_attr)/self.sec_attr
   def __pow__(self, other):
      return Time(self.sec_attr**other)

class bcolors :
   """color and font style definitions for changing output appearance"""
   # Reset (user after applying a color to return to normal coloring)
   ENDC   ='\033[0m'    

   # Regular Colors
   BLACK  ='\033[0;30m' 
   RED    ='\033[0;31m' 
   GREEN  ='\033[0;32m' 
   YELLOW ='\033[0;33m' 
   BLUE   ='\033[0;34m' 
   PURPLE ='\033[0;35m' 
   CYAN   ='\033[0;36m' 
   WHITE  ='\033[0;37m' 

   # Text Style
   BOLD = '\033[1m'
   UNDERLINE = '\033[4m'
   
colors={"red"     :(lambda text : bcolors.RED   +text+bcolors.ENDC),
        "green"   :(lambda text : bcolors.GREEN +text+bcolors.ENDC),
        "blue"    :(lambda text : bcolors.BLUE  +text+bcolors.ENDC),
        "yellow"  :(lambda text : bcolors.YELLOW+text+bcolors.ENDC),
        "stdcolor":(lambda text : text)}

class Out:

   @staticmethod
   def Print(msg,color="stdcolor"):
      print(colors[color](msg))

   @staticmethod
   def PrintSection(msg,color="stdcolor"):
      print("-"*132)
      print(colors[color]("  "+msg))

   @staticmethod
   def PrintIteration(msg,color="stdcolor"):
      print("="*132)
      print(colors[color]("  "+msg))
      print("="*132)

   @staticmethod
   def Log(msg,color="stdcolor"):
      log = logging.getLogger('logger')
      log.info(colors[color](msg))
      print(colors[color](msg))

   @staticmethod
   def Debug(msg,color="stdcolor"):
      log = logging.getLogger('logger')
      log.info(colors[color](msg))

   @staticmethod
   def PrintHeader():
      msg1="""                              `7MM***Mq.   .g8**8q. `7MMF'   `7MF'`7MN.   `7MF' .g8***bgd `7MM***YMM 
                                   MM   `MM..dP'    `YM. MM       M    MMN.    M .dP'     `M   MM    `7 
                                   MM   ,M9 dM'      `MM MM       M    M YMb   M dM'       `   MM   d   
                                   MMmmdM9  MM        MM MM       M    M  `MN. M MM            MMmmMM   
                                   MM       MM.      ,MP MM       M    M   `MM.M MM.           MM   Y  ,
                                   MM       `Mb.    ,dP' YM.     ,M    M     YMM `Mb.     ,'   MM     ,M
                                 .JMML.       `*bmmd*'    `bmmmmd*'  .JML.    YM   `*bmmmd'  .JMMmmmmMMM"""
      msg2="""                                 Propagation of Uncertainty - Framework for HPC UQ implementations"""
      Print("="*132)
      Print(msg1,"yellow")
      Print("="*132)
      Print(msg2,"yellow")
      Print("="*132)
