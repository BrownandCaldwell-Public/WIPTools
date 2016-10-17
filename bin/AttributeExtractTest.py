import time, os
import numpy

def extractAlongStream(strmInvPts, flowdirData, streamRas, cellsize):
    '''process (loop through) datasets'''
    
    #Make output array
    height = flowdirData.shape[0]
    width  = flowdirData.shape[1]
    # print "Rows: %i\tCols: %i" % (height, width)
    outputData = numpy.copy(strmInvPts)
    
    # print "Starting at %s" % (time.asctime())
    count = 0
    R = 0
    C = 0
    r = 0
    c = 0
    flowdir = 0
    stream = 0
    strmInvPt = 0.0
    DSstrmInvPt = 0.0
    calc = 1.0
    dist = 1.0
    
    complete = False
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
                        # print r, c, calc
                        outputData[r+R,c+C] = calc
                        complete = False
                
    return outputData
    
if __name__ == '__main__':
    import arcpy
    
    inputraster = arcpy.Raster("fBHght_RB.tif")
    flowdir = arcpy.Raster("flowdir.tif")
    streams = arcpy.Raster("streams.tif")
    lowerLeft = arcpy.Point(flowdir.extent.XMin,flowdir.extent.YMin)
    cellSize = flowdir.meanCellWidth
    
    nStreamInv = arcpy.RasterToNumPyArray(inputraster, nodata_to_value=-1).astype(numpy.double)
    # print nStreamInv
    nflowdir   = arcpy.RasterToNumPyArray(flowdir, nodata_to_value=0).astype(numpy.int)
    nStream    = arcpy.RasterToNumPyArray(streams, nodata_to_value=0).astype(numpy.int)
    
    arr = extractAlongStream(nStreamInv, nflowdir, nStream, 0)

    newRaster = arcpy.NumPyArrayToRaster(arr, lowerLeft, cellSize, value_to_nodata=0)
    newRaster.save(os.path.join(os.getcwd(), "test_1.tif"))
    
    