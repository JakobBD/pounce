import numpy as np
import inspect

from helpers.printtools import *


def SafeSqrt(arg):
   if arg >= 0.:
      return np.sqrt(arg)
   else: 
      info=inspect.getouterframes( inspect.currentframe() )[1]
      Print(red("Warning: ")+"Sqrt received invalid value "+str(arg)+". Is set to 0.")
      IndentIn()
      Print("line:     "+str(info.code_context[0])[:-1])
      Print("function: "+str(info.function))
      Print("file:     "+str(info.filename))
      Print("line no:  "+str(info.lineno)+"\n")
      IndentOut()
      return 0.

