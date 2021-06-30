import pickle
import os
import tarfile
import glob
from .printtools import *


# These are place holders and overwritten during config
sim=None
archive_level=None
project_name=None
do_pickle=None


def update_step(string=None):
    if string:
        sim.current_iter.finished_steps.append(string)
    if do_pickle: 
        fn_step = "pickle/I{}_S{}.pickle".format(sim.current_iter.n,
                                                 len(sim.current_iter.finished_steps))
        for fn in [sim.filename, fn_step]: 
            with open(fn, 'wb') as f:
                pickle.dump(sim, f, 2)


def run_step(description, func, *args, **kwargs):
    if description not in sim.current_iter.finished_steps:
        print_step(description+":")
        func(*args,**kwargs)
        update_step(string=description)


def iteration(wrapped_function):
    def iteration_wrapper(self):
        self.current_iter.start()
        wrapped_function(self)
        archive()
        self.current_iter.finished = True
    return iteration_wrapper


def archive(): 
    if archive_level == 0: 
        return
    description="Archive"
    run_step(description,archive_loc)

    # mark archiving as done. Pickle new state and add to archive.
    # This prevents simulations restarted from archive from
    # instantly archiving the very same data again.
    if description not in sim.current_iter.finished_steps:
        archive_name = 'archive/%s.tar.gz'%(sim.current_iter.name.replace(" ","_"))
        with tarfile.open(archive_name, "r+:gz") as tar:
            tar.add(sim.pickle_file)


def archive_loc():
    if not os.path.isdir('archive'): 
        os.mkdir('archive')
    archive_name = 'archive/%s.tar.gz'%(sim.current_iter.name.replace(" ","_"))
    files = glob.glob('*')
    p_print("Write to file "+yellow(archive_name))
    with tarfile.open(archive_name, "w:gz") as tar:
        for fn in files: 
            if fn not in [sim.pickle_file, 'archive'] \
                    and not os.path.islink(fn):
                tar.add(fn)


