from solver import Solver

@Solver.RegisterSubclass('internal')
class SolverInternal(Solver):
   def Report(self): 
      print("I am Internal")
