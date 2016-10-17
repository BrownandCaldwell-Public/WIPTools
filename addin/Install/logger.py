import sys
from os import remove
from pprint import pformat
from time import asctime as now

logfname = sys.argv[0] + '.log'

def clean():
    try:
        remove(logfname)
    except:
        log("Could not delete logfile first")

def write(s):
    sys.__stdout__.write(str(s))
    log(s)
    
def log(obj):
    if type(obj)  in [dict, list]:
        s = pformat(obj)
    else:
        s = str(obj)
        
    log = file(logfname, 'a')
    log.write(s)
    log.close()
    
def flush():
    sys.__stdout__.flush()
    sys.__stderr__.flush()
    
log(logfname + '\n')
log(now() + '\n')
log("_" *50 + '\n')