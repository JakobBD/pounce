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
    msg2="""                                 Propagation of Uncertainty - Framework for HPC UQ implementations
                                     You queue UQ simulations? That's your cue to use POUNCE!"""
    print("="*132)
    print(yellow(msg1))
    print("="*132)
    print(yellow(msg2))
    print("="*132)



class StdOutTable():
    """
    Buffers several values for each batch for stdout in ordered table.
    Called in three steps:
    - before loop over batches: init class and set_descriptions
    - during loop over batches: update (for each batch) 
    - after  loop over batches: print
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
        name=level.__class__.__name__+" "+level.name
        if name in self.header_entries: 
            i_col=self.header_entries.index(name)
        else: 
            i_col=len(self.header_entries)
            self.header_entries.append(name)
            [row.values.append('dummy') for row in self.rows]
        attr_names=[row.attr for row in self.rows]
        for attr_name in attr_names:
            attr=level
            for word in attr_name.split("__"):
                attr=getattr(attr,word)
            for row in self.rows: 
                if row.attr==attr_name:
                    row.values[i_col]=attr

    def p_print(self):
        self.descr_length=max([len(row.description) for row in self.rows])
        n_entries=len(self.header_entries)
        self.str_length=max([len(h) for h in self.header_entries])
        self.str_length=max(11,self.str_length)
        self.l=str(self.str_length)
        self.lm2=str(self.str_length-2)
        print(indent+" "*self.descr_length+" ║ "
              +"".join(["%11s ║ "%(n) for n in self.header_entries]))
        sep_str="═"*self.str_length+"═╬═"
        print(indent+"═"*self.descr_length+"═╬═"+sep_str*n_entries)
        for row in self.rows:
            row.descr_length=self.descr_length
            row.str_length=self.str_length
            row.p_print(self.l,self.lm2)

    def print_row_by_name(self,attr):
        for row in self.rows:
            if row.attr == attr: 
                row.p_print(self.l,self.lm2)


class TableRow():
    def __init__(self,attr):
        self.attr=attr
        self.values=[]

    def p_print(self,l,lm2):
        self.string=" "*(self.descr_length-len(self.description))\
                    +self.description+" ║ "
        for value in self.values: 
            if "time" in self.description.lower():
                self.add_string(("%"+l+"s")%(time_to_str2(value)))
            elif "%" in self.description:
                self.add_string(("%"+lm2+".1f %%")%(100*value))
            elif isinstance(value,str): 
                self.add_string(("%"+l+"s")%(value))
            elif isinstance(value,int): 
                self.add_string(("%"+l+"d")%(value))
            elif isinstance(value,(float,np.ndarray)): 
                self.add_string(("%"+l+".4e")%(value))
            else:
                raise Exception("unknown type",type(value))
        print(indent+self.string)

    def add_string(self,string):
        self.string+=yellow(string)+" ║ "


def time_to_str2(sec):
    list_=sec_to_list(sec)
    tmp=["%2d"%(int(i)) for i in list_]
    return "{}h {}m {}s".format(*tmp)






