# This script compiles ceres. You have to run it before running setup.py.
# (at some point we will run it from setup.py)

import os
import shutil


def is_win():
    return os.name == 'nt'

def is_linux():
    return os.name == 'posix'

def prepare_eigen():
    cwd = os.getcwd()

    try:
        # Check if the Core directory is *ignored* by git by default. We need to make sure this doesn't happen to us
        if not os.path.isdir('eigen/Eigen/src/Core') or not os.path.isfile('eigen/scripts/buildtests.in'):
            print('Your Eigen sources are missing some files')
            print("This is because Eigen's .gitignore ignores `core` and `*build*`. Please remove both from Eigen's .gitignore and commit again")
            raise ValueError("Misconfigured Eigen")
        os.makedirs('build/eigen')
        os.chdir('build/eigen')

        cmd = 'cmake ../../eigen'
        if is_win():
            cmd += ' -DCMAKE_GENERATOR_PLATFORM=x64'
        os.system(cmd)
    finally:
        os.chdir(cwd)

def prepare_ceres():
    cwd = os.getcwd()

    try:
        os.makedirs('build/ceres')
        os.chdir('build/ceres')

        cmd = 'cmake ../../ceres -DMINIGLOG=ON -DEIGEN_INCLUDE_DIR_HINTS="../eigen"'
        if is_win():
            cmd += ' -DCMAKE_GENERATOR_PLATFORM=x64'
        os.system(cmd)
    finally:
        os.chdir(cwd)

def compile_ceres():
    cwd = os.getcwd()

    try:
        if os.name == 'nt':
            os.system('msbuild ./build/ceres/internal/ceres/ceres.vcxproj /p:Configuration=Release')
        else:
            os.chdir('build/ceres')
            os.system('make -j8')
    finally:
        os.chdir(cwd)

def run():
    if os.path.isdir('build'):
        shutil.rmtree('build')
    prepare_eigen()
    prepare_ceres()
    compile_ceres()

if __name__ == '__main__':
    run()