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
                           self.stages[0].active_batches)

        for stage in self.stages:
            stage.process(iteration)

        # Prepare next iteration
        # self.get_new_n_current_samples() !TODO_MAKE_STEP
        iteration.run_step("Get number of samples for next iteration",
                           self.get_new_n_current_samples)
                           



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
        self.archive_name = 'archive/%s.tar.gz'%(iter_.name.replace(" ","_"))
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

    def __init__(self, *args):
        super().__init__(*args)
        self.batches = []

    def fill(self, name, multi_sample):
        self.name = name
        self.multi_sample = multi_sample

    def prepare_set(self):
        for batch in self.active_batches: 
            batch.prepare()

    def process(self,iteration):
        iteration.run_step("Allocate resources for "+self.name,
                           self.allocate_resources)

        iteration.run_step("Prepare "+self.name,
                           self.prepare_set)

        iteration.run_step("Run "+self.name,
                           self.run_batches)

    @property
    def active_batches(self):
        try: 
            return [b for b in self.batches if b.samples.n > 0]
        except AttributeError: 
            return self.batches

    @property
    def unfinished(self):
        return [b for b in self.active_batches if not getattr(b,"finished",False)]



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

    def start(self):
        print_major_section("Start " + self.name)
        if self.finished_steps:
            p_print(green("Skipping finished steps of iteration:"))
            [p_print("  "+i) for i in self.finished_steps]

