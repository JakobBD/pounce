import h5py
import numpy as np
import subprocess
import glob

from .solver import Solver
from helpers.printtools import *

@Solver.RegisterSubclass('flexi')
class SolverFlexi(Solver):
   subclassDefaults={
         "prmfiles" : {"mainSolver": "","iterationPostproc": ""}
      }

   def PrepareSimulations(self,batches,stochVars):
      """ Prepares the simulation by generating the runCommand
      and writing the HDF5 file containing all samples of the current iteration
      and the current samples.
      """
      for batch in batches:
         Print("Write HDF5 parameter file for simulation "+batch.name)
         batch.projectName = self.projectName+'_'+batch.name
         batch.h5PrmFileName = 'input_'+batch.projectName+'.h5'
         self.WriteHdf5(batch,stochVars)
         batch.runCommand = self.exePaths["mainSolver"] + ' ' + batch.h5PrmFileName + ' ' + self.prmfiles["mainSolver"]


   def WriteHdf5(self,batch,stochVars):
      """ Writes the HDF5 file containing all necessary data for flexi run
      to run.
      """
      h5f = h5py.File(batch.h5PrmFileName, 'w')
      h5f.create_dataset('Samples', data=batch.samples.nodes)
      h5f.create_dataset('Weights', data=batch.samples.weights)
      h5f.attrs.create('StochVarNames', [var.name.ljust(255) for var in stochVars], (len(stochVars),), dtype='S255' )
      h5f.attrs.create('iOccurrence', [var.iOccurrence for var in stochVars], (len(stochVars),) )
      h5f.attrs.create('iArray', [var.iPos for var in stochVars], (len(stochVars),) )
      h5f.attrs["nStochVars"] = len(stochVars)
      h5f.attrs["nGlobalRuns"] = batch.samples.n
      h5f.attrs["nPreviousRuns"] = batch.samples.nPrevious
      h5f.attrs["nParallelRuns"] = batch.nParallelRuns

      batch.solverPrms.update({"ProjectName":self.projectName+"_"+batch.name})
      dtypes=[( "Int",    int,    None,    lambda x:x),
              ( "Str",    str,    "S255",  lambda x:x.ljust(255)),
              ( "Real",   float,  None,    lambda x:x)]

      for       dtypeName,dtypeIn,dtypeOut,func in dtypes: 
         names=[ key.ljust(255) for key, value in batch.solverPrms.items() if isinstance(value,dtypeIn)]
         values=[ func(value) for value in batch.solverPrms.values() if isinstance(value,dtypeIn)]
         nVars=len(names)
         h5f.attrs["nLevelVars"+dtypeName]=nVars
         h5f.attrs.create('LevelVarNames'+dtypeName, names,  shape=(nVars,), dtype='S255' )
         h5f.attrs.create('LevelVars'+dtypeName,     values, shape=(nVars,), dtype=dtypeOut )

      h5f.close()

   def PreparePostproc(self,postprocBatches):
      """ Prepares the postprocessing by generating the runPostprocCommand.
      """
      for postproc in postprocBatches: 
         names=[p.name for p in postproc.participants]
         Print("Generate Post-proc command for simulation(s) "+", ".join(names))
         postproc.runCommand = self.exePaths["iterationPostproc"] + " " + self.prmfiles["iterationPostproc"]
         # this is a rather ugly current flexi implementation
         postproc.projectName = postproc.participants[0].projectName
         postproc.outputFilename = 'postproc_'+postproc.projectName+'_state.h5'
         for p in postproc.participants:
            filename=sorted(glob.glob(p.projectName+"_State_*.h5"))[-1]
            postproc.runCommand=postproc.runCommand+' '+filename

   def PrepareSimuPostproc(self,simuPostproc):
      simuPostproc.args=[p.postproc.outputFilename for p in simuPostproc.participants]
      simuPostproc.runCommand=self.exePaths["simulationPostproc"] + " " + " ".join(simuPostproc.args)

   def GetPostprocQuantityFromFile(self,postproc,quantityName):
      """ Readin sigmaSq or avgWalltime for MLMC.
      """
      h5f = h5py.File(postproc.outputFilename, 'r')
      quantity = h5f.attrs[quantityName]
      h5f.close()
      return quantity

   def GetWorkMean(self,postproc):
      return sum(p.currentAvgWork for p in postproc.participants)

   def CheckFinished(self,batch):
      #TODO: some more checks, e.g. empty stderr
      try:
         args=['tail','-n','3',batch.logfileName]
         output=subprocess.run(args,stdout=subprocess.PIPE)
         output=output.stdout.decode("utf-8").splitlines()
         batch.currentAvgWork=float(output[2])
         return output[0]=="FLEXIBATCH FINISHED"
      except: 
         return False


# class QoIState():
   # pass

# QoIs={"state":QoIState}
