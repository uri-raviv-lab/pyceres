# This script builds a Pyceres wheel for you. You should run it from a python environment
# with the right python version. cmake and msbuild should be on the system path for this to work.

pip install -r .\requirements.txt
python .\compile.py
python setup.py prepare
pip wheel .
