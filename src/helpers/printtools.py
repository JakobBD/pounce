import logging
import textwrap
import numpy as np

class Bcolors :
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
   

def red   (text): return Bcolors.RED   +text+Bcolors.ENDC
def green (text): return Bcolors.GREEN +text+Bcolors.ENDC
def blue  (text): return Bcolors.BLUE  +text+Bcolors.ENDC
def yellow(text): return Bcolors.YELLOW+text+Bcolors.ENDC
def cyan  (text): return Bcolors.CYAN  +text+Bcolors.ENDC

colors={"red"     :red,
        "green"   :green,
        "blue"    :blue,
        "yellow"  :yellow,
        "cyan"    :cyan}

indent=" "

def IndentIn():
   global indent
   indent+="  "

def IndentOut():
   global indent
   indent=indent[:-2]

def Print(msg):
   [print(line) for line in textwrap.wrap(msg, width=132, initial_indent=indent, subsequent_indent=indent+"   ")]

def PrintStep(msg):
   print("-"*132)
   print(green(" "+msg)+"\n")

def PrintMajorSection(msg,color="stdcolor"):
   print("\n"+"="*132)
   print(cyan(" "+msg))
   print("="*132)

def PrintHeader():
   msg1="""                              `7MM***Mq.   .g8**8q. `7MMF'   `7MF'`7MN.   `7MF' .g8***bgd `7MM***YMM 
                                MM   `MM..dP'    `YM. MM       M    MMN.    M .dP'     `M   MM    `7 
                                MM   ,M9 dM'      `MM MM       M    M YMb   M dM'       `   MM   d   
                                MMmmdM9  MM        MM MM       M    M  `MN. M MM            MMmmMM   
                                MM       MM.      ,MP MM       M    M   `MM.M MM.           MM   Y  ,
                                MM       `Mb.    ,dP' YM.     ,M    M     YMM `Mb.     ,'   MM     ,M
                              .JMML.       `*bmmd*'    `bmmmmd*'  .JML.    YM   `*bmmmd'  .JMMmmmmMMM"""
   msg2="""                                 Propagation of Uncertainty - Framework for HPC UQ implementations"""
   print("="*132)
   print(yellow(msg1))
   print("="*132)
   print(yellow(msg2))
   print("="*132)



def Log(msg):
   log = logging.getLogger('logger')
   log.info(msg)

def Debug(msg):
   log = logging.getLogger('logger')
   log.debug(msg)





class StdOutTable():
   """
   Helper class for GetNewNCurrentSamples routine.
   Outsourced for improved readability.
   Prints values for each level in ordered table to stdout.
   """
   def __init__(self,*args):
      self.strs=[]
      for arg in args:
         self.strs.append(TableString(arg))
         self.names=[]

   def Descriptions(self,*args):
      for iArg,arg in enumerate(args):
         self.strs[iArg].description=arg

   def Update(self,level):
      self.names.append(level.name)
      attrNames=[s.attr for s in self.strs]
      for attrName in attrNames:
         attr=level
         for word in attrName.split("__"):
            attr=getattr(attr,word)
         for s in self.strs: 
            if s.attr==attrName:
               s.values.append(attr)

   def Print(self,batchStr):
      descriptionLength=max([len(s.description) for s in self.strs])
      nEntries=len(self.names)
      Print(" "*descriptionLength+" ║ "+"".join(["%11s ║ "%(batchStr+" "+n) for n in self.names]))
      sepStr="═"*11+"═╬═"
      Print("═"*descriptionLength+"═╬═"+sepStr*nEntries)
      for s in self.strs:
         s.strOut=" "*(descriptionLength-len(s.description))+s.description+" ║ "
         for value in s.values: 
            if isinstance(value,str): 
               s.strOut=s.strOut+"%11s ║ "%(value)
            elif isinstance(value,int): 
               s.strOut=s.strOut+"%11d ║ "%(value)
            elif isinstance(value,(float,np.ndarray)): 
               s.strOut=s.strOut+"%11.4e ║ "%(value)
            else:
               raise Exception("unknown type",type(value))
         Print(s.strOut)



class TableString():
   def __init__(self,attr):
      self.attr=attr
      self.values=[]









