import logging
import textwrap
import numpy as np
from .time import Time

class Bcolors :
    """color and font style definitions for changing output appearance
    """
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


indent=" "

def indent_in():
    global indent
    indent+="  "

def indent_out():
    global indent
    indent=indent[:-2]

def p_print(msg):
    lines=textwrap.wrap(msg, width=132, initial_indent=indent, 
                        subsequent_indent=indent+"    ")
    for line in lines:
        print(line) 

def print_step(msg):
    print("-"*132)
    print(green(" "+msg)+"\n")

def print_major_section(msg,color="stdcolor"):
    print("\n"+"="*132)
    print(cyan(" "+msg))
    print("="*132)

def print_header():
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



class StdOutTable():
    """
    Helper class for get_new_n_current_samples routine.
    Outsourced for improved readability.
    Prints values for each level in ordered table to stdout.
    """
    def __init__(self,*args):
        self.rows=[]
        for arg in args:
            self.rows.append(TableRow(arg))
            self.header_entries=[]

    def set_descriptions(self,*args):
        for i_arg,arg in enumerate(args):
            self.rows[i_arg].description=arg

    def update(self,level):
        self.header_entries.append(level.__class__.__name__+" "+level.name)
        attr_names=[row.attr for row in self.rows]
        for attr_name in attr_names:
            attr=level
            for word in attr_name.split("__"):
                attr=getattr(attr,word)
            for row in self.rows: 
                if row.attr==attr_name:
                    row.values.append(attr)

    def p_print(self):
        description_length=max([len(row.description) for row in self.rows])
        n_entries=len(self.header_entries)
        p_print(" "*description_length+" ║ "
                +"".join(["%11s ║ "%(n) for n in self.header_entries]))
        sep_str="═"*11+"═╬═"
        p_print("═"*description_length+"═╬═"+sep_str*n_entries)
        for row in self.rows:
            row.string=" "*(description_length-len(row.description))\
                       +row.description+" ║ "
            for value in row.values: 
                if "time" in row.description.lower():
                    row.string=row.string+"%11s ║ "%(Time(value).str2)
                elif "%" in row.description:
                    row.string=row.string+"%9.1f %% ║ "%(100*value)
                elif isinstance(value,str): 
                    row.string=row.string+"%11s ║ "%(value)
                elif isinstance(value,int): 
                    row.string=row.string+"%11d ║ "%(value)
                elif isinstance(value,(float,np.ndarray)): 
                    row.string=row.string+"%11.4e ║ "%(value)
                else:
                    raise Exception("unknown type",type(value))
            p_print(row.string)



class TableRow():
    def __init__(self,attr):
        self.attr=attr
        self.values=[]









