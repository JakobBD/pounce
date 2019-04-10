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
from level.level import Level
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
    general = GeneralConfig(prms["general"])
    sim.stoch_vars = config_list("stoch_vars", prms, StochVar.create, sim)

    # in the multilevel case, some firther setup is needed for the
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

    n_finished_iter = (len(sim.iterations)
                       - (1 if sim.do_continue else 0))
    if n_finished_iter > 0:
        p_print(cyan("Skipping %i finished Iteration(s)."%(n_finished_iter)))

    globels.sim = sim
    return sim


def config_list(string,prms,class_init,*args):
    """
    Checks for correct input format for list type input and
    initializes (sub-) class for given input
    """
    if string not in prms:
        raise Exception("Required parameter '"
                        +string+"' is not set in parameter file!")
    if not isinstance(prms[string],list):
        raise Exception("Parameter'"+string+"' needs to be defined as a list!")
    p_print("Setup "+yellow(string)+" - Number of " + string + " is "
            + yellow(str(len(prms[string]))) + ".")
    indent_in()
    classes = [class_init(sub_dict,*args) for sub_dict in prms[string]]
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

    d.print_()
    sys.exit()

class DefaultFile():

    def __init__(self):
        print("\n_print default YML File\n"+"-"*132+"\n_config:\n")
        self.all_defaults = {}
        self.subclasses = []

        # add general config parameters
        self.all_defaults["general"] = GeneralConfig.defaults()

        self.all_defaults["stoch_vars"] = self.get_list_defaults(StochVar)

    def process_subclass(self, parent, add_to_lists="default", 
                         add_to_dict="default"): 
        if add_to_lists == "default": 
            add_to_lists = self.subclasses
        if add_to_dict == "default": 
            add_to_dict = self.all_defaults
            # print(add_to_dict)

        subclass = self.inquire_subclass(parent)

        # add to list, as might be needed for defaults_add
        for list_ in add_to_lists:
            list_.append(subclass)

        # add defaults for this class to dict with all defaults
        add_to_dict[parent.name()] = subclass.defaults()
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
        globels.archive_level=self.archive_level
        globels.project_name=self.project_name
