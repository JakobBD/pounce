from solver import Solver

@Solver.RegisterSubclass('flexi')
class SolverFlexi(Solver):
   def Report(self): 
      print("I am FLEXI")
