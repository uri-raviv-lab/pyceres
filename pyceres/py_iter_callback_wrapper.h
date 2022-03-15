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
        freopen("C:\\Users\\chana\\Downloads\\output.txt", "w", stdout);
        cout << "PyIterationCallbackWrapper(const && rhs)" << endl;
    }

    PyIterationCallbackWrapper(PyIterationCallbackWrapper &&rhs) : held(rhs.held)
    {
        freopen("C:\\Users\\chana\\Downloads\\output.txt", "w", stdout);
        cout << "PyIterationCallbackWrapper(&& rhs)" << endl;
        rhs.held = 0;
    }

    // need no-arg constructor to stack allocate in Cython
    PyIterationCallbackWrapper() : PyIterationCallbackWrapper(nullptr)
    {
        freopen("C:\\Users\\chana\\Downloads\\output.txt", "w", stdout);
        cout << "PyIterationCallbackWrapper()" << endl;
    }

    ~PyIterationCallbackWrapper()
    {
        freopen("C:\\Users\\chana\\Downloads\\output.txt", "w", stdout);
        cout << "~PyIterationCallbackWrapper()" << endl;
        Py_XDECREF(held);
    }

    PyIterationCallbackWrapper &operator=(const PyIterationCallbackWrapper &rhs)
    {
        freopen("C:\\Users\\chana\\Downloads\\output.txt", "w", stdout);
        cout << "operator= 1" << endl;
        PyIterationCallbackWrapper tmp = rhs;
        return (*this = std::move(tmp));
    }

    PyIterationCallbackWrapper &operator=(PyIterationCallbackWrapper &&rhs)
    {
        freopen("C:\\Users\\chana\\Downloads\\output.txt", "w", stdout);
        cout << "operator= 1" << endl;
        held = rhs.held;
        rhs.held = 0;
        return *this;
    }

    ceres::CallbackReturnType operator ()(const ceres::IterationSummary &)
    {
        int flag = 0;
        cout << "operator() 1" << endl;
        if (held)
        { // nullptr check
            cout << "operator() 2" << endl;
            flag = call_iteration_function(held); // note, no way of checking for errors until you return to Python
            cout << "operator() 3  the flag =" << flag << endl;
        }
        cout << "operator() 4" << endl;
        // ceres::CallbackReturnType returnType = <ceres::CallbackReturnType>flag;
        return ceres::SOLVER_CONTINUE;
    }

    int operator()()
    {
        freopen("C:\\Users\\chana\\Downloads\\output.txt", "w", stdout);
        int flag = 0;
        // double* tmp_p = new double[numParams];

        // send tmp_p because cython can't receive const* const*.
        // This  doesn't matter because we don't change this values

        // for (int i = 0; i < numParams; i++)
        // {
        //     tmp_p[i] = p[0][i];
        // }
        cout << "operator() 1" << endl;
        if (held)
        { // nullptr check
            cout << "operator() 2" << endl;
            flag = call_iteration_function(held); // note, no way of checking for errors until you return to Python
            cout << "operator() 3  the flag =" << flag << endl;
        }
        // delete tmp_p;
        cout << "operator() 4" << endl;
        return flag;
    }

private:
    PyObject *held;
};