REM To build the compile environment, use anaconda and cython:
REM C:\ProgramData\Miniconda3\Scripts\activate.bat
REM conda create --clone %LOCALAPPDATA%\ESRI\conda\envs\arcgispro-py3-clone --name cython
REM activate cython
REM conda install cython

python setup.py build_ext --inplace
