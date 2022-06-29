import cython
from libc.stdio cimport printf #printf for debugging
from libcpp cimport int
from libcpp.string cimport string

# although we dont use these imports, without them this file doesnt compile
import numpy as np
cimport numpy as np

from enum import Enum
def enum(*sequential, **named):
    enums = dict(zip(sequential, range(len(sequential))), **named)
    reverse = dict((value, key) for key, value in enums.iteritems())
    enums['reverse_mapping'] = reverse
    return type('Enum', (), enums)

CallbackReturnType = enum("SOLVER_CONTINUE", "SOLVER_ABORT", "SOLVER_TERMINATE_SUCCESSFULLY")


cdef public int call_iteration_function(obj) :
    # for some unknown reason you can't use numpy here ( cdef double[:] view fail, np_x.data fail)
    # however we must convert c types to python types. so we will create python lists that contain the values
    cdef int CallbackReturnType_int
    CallbackReturnType_int = obj()
    return CallbackReturnType_int