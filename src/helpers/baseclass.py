import copy
import inflection

from helpers.printtools import *
from helpers.tools import *


class BaseClass():
    """
    Skeleton for most classes to inherit from.
    Provides methods for user input and to choose subclasses from a 
    user input string
    """

    def __init__(self,class_dict,*further_classes):
        self.read_prms(class_dict,*further_classes)

    def read_prms(self,input_prm_dict,*further_classes):
        """
        Gets user input for own class as a dictionary.
        Compares user input against defaults for parent class and 
        subclass. Throws errors for invali input, else converts input 
        dict to class attributes
        """

        p_print("  Setup class "+yellow(self.__class__.__name__))
        # initialize attribute dict with default values
        attributes=self.defaults(*further_classes)

        # overwrite defaults with custom input prms
        for input_prm_name,input_value in input_prm_dict.items():
            if (input_prm_name not in attributes 
                    and not input_prm_name.startswith("_")):
                raise InputPrmError("'"+input_prm_name
                                    +"' is not a valid input parameter name!")
            else:
                attributes[input_prm_name]=input_value

        # check if all mandatory input prms are set
        for prm_name,prm_value in attributes.items():
            if prm_value is "NODEFAULT":
                raise InputPrmError("'"+prm_name+"' is not set in parameter"
                                    "file and has no default value!")

        # convert dict to class attributes
        for prm_name,prm_value in attributes.items():
            if "time" in prm_name.lower(): 
                prm_value=parse_time_to_seconds(prm_value)
            setattr(self,prm_name,prm_value)

    @classmethod
    def create(cls,class_dict,*args):
        """
        Choose subclass via a input string and init.
        Further user input for this class is passed to init as a dict
        """
        subclass_key=class_dict["_type"]
        subcls=cls.subclass(subclass_key)
        p_print("Chosen subclass of "+yellow(cls.name())
                +" is "+yellow(subcls.name())+".")
        return subcls(class_dict,*args)

    @classmethod
    def subclass(cls,string):
        for subclass in cls.__subclasses__():
            if string == subclass.name():
                return subclass
        raise InputPrmError(
            "'{}' is not a valid {}".format(string,cls.name()))
    
    @classmethod
    def defaults_class(cls,key=None):
        defaults={}
        for c in reversed(cls.__mro__): 
            if key: 
                try: 
                    defaults_update = c.defaults_add[key]
                except (AttributeError, KeyError) as e:
                    defaults_update = {}
            else:
                try: 
                    defaults_update = c.defaults_
                except AttributeError:
                    defaults_update={}
            defaults.update(copy.deepcopy(defaults_update))
        return defaults

    @classmethod
    def defaults(cls,*args): 
        d=cls.defaults_class()
        if args:
            keys=[c.__name__ for c in reversed(cls.__mro__[:-2])]
        for arg in args: 
            for key in keys: 
                d.update(arg.defaults_class(key))
        d.update({"_type": cls.name()})
        return d

    @classmethod
    def name(cls):
        return inflection.underscore(cls.__name__)

class InputPrmError(Exception):
    pass
