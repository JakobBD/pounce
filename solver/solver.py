from baseclass import BaseClass


class Solver(BaseClass): 
   pass

@Solver.RegisterSubclass('internal')
class InternalSolver(Solver):
   pass

@Solver.RegisterSubclass('flexi')
class FlexiSolver(Solver):
   pass
