from pyceres import PyProblem, PySolverOptions, PyResidual, PyTrivialLoss, PySolverSummary, solve, SolverTerminationType
import numpy as np
import math
from copy import deepcopy

class FakeFittingPreferences:
    def __init__(self):
        self.convergence = 0.1
        self.step_size=0.01
        self.der_eps=0.1
        self.fitting_iterations=20


class CalculationInput:
    def __init__(self, x, y, params):
        self.x = x
        self.y = y
        self.params=params
        self.FittingPreferences=FakeFittingPreferences()

    def get_mutable_params(self):
        return self.params

    def set_mutable_parameter_values(self, params):
        self.params=params

class CalcResult:
    def __init__(self, arr):
        self.y=arr

class CalcRunner:
    def generate(self, calc_input, *args, **kwargs):
        return self.my_func(calc_input)

    def my_func(self, calc_input):
        params = calc_input.params
        x = calc_input.x
        return CalcResult([x[0] * params[0], x[1] * params[1], x[2]+params[0]])


class TestResidual:
    def __init__(self, calc_input:CalculationInput, calc_runner:CalcRunner, best_params, best_eval):
        self.calc_input = deepcopy(calc_input)
        self.calc_runner = calc_runner
        self.np_y = np.asanyarray(self.calc_input.y, dtype=np.double)
        self._best_params = best_params
        self._best_eval = best_eval

    def run_generate(self, params, num_residual):
        self.calc_input.set_mutable_parameter_values(params)
        calc_result = self.calc_runner.generate(self.calc_input)
        residual = np.asanyarray(calc_result.y, dtype=np.double)
        res = self.calc_residual(residual, num_residual) #note that residual changes within this function
        if res < self.best_eval:
            self.best_eval = res
            if self.best_params.size != 0:
                self.best_params = params
        return residual

    @property
    def best_eval(self):
        """
        double array. we works with array in order to mimic double* (pointer) behavior
        """
        return self._best_eval[0]

    @best_eval.setter
    def best_eval(self, best_val):
        self._best_eval[0] = best_val

    @property
    def best_params(self):
        """
        double array. we change the values inside the array and to the array itself because we want to
         mimic pointers behavior
        """
        return self._best_params

    @best_params.setter
    def best_params(self, new_best_params):
        for i in range(len(new_best_params)):
            self._best_params[i] = new_best_params[i]

    def calc_residual(self, residual, num_residual):
        res = np.double(0)
        for i in range(num_residual):
            residual[i] = math.fabs(self.np_y[i] - residual[i])
            res += residual[i] * residual[i]
        res /= 2.0
        return res

class Optimizer:
    def __init__(self, calc_input):
        self.calc_input = calc_input
        self.calc_runner = CalcRunner()
        self.problem = PyProblem()
        self.options = PySolverOptions()
        self.options.linear_solver_type=1
        self.best_params = None
        self.best_val = np.array([np.inf])
        self.bConverged = False
        self._best_results = None
        self.init_problem()

    def init_problem(self):
        self.bConverged = False
        #fitting preferences:

        fit_pref = self.calc_input.FittingPreferences
        # This is the convergence that was writen in dplus
        conv = fit_pref.convergence * np.mean(self.calc_input.y) * 0.001
        self.options.function_tolerance = conv
        self.options.update_state_every_iteration = True
        self.options.gradient_tolerance = 1e-4 * self.options.function_tolerance
        mut_param = self.calc_input.get_mutable_params()

        paramdata = np.zeros(shape=(1,len(mut_param)))
        for i in range (len(paramdata[0])):
            paramdata[0][i] = mut_param[i]

        mut_param_values = self.calc_input.get_mutable_params()
        self.best_params = np.asanyarray(mut_param_values, dtype=np.double)
        self.best_val = np.array([np.inf])

        cost_class = TestResidual(self.calc_input, self.calc_runner, self.best_params, self.best_val)
        y = np.asarray(self.calc_input.y)
        self.cost_function = PyResidual(np.asanyarray(self.calc_input.x, dtype=np.double),
                                        np.asanyarray(self.calc_input.y, dtype=np.double),
                                        len(mut_param_values),
                                        len(y),
                                        cost_class.run_generate,
                                        fit_pref.step_size,
                                        fit_pref.der_eps,
                                        self.best_params,
                                        self.best_val)
        self.options.max_num_iterations = fit_pref.fitting_iterations
        self.params_value = paramdata[0]

        self.problem.add_residual_block(self.cost_function, PyTrivialLoss(), paramdata)


        self.options.minimizer_progress_to_stdout = True
        self.options.use_nonmonotonic_steps = True

    def solve(self): #this function is called "iterate" in D+
        self._best_results = None
        summary = PySolverSummary()
        solve(self.options, self.problem, summary)

        print(summary.fullReport().decode("utf-8"))
        print("\n")
        cur_eval = summary.final_cost
        self.bConverged = (summary.termination_type == SolverTerminationType.CONVERGENCE)
        flag_valid_constraint = True
        if (flag_valid_constraint):
            cur_eval = self.best_val
            self.calc_input.set_mutable_parameter_values(self.best_params)
        return cur_eval

    @property
    def best_results(self):
        if not self._best_results:
            self._best_results = self.calc_runner.generate(self.calc_input)
        return self._best_results


    @staticmethod
    def fit(calc_input, calc_runner=None, save_amp=False):
        if not calc_runner:
            from dplus.CalculationRunner import LocalRunner
            calc_runner = LocalRunner()
        session_dir = calc_runner.session_directory
        PyCeresOptimizer.save_status(session_dir, error=False, is_running=True)
        try:
            optimizer = PyCeresOptimizer(calc_input, calc_runner, save_amp)
            gof = optimizer.solve()
            print("Iteration GoF = %f\n", gof)

            best_results = optimizer.best_results
            data_path = os.path.join(session_dir, "data.json")
            PyCeresOptimizer.save_dplus_arrays(best_results, data_path)
            PyCeresOptimizer.save_status(session_dir, error=False, is_running=False, progress=1.0, code=0, message="OK")
            return best_results
        except Exception as e:
            PyCeresOptimizer.save_status(session_dir, error=False, code=24, message=str(e), is_running=False, progress=0)
            raise e

    @staticmethod
    def save_status(session_dir, error,is_running=False, progress=0.0, code=0, message="OK"):
        if not error:
            status_dict = {"isRunning": is_running, "progress": progress, "code": code,
                           "message": str(message)}
        else:
            status_dict = {"error": {"code": code, "message": str(message)}}
        with open(os.path.join(session_dir, "fit_job.json"), 'w') as file:
            json.dump(status_dict, file)

    @staticmethod
    def save_dplus_arrays(best_results, outfile=None):
        '''
        a function for saving fit results in the bizarre special format D+ expects
        :param outfile:
        :return:
        '''
        param_tree = best_results._calc_data._get_dplus_fit_results_json()
        result_dict = {
            "ParameterTree": param_tree,
            "Graph": list(best_results.y)
        }
        if outfile:
            with open(outfile, 'w') as file:
                json.dump(_handle_infinity_for_json(result_dict), file, cls=NumpyHandlingEncoder)

        return result_dict




def fit():
    c=CalculationInput([2,4,6], [0, 2], [2,-4,6])
    optimizer = Optimizer(c)
    gof = optimizer.solve()
    print("Iteration GoF = %f\n", gof)


if __name__=="__main__":
    fit()