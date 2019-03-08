import copy

from helpers.printtools import *
from helpers.time import Time


class BaseClass():
    """
    Skeleton for most classes to inherit from.
    Provides methods for user input and to choose subclasses from a 
    user input string
    """
    class_defaults={}
    subclass_defaults={}

    def __init__(self,class_dict,*further_defaults):
        for dict_ in further_defaults:
            self.class_defaults.update(dict_)
        self.read_prms(class_dict)

    def read_prms(self,input_prm_dict):
        """
        Gets user input for own class as a dictionary.
        Compares user input against defaults for parent class and 
        subclass. Throws errors for invali input, else converts input 
        dict to class attributes
        """

        p_print("  Setup class "+yellow(self.__class__.__name__))
        # initialize attribute dict with default values
        attributes={}
        attributes.update(copy.deepcopy(self.class_defaults))
        attributes.update(copy.deepcopy(self.subclass_defaults))

        # overwrite defaults with custom input prms
        for input_prm_name,input_value in input_prm_dict.items():
            if (input_prm_name not in attributes 
                    and not input_prm_name.startswith("_")):
                raise Exception("'"+input_prm_name
                                +"' is not a valid input parameter name!")
            else:
                attributes[input_prm_name]=input_value

        # check if all mandatory input prms are set
        for prm_name,prm_value in attributes.items():
            if prm_value is "NODEFAULT":
                raise Exception("'"+prm_name+"' is not set in parameter file"
                                "and has no default value!")

        # convert dict to class attributes
        for prm_name,prm_value in attributes.items():
            setattr(self,prm_name,prm_value)

    @classmethod
    def register_subclass(cls, subclass_key):
        """
        this is called before defining a cubclass of a parent class.
        It adds each subclass to a dict, so that the subclass can be 
        chosen via a user input string.
        """
        def decorator(subclass):
            if subclass_key in cls.subclasses: 
                raise Exception("two subclasses with key '%s'"%(subclass_key)
                                +" for class " + cls.__name__)
            else: 
                cls.subclasses[subclass_key] = subclass
            return subclass
        return decorator

    @classmethod
    def create(cls,class_dict,*args):
        """
        Choose subclass via a input string and init.
        Further user input for this class is passed to init as a dict
        """
        subclass_key=class_dict["_type"]
        # del class_dict["_type"]
        if subclass_key not in cls.subclasses:
            raise ValueError(
                "'{}' is not a valid {}".format(subclass_key,cls.__name__))
        p_print("Chosen subclass of "+yellow(cls.__name__)
                +" is "+yellow(subclass_key)+".")
        return cls.subclasses[subclass_key](class_dict,*args)

