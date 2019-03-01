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

def indent_in():
   global indent
   indent+="  "

def indent_out():
   global indent
   indent=indent[:-2]

def p_print(msg):
   [print(line) for line in textwrap.wrap(msg, width=132, initial_indent=indent, subsequent_indent=indent+"   ")]

def print_step(msg):
   print("-"*132)
   print(green(" "+msg)+"\n")

def print_major_section(msg,color="stdcolor"):
   print("\n"+"="*132)
   print(cyan(" "+msg))
   print("="*132)

def print_header():
   msg1="""                              `7_mM***Mq.   .g8**8q. `7_mMF'   `7_mF'`7_mN.   `7_mF' .g8***bgd `7_mM***YMM 
                                MM   `MM..d_p'    `YM. MM       M    MMN.    M .d_p'     `M   MM    `7 
                                MM   ,M9 d_m'      `MM MM       M    M YMb   M d_m'       `   MM   d   
                                MMmmdM9  MM        MM MM       M    M  `MN. M MM            MMmmMM   
                                MM       MM.      ,MP MM       M    M   `MM.M MM.           MM   Y  ,
                                MM       `Mb.    ,d_p' YM.     ,M    M     YMM `Mb.     ,'   MM     ,M
                              .JMML.       `*bmmd*'    `bmmmmd*'  .JML.    YM   `*bmmmd'  .JMMmmmmMMM"""
   msg2="""                                 Propagation of Uncertainty - Framework for HPC UQ implementations"""
   print("="*132)
   print(yellow(msg1))
   print("="*132)
   print(yellow(msg2))
   print("="*132)



def log(msg):
   log = logging.get_logger('logger')
   log.info(msg)

def debug(msg):
   log = logging.get_logger('logger')
   log.debug(msg)





class StdOutTable():
   """
   Helper class for get_new_n_current_samples routine.
   Outsourced for improved readability.
   Prints values for each level in ordered table to stdout.
   """
   def __init__(self,*args):
      self.strs=[]
      for arg in args:
         self.strs.append(TableString(arg))
         self.names=[]

   def descriptions(self,*args):
      for i_arg,arg in enumerate(args):
         self.strs[i_arg].description=arg

   def update(self,level):
      self.names.append(level.name)
      attr_names=[s.attr for s in self.strs]
      for attr_name in attr_names:
         attr=level
         for word in attr_name.split("__"):
            attr=getattr(attr,word)
         for s in self.strs: 
            if s.attr==attr_name:
               s.values.append(attr)

   def p_print(self,batch_str):
      description_length=max([len(s.description) for s in self.strs])
      n_entries=len(self.names)
      p_print(" "*description_length+" ║ "+"".join(["%11s ║ "%(batch_str+" "+n) for n in self.names]))
      sep_str="═"*11+"═╬═"
      p_print("═"*description_length+"═╬═"+sep_str*n_entries)
      for s in self.strs:
         s.str_out=" "*(description_length-len(s.description))+s.description+" ║ "
         for value in s.values: 
            if isinstance(value,str): 
               s.str_out=s.str_out+"%11s ║ "%(value)
            elif isinstance(value,int): 
               s.str_out=s.str_out+"%11d ║ "%(value)
            elif isinstance(value,(float,np.ndarray)): 
               s.str_out=s.str_out+"%11.4e ║ "%(value)
            else:
               raise Exception("unknown type",type(value))
         p_print(s.str_out)



class TableString():
   def __init__(self,attr):
      self.attr=attr
      self.values=[]









