//TODO: add credit
#include <Python.h>
#include <string>
#include "call_cost_function.h" // cython helper file
#include <iostream>
using namespace std;
class PyCostFuncWrapper {
public:
    // constructors and destructors mostly do reference counting
    PyCostFuncWrapper(PyObject* o): held(o) {
        Py_XINCREF(o);
    }

    PyCostFuncWrapper(const PyCostFuncWrapper& rhs): PyCostFuncWrapper(rhs.held) { // C++11 onwards only
    }

    PyCostFuncWrapper(PyCostFuncWrapper&& rhs): held(rhs.held) {
        rhs.held = 0;
    }

    // need no-arg constructor to stack allocate in Cython
    PyCostFuncWrapper(): PyCostFuncWrapper(nullptr) {
    }

    ~PyCostFuncWrapper() {
        Py_XDECREF(held);
    }

    PyCostFuncWrapper& operator=(const PyCostFuncWrapper& rhs) {
        PyCostFuncWrapper tmp = rhs;
        return (*this = std::move(tmp));
    }

    PyCostFuncWrapper& operator=(PyCostFuncWrapper&& rhs) {
        held = rhs.held;
        rhs.held = 0;
        return *this;
    }

    bool operator()(const double* x,  double const* const* p, double* residual, int numResiduals, int numParams) {
        bool flag = false;
        double* tmp_p = new double[numParams];
        // send tmp_p because cython can't receive const* const*.
        // This  doesn't matter because we don't change this values
        for (int i = 0; i < numParams; i++)
        {
            tmp_p[i] = p[0][i];
        }
        if (held) { // nullptr check
            flag = call_cost_function(held,x, tmp_p, residual, numResiduals, numParams); // note, no way of checking for errors until you return to Python
        }
        delete tmp_p;
        return flag;
    }

private:
    PyObject* held;
};