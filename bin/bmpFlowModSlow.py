import time, os
import numpy

def flowAccumulate(flowdirData, weightData, bmppointData):
    '''process (loop through) datasets'''
    
    #Make output array
    height = flowdirData.shape[0]
    width  = flowdirData.shape[1]
    # print "Rows: %i\tCols: %i" % (height, width)
    outputData = numpy.empty([height, width], dtype=float)
    
    # print "Starting at %s" % (time.asctime())
    count = 0
    passedVal = 1
    
    for R in range(1, height-1):
        for C in range(1, width-1):
            c = C
            r = R
            count += 1

            weight = weightData[r, c]
                    
            while 0 < r < height-1 and 0 < c < width-1:
            
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
    
if __name__ == '__main__':
    import arcpy
    arcpy.env.overwriteOutput = True
    
    inRas = arcpy.Raster('flowdir.tif')
    lowerLeft = arcpy.Point(inRas.extent.XMin,inRas.extent.YMin)
    cellSize = inRas.meanCellWidth
    start = time.time()
    flowdir = arcpy.RasterToNumPyArray(inRas, nodata_to_value=0)
    weight  = arcpy.RasterToNumPyArray(arcpy.Raster('TSSProd.tif')  , nodata_to_value=0)
    bmps    = arcpy.RasterToNumPyArray(arcpy.Raster('weightred.tif'), nodata_to_value=0)
    arr = flowAccumulate(flowdir, weight, bmps)
    newRaster = arcpy.NumPyArrayToRaster(arr, lowerLeft, cellSize, value_to_nodata=0)
    newRaster.save(os.path.join(os.getcwd(), "flowSlo2.tif"))
    
    print ("Took %6.2f seconds" % (time.time()-start))
    raw_input("Press any key to continue . . . ")
    