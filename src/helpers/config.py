# ---------- external imports ----------
import sys
import yaml
import pickle
from pick import pick
# ---------- local imports -------------
import simulation
from uqmethod.uqmethod import UqMethod
from machine.machine import Machine
from solver.solver import Solver
from stochvar.stochvar import StochVar
from level.level import Level
from helpers.baseclass import BaseClass
from helpers.printtools import *
from helpers.tools import *


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
    sim = simulation.Simulation(prms["general"])
    sim.uq_method = UqMethod.create(prms["uq_method"])
    sim.machine = Machine.create(prms["machine"])
    sim.solver = Solver.create(prms["solver"])

    # initialize lists of classes for all levels, stoch_vars and qois
    sim.uq_method.stoch_vars = config_list(
        "stoch_vars",prms,StochVar.create,
        sim.uq_method)

    sim.uq_method.levels = config_list(
        "levels",prms,Level,
        sim.uq_method,sim.machine)

    sim.solver.qois = config_list(
        "qois",prms,sim.solver.QoI.create,
        sim.uq_method)

    # in the multilevel case, some firther setup is needed for the
    # levels (mainly sorting prms into sublevels f and c)
    sim.uq_method.setup_batches(sim.solver.qois)

    simulation.sim = sim
    return sim

def restart(prmfile=None):
    with open('pounce.pickle', 'rb') as f:
        sim = pickle.load(f)
    if prmfile:
        raise Exception("Modifying parameters at restart is not yet "
                        "implemented")

    n_finished_iter = (len(sim.iterations)
                       - (1 if sim.uq_method.do_continue else 0))
    if n_finished_iter > 0:
        p_print(cyan("Skipping %i finished Iteration(s)."%(n_finished_iter)))

    simulation.sim = sim
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

    print("\n_print default YML File\n"+"-"*132+"\n_config:\n")
    all_defaults = {}
    subclasses = []

    # Get defaults for parent classes uq_method, machine and solver.
    for parent_class in [UqMethod, Machine, Solver]:

        # Inquire user input to choose subclass for which defaults are
        # to be printed
        subclass = inquire_subclass(parent_class)

        # add to list, as might be needed for defaults_add
        subclasses += [subclass]

        #store solver to pick QoI from 
        if parent_class is Solver: 
            solver = subclass

        # add defaults for this class to dict with all defaults
        all_defaults[parent_class.name()] = subclass.defaults()

    # we update the large defaults dict with a list containing our
    # level dict.
    # This outputs the defaults for n_levels = 1 in the correct format
    all_defaults["levels"] = [Level.defaults(*subclasses)]

    var_defaults=get_list_defaults(StochVar,*subclasses)
    all_defaults["stoch_vars"] = var_defaults

    # QoIs
    qoi_defaults=get_list_defaults(solver.QoI,*subclasses)
    all_defaults["qois"] = qoi_defaults

    # add general config parameters
    all_defaults["general"] = simulation.Simulation.defaults()

    msg="Enter file name for output (press enter for stdout):\n"
    filename_out=input(msg)
    if filename_out:
        sys.stdout = open(filename_out, 'w')
    else:
        print("\n_default YML File:\n"+"-"*132+"\n")
    print(yaml.dump(all_defaults, default_flow_style=False))
    sys.exit()


def get_list_defaults(parent, *args):
    """ output a list of all implemented types of list-input items
    (e.g. stoch_var, qoi)
    """
    return [sub.defaults(*args) for sub in parent.__subclasses__()]


def inquire_subclass(parent_class, prepend=""):
    """
    Asks for user input to choose one of the available subclasses
    """
    msg = "Please choose a "+parent_class.name()+":"
    if prepend: 
        msg = prepend+": "+msg
    subclasses = {c.name(): c for c in parent_class.__subclasses__()}
    subclass_name,_=pick(list(subclasses.keys()), msg)
    return subclasses[subclass_name]
