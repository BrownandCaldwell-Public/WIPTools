@REM To build the compiled tools (BMP2DA and AttExtract), use MSVC build tools, anaconda, and cython:

@REM Run all these commands from the *anaconda* command prompt called "x64 Native Tools Command Prompt for Visual Studio" 
@REM that comes with the MS Visual Studio build tools (sometimes you have to add the C++ component manually in the installer options)
REM activate "C:\Program Files\ArcGIS\Pro\bin\Python\envs\arcgispro-py3"
@REM Sometimes the version of conda that comes with Pro has a couple packages that need to be upgraded 
@REM before conda will be able to connect to the repos:
REM conpda update certifi openssl
@REM And sometimes it still complains, so as a last resort:
REM conda config --set ssl_verify false

@REM clone the default conda env that Pro has built arcpy against so you can modify by adding cython
REM conda create --clone "C:\Program Files\ArcGIS\Pro\bin\Python\envs\arcgispro-py3" --name wiptools

REM activate wiptools
REM conda install cython 
REM cd /d V:\WIPTools\bin
python setup.py build_ext --inplace
