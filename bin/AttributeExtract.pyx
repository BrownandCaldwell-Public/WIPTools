import time
import numpy
from cpython cimport bool
cimport numpy
ITYPE = numpy.int
ctypedef numpy.int_t ITYPE_t
DTYPE = numpy.double
ctypedef numpy.double_t DTYPE_t

def extractAlongStream(numpy.ndarray[DTYPE_t, ndim=2] strmInvPts  not None, 
                       numpy.ndarray[ITYPE_t, ndim=2] flowdirData not None, 
                       numpy.ndarray[ITYPE_t, ndim=2] streamRas   not None,
                       double cellsize):
    '''process (loop through) datasets'''
    
    #Make output array
    cdef int height = flowdirData.shape[0]
    cdef int width  = flowdirData.shape[1]
    # print "Rows: %i\tCols: %i" % (height, width)
    cdef numpy.ndarray[DTYPE_t, ndim=2] outputData = numpy.copy(strmInvPts)
    
    # print "Starting at %s" % (time.asctime())
    cdef int count = 0
    cdef int R = 0
    cdef int C = 0
    cdef int r = 0
    cdef int c = 0
    cdef int flowdir = 0
    cdef int stream = 0
    cdef double strmInvPt = 0.0
    cdef double DSstrmInvPt = 0.0
    cdef double calc = 1.0
    cdef double dist = 1.0
    
    cdef bool complete = False
    while not complete:
        complete = True
        
        for r in range(height):
            for c in range(width):
            
                strmInvPt = outputData[r,c]
                if strmInvPt >= 0:
                    
                    flowdirval = flowdirData[r, c]
                    if flowdirval == 1:
                        C = 1
                        R = 0
                        dist = 1.0
                    elif flowdirval == 2:
                        C = 1
                        R = 1
                        dist = 1.41421
                    elif flowdirval == 4:
                        C = 0
                        R = 1
                        dist = 1.0
                    elif flowdirval == 8:
                        C = -1
                        R = 1
                        dist = 1.41421
                    elif flowdirval == 16:
                        C = -1
                        R = 0
                        dist = 1.0
                    elif flowdirval == 32:
                        C = -1
                        R = -1
                        dist = 1.41421
                    elif flowdirval == 64:
                        C = 0
                        R = -1
                        dist = 1.0
                    elif flowdirval == 128:
                        C = 1
                        R = -1
                        dist = 1.41421
                    else: break    
                    
                    DSstrmInvPt = outputData[r+R,c+C]
                    stream = streamRas[r,c]
                    if stream > 0:
                        calc = strmInvPt - cellsize * dist
                    else:
                        calc = strmInvPt
                        
                    if DSstrmInvPt < 0 and calc >=0:
                        outputData[r+R,c+C] = calc
                        complete = False
                
    return outputData
    
