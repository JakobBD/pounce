import pickle
import os
import tarfile
import glob

from helpers import globels
from helpers.printtools import *
from helpers.tools import *
from helpers.baseclass import BaseClass

class Simulation(BaseClass):

    def __init__(self, class_dict):
        super().__init__(class_dict)
        self.filename = "pounce.pickle"

    def run(self):
        """Main Loop for UQMethod.
        """
        # main loop
        self.iterations = []
        self.do_continue = True
        while self.do_continue:
            n_iter = len(self.iterations) 
            if n_iter == self.n_max_iter:
                self.do_continue = False
            if self.do_continue:
                self.current_iter = Iteration(n=n_iter+1)
                self.run_iteration(self.current_iter)

        if self.has_simulation_postproc:
            string="simulation postproc"
            if not self.current_iter.name == string: 
                self.current_iter = Iteration(name=string)
            self.process_simulation_postproc(self.current_iter)

        print_major_section("POUNCE Finished")


    @make_iter
    def run_iteration(self,iteration):
        """General procedure:

        1. Let machine decide how many samples to compute.
        2. Generate samples and weights.
        3. Compute samples on system
        """

        # Prepare next iteration
        iteration.run_step("Get samples",
                           self.get_samples, 
                           self.main_simulation.active())

        self.main_simulation.process(iteration)

        self.iteration_postproc.process(iteration)

        # Prepare next iteration
        iteration.run_step("Get number of samples for next iteration",
                           self.get_new_n_current_samples,
                           iteration.n)



    @make_iter
    def process_simulation_postproc(self,iteration):
        self.simulation_postproc.process(iteration)


    def archive(self): 
        if globels.archive_level == 0: 
            p_print("Archiving is deactivated.")
            return
        if not os.path.isdir('archive'): 
            os.mkdir('archive')
        iter_ = self.current_iter
        self.archive_name = 'archive/iter_%s.tar.gz'%(iter_.name)
        self.files = glob.glob('*')
        # prevent simulations restarted from archive from
        # writing the very same data to archive again.
        pf_temp = '.temp.pickle'
        iter_.update_step(filename=pf_temp)
        p_print("Write to file "+yellow(self.archive_name))
        with tarfile.open(self.archive_name, "w:gz") as tar:
            for fn in self.files: 
                if fn not in [self.filename, "archive"] \
                        and not os.path.islink(fn):
                    tar.add(fn)
            tar.add(pf_temp,arcname=self.filename)
        os.remove(pf_temp)



class Stage():

    def fill(self, name, multi_sample, batches):
        self.name = name
        self.multi_sample = multi_sample
        self.batches = batches

    def prepare_set(self, *args):
        for batch in self.active(): 
            batch.prepare(*args)

    def process(self,iteration):
        iteration.run_step("Allocate resources for "+self.name,
                           self.allocate_resources,
                           self.active())

        iteration.run_step("Prepare "+self.name,
                           self.prepare_set,
                           globels.sim) # TODO: replace globels!!!

        iteration.run_step("Run "+self.name,
                           self.run_batches,
                           self.active())

    def active(self):
        try: 
            return [b for b in self.batches if b.samples.n > 0]
        except AttributeError: 
            return self.batches

    def __getitem__(self, index): 
        return self.batches[index]



class Iteration():

    def __init__(self, n=None, name=None):
        self.finished_steps = []
        self.n = n
        if name:
            self.name = name
        else:
            self.name = "iteration " + str(n)

    def update_step(self, string=None, filename=None):
        if string:
            self.finished_steps.append(string)
        if not filename: 
            filename = globels.sim.filename
        with open(filename, 'wb') as f:
            pickle.dump(globels.sim, f, 2)

    def run_step(self, description, func, *args, **kwargs):
        if description not in self.finished_steps:
            print_step(description+":")
            func(*args,**kwargs)
            self.update_step(string=description)

    def print_unfinished_steps(self):
        if self.finished_steps:
            p_print(green("Skipping finished steps of iteration:"))
            [p_print("  "+i) for i in self.finished_steps]

    def start(self):
        print_major_section("Start " + self.name)
        if self.finished_steps:
            p_print(green("Skipping finished steps of iteration:"))
            [p_print("  "+i) for i in self.finished_steps]

