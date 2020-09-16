from .solver import Solver,QoI

class SurrogateModel(Solver):

    defaults_ = {
        "solver_prms" : "dummy_unused",
        "exe_path" : "dummy_unused",
        "n_samples_input": "NODEFAULT",
        "i_model_input": "NODEFAULT"
            }

    def __init__(self,*args,**kwargs): 
        super().__init__(*args,**kwargs)
        # has to be done since mfmc overwrites defaults 
        self.is_surrogate = True

    class QoI(QoI):

        defaults_ = {
            "exe_path" : "dummy_unused"
                }

        def __init__(self,*args,**kwargs): 
            super().__init__(*args,**kwargs)
            self.internal = True

        def get_current_work_mean(self):
            return self.current_work_mean

