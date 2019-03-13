import pickle
import os
import tarfile
import glob

from helpers.printtools import *
from helpers.baseclass import BaseClass

class Simulation(BaseClass):

    class_defaults={"archive_level" : 0,
                    # to keep parameter files compatible
                    "output_level" : "dummy"}

    def __init__(self,class_dict):
        super().__init__(class_dict)
        self.iterations=[Iteration(1)]
        self.filename = "pounce.pickle"

    def run(self):
        """Main Loop for UQMethod.
        """
        # main loop
        while self.uq_method.do_continue:
            self.run_iteration(self.iterations[-1])

        print_major_section("Last iteration finished. Exit loop. "
                            "Start Post-Processing")

        if self.uq_method.has_simulation_postproc:
            if not getattr(self,"simu_postproc_iter",None):
                self.simu_postproc_iter=Iteration(-1)
            self.run_simulation_postproc(self.simu_postproc_iter)

        print_major_section("POUNCE Finished")


    def run_iteration(self,iteration):
        """General procedure:

        1. Let machine decide how many samples to compute.
        2. Generate samples and weights.
        3. Compute samples on system
        """

        # Prepare next iteration

        print_major_section("Start iteration %d"%(iteration.n))
        if iteration.finished_steps:
            p_print(green("Skipping finished steps of iteration:"))
            [p_print("  "+i) for i in iteration.finished_steps]

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
                           self.uq_method.solver_batches,self.uq_method)

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
                           self.uq_method.postproc_batches,self,self.solver,
                               postproc_type="iter")

        # Prepare next iteration

        if iteration.n == self.uq_method.n_max_iter:
            self.uq_method.do_continue=False
            return

        iteration.run_step("Get number of samples for next iteration",
                           self.uq_method.get_new_n_current_samples,
                           self,
                           self.solver,iteration.n)

        iteration.run_step("Archive",
                           iteration.archive,
                           self,
                           self.archive_level,self)

        if self.uq_method.do_continue:
            self.iterations.append(Iteration(iteration.n+1))

        return


    def run_simulation_postproc(self,postproc):

        postproc.run_step("Allocate resources for simulation postproc",
                          self.machine.allocate_resources_simu_postproc,
                          self,
                          self.uq_method.qois)

        postproc.run_step("Prepare simulation postprocessing",
                          self.solver.prepare_simu_postproc,
                          self,
                          self.uq_method.qois)

        postproc.run_step("Run simulation postprocessing",
                          self.machine.run_batches,
                          self,
                          self.uq_method.qois,self,self.solver,
                              postproc_type="simu")





class Iteration():

    def __init__(self,n):
        self.finished_steps=[]
        self.n=n

    def update_step(self,simulation,string=None,filename=None):
        if string:
            self.finished_steps.append(string)
        if not filename: 
            filename=simulation.filename
        with open(filename, 'wb') as f:
            pickle.dump(simulation, f, 2)

    def run_step(self,description,func,simulation,*args,**kwargs):
        if description not in self.finished_steps:
            print_step(description+":")
            func(*args,**kwargs)
            self.update_step(simulation,string=description)

    def archive(self,archive_level,simulation): 
        if archive_level == 0: 
            p_print("Archiving is deactivated.")
            return
        if not os.path.isdir('archive'): 
            os.mkdir('archive')
        self.archive_name='archive/iter_%d.tar.gz'%(self.n)
        self.files=glob.glob('*')
        # prevent simulations restarted from archive from
        # writing the very same data to archive again.
        pf_temp='.temp.pickle'
        self.update_step(simulation,filename=pf_temp)
        p_print("Write to file "+yellow(self.archive_name))
        with tarfile.open(self.archive_name, "w:gz") as tar:
            for fn in self.files: 
                print(fn)
                if os.path.islink(fn): 
                    print(fn)
                if fn not in [simulation.filename,"archive"] \
                        and not os.path.islink(fn):
                    tar.add(fn)
            tar.add(pf_temp,arcname=simulation.filename)
        os.remove(pf_temp)


