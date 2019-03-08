import pickle

from helpers.printtools import *

class Simulation():

    def __init__(self):
        self.iterations=[Iteration()]
        self.filename = "pickle"

    def run(self):
        """Main Loop for UQMethod.
        """
        # main loop
        while self.uq_method.do_continue:
            self.run_iteration(self.iterations[-1])

        print_major_section("Last iteration finished. Exit loop. Start Post-Processing")

        if self.uq_method.has_simulation_postproc:
            self.simulation_postproc()

        print_major_section("POUNCE Finished")


    def simulation_postproc(self):
        self.machine.allocate_resources_simu_postproc(self.uq_method.qois)
        self.solver.prepare_simu_postproc(self.uq_method.qois)
        self.machine.run_batches(self.uq_method.qois,self,self.solver,postproc_type="simu")


    def run_iteration(self,iteration):
        """General procedure:

        1. Let machine decide how many samples to compute.
        2. Generate samples and weights.
        3. Compute samples on system
        """

        # Prepare next iteration

        print_major_section("Start iteration %d"%(len(self.iterations)))
        if iteration.finished_steps:
            PPrint(green("Skipping finished steps of iteration:"))
            [PPrint("  "+i) for i in iteration.finished_steps]

        iteration.run_step("Get samples",
                                self.uq_method.get_nodes_and_weights,
                                self)

        # Simulations

        iteration.run_step("Allocate resources",
                                self.machine.allocate_resources,
                                self,
                                self.uq_method.solver_batches)

        iteration.run_step("Prepare simulations",
                                self.solver.prepare_simulations,
                                self,
                                self.uq_method.solver_batches,self.uq_method.stoch_vars)

        iteration.run_step("Run simulations",
                                self.machine.run_batches,
                                self,
                                self.uq_method.solver_batches,self,self.solver)

        # Post-Processing

        iteration.run_step("Allocate resources Postproc",
                                self.machine.allocate_resources_postproc,
                                self,
                                self.uq_method.postproc_batches)

        iteration.run_step("Prepare postprocessing",
                                self.solver.prepare_postproc,
                                self,
                                self.uq_method.postproc_batches)

        iteration.run_step("Run postprocessing",
                                self.machine.run_batches,
                                self,
                                self.uq_method.postproc_batches,self,self.solver,postproc_type="iter")

        # Prepare next iteration

        if len(self.iterations) == self.uq_method.n_max_iter:
            self.uq_method.do_continue=False
            return

        iteration.run_step("Get number of samples for next iteration",
                                self.uq_method.get_new_n_current_samples,
                                self,
                                self.solver)

        if self.uq_method.do_continue:
            self.iterations.append(Iteration())

        return



class Iteration():

    def __init__(self):
        self.finished_steps=[]

    def update_step(self,simulation,string=None):
        if string:
            self.finished_steps.append(string)
        with open(simulation.filename, 'wb') as f:
            pickle.dump(simulation, f, 2)

    def run_step(self,description,func,simulation,*args,**kwargs):
        if description not in self.finished_steps:
            print_step(description+":")
            func(*args,**kwargs)
            self.update_step(simulation,description)
