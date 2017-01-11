REM pip install Cython
REM SET VS90COMNTOOLS=%VS110COMNTOOLS%
SET VS90COMNTOOLS=%VS140COMNTOOLS%
C:\python27\ArcGIS10.3\python setup.py build_ext --inplace
