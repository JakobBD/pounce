import logging
import textwrap
import numpy as np

class Bcolors :
    """
    color and font style definitions for changing output appearance
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
    """
    wrapper for normal stdout print commands
    """
    lines=textwrap.wrap(msg, width=132, initial_indent=indent, 
                        subsequent_indent=indent+"    ")
    for line in lines:
        print(line) 

def print_step(msg):
    print("-"*132)
    print(green(" "+msg)+"\n")

def print_major_section(msg,color="stdcolor"):
    """
    such as at the beginning of iterations
    """
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
    msg2="""                                 Propagation of Uncertainty - Framework for HPC UQ implementations
                                     You queue UQ simulations? That's your cue to use POUNCE!"""
    print("="*132)
    print(yellow(msg1))
    print("="*132)
    print(yellow(msg2))
    print("="*132)


def print_table(table): 
    table.field_names = [yellow(s) for s in table.field_names]
    for r in table._rows: 
        for i,f in enumerate(r): 
            if "time" in table.field_names[i]:
                r[i] = ("%0s")%(time_to_str2(f))
            elif "%" in table.field_names[i]:
                r[i] = ("%0.1f %%")%(100*f)
            elif isinstance(f,(float,np.ndarray)): 
                r[i] = ("%0.4e")%(f)
        r[0] = yellow(r[0])
    table.vertical_char = "║"
    table.horizontal_char = "═"
    table.junction_char = "╬"
    table.align = "r"
    print(table)
    print()


def time_to_str2(sec):
    list_=sec_to_list(sec)
    tmp=["%2d"%(int(i)) for i in list_]
    return "{}h {}m {}s".format(*tmp)






