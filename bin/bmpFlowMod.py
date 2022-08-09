

print ("Loading arcpy")
# import library packages
import arcpy, os, sys, numpy
from bmpFlowModFast import *

print ("Checking inputs")
# get parameters (input and output datasets, filenames, etc)
# Flow_Direction = Raster(arcpy.getParameterAsText(0))
# BMP_Points     = Raster(arcpy.getParameterAsText(1))
# Output         = arcpy.getParameterAsText(2)
Flow_Direction = arcpy.Raster(r"V:\WIPTools\tests\NMC\Pro\Default.gdb\flowdir")
# BMP_Points     = arcpy.Raster("C:/Users/csomerlot/Desktop/Lab05Data/Lab05Geodatabase.gdb/BMP_Points_PointToRaster")
Output           = r"V:\WIPTools\tests\NMC\Pro\Default.gdb\output"

# set environment 

# create variables to hold input and output datasets
flowdirData = arcpy.RasterToNumPyArray(Flow_Direction).astype(numpy.int64)
lowerLeft = arcpy.Point(Flow_Direction.extent.XMin,Flow_Direction.extent.YMin)
cellSize  = Flow_Direction.meanCellWidth
height = len(flowdirData)
width = len(flowdirData[0])

# bmppointData = arcpy.RasterToNumPyArray(BMP_Points)
# if BMP_Points.extent.XMin != Flow_Direction.extent.XMin:
    # print BMP_Points.extent.XMin, Flow_Direction.extent.XMin
    # raise Exception("Xmin of extents not the same")
# if BMP_Points.extent.YMin != Flow_Direction.extent.YMin: raise Exception("YMin of extents are not the same") 
# if BMP_Points.meanCellWidth != Flow_Direction.meanCellWidth: raise Exception("Cell sizes are not the same")
# if len(bmppointData) != height:
    # print len(bmppointData[0]), height, width
    # raise Exception("Heights are not the same")
# if len(bmppointData[0]) != width: raise Exception("Widths are not the same")
print("Inputs are good, running D8")
outputData = flowAccumulate(flowdirData)
print("D8 done, saving results")
# save outputs
outputRaster = arcpy.NumPyArrayToRaster(outputData,lowerLeft,cellSize)
outputRaster.save(Output)
print("Saved")