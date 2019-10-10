
from helpers import globels
from helpers.printtools import *
from helpers.tools import *
from helpers.baseclass import BaseClass

class Simulation(BaseClass):
    """
    Organizes how the simulation is run, i.e. how iterations follow 
    each other in a loop and how an iteration looks. 
    Simulation is a parent class to UqMethod, where routines can be
    overwritten.
    """

    def __init__(self, class_dict):
        super().__init__(class_dict)
        self.iterations=[]
        self.current_iter=None
        self.filename = "pounce.pickle"
        self.iter_loop_finished = False


    def run(self):
        """
        Default main simulation loop: Iterate until finished or 
        maximum number of iterations is reached, the npost-process 
        if necessary.
        """
        while not self.iter_loop_finished:
            n_iter = len(self.iterations)
            if n_iter == 0 or self.current_iter.finished: 
                n_iter += 1
                Iteration(n_iter)
            self.run_iteration()
            if n_iter == self.n_max_iter:
                self.iter_loop_finished = True

        if self.has_simulation_postproc:
            string="simulation postproc"
            if not self.current_iter.name == string: 
                self.current_iter = Iteration(name=string)
            self.process_simulation_postproc()

        print_major_section("POUNCE Finished")


    @globels.iteration
    def run_iteration(self):
        """
        Default iterations:
        - Get samples to run
        - process all external stages (e.g. main simulation and
          post-processing of the iteration)
        - prepare next iteration
        """
        # Prepare next iteration
        globels.run_step("Get samples",
                         self.get_samples, 
                         self.stages[0].active_batches)
        for stage in self.stages:
            stage.process()
        # Prepare next iteration
        globels.run_step("Prepare next iteration",
                         self.prepare_next_iteration)
                           

    @globels.iteration
    def process_simulation_postproc(self):
        self.simulation_postproc.process()




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

    def process(self):
        globels.run_step("Allocate resources for "+self.name,
                         self.allocate_resources)

        globels.run_step("Prepare "+self.name,
                         self.prepare_set)

        globels.run_step("Run "+self.name,
                         self.run_batches)

    @property
    def active_batches(self):
        try: 
            return [b for b in self.batches if b.samples.n > 0]
        except AttributeError: 
            return self.batches

    @property
    def unfinished_batches(self):
        return [b for b in self.active_batches if not getattr(b,"finished",False)]

    def check_all_finished(self):
        finished = [batch.check_finished() for batch in self.batches]
        if all(finished): 
                p_print("All jobs finished.")
        else:
            tmp=[batch.name for batch,is_finished in zip(self.batches,finished) \
                 if not is_finished]
            raise Exception("not all jobs finished. "
                            +"Problems with batch(es) "+", ".join(tmp)+".")




class Iteration():

    def __init__(self, n=None, name=None):
        self.finished_steps=[]
        self.finished = False
        globels.sim.current_iter=self
        globels.sim.iterations.append(self)
        self.n = n
        self.name = name if name else "iteration " + str(n)

    def start(self):
        print_major_section("Start " + self.name)
        if self.finished_steps:
            p_print(green("Skipping finished steps of iteration:"))
            [p_print("  "+i) for i in self.finished_steps]






