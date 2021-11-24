# This script compiles ceres. You have to run it before running setup.py.
# (at some point we will run it from setup.py)

import os
import shutil

def prepare_eigen():
    cwd = os.getcwd()

    try:
        # Check if the Core directory is *ignored* by git by default. We need to make sure this doesn't happen to us
        if not os.path.isdir('eigen/Eigen/src/Core'):
            print('Your Eigen sources miss the Eigen/src/Core directory.')
            print("This is because Eigen's .gitignore ignores `core`, which on Windows also includes Core")
            print("Please make sure `core` is removed from eigen/.gitignore before pushing a new Eigen version to our repo")
            raise ValueError("Misconfigured Eigen")
        os.makedirs('build/eigen')
        os.chdir('build/eigen')
        os.system('cmake ../../eigen -DCMAKE_GENERATOR_PLATFORM=x64')
    finally:
        os.chdir(cwd)

def prepare_ceres():
    cwd = os.getcwd()

    try:
        os.makedirs('build/ceres')
        os.chdir('build/ceres')
        os.system('cmake ../../ceres -DCMAKE_GENERATOR_PLATFORM=x64 -DMINIGLOG=ON -DEIGEN_INCLUDE_DIR_HINTS="../eigen"')
    finally:
        os.chdir(cwd)

def compile_ceres():
    if os.name == 'nt':
        os.system('msbuild ./build/ceres/internal/ceres/ceres.vcxproj /p:Configuration=Release')
    else:
        raise ValueError("Non windows OSes are not supported yet")

def run():
    if os.path.isdir('build'):
        shutil.rmtree('build')
    prepare_eigen()
    prepare_ceres()
    compile_ceres()

if __name__ == '__main__':
    run()