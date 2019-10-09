# ---------- external imports ----------
import sys
import yaml
import pickle
from pick import pick
# ---------- local imports -------------
from uqmethod.uqmethod import UqMethod
from machine.machine import Machine
from solver.solver import Solver
from stochvar.stochvar import StochVar
from helpers.baseclass import BaseClass
from helpers.printtools import *
from helpers.tools import *
from helpers import globels


def config(prmfile):
    """
    Reads all user input and sets up (sub-)classes according to this
    input
    """
    # read user input to dict
    with open(prmfile, 'r') as f:
        prms = yaml.safe_load(f)

    # sets up global tools like logger
    print_step("Read parameters")

    # initialize classes according to chosen subclass
    sim = UqMethod.create(prms["uq_method"])
    sim.cfg = GeneralConfig(prms["general"])

    # in the multilevel case, some further setup is needed for the
    # levels (mainly sorting prms into sublevels f and c)
    sim.setup(prms)


    globels.sim = sim
    return sim

def restart(prmfile=None):
    with open('pounce.pickle', 'rb') as f:
        sim = pickle.load(f)
    if prmfile:
        raise Exception("Modifying parameters at restart is not yet "
                        "implemented")

    n_finished_iter = len(sim.iterations) \
                    - (0 if sim.current_iter.finished else 1)
    if n_finished_iter > 0:
        p_print(cyan("Skipping %i finished Iteration(s)."%(n_finished_iter)))

    globels.sim = sim
    sim.cfg.copy_to_globels()
    return sim


def config_list(name,prms,class_init,*args,sub_list_name=None):
    """
    Checks for correct input format for list type input and
    initializes (sub-) class for given input
    """
    if name not in prms:
        raise Exception("Required parameter '"
                        +name+"' is not set in parameter file!")
    if sub_list_name: 
        try:
            prms_loc=prms[name][sub_list_name]
            for_all = copy.deepcopy(prms[name])
            del for_all[sub_list_name]
            for entry in prms_loc: 
                entry.update(for_all)
        except KeyError: 
            print(prms)
            raise Exception("Revise input prm structure of "+name+"!")
    else: 
        prms_loc=prms[name]
    if not isinstance(prms_loc,list):
        raise Exception("Parameter'"+name+"' needs to be defined as a list!")
    p_print("Setup "+yellow(name)+" - Number of " + name + " is "
            + yellow(str(len(prms_loc))) + ".")
    indent_in()
    classes = [class_init(sub_dict,*args) for sub_dict in prms_loc]
    indent_out()
    return classes



def print_default_yml_file():
    """
    Asks for user input to choose one of the available subclasses,
    builds up dictionary of defaults for all variables for this sub
    class combinatiion, then prints default YML file using yaml.dump.
    """
    d = DefaultFile()

    uq_method = d.process_subclass(UqMethod)

    uq_method.default_yml(d)

    d.clean()
    d.print_()
    sys.exit()

class DefaultFile():

    def __init__(self):
        print("\n_print default YML File\n"+"-"*132+"\n_config:\n")
        self.all_defaults = {}
        self.subclasses = []

        # add general config parameters
        self.all_defaults["general"] = GeneralConfig.defaults(with_type=False)

        self.all_defaults["stoch_vars"] = self.get_list_defaults(StochVar)

    def clean(self): 
        self.all_defaults = self.clean_(self.all_defaults)

    def clean_(self,dict_in): 
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
        """ inquires subclass, and adds its default prms to dict. 
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
        """ output a list of all implemented types of list-input items
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
        msg="Enter file name for output (press enter for stdout):\n"
        filename_out=input(msg)
        if filename_out:
            sys.stdout = open(filename_out, 'w')
        else:
            print("\n_default YML File:\n"+"-"*132+"\n")
        print(yaml.dump(self.all_defaults, default_flow_style=False))


class GeneralConfig(BaseClass):

    defaults_ = {
        "archive_level" : 0,
        "project_name" : "NODEFAULT"
        }

    def __init__(self,*args): 
        super().__init__(*args)
        self.copy_to_globels()

    def copy_to_globels(self):
        globels.archive_level=self.archive_level
        globels.project_name=self.project_name
