import os
import numpy
import shutil
import sys
from setuptools import setup
from distutils.extension import Extension
import setuptools

INCLUDE_DIR = "IncludeFiles"
COMMON_DIR = os.path.join(INCLUDE_DIR, "Common")
CERES_INCLUDE = os.path.join(COMMON_DIR, "ceres", "include")
MINIGLOG=os.path.join(CERES_INCLUDE, "miniglog")

with open(os.path.join(os.path.dirname(__file__), 'README.md')) as readme:
    README = readme.read()

with open(os.path.join(os.path.dirname(__file__), 'LICENSE')) as license:
    LICENSE = license.read()

extra_compile_args = []
extra_link_args = []
if sys.platform == 'win32':
    LIB_DIR = r"./ceres-bin/lib/Release/ceres.lib"
    macros = [('GOOGLE_GLOG_DLL_DECL', '_CRT_SECURE_NO_WARNINGS'),
              ('CERES_USE_CXX_THREADS', None),
              ('_MBCS', None),
              ('CERES_USING_STATIC_LIBRARY', None)]
    extra_compile_args = ['/Ox']
    # extra_link_args = ['/debug']
elif sys.platform in ['linux', 'linux2']:
    extra_compile_args = ['-fPIC', '-std=c++14']
    LIB_DIR = r"../Common/ceres/bin/lib/libceres.a"
    macros = [('GOOGLE_GLOG_DLL_DECL', '_CRT_SECURE_NO_WARNINGS'),
              ('CERES_USE_CXX_THREADS', None),
              ('_MBCS', None),
              ('CERES_USING_STATIC_LIBRARY', None)]

# allow setup.py to be run from any path
os.chdir(os.path.normpath(os.path.join(os.path.abspath(__file__), os.pardir)))
class PrepareCommand(setuptools.Command):
    description = "Build pyx files so there's no cython dependence in installation"
    user_options = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        print("running prepare command")
        self.copy_source_files()
        second_pyx = './ceres_wrap/call_obj.pyx'
        self.convert_to_c(second_pyx)
        third_pyx = './ceres_wrap/cython_ceres.pyx'
        self.convert_to_c(third_pyx)

    def copy_source_files(self):
        if os.path.exists("IncludeFiles"):
            shutil.rmtree("IncludeFiles")
        # create directories with the same hierarchy as dplus
        backend_dir = os.path.join(INCLUDE_DIR, "Backend", "Backend")
        os.makedirs(backend_dir)
        print("copying backend files")
        #shutil.copy(r"../Backend/Backend/PeriodicSplineSolver.h", backend_dir)
        shutil.copy(r"./Residual.h", backend_dir)

        os.makedirs(COMMON_DIR)
        print("copying common files")
        shutil.copy(r"./Common.h", COMMON_DIR)
        shutil.copytree(r"./Eigen", os.path.join(COMMON_DIR, "Eigen"))

        #os.makedirs(CERES_INCLUDE)
        print("copying ceres files")
        shutil.copytree(r"./ceres/include", CERES_INCLUDE)
        shutil.copy(r"./ceres/config/ceres/internal/config.h", os.path.join(CERES_INCLUDE, "ceres","internal"))

        print("copying miniglog files")
        shutil.copytree("./ceres/internal/ceres/miniglog", MINIGLOG)


    def convert_to_c(self, pyx):
        #creates fast.h and fast.c in cpp_wrapper folder
        print('Converting pyx files to C++ sources...')
        print(pyx)
        self.cython(pyx)
        print('Converting {} pyx files to C++ sources...'.format(pyx.split("/")[-1]))


    def cython(self, pyx):
        from Cython.Compiler.CmdLine import parse_command_line
        from Cython.Compiler.Main import compile
        options, sources = parse_command_line(['-2', '-v', '--cplus', pyx])
        result = compile(sources, options)
        if result.num_errors > 0:
            print('Errors converting %s to C++' % pyx, file=sys.stderr)
            raise Exception('Errors converting %s to C++' % pyx)
        self.announce('Converted %s to C++' % pyx)

class MoveCommand(setuptools.Command):
    description = "Move pyd or so files to create installation"
    user_options = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        print("running move command")
        self.copy_source_files()

    def copy_source_files(self):
        build_dir='build'
        lib_dir=''
        for dir in os.listdir(build_dir):
            if 'lib' in str(dir):
                lib_dir=os.path.join(build_dir, dir)
        names=[]
        if lib_dir:
            
            for name in os.listdir(lib_dir):
                print(name)
                if ".pyd" in name or ".so" in str(name):
                    shutil.copy(os.path.join(lib_dir, name), os.path.dirname(__file__))
                    names.append(name)
        if names:
            print("copied pyd files %s" % str(names))
        else:
            print("copying failed")
         
     
        


setup(
    name='ceres-wrap',
    version='4.3.8.1',
    packages=['ceres_wrap'],
	install_requires=['numpy>=1.10'],
    include_package_data=True,
    license=LICENSE,  # example license
    description='Wrap ceres',
    url='researchsoftware.co.il',
    author='Devora Witty',
    author_email='devorawitty@researchsoftware.co.il',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Console',
        'Intended Audience :: Science/Research',
        'License :: Other/Proprietary License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3.8',
        'Topic :: Scientific/Engineering :: Chemistry',
    ],
    cmdclass={
        'prepare': PrepareCommand,
        'move': MoveCommand
    },
    ext_modules=[
        Extension(
             "cython_ceres",
             ["ceres_wrap/cython_ceres.pyx", "ceres_wrap/call_obj.pyx"],
             language='c++',
             include_dirs=[CERES_INCLUDE, INCLUDE_DIR, COMMON_DIR, MINIGLOG, numpy.get_include()],
             define_macros=macros,
             extra_compile_args=extra_compile_args,
             extra_objects=[LIB_DIR]),
    ]
)
