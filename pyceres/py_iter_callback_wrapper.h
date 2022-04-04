// TODO: add credit
#include <Python.h>
#include <string>
#include "iteration_callback_func.h" // cython helper file
#include "ceres/iteration_callback.h"
#include <iostream>
using namespace std;
class PyIterationCallbackWrapper : public ceres::IterationCallback
{
public:
    // constructors and destructors mostly do reference counting
    PyIterationCallbackWrapper(PyObject *o) : held(o)
    {
        Py_XINCREF(o);
    }

    PyIterationCallbackWrapper(const PyIterationCallbackWrapper &rhs) : PyIterationCallbackWrapper(rhs.held)
    { // C++11 onwards only
    }

    PyIterationCallbackWrapper(PyIterationCallbackWrapper &&rhs) : held(rhs.held)
    {
        rhs.held = 0;
    }

    // need no-arg constructor to stack allocate in Cython
    PyIterationCallbackWrapper() : PyIterationCallbackWrapper(nullptr)
    {
    }

    ~PyIterationCallbackWrapper()
    {
        Py_XDECREF(held);
    }

    PyIterationCallbackWrapper &operator=(const PyIterationCallbackWrapper &rhs)
    {
        PyIterationCallbackWrapper tmp = rhs;
        return (*this = std::move(tmp));
    }

    PyIterationCallbackWrapper &operator=(PyIterationCallbackWrapper &&rhs)
    {
        held = rhs.held;
        rhs.held = 0;
        return *this;
    }

    ceres::CallbackReturnType operator ()(const ceres::IterationSummary &)
    {
        cout << &call_iteration_function<<endl;
        int flag = 0;
        if (held)
        { // nullptr check
            flag = call_iteration_function(held); // note, no way of checking for errors until you return to Python
        }
        // ceres::CallbackReturnType returnType = <ceres::CallbackReturnType>flag;
        return ceres::CallbackReturnType(flag);
    }

    int operator()()
    {
        int flag = 0;
        // double* tmp_p = new double[numParams];

        // send tmp_p because cython can't receive const* const*.
        // This  doesn't matter because we don't change this values

        // for (int i = 0; i < numParams; i++)
        // {
        //     tmp_p[i] = p[0][i];
        // }
        if (held)
        { // nullptr check
            flag = call_iteration_function(held); // note, no way of checking for errors until you return to Python
        }
         return ceres::CallbackReturnType(flag);
    }

private:
    PyObject *held;
};