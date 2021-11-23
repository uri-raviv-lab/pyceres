# This script compiles ceres. You have to run it before running setup.py.
# (at some point we will run it from setup.py)

import os
import shutil

def prepare_eigen():
    cwd = os.getcwd()

    try:
        if os.path.isdir('eigen-build'):
            shutil.rmtree('eigen-build')
        os.makedirs('eigen-build')
        os.chdir('eigen-build')
        os.system('cmake ..\eigen -DCMAKE_GENERATOR_PLATFORM=x64')
    finally:
        os.chdir(cwd)

def prepare_ceres():
    cwd = os.getcwd()

    try:
        if os.path.isdir('ceres-bin'):
            shutil.rmtree()
        os.makedirs('ceres-bin')
        os.chdir('ceres-bin')
        os.system('cmake ..\ceres -DCMAKE_GENERATOR_PLATFORM=x64 -DMINIGLOG=ON -DEIGEN_INCLUDE_DIR_HINTS="..\eigen-build"')
    finally:
        os.chdir(cwd)

def compile_ceres():
    if os.name == 'nt':
        os.system('msbuild .\ceres-bin\internal\ceres\ceres.vcxproj /p:Configuration=Release')
    else:
        raise ValueError("Non windows OSes are not supported yet")

def run():
    prepare_eigen()
    prepare_ceres()
    compile_ceres()

if __name__ == '__main__':
    run()