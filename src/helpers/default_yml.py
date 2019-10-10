# ---------- external imports ----------
import sys
import yaml
from pick import pick
# ---------- local imports -------------
from uqmethod.uqmethod import UqMethod
from .config import GeneralConfig
from machine.machine import Machine
from stochvar.stochvar import StochVar
from helpers.printtools import *
from helpers.tools import *


def print_default_yml_file():
    """
    Asks for user input to choose one of the available subclasses,
    builds up dictionary of defaults for all variables for this sub
    class combinatiion, then prints default YML file using yaml.dump.
    """
    d = DefaultFile()

    uq_method = d.process_subclass(UqMethod)

    # a part of the yml file layout is uq method specific
    uq_method.default_yml(d)

    d.clean()
    d.print_()
    sys.exit()


class DefaultFile():
    """
    container for the defaults dictionary and its manipulating
    functions
    """

    def __init__(self):
        print("\n_print default YML File\n"+"-"*132+"\n_config:\n")
        self.all_defaults = {}
        self.subclasses = []

        # add general config parameters
        self.all_defaults["general"] = GeneralConfig.defaults(with_type=False)

        self.all_defaults["stoch_vars"] = self.get_list_defaults(StochVar)

    def clean(self): 
        """
        remove input prms with value "dummy_unused";
        wrapper for recursive function clean_
        """
        self.all_defaults = self.clean_(self.all_defaults)

    def clean_(self,dict_in): 
        """
        recursively remove input prms with value "dummy_unused"
        """
        if not isinstance(dict_in,dict): 
            return dict_in
        dict_out = {k: v for k,v in dict_in.items() if v != "dummy_unused"}
        for k,v in dict_out.items():
            if isinstance(v,dict): 
                dict_out[k] = self.clean_(v)
            elif isinstance(v,list):
                dict_out[k] = [self.clean_(i) for i in v]
        return dict_out


    def process_subclass(self, parent):
        """ 
        inquires subclass, and adds its default prms to dict. 
        Returns the class as an object
        """
        subclass = self.inquire_subclass(parent)
        # add defaults for this class to dict with all defaults
        self.all_defaults[parent.name()] = subclass.defaults(*self.subclasses)
        # add to subclasses list, as might influence other class defaults
        self.subclasses.append(subclass)
        return subclass

    def get_machine(self): 
        machine = self.process_subclass(Machine)
        self.all_defaults["machine"] = machine.defaults()
        if not machine.name() == "local": 
            if self.inquire("Perform post-processing locally?"):
                MachineLocal = Machine.subclass("local")
                self.all_defaults["machine_postproc"] = MachineLocal.defaults()


    def get_list_defaults(self, parent, args="default"):
        """ 
        output a list of all implemented types of list-input items
        (e.g. stoch_var, qoi)
        """
        if args == "default": 
            args = self.subclasses
        return [sub.defaults(*args) for sub in parent.__subclasses__()]

    def inquire(self, msg):
        answer,_ = pick(["yes", "no"], msg)
        return answer == "yes"

    def inquire_subclass(self, parent_class, description=None):
        """
        Asks for user input to choose one of the available subclasses
        """
        msg = "Please choose a "+parent_class.name()+":"
        if description: 
            msg = description+": "+msg
        subclasses = {c.name(): c for c in parent_class.__subclasses__()}
        subclass_name,_=pick(list(subclasses.keys()), msg)
        return subclasses[subclass_name]

    def expand_to_several(self,sub,list_name,keys=None,exclude=[]):
        """
        Some classes will have several instances. 
        In the ini file, it is desirable to specify some defaults for
        all instances, and some for each instance seperately.
        In this routine, the defaults of a class are split into a dict
        (if keys are given) or a list with one example entry (else)
        each including all defaults of the class but the excluded ones. 
        This sub-dict/list is then placed inside the default dict for 
        the class. The excluded items are specified once and are used
        for all instances of the class.
        """
        for_all={}
        for exclude_item in exclude: 
            for_all[exclude_item]=sub[exclude_item]
            del sub[exclude_item]
        if keys: 
            sub = {list_name : {key : sub for key in keys}}
        else: 
            sub = {list_name : [sub] }
        sub.update(for_all)
        return sub

    def print_(self):
        """
        print dict of defaults either to stdout or to specified file
        """
        msg="Enter file name for output (press enter for stdout):\n"
        filename_out=input(msg)
        if filename_out:
            sys.stdout = open(filename_out, 'w')
        else:
            print("\n_default YML File:\n"+"-"*132+"\n")
        print(yaml.dump(self.all_defaults, default_flow_style=False))


