import logging

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
   

red      = lambda text : Bcolors.RED   +text+Bcolors.ENDC
green    = lambda text : Bcolors.GREEN +text+Bcolors.ENDC
blue     = lambda text : Bcolors.BLUE  +text+Bcolors.ENDC
yellow   = lambda text : Bcolors.YELLOW+text+Bcolors.ENDC
cyan     = lambda text : Bcolors.CYAN  +text+Bcolors.ENDC
stdcolor = lambda text : text

colors={"red"     :red,
        "green"   :green,
        "blue"    :blue,
        "yellow"  :yellow,
        "cyan"    :cyan,
        "stdcolor":stdcolor}

indent=" "

def IndentIn():
   global indent
   indent+="  "

def IndentOut():
   global indent
   indent=indent[:-2]

def Print(msg,color="stdcolor"):
   print(colors[color](indent+msg))

def PrintMinorSection(msg):
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



def Log(msg,color="stdcolor"):
   log = logging.getLogger('logger')
   log.info(colors[color](msg))

def Debug(msg,color="stdcolor"):
   log = logging.getLogger('logger')
   log.info(colors[color](msg))













