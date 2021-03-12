from .solver import Solver,QoI

class SurrogateModel(Solver):

    defaults_ = {
        "solver_prms" : "dummy_unused",
        "exe_path" : "dummy_unused",
        "n_samples_input": "NODEFAULT",
        "i_model_input": "NODEFAULT"
            }

    is_surrogate = True

    class QoI(QoI):

        defaults_ = {
            "exe_path" : "dummy_unused"
                }

        internal = True

        def get_current_work_mean(self):
            return self.current_work_mean

