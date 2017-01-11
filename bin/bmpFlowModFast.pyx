
"""
WIP Tools 3.0
Copyright (C) 2016 Brown and Caldwell

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""

import time
import numpy
cimport numpy
ITYPE = numpy.int
ctypedef numpy.int_t ITYPE_t
DTYPE = numpy.double
ctypedef numpy.double_t DTYPE_t

def flowAccumulate(numpy.ndarray[ITYPE_t, ndim=2] flowdirData not None, numpy.ndarray[DTYPE_t, ndim=2] weightData=None, numpy.ndarray[DTYPE_t, ndim=2] bmppointData=None):
    '''process (loop through) datasets'''
    
    #Make output array
    cdef int height = flowdirData.shape[0]
    cdef int width  = flowdirData.shape[1]
    # print "Rows: %i\tCols: %i" % (height, width)
    cdef numpy.ndarray[DTYPE_t, ndim=2] outputData = numpy.empty([height, width], dtype=DTYPE)
    
    # print "Starting at %s" % (time.asctime())
    cdef int count = 0
    cdef int R = 0
    cdef int C = 0
    cdef int r = 0
    cdef int c = 0
    cdef int flowdir = 0
    cdef double weight = 1.0
    
    for R in range(1, height-1):
        for C in range(1, width-1):
            c = C
            r = R
            count += 1

            if isinstance(weightData, numpy.ndarray): 
                weight = weightData[r, c]
            else:
                weight = 1.0
                    
            while 0 < r < height-1 and 0 < c < width-1:
            
                if isinstance(bmppointData, numpy.ndarray):
                    bmpval = bmppointData[r, c]
                    if bmpval > 0: 
                        weight = weight * (1 - bmpval)
                        
                outputData[r, c] += weight
                
                flowdirval = flowdirData[r, c]
                if flowdirval == 1:
                    c += 1
                    r += 0
                elif flowdirval == 2:
                    c += 1
                    r += 1
                elif flowdirval == 4:
                    c += 0
                    r += 1
                elif flowdirval == 8:
                    c += -1
                    r += 1
                elif flowdirval == 16:
                    c += -1
                    r += 0
                elif flowdirval == 32:
                    c += -1
                    r += -1
                elif flowdirval == 64:
                    c += 0
                    r += -1
                elif flowdirval == 128:
                    c += 1
                    r += -1
                else: break    
                
    return outputData
    
