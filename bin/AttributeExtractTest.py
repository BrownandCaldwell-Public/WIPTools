import time, os, sys
import numpy
import arcpy
from arcpy.sa import *

def AttExtract(streamInvPts, flowdir, streams, outputname=None):
    import AttributeExtract
    print("\tRunning AttExtract...")
    
    lowerLeft = arcpy.Point(flowdir.extent.XMin,flowdir.extent.YMin)
    cellSize = flowdir.meanCellWidth
    

    start = time.time()
    nflowdir = arcpy.RasterToNumPyArray(flowdir, nodata_to_value=0).astype(numpy.int64)
    
    if type(streamInvPts) == arcpy.Raster:
        nStreamInv = arcpy.RasterToNumPyArray(streamInvPts, nodata_to_value=0).astype(numpy.double)
        if nStreamInv.size != nflowdir.size:
            raise Exception("Input StreamInvPoint raster (%s) is not the same size (%s) as flow direction raster size (%s)" % (streamInvPts.cataprintPath, nStreamInv.size, nflowdir.size))
    else: raise Exception("Input StreamInvPoint (%s) is not a raster" % (streamInvPts.cataprintPath))
    if type(streams) == arcpy.Raster:
        nStream = arcpy.RasterToNumPyArray(streams, nodata_to_value=0).astype(numpy.int64)
        if nStream.size != nflowdir.size:
            raise Exception("Input Stream raster (%s) is not the same size (%s) as flow direction raster size (%s)" % (streams.cataprintPath, nStream.size, nflowdir.size))

    nStream  = arcpy.RasterToNumPyArray(streams, nodata_to_value=0).astype(numpy.int64)
    # if not cellSize: cellSize = 0
    
    
    arr, iterations = AttributeExtract.extractAlongStream(nStreamInv, nflowdir, nStream, cellSize, False)

    newRaster = arcpy.NumPyArrayToRaster(arr, lowerLeft, cellSize, value_to_nodata=0)
    if outputname != None:
        newRaster.save(os.path.join(arcpy.env.workspace, outputname))
        # print("\tOutput: " + os.path.join(arcpy.env.scratchFolder, outputname))
        # stats = arr.flatten()
        # print("\t\tMax: %s Min: %s Avg: %s Med: %s Std: %s Var: %s" % (numpy.amax(stats), numpy.amin(stats), numpy.average(stats), numpy.median(stats), numpy.std(stats), numpy.var(stats)))
    print( "\tAttExtract took %6.2f seconds for %i interations" % (time.time()-start, iterations))
    
    return newRaster

if __name__ == '__main__':
    arcpy.env.workspace = r'Q:\95311_Haresnipe\MapDocs\WIPTools\scratch\scratch'
    arcpy.env.overwriteOutput = True
    field = "RB_length"
    AttributeRaster = Raster(os.path.join(arcpy.env.workspace, "f" + field +".tif"))
    flowdir = Raster(os.path.join(arcpy.env.workspace, "flowdir.tif"))
    streams = Raster(os.path.join(arcpy.env.workspace, "streams.tif"))
    Units = flowdir.meanCellWidth

    print("\tExtract %s attribute with cellsize %s to %s..." % (field, Units, os.path.join(arcpy.env.workspace, field+"e")))
    extract = AttExtract(AttributeRaster, flowdir, streams, os.path.join(arcpy.env.workspace, "AttExtest"))
    
