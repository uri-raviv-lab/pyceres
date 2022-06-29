from dplus_ceres import PyProblem, PySolverOptions, PyResidual, PyTrivialLoss, PySolverSummary, solve, SolverTerminationType
import numpy as np
import math
from time import sleep
from copy import deepcopy
import threading

stop_flag = dict(stop=0)

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
        assert(len(x)==len(y))
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
        sleep(0.1)
        return CalcResult([x[0] * params[0] * params[1] + x[1], x[1] * params[1], x[2]+params[0]])


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


def my_callback_function(iteration_summary=None):
    if stop_flag["stop"]<2:
        return 0
    return 1

class Optimizer:
    def __init__(self, calc_input):
        self.calc_input = calc_input
        self.calc_runner = CalcRunner()
        self.problem = PyProblem()
        self.options = PySolverOptions()
        self.options.set_callbacks(my_callback_function)
        self.options.linear_solver_type=1
        self.best_params = None
        self.best_val = np.array([np.inf])
        self.bConverged = False
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



class FitWithThread():
    def __init__(self):
        self.cur_thread=None
    def fit(self):
        c=CalculationInput([1,2,3], [2,6,5], [10,-30])
        optimizer = Optimizer(c)
        gof = optimizer.solve()
        print("Iteration GoF = %f\n", gof)
        print("best params are", optimizer.best_params)
    def fit_async(self):
        self.cur_thread = threading.Thread(target=self.fit)
        self.cur_thread.start()
        hi=1
    def stop(self):
        stop_flag["stop"]=5
        self.cur_thread.join()
    def get_status(self):
        try:
            if self.cur_thread:
                is_alive = self.cur_thread.is_alive()
                if is_alive:
                    result = {"isRunning": True, "progress": 0.0, "code": -1, "message": ""}
                else:
                    if stop_flag["stop"] == 5:
                        result = {"error": {"code": 22, "message": "job stop run"}}
                    else:
                        result = {"isRunning": False, "progress": 100.0, "code": 0, "message": ""}
                    self.cur_thread.join()
            else:
                result = {"isRunning": False, "progress": 0.0, "code": -1, "message": ""}
        except Exception as ex:
            return {"error": {"code": 22, "message": str(ex)}}
        return result


if __name__=="__main__":
    f=FitWithThread()
    f.fit_async()
    f.stop()
    print(f.get_status())