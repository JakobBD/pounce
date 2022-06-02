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

    cname = "UNNAMED CLASS"

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
            if prm_value == "NODEFAULT":
                print(self.__class__.__name__)
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
        p_print("Chosen subclass of "+yellow(cls.__name__)
                +" is "+yellow(subcls.cname)+".")
        return subcls(class_dict,*args)

    @classmethod
    def subclass(cls,string):
        """
        choose subclass of a class by string
        """
        coll = []
        for sc in cls.__subclasses__():
            cls.recursive_subclasses(coll,sc) 
        for subclass in coll: 
            if string == subclass.cname:
                return subclass
        print(coll)
        raise InputPrmError(
            "'{}' is not a valid {}".format(string,cls.__name__))

    @classmethod
    def recursive_subclasses(cls,collection,subclass): 
        collection.append(subclass)
        for ssc in subclass.__subclasses__(): 
            cls.recursive_subclasses(collection,ssc) 
    
    @classmethod
    def defaults_class(cls,key=None):
        """
        get defaults for a class from its own class and parents, 
        via the multi resolution order list.
        """
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
    def defaults(cls,*args,with_type=True): 
        """
        get defaults for a class, first from its own class and parents, 
        then from further input classes.
        _type (i.e. the subclass name) is added optionally
        """
        d=cls.defaults_class()
        if args:
            keys=[c.__name__ for c in reversed(cls.__mro__[:-2])]
        for arg in args: 
            for key in keys: 
                d.update(arg.defaults_class(key))
        if with_type:
            d.update({"_type": cls.cname})
        return d

    # @classmethod
    # def cname(cls):
        # """
        # translate class name from camel case (MyClass) to 
        # underscore (my_class) for consistent yml input
        # """
        # return inflection.underscore(cls.__name__)

class InputPrmError(Exception):
    pass
