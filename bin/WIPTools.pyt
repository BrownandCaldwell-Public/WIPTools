

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

Linking this library statically or dynamically with other modules is making a combined work based on this library. Thus, the terms and conditions of the GNU General Public License cover the whole combination.
As a special exception, the copyright holders of this library give you permission to link this library with independent modules such as arcpy to produce an executable, regardless of the license terms of these independent modules, and to copy and distribute the resulting executable under terms of your choice, provided that you also meet, for each linked independent module, the terms and conditions of the license of that module. An independent module is a module which is not derived from or based on this library. If you modify this library, you may extend this exception to your version of the library, but you are not obliged to do so. If you do not wish to do so, delete this exception statement from your version.
"""

import arcpy
from arcpy.sa import *
import sys, os, time, traceback
import numpy

sys.path.append(os.path.split(__file__)[0])
import regression
from regression import urbanQcp

logfname   = __file__+".log"

#<details>    
def CalcErosivity(DefEro, TSSprod, pointSrcRaster, URratio, Streams_rc):
    
    if type(pointSrcRaster) == Raster:
        pointsrc = True
    else:
        pointsrc = False
    
    log("   Adding erosivity (defero is %s and pointsrc is %s)..." % ((DefEro != 0), pointsrc))
    if DefEro and not pointsrc:
        output = ( Streams_rc * Power(URratio, 1.5 ) + BooleanNot( Streams_rc)) * TSSprod 
    elif not DefEro and pointsrc:
        output = TSSprod + pointSrcRaster
    elif not DefEro and not pointsrc:
        output = TSSprod 
    else: 
        output = (( Streams_rc * Power( URratio, 1.5 ) + BooleanNot( Streams_rc)) * TSSprod  ) + pointSrcRaster
    output.save(GetTempRasterPath("ero_out"))
    cleanoutput = RemoveNulls(output)
    cleanoutput.save(GetTempRasterPath("ero_nul"))
    return cleanoutput 
    
def log(message, err=False):
    ''' Logging function that write to the log file, and ArcGIS geoprocessor messages'''
    # if not message.startswith("  "):
        # message = " Step %s: %s" % (Step(), message)
    message = str(message)
    if arcpy: 
        if err: arcpy.AddError(message)
        else: arcpy.AddMessage(message)
    with file(logfname, 'a') as logfile:
        logfile.write(message+"\n")
    
def GetBasin():
    try:
        bf = open("Basin.dat", "r")
        Basin = bf.readline().strip()
        bf.close()
        return Basin
    except Exception as e:
        raise e

def EH(i, j, k):
    data = traceback.format_exception(i,j,k)
    for l in data:
        log("\t" + l.strip(), True)

    raise Exception()
     
def BMP2DA(flowdir, outputname=None, weightsInput=None, bmpsInput=None):
    import bmpFlowModFast
    log("    Running BMP2DA...")
    
    lowerLeft = arcpy.Point(flowdir.extent.XMin,flowdir.extent.YMin)
    cellSize = flowdir.meanCellWidth

    start = time.time()
    nflowdir = arcpy.RasterToNumPyArray(flowdir, nodata_to_value=0).astype(numpy.int)
    
    if type(weightsInput) == arcpy.Raster:
        nweight = arcpy.RasterToNumPyArray(weightsInput, nodata_to_value=0).astype(numpy.double)
        if nweight.size != nflowdir.size:
            raise Exception("Input weight raster (%s) is not the same size (%s) as flow direction raster size (%s)" % (weightsInput.catalogPath, nweight.size, nflowdir.size))
    else:
        nweight = None
    if type(bmpsInput) == arcpy.Raster:
        nbmppts = arcpy.RasterToNumPyArray(bmpsInput, nodata_to_value=0).astype(numpy.double)
        if nbmppts.size != nflowdir.size:
            raise Exception("Input weight raster (%s) is not the same size (%s) as flow direction raster size (%s); was the processing extent env variable set up?" % (bmpsInput.catalogPath, nbmppts.size, nflowdir.size))
    else:
        nbmppts = None
    
    arr = bmpFlowModFast.flowAccumulate(nflowdir, nweight, nbmppts)

    newRaster = arcpy.NumPyArrayToRaster(arr, lowerLeft, cellSize, value_to_nodata=0)
    if outputname != None:
        newRaster.save(os.path.join(arcpy.env.scratchFolder, outputname))
        # log("\tOutput: " + os.path.join(arcpy.env.scratchFolder, outputname))
        # stats = arr.flatten()
        # log("\t\tMax: %s Min: %s Avg: %s Med: %s Std: %s Var: %s" % (numpy.amax(stats), numpy.amin(stats), numpy.average(stats), numpy.median(stats), numpy.std(stats), numpy.var(stats)))
    log( "    BMP2DA took %6.2f seconds" % (time.time()-start) )
    
    return newRaster

def AttExtract(streamInvPts, flowdir, streams, outputname=None):
    import AttributeExtract
    log("\tRunning AttExtract...")
    
    lowerLeft = arcpy.Point(flowdir.extent.XMin,flowdir.extent.YMin)
    cellSize = flowdir.meanCellWidth

    start = time.time()
    nStreamInv = arcpy.RasterToNumPyArray(streamInvPts, nodata_to_value=0).astype(numpy.double)
    nflowdir = arcpy.RasterToNumPyArray(flowdir, nodata_to_value=0).astype(numpy.int)
    nStream  = arcpy.RasterToNumPyArray(streams, nodata_to_value=0).astype(numpy.int)
    if not cellsize: cellsize = 0
    
    
    arr = AttributeExtract.extractAlongStream(nStreamInv, nflowdir, nStream, cellsize)

    newRaster = arcpy.NumPyArrayToRaster(arr, lowerLeft, cellSize, value_to_nodata=0)
    if outputname != None:
        newRaster.save(os.path.join(arcpy.env.scratchFolder, outputname))
        # log("\tOutput: " + os.path.join(arcpy.env.scratchFolder, outputname))
        # stats = arr.flatten()
        # log("\t\tMax: %s Min: %s Avg: %s Med: %s Std: %s Var: %s" % (numpy.amax(stats), numpy.amin(stats), numpy.average(stats), numpy.median(stats), numpy.std(stats), numpy.var(stats)))
    log( "\tAttExtract took %6.2f seconds" % (time.time()-start) )
    
    return newRaster

def ProtLength(pt, flowdir, singleQ, existingQ):
    
    # for r in [pt, flowdir, singleQ, existingQ]:
    # pt = self.MakeTempRaster(pt, "protleng")
    # flowdir = self.MakeTempRaster(flowdir, "protleng")
    # singleQ = self.MakeTempRaster(singleQ, "protleng")
    # existingQ = self.MakeTempRaster(existingQ, "protleng")
    
    args = '"%s" "%s" "%s" "%s"' % (pt.catalogPath, flowdir.catalogPath, singleQ.catalogPath, existingQ.catalogPath)
    Csharpdata = RunScript("ProtLen.exe", args, True)
   
    substring = "Length computed as: "
    ans = 0
    for line in Csharpdata:
        if substring in line:
            ans = float(line.strip().replace(substring, ""))
   
    if not ans:
        raise Exception("Invalid result from ProtLen.exe: %s" % Csharpdata)
    return ans
    
def AddID(vec, id):
            
    if not id in ListofFields(vec):
        arcpy.AddField_management(vec, id, "LONG", "", "", "", "", "NON_NULLABLE", "NON_REQUIRED", "")
        
    rows = arcpy.UpdateCursor(vec)
    
    for row in rows:
        row.setValue(id, 1)
        rows.updateRow(row)

def GetDataTable(table):
    
    if not table.endswith(".csv"): log( "Warning, your data table does not appear to be comma-seprated" )
        
    table = os.path.join(os.path.join(arcpy.env.workspace, r"..\Tooldata"), table)
    f = file(table)
    dic = {}
    header = f.readline().strip().split(',')
    
    data = f.readlines()
    for i in range(len(data)):
        thisdata = data[i].strip().split(',')
        dic[thisdata[0]] = {}
        for k, v in zip(header[1:], thisdata[1:]):
            dic[thisdata[0]][k] = float(v)
    
    f.close()
    return dic
    
def Step():
    self.step += 1
    return self.step
    
def Zonal(raster, stat='SUM'):
    LoadTable = os.path.join(arcpy.env.scratchFolder, 'load.dbf')
    
    outZSaT  = ZonalStatisticsAsTable(arcpy.env.mask, "Value", raster, LoadTable, "DATA")
    rows = arcpy.UpdateCursor(LoadTable)
    computation = rows.next().getValue(stat)
    
    return computation
    
def SetAtt(OID, att, val, lyr, alias=None):
    log("\t\tPID: %s\n\t\tAttribute: %s\n\t\tValue: %s\n\t\tLayer: %s" % (OID, att, val, lyr) )
    OIDfield = arcpy.Describe(lyr).OIDFieldName
    if not alias: alias = att
    
    if not att in ListofFields(lyr):
        log( "\tAdding field: %s (%s)" % (att, alias) )
        arcpy.AddField_management(lyr, att, "DOUBLE", "", "", "", alias, "NULLABLE", "NON_REQUIRED", "")
        
    rows = arcpy.UpdateCursor(lyr)
    
    for row in rows:
        if row.getValue(OIDfield) == OID:
            row.setValue(att, val)
            rows.updateRow(row)
        
def Summarize(raster, points, alias=None, PID=-1):
    name = os.path.split(raster.catalogPath)[1][:8].strip()
    temp_vec = os.path.join(arcpy.env.scratchFolder, name + ".shp")
    arcpy.sa.ExtractValuesToPoints(points, raster, temp_vec)
   
    
    rows = arcpy.SearchCursor(temp_vec)
    
    for row in rows:
        thisPID = row.getValue("PID")
        if PID == thisPID or PID < 0:
            SetAtt(thisPID, name, row.getValue("RASTERVALU"), points, alias)
    
def GetAlias(input):
    aliases = {
        'TotalNitrogen':["tn", "nitro", "nitrogen", "nit"],
        'TotalPhosphorus':["tp", "pho", "phosp"],
        'FecalColiform':["fc", "fecal", "feccol"],
        'Sediment':["tss", "sed", "sediment"],
        'BOD':['bod'],
        'Zinc':["zinc", "zn", "zi"],
        'Copper':["copper", "cu", "co"]
    }
    
    parameter_dict = {}
    for alias in aliases:
        for substring in aliases[alias]:
            if type( input ) == list: 
                for this_input in input:
                    if this_input.lower().startswith(substring):
                        parameter_dict[alias] = this_input
            else:
                if input.lower().startswith(substring):
                    return alias
    if not parameter_dict:
        raise Exception("No parameters found to match %s, stopping" % input)
    
    return parameter_dict
    
def GetTempRasterPath(outputname):
    newname = os.path.join(arcpy.env.scratchFolder, outputname)
    i = 1
    while os.path.exists(newname):
        newname = os.path.join(arcpy.env.scratchFolder, outputname+str(i))
        i+=1
    # log(newname)
    return newname
    
def SetPIDs(vec):
    if ".mdb" in vec.lower() or ".gdb" in vec.lower():
        OID = "OBJECTID"
    elif vec.lower().endswith(".shp"):
        OID = "FID"
    else:
        raise Exception("Can not determine OID field for " + vec)

    if not 'PID' in ListofFields(vec):
        log( "Adding PID field" )
        arcpy.AddField_management(vec, 'PID', "SHORT", "", "", "", "", "NULLABLE", "REQUIRED", "")

    rows = arcpy.UpdateCursor(vec)
    
    for row in rows:     
        val = row.getValue(OID)
        row.setValue("PID", int(val))
        rows.updateRow(row)
        
def ListofFields(lyr):
    fields = arcpy.ListFields(lyr)
    return [f.name for f in fields]

def ConvertGRIDCODEatt(lyr):
    arcpy.AddField_management(lyr, "Ratio", "DOUBLE", "", "", "", "", "", "NON_REQUIRED", "")
    rows = arcpy.UpdateCursor(lyr)
     
    for row in rows:
        val = row.getValue('GRID_CODE')
        row.setValue("Ratio", val/10000.0)
        rows.updateRow(row)
        
def RemoveNulls(raster):
    return Con(IsNull(raster),0,raster)
    
def GetSubset(input, output, query):
    arcpy.MakeFeatureLayer_management(input, 'subset')
    try:
        arcpy.SelectLayerByAttribute_management('subset', "NEW_SELECTION", query)
    except Exception as err:
        log('Bad query: "%s"' % query)
        raise err
    arcpy.CopyFeatures_management('subset', output)
    count = int(arcpy.GetCount_management(output).getOutput(0))
    log("  %s, found %s" % (query, count))
    return count

def ChannelProtection( Basin, BMP_pts, fld, flowdir, Cum_da, Cumulative_Impervious):
        """Flow reduction calcs"""

        log("   Convert Single BMP Project to Raster...")
        # flowdir = ExtractByMask(flowdir_lrg, mask)
        RasBMPpts = GetTempRasterPath("RasBMPpts")
        arcpy.FeatureToRaster_conversion(BMP_pts, fld, RasBMPpts, flowdir)
        thisBMPras = Raster(RasBMPpts)
        cellSize = arcpy.Describe(Cum_da).MeanCellHeight

        if Basin == 'Georgia Region 1':
                Mod_da = 640 * Power( ( thisBMPras / ((190 * 0.875) * Power( 10,(Cumulative_Impervious * 0.0116 )) )), ( 1 / 0.751) )
        elif Basin == 'Chattahoochee  GA (Rural and Urban)':
                Mod_da = 640 * Power( ( thisBMPras / ( 146 * Power( Cumulative_Impervious, 0.31 ) ) ), ( 1 / 0.73 ) )
        elif Basin == 'Altamaha GA (Rural and Urban)':
                Mod_da = 640 * Power( ( thisBMPras / ( 127 * Power( Cumulative_Impervious, 0.31 ) ) ), ( 1 / 0.7 ) )
        elif Basin in ['Region 1  2006 (Rural) - Blue Ridge NC 2002 (Urban)', 'Blue Ridge Piedmont  NC 2002 (Rural and Urban)']:
                Mod_da = 640 * Power( ( thisBMPras / ( 28.5 * Power( Cumulative_Impervious, 0.686 ) ) ), ( 1 / 0.739 ) )
                
##             for below use inverse of: (Power( ( cum_da / 640 ) , 0.554 ) * (1.36 * 0.875)) * ( Power( impcov, 1.241 )) * ( Power( rural2yrQ(Basin,cum_da), 0.323))

        elif Basin in ['SC Piedmont', 'SC Blue Ridge', 'SC Sand Hills', 'SC Coastal']:
                Mod_da = 640 * Power( ( thisBMPras / ( ( (1.36 * 0.875) * Power( rural2yrQ(Basin,Cum_da), 0.323) ) * Power( Cumulative_Impervious, 1.241 ) ) ), ( 1 / 0.554 ) )

        else: raise Exception("Unknown basin: " + Basin)

        log("   Convert to percent reduction in accumulation...")
        acc_red = 1 - ( Mod_da / Cum_da)
        Mod_da.save(os.path.join(arcpy.env.scratchFolder,"Mod_da_test"))
        # Cumulative_Impervious.save(os.path.join(arcpy.env.scratchFolder,"CumImp_test"))
        # Cum_da.save(os.path.join(arcpy.env.scratchFolder,"Cum_da_test"))
        acc_red.save(os.path.join(arcpy.env.scratchFolder,"acc_red_cp"))
        # flowdir.save(os.path.join(arcpy.env.scratchFolder,"flowdir_test"))
        
        ModCumDa_u = BMP2DA(flowdir, "ModCumDa_asc", Raster(arcpy.env.mask), acc_red)

        log("   Convert units...")
        conv = (cellSize*cellSize) / 43560
        ModCumDa = ModCumDa_u * conv
    
        log("   Calculating urbanQcp...")
        uQcp = urbanQcp(Basin, ModCumDa, Cumulative_Impervious)

        return ModCumDa, thisBMPras, uQcp
#</details> 

class tool(object):
    def execute(self):
        self.checkEnvVars()
        mxd = arcpy.mapping.MapDocument("CURRENT")
        log("\n%s run started at %s from %s using workspace %s and possibly mxd %s" % (self.__class__.__name__, time.ctime(), __file__, arcpy.env.workspace, mxd.filePath))
        
    def __del__(self):
        pass
        # log("Done at " + time.asctime() +"\n\n")
        
    def checkEnvVars(self):
        # for i in arcpy.ListEnvironments():
            # log("Env %s\t%s" % (i, arcpy.env[i]))
        
        if not arcpy.env.workspace:
            raise Exception("Workspace is not set in geoprocessing env settrings. Fix and rerun")
        if not 'gdb' in arcpy.env.workspace:
            raise Exception("Workspace is not a fileGDB. Fix and rerun")
        if not arcpy.env.mask:
            raise Exception("Mask is not set in geoprocessing env settrings. Fix and rerun")
    
    def close(self):
        log("\n%s done at %s" % (self.__class__.__name__, time.ctime()))
    
class Toolbox(object):
    def __init__(self):
        self.label = "WIP Tools"
        self.alias = "WIP Tools"
        # self.tools = [Baseline, CIP]
        self.tools = [TopoHydro, ImpCov, Runoff, ProdTrans, Baseline, CIP, SingleBMP]
        # if arcpy.env.scratchWorkspace == None or arcpy.env.scratchWorkspace == "" or arcpy.env.scratchWorkspace.endswith('Default.gdb'):
            # arcpy.env.scratchWorkspace = os.path.split(arcpy.env.workspace)[0]

class TopoHydro(tool):
    def __init__(self):
        self.label = "TopoHydro"
        self.description = "Topopgraphy and Hydrology Setup"
        
    def getParameterInfo(self):
        parameters = []
        
        parameters += [arcpy.Parameter(
        displayName="Input DEM",
        name="dem",
        datatype=["DERasterDataset", "GPRasterLayer"],
        parameterType="Required",
        direction="Input")]
        
        parameters += [arcpy.Parameter(
        displayName="Mask",
        name="mask",
        datatype=["DERasterDataset", "GPRasterLayer", "DEFeatureDataset", "GPFeatureLayer"],
        parameterType="Optional",
        direction="Input")]
        
        parameters += [arcpy.Parameter(
        displayName="Threshold for Stream Formation (in acres)",
        name="threshold",
        datatype="GPDouble",
        parameterType="Required",
        direction="Input")]
        
        parameters += [arcpy.Parameter(
        displayName="Manually Delinated Streams",
        name="input streams",
        datatype=["DERasterDataset", "GPRasterDataLayer", "DEFeatureDataset", "GPFeatureLayer"],
        parameterType="Optional",
        direction="Input")]
        
        parameters += [arcpy.Parameter(
        displayName="Flow Direction",
        name="flowdir",
        datatype="DERasterDataset",
        parameterType="Derived",
        direction="Output")]
        parameters[-1].value = os.path.join(arcpy.env.workspace,"Flowdir")
        parameters[-1].parameterDependencies = [arcpy.env.workspace]
        
        parameters += [arcpy.Parameter(
        displayName="Flow Accumulation",
        name="flowacc",
        datatype="DERasterDataset",
        parameterType="Derived",
        direction="Output")]
        parameters[-1].value = os.path.join(arcpy.env.workspace,"Flow_acc")
        parameters[-1].parameterDependencies = [arcpy.env.workspace]
        
        parameters += [arcpy.Parameter(
        displayName="Cumulative Drainage Area",
        name="cumda",
        datatype="DERasterDataset",
        parameterType="Derived",
        direction="Output")]
        parameters[-1].value = os.path.join(arcpy.env.workspace,"Cumda")
        parameters[-1].parameterDependencies = [arcpy.env.workspace]
        
        parameters += [arcpy.Parameter(
        displayName="Streams",
        name="output streams",
        datatype="DERasterDataset",
        parameterType="Derived",
        direction="Output")]
        parameters[-1].value = os.path.join(arcpy.env.workspace,"Streams")
        parameters[-1].parameterDependencies = [arcpy.env.workspace]
        
        return parameters

    def updateParameters(self, parameters):
        return

    def execute(self, parameters, messages):
        try:
            tool.execute(self)
            tempdem = parameters[0].valueAsText
            ThisMask = parameters[1].valueAsText
            Threshold_for_stream_formation__acres_ = parameters[2].valueAsText
            manualStreams = parameters[3].valueAsText
            flowdirPath = parameters[4].valueAsText
            flowaccPath = parameters[5].valueAsText
            cumdaPath = parameters[6].valueAsText
            streamsPath = parameters[7].valueAsText
            
            if ThisMask:
                log("A Mask has been specified")
                maskDesc = arcpy.Describe(ThisMask)
                if not maskDesc.DatasetType == 'RasterDataset':
                    log("  Mask is not raster, converting to raster first")
                    arcpy.PolygonToRaster_conversion(ThisMask, maskDesc.OIDFieldName, os.path.join(arcpy.env.scratchFolder, "TempMask"),"MAXIMUM_AREA", "None", tempdem)
                    TempMask = Raster(os.path.join(arcpy.env.scratchFolder, "TempMask"))
                     
                else:
                    TempMask = ThisMask
                   
                Mask = Reclassify(TempMask, "VALUE", "0 1000000000000 1", "DATA")
                Input_DEM = Con(Mask, tempdem)
                
            else:
                Input_DEM = tempdem
          
            # Input_DEM now represents the area of interest, or mask. 
            arcpy.env.extent = ThisMask
            arcpy.env.snapRaster = tempdem
            dsc = arcpy.Describe(Input_DEM)
            cellSize = dsc.MeanCellHeight
            # log( "Input DEM data type = %s, %s, %s" % (dsc.DatasetType, dsc.DataType, dsc.IsInteger) )
            mainMask = Reclassify(Input_DEM, "VALUE", "0 1000000000000 1; 0 NoData", "DATA")
            mainMask.save("Mask")
            arcpy.env.snapRaster = mainMask
            arcpy.env.mask = mainMask
            
            log("Fill DEM...")
            Filled_DEM = arcpy.sa.Fill(Input_DEM)
            log("Calculate Flow Direction...")
            flowdir = FlowDirection(Filled_DEM, "NORMAL") * arcpy.env.mask # NORMAL should be FORCE?
            flowdir.save(flowdirPath)
            log("Accumulate Flow")
            Flow_Acc = BMP2DA(flowdir, "CumDa.tif")
            Flow_Acc.save(flowaccPath)
            
            log("Drainage Area Calculation...")
            CumDA = Flow_Acc * cellSize * cellSize / 43560
            CumDA.save(cumdaPath)
            
            if not manualStreams:
                log("Stream Calculation...")
                Stream_Raster = CumDA > float(Threshold_for_stream_formation__acres_)
            else:
                Stream_Raster = Raster(manualStreams)
            
            log("Remove background values...")
            Streams_Output_Raster = Reclassify(Stream_Raster, "VALUE", "0 NODATA;1 1","DATA")
            Streams_Output_Raster.save(streamsPath)
             
            log("Vectorize streams...")
            StreamToFeature(Streams_Output_Raster, flowdir, "streamsvec", "SIMPLIFY")
            
            tool.close(self)
        except:       
            i, j, k = sys.exc_info()
            EH(i, j, k)
            
class ImpCov(tool):
    def __init__(self):
        self.label = "ImpCov"
        self.description = "Impervious Cover"
        
    def getParameterInfo(self):
        parameters = []
        
        parameters += [arcpy.Parameter(
        displayName="Impervious Polygons",
        name="imperviouspolys",
        datatype=["DEFeatureDataset", "GPFeatureLayer"],
        parameterType="Required",
        direction="Input")]
        
        parameters += [arcpy.Parameter(
        displayName="lakes Polygons",
        name="lakespolys",
        datatype=["DEFeatureDataset", "GPFeatureLayer"],
        parameterType="Required",
        direction="Input")]
        
        parameters += [arcpy.Parameter(
        displayName="Flow Direction",
        name="flowdir",
        datatype="DERasterDataset",
        parameterType="Required",
        direction="Input")]
        parameters[-1].value = os.path.join(arcpy.env.workspace,"Flowdir")
        
        parameters += [arcpy.Parameter(
        displayName="Flow Accumulation",
        name="flowacc",
        datatype="DERasterDataset",
        parameterType="Required",
        direction="Input")]
        parameters[-1].value = os.path.join(arcpy.env.workspace,"Flow_acc")
        
        parameters += [arcpy.Parameter(
        displayName="Cumulative Drainage Area",
        name="cumda",
        datatype="DERasterDataset",
        parameterType="Required",
        direction="Input")]
        parameters[-1].value = os.path.join(arcpy.env.workspace,"Cumda")
        
        parameters += [arcpy.Parameter(
        displayName="Streams",
        name="streams",
        datatype="DERasterDataset",
        parameterType="Required",
        direction="Input")]
        parameters[-1].value = os.path.join(arcpy.env.workspace,"Streams")
        
        parameters += [arcpy.Parameter(
        displayName="Impervious Cover",
        name="impcov",
        datatype="DERasterDataset",
        parameterType="Derived",
        direction="Output")]
        parameters[-1].value = os.path.join(arcpy.env.workspace,"impcov")
        # parameters[-1].parameterDependencies = [arcpy.env.workspace]
        
        parameters += [arcpy.Parameter(
        displayName="Cumulative Impervious Cover",
        name="cumimpcov",
        datatype="DERasterDataset",
        parameterType="Derived",
        direction="Output")]
        parameters[-1].value = os.path.join(arcpy.env.workspace,"cumimpcov")
        # parameters[-1].parameterDependencies = [arcpy.env.workspace]
        
        parameters += [arcpy.Parameter(
        displayName="Cumulative Impervious Cover with Lakes",
        name="cumimpcovlakes",
        datatype="DERasterDataset",
        parameterType="Derived",
        direction="Output")]
        parameters[-1].value = os.path.join(arcpy.env.workspace,"cumimpcovlakes")
        # parameters[-1].parameterDependencies = [arcpy.env.workspace]
        
        parameters += [arcpy.Parameter(
        displayName="Cumulative Impervious Vector",
        name="cumimpcovvec",
        datatype="DEFeatureDataset",
        parameterType="Derived",
        direction="Output")]
        parameters[-1].value = os.path.join(arcpy.env.workspace,"cumimpcovvec")
        # parameters[-1].parameterDependencies = [arcpy.env.workspace]
        
        parameters += [arcpy.Parameter(
        displayName="Raster Lakes",
        name="lakes",
        datatype="DERasterDataset",
        parameterType="Derived",
        direction="Output")]
        parameters[-1].value = os.path.join(arcpy.env.workspace,"lakes")
        # parameters[-1].parameterDependencies = [arcpy.env.workspace]
        
        return parameters

    def updateParameters(self, parameters):
        return

    def execute(self, parameters, messages):
        try:
            tool.execute(self)
            # Script arguments...
            Impervious_Polygons_Vector_preclip = parameters[0].valueAsText
            Lakes_Polygon_Vector_preclip = parameters[1].valueAsText
            Flow_Direction_Raster = Raster(parameters[2].valueAsText) * arcpy.env.mask
            Flow_Accumulation = Raster(parameters[3].valueAsText)
            Cum_da = Raster(parameters[4].valueAsText)
            Streams = Raster(parameters[5].valueAsText)
            impcovPath = parameters[6].valueAsText
            cumimpcovPath = parameters[7].valueAsText
            cumimpcovlakesPath = parameters[8].valueAsText
            vector = parameters[9].valueAsText
            lakesPath = parameters[10].valueAsText
            
            # cellSize = hp.units['cellsqft']**0.5
            arcpy.env.cellSize = "MINOF"
            cellSize = arcpy.Describe(Cum_da).MeanCellHeight
            
            log(" Clipping input vectors to work area (or mask)")
            vecMask = os.path.join(arcpy.env.scratchFolder,"vectMask.shp")
            arcpy.RasterToPolygon_conversion(arcpy.env.mask, vecMask, "SIMPLIFY", "Value")
            
            Lakes_Polygon_Vector = os.path.join(arcpy.env.scratchFolder, "lakespolyvec.shp")
            arcpy.Clip_analysis(Lakes_Polygon_Vector_preclip, vecMask, Lakes_Polygon_Vector)
            Impervious_Polygons_Vector = os.path.join(arcpy.env.scratchFolder, "imppolyvec.shp")
            arcpy.Clip_analysis(Impervious_Polygons_Vector_preclip, vecMask, Impervious_Polygons_Vector)
            
            # Data Validation
            count = int(arcpy.GetCount_management(Impervious_Polygons_Vector).getOutput(0))
            if count < 1:
                raise Exception("No impervious areas in the study area")
            count = int(arcpy.GetCount_management(Lakes_Polygon_Vector).getOutput(0))
            if count < 1:
                raise Exception("No lakes in the study area")
            
            log("Converting impervious polygons to raster...")
            impid = 'NewId'
            AddID(Impervious_Polygons_Vector, impid)
            
            # arcpy.env.cellSize = float(cellSize)/10
            Feature_Impe1 = os.path.join(arcpy.env.scratchFolder,"Feature_Impe1")
            arcpy.PolygonToRaster_conversion(Impervious_Polygons_Vector, impid, (os.path.join(arcpy.env.scratchFolder,"Feature_Impe1")),"MAXIMUM_AREA","None", float(cellSize)/10)
            
            log("Reclassifying impervious raster...")
            Reclass_Feat1 = RemoveNulls(Feature_Impe1)
            Reclass_Feat1.save(os.path.join(arcpy.env.scratchFolder,"Reclass_Feat1"))
            # arcpy.env.cellSize = float(cellSize)
            
            log("Computing block statistics...")
            BlockSt_Recl1 = BlockStatistics(Reclass_Feat1, NbrRectangle(10, 10, "CELL"), "SUM", "DATA")
            BlockSt_Recl1.save(os.path.join(arcpy.env.scratchFolder,"BlockSt_Recl1"))
            
            log("Aggregate...")
            Imp_Cover_pc = Aggregate(BlockSt_Recl1,10, "MEAN", "EXPAND", "DATA")
            Imp_Cover = ExtractByMask(Imp_Cover_pc, arcpy.env.mask)
            
        ##    Imp_Cover_pc = arcpy.env.mask * Imp_Cover  ## DOES NOT WORK
            Imp_Cover.save(impcovPath)
            
            Flow_Accumulation_weighted = BMP2DA(Flow_Direction_Raster,"flow_accw.tif", Imp_Cover)
            Flow_Accumulation_weighted_nonulls = RemoveNulls(Flow_Accumulation_weighted)
            
            log("Divide...")
            cumimpcov=Flow_Accumulation_weighted_nonulls / Flow_Accumulation
            cumimpcov.save(cumimpcovPath)
            
            log("Clip output to streams...")
            Clipped_ = Int(RoundUp(RoundDown(cumimpcov * Streams * 20000 ) / 2))
            
            log("Vectorize...")
            StreamToFeature(Clipped_, Flow_Direction_Raster, vector, "NO_SIMPLIFY")
            ConvertGRIDCODEatt(vector)
            
            # Add lakes for other tools that use it
            log("Lake features to Raster...")
            lakeid = "NewId"
            AddID(Lakes_Polygon_Vector, lakeid)
            lakes_temp = os.path.join(arcpy.env.scratchFolder, "lakes_temp")
            arcpy.PolygonToRaster_conversion(Lakes_Polygon_Vector, lakeid, lakes_temp,"MAXIMUM_AREA","None", Flow_Direction_Raster)
            Lakes = Reclassify(lakes_temp, "VALUE", "-10000000000 10000000000 1;NODATA 0", "DATA")
            arcpy.CopyRaster_management(in_raster=Lakes, out_rasterdataset=lakesPath, pixel_type="8_BIT_UNSIGNED")
            
            log("Add lakes to Impervious Cover...")
            Impervious_Cover_Lakes = (Imp_Cover*(BooleanNot(Lakes))+(Lakes*100))
            
            log("Flow Accum with Lakes...")
            Flow_Accumulation_lakes=BMP2DA(Flow_Direction_Raster, "LFlowacc.tif", Impervious_Cover_Lakes)
            
            log("Divide...")
            cumimpcovlake = RemoveNulls(Flow_Accumulation_lakes)/Flow_Accumulation
            cumimpcovlake.save(cumimpcovlakesPath)
                
            tool.close(self)

        except:       
            i, j, k = sys.exc_info()
            EH(i, j, k)
            
class Runoff(tool):
    def __init__(self):
        self.label = "Runoff"
        self.description = "Runoff"
        
    def __del__(self):
        super(tool, self).__del__()
        
    def getParameterInfo(self):
        parameters = []
        
        parameters += [arcpy.Parameter(
            displayName="Landuse Layer",
            name="landuse",
            datatype=["GPFeatureLayer", 'DEFeatureDataset'],
            parameterType="Required",
            direction="Input")]
            
        parameters += [arcpy.Parameter(
            displayName="Landuse Field",
            name="landuseAtt",
            datatype="GPString",
            parameterType="Required",
            direction="Input")]
        parameters[-1].filter.type = "ValueList"
        
        parameters += [arcpy.Parameter(
            displayName="Soils Layer",
            name="soils",
            datatype=["GPFeatureLayer", 'DEFeatureDataset'],
            parameterType="Required",
            direction="Input")]
            
        parameters += [arcpy.Parameter(
            displayName="Soils Field",
            name="soilsAtt",
            datatype="GPString",
            parameterType="Required",
            direction="Input")]
        parameters[-1].filter.type = "ValueList"
        
        parameters += [arcpy.Parameter(
        displayName="Storm Recurrence Intervals",
        name="pdepth",
        datatype="GPValueTable",
        parameterType="Required",
        direction="Input")]
        parameters[-1].columns = [['String', 'Storm'], ['Double', 'Rain depth'], ['Double', 'Base CN']]
        parameters[-1].filters[0].type = "ValueList"
        parameters[-1].filters[0].list = ["WQV", '1yr', '10yr', '25yr']
        
        parameters += [arcpy.Parameter(
        displayName="Curve Number (CN) Table (lut.csv)",
        name="lut",
        datatype=["DETable","GPTableView"],
        parameterType="Required",
        direction="Input")]
        
        parameters += [
        arcpy.Parameter(
        displayName="Basin",
        name="basin",
        datatype="String",
        parameterType="Required",
        direction="Input")]
        parameters[-1].filter.type = "ValueList"
        parameters[-1].filter.list = [
            "Georgia Region 1", 
            "Chattahoochee  GA (Rural and Urban)", 
            "Altamaha GA (Rural and Urban)", 
            "Region 1  2006 (Rural) - Blue Ridge NC 2002 (Urban)", 
            "Blue Ridge Piedmont  NC 2002 (Rural and Urban)",
            "SC Piedmont",
            'SC Blue Ridge', 
            'SC Sand Hills',
            'SC Coastal'
        ]
        
        parameters += [arcpy.Parameter(
        displayName="Flow Direction",
        name="flowdir",
        datatype="DERasterDataset",
        parameterType="Required",
        direction="Input")]
        parameters[-1].value = os.path.join(arcpy.env.workspace,"flowdir")
        
        parameters += [arcpy.Parameter(
        displayName="Cumulative Drainage Area",
        name="cumda",
        datatype="DERasterDataset",
        parameterType="Required",
        direction="Input")]
        parameters[-1].value = os.path.join(arcpy.env.workspace,"Cumda")
        
        parameters += [arcpy.Parameter(
        displayName="Flow Accumulation",
        name="flowacc",
        datatype="DERasterDataset",
        parameterType="Required",
        direction="Input")]
        parameters[-1].value = os.path.join(arcpy.env.workspace,"Flow_acc")
        
        parameters += [arcpy.Parameter(
        displayName="Cumulative Impervious Cover with Lakes",
        name="cumimpcovlakes",
        datatype="DERasterDataset",
        parameterType="Required",
        direction="Input")]
        parameters[-1].value = os.path.join(arcpy.env.workspace,"cumimpcovlakes")
        
        parameters += [arcpy.Parameter(
        displayName="Output Flood Storage",
        name="outputvols",
        datatype="DERasterDataset",
        parameterType="Derived",
        direction="Output")]
        parameters[-1].value = os.path.join(arcpy.env.workspace,"wqv")
        
        parameters += [arcpy.Parameter(
        displayName="Output Undeveloped Discharge",
        name="undevq",
        datatype="DERasterDataset",
        parameterType="Derived",
        direction="Output")]
        parameters[-1].value = os.path.join(arcpy.env.workspace,"undevQ")
        
        parameters += [arcpy.Parameter(
        displayName="Output Urban 2yr Discharge",
        name="urban2yrQ",
        datatype="DERasterDataset",
        parameterType="Derived",
        direction="Output")]
        parameters[-1].value = os.path.join(arcpy.env.workspace,"urban2yrQ")
        
        parameters += [arcpy.Parameter(
        displayName="Output Urban 10yr Discharge",
        name="urban10yrQ",
        datatype="DERasterDataset",
        parameterType="Derived",
        direction="Output")]
        parameters[-1].value = os.path.join(arcpy.env.workspace,"urban10yrQ")
        
        parameters += [arcpy.Parameter(
        displayName="Output Urban 25yr Discharge",
        name="urban25yrQ",
        datatype="DERasterDataset",
        parameterType="Derived",
        direction="Output")]
        parameters[-1].value = os.path.join(arcpy.env.workspace,"urban25yrQ")
        
        return parameters

    def updateParameters(self, parameters):
        for p in [1, 3]:
            param = parameters[p]
            if parameters[p-1].value:
                fields = arcpy.ListFields(parameters[p-1].value)
                l = [f.name for f in fields]
                param.filter.list = l
        return

    def execute(self, parameters, messages):
        try:
            tool.execute(self)
            Landuse = parameters[0].valueAsText
            LanduseAtt = parameters[1].valueAsText
            Soils = parameters[2].valueAsText
            SoilsAtt = parameters[3].valueAsText
            stormdata = parameters[4].value
            lutFile = parameters[5].valueAsText
            Basin = parameters[6].valueAsText
            flowdir = Raster(parameters[7].valueAsText)
            cum_da = Raster(parameters[8].valueAsText)
            flowacc = Raster(parameters[9].valueAsText)
            cumimpcovlake = Raster(parameters[10].valueAsText)
            volflood = parameters[11].valueAsText
            undevqPath = parameters[12].valueAsText
            urban2yrQPath = parameters[13].valueAsText
            urban10yrQPath = parameters[14].valueAsText
            urban25yrQPath = parameters[15].valueAsText
            
            Units = flowdir.meanCellWidth
            CurveN = None
            
            for storm in stormdata:
                pname, pdepth, baseCN = storm
                if pname == "WQV":
                    #   WQV ----------------------------------------------------------------------------------------------------------------------------------------------------------------------
                    log("WQV Volume Calc...")
                    Convraster = (cum_da * 43560)/12 
                    
                    WQVin = ((cumimpcovlake * 0.009) + 0.05) * float(pdepth)#["WQdepth"]
                    WQVin.save(os.path.join(arcpy.env.scratchFolder,'vol'+pname))

                    log("WQV Conv Calc...")
                    WQV = WQVin * Convraster
                    WQV.save(volflood)
                    
                else:
                    if not type(CurveN) == arcpy.Raster:
                        log(" Clipping input vectors to work area (or mask)")
                        vecMask = os.path.join(arcpy.env.scratchFolder, "vectMask.shp")
                        arcpy.RasterToPolygon_conversion(arcpy.env.mask, vecMask, "SIMPLIFY", "Value")
                        
                        log("Clip inputs to watershed...")
                        arcpy.Clip_analysis(Soils,  vecMask, os.path.join(arcpy.env.scratchFolder,"Soilsclpd.shp"))
                        arcpy.Clip_analysis(Landuse, vecMask, os.path.join(arcpy.env.scratchFolder,"LUclpd.shp"))
                        
                        log("Union of soils and landuse...")
                        arcpy.Union_analysis([os.path.join(arcpy.env.scratchFolder,"LUclpd.shp"), os.path.join(arcpy.env.scratchFolder,"Soilsclpd.shp")], os.path.join(arcpy.env.scratchFolder,"union.shp"))
                        
                        log("Add Curve Number to union...")
                        LUcodes = GetDataTable(lutFile)
                        print(LUcodes)
                        
                        arcpy.AddField_management(os.path.join(arcpy.env.scratchFolder,"union.shp"), "CN", "LONG", "", "", "", "", "NON_NULLABLE", "NON_REQUIRED", "")
                        rows = arcpy.UpdateCursor(os.path.join(arcpy.env.scratchFolder,"union.shp"))
                        row = next(rows)
                        while row:
                            CN = 1
                            
                            SoilType = row.getValue(SoilsAtt)
                            if SoilType not in ["A", "B", "C", "D", "W", "BorrowPits", "GulliedLand", "UL"]:
                                log("  Soil type " + SoilType + " is not equal to A, B, C, D, W (Water), BorrowPits, GulliedLand, or UL (Urban Land), skipping")
                            else:
                                
                                LUType = row.getValue(LanduseAtt)
                                if SoilType in ["A", "B", "C", "D"]:
                                    SoilType = "CurveN" + SoilType
                                    
                                if not LUType in LUcodes:
                                    log("  Could not find " + LUType + " in land use table (LUT), skipping")
                                else:
                                    CN = LUcodes[LUType][SoilType]
                                    
                            row.setValue("CN", CN)
                            rows.updateRow(row)
                            row = next(rows)
                        del row, rows
                        
                        log("Convert union to raster...")
                        arcpy.PolygonToRaster_conversion(os.path.join(arcpy.env.scratchFolder,"union.shp"), "CN", os.path.join(arcpy.env.scratchFolder,"CurveN"),"MAXIMUM_AREA","None", cum_da)
                        CurveN = Raster(os.path.join(arcpy.env.scratchFolder,"CurveN"))
                    
                    if pname == "1yr":
                    
                        #   1-yr ----------------------------------------------------------------------------------------------------------------------------------------------------------------------
                        log("1yr Vol Calc...")
                        # should pull out precip value to tool data table...
                        V1in = Power( ( float(pdepth) - 0.2 * (( 1000.00 / CurveN ) - 10) ), 2) / ( float(pdepth) + (0.8 * (( 1000.00 / CurveN ) - 10)))
                        # V1in.save(os.path.join(arcpy.env.scratchFolder, "V1in"))
                        
                        log("1yr Vol Conv...")
                        V1ft = V1in * Units * Units / 12 * arcpy.env.mask
                        
                        log("1yr Flow Accum...")
                        vol1yr = BMP2DA(flowdir, "V1.tif", V1ft)
                            
                        chnnl_prot = arcpy.env.mask * vol1yr
                        chnnl_prot.save("chnnl_prot")
                    
                    else:
                        # 10yr or 25-yr ---------------------------------------------------------------------------------------------------------------------------------------
                        log("%s Urban Vol Calc..." % pname)
                        _V25U = Power((float(pdepth) - 0.2 * (( 1000.00 / CurveN ) - 10)) , 2) / (float(pdepth) + (0.8 * (( 1000.00 / CurveN ) - 10)))

                        log("%s Conv..." % pname)
                        V25_U_ft= _V25U * Units * Units / 12 #* arcpy.env.mask
                        
                        log("%s Urban Flow Accum..." % pname)
                        V25U = BMP2DA(flowdir, "V25U", V25_U_ft)
                        
                        log("%s Rural Vol Calc..." % pname)
                        _V25R = Power((float(pdepth) - 0.2 * (( 1000.00 / float(baseCN)) - 10)), 2) / (float(pdepth) + (0.8 * (( 1000.00 / float(baseCN)) - 10)))

                        log("%s Rural Vol Conv..." % pname)
                        V25_R_ft = _V25R * Units * Units / 12 #* arcpy.env.mask
                        
                        log("%s Rural Flow Accum..." % pname)
                        V25R = BMP2DA(flowdir, "V25R", V25_R_ft)
                        
                        log("%s Flood storage..." % pname)
                        V25Flood = arcpy.env.mask * (V25U - V25R)
                        V25Flood.save("V%sFlood" % pname)
                
            ## These should be simple raster calculator statements in model builder, no?
            
            log("Calculating Undeveloped Discharge...")            
            UndevQ = regression.ruralQcp(Basin, cum_da)
            UndevQ.save(undevqPath)
            urban2yrQ = regression.urban2yrQ(Basin, cum_da,cumimpcovlake)
            urban2yrQ.save(urban2yrQPath)
            urban10yrQ = regression.urban10yrQ(Basin,cum_da,cumimpcovlake)
            urban10yrQ.save(urban10yrQPath)
            urban25yrQ = regression.urban25yrQ(Basin,cum_da,cumimpcovlake)
            urban25yrQ.save(urban25yrQPath)
            
            tool.close(self)
            
        except:       
            i, j, k = sys.exc_info()
            EH(i, j, k)

class ProdTrans(tool):
    def __init__(self):
        self.label = "ProdTrans"
        self.description = "Production and Transport Setup"
        
    def __del__(self):
        super(tool, self).__del__()
        
    def getParameterInfo(self):
        parameters = []
        
        parameters += [arcpy.Parameter(
        displayName="Stream Inventory Points",
        name="strinvpts",
        datatype="GPFeatureLayer",
        parameterType="Required",
        direction="Input")]
        parameters[-1].filter.list = ["Point"]
        
        parameters += [arcpy.Parameter(
        displayName="Right bank erosion field",
        name="rb_ero",
        datatype="GPString",
        parameterType="Required",
        direction="Input")]
        parameters[-1].filter.type = "ValueList"
        
        parameters += [arcpy.Parameter(
        displayName="Right bank height field",
        name="rb_hgt",
        datatype="GPString",
        parameterType="Required",
        direction="Input")]
        parameters[-1].filter.type = "ValueList"
        
        parameters += [arcpy.Parameter(
        displayName="Right bank length field",
        name="rb_len",
        datatype="GPString",
        parameterType="Required",
        direction="Input")]
        parameters[-1].filter.type = "ValueList"
        
        parameters += [arcpy.Parameter(
        displayName="Left bank erosion field",
        name="lb_ero",
        datatype="GPString",
        parameterType="Required",
        direction="Input")]
        parameters[-1].filter.type = "ValueList"
        
        parameters += [arcpy.Parameter(
        displayName="Left bank height field",
        name="lb_hgt",
        datatype="GPString",
        parameterType="Required",
        direction="Input")]
        parameters[-1].filter.type = "ValueList"
        
        parameters += [arcpy.Parameter(
        displayName="Left bank length field",
        name="lb_len",
        datatype="GPString",
        parameterType="Required",
        direction="Input")]
        parameters[-1].filter.type = "ValueList"
        
        parameters += [arcpy.Parameter(
        displayName="Channel roughness field",
        name="n_channel",
        datatype="GPString",
        parameterType="Required",
        direction="Input")]
        parameters[-1].filter.type = "ValueList"
        
        parameters += [arcpy.Parameter(
        displayName="Bank width field",
        name="bankwidth",
        datatype="GPString",
        parameterType="Required",
        direction="Input")]
        parameters[-1].filter.type = "ValueList"
        
        parameters += [arcpy.Parameter(
        displayName="Bank Depth field",
        name="bankdepth",
        datatype="GPString",
        parameterType="Required",
        direction="Input")]
        parameters[-1].filter.type = "ValueList"
        
        
        
        parameters += [arcpy.Parameter(
        displayName="Landuse",
        name="landuse",
        datatype="GPFeatureLayer",
        parameterType="Required",
        direction="Input")]
        parameters[-1].filter.list = ["Polygon"]
        
        parameters += [arcpy.Parameter(
        displayName="Landuse field",
        name="lu_fld",
        datatype="GPString",
        parameterType="Required",
        direction="Input")]
        parameters[-1].filter.type = "ValueList"
        
        parameters += [arcpy.Parameter(
        displayName="Upland Export field",
        name="export_fld",
        datatype="GPString",
        parameterType="Required",
        direction="Input")]
        parameters[-1].filter.type = "ValueList"
        
        parameters += [arcpy.Parameter(
        displayName="Mannings N field",
        name="mannings_fld",
        datatype="GPString",
        parameterType="Required",
        direction="Input")]
        parameters[-1].filter.type = "ValueList"
        
        parameters += [arcpy.Parameter(
        displayName="Point Sources",
        name="pointsrc",
        datatype="GPFeatureLayer",
        parameterType="Optional",
        direction="Input")]
        parameters[-1].filter.list = ["Point"]
        
        parameters += [arcpy.Parameter(
        displayName="Point Sources field",
        name="ps_fld",
        datatype="GPString",
        parameterType="Optional",
        direction="Input")]
        parameters[-1].filter.type = "ValueList"
        
        parameters += [arcpy.Parameter(
        displayName="K Die-off Raster",
        name="k",
        datatype=["DERasterDataset", "GPRasterLayer"],
        parameterType="Optional",
        direction="Input")]
        
        parameters += [arcpy.Parameter(
        displayName="Slope Raster",
        name="slope",
        datatype=["DERasterDataset", "GPRasterLayer"],
        parameterType="Required",
        direction="Input")]
        
        parameters += [arcpy.Parameter(
        displayName="Hydraulic Geometry coefficient",
        name="hyd_coe",
        datatype="GPDouble",
        parameterType="Required",
        direction="Input")]
        
        parameters += [arcpy.Parameter(
        displayName="Hydraulic Geometry exponent",
        name="hyd_exp",
        datatype="GPDouble",
        parameterType="Required",
        direction="Input")]
        
        parameters += [arcpy.Parameter(
        displayName="Default Roughness n Value",
        name="n",
        datatype="GPDouble",
        parameterType="Required",
        direction="Input")]
        
        parameters += [arcpy.Parameter(
        displayName="Default % Erosion Rate",
        name="defero",
        datatype="GPDouble",
        parameterType="Required",
        direction="Input")]
        
        parameters += [arcpy.Parameter(
        displayName="Instream default production rate",
        name="defprod",
        datatype="GPDouble",
        parameterType="Required",
        direction="Input")]
        
        
        parameters += [arcpy.Parameter(
        displayName="Flow Direction",
        name="flowdir",
        datatype="DERasterDataset",
        parameterType="Required",
        direction="Input")]
        parameters[-1].value = os.path.join(arcpy.env.workspace,"flowdir")
        
        parameters += [arcpy.Parameter(
        displayName="Cumulative Drainage Area",
        name="cumda",
        datatype="DERasterDataset",
        parameterType="Required",
        direction="Input")]
        parameters[-1].value = os.path.join(arcpy.env.workspace,"Cumda")
        
        parameters += [arcpy.Parameter(
        displayName="Streams",
        name="streams",
        datatype="DERasterDataset",
        parameterType="Required",
        direction="Input")]
        parameters[-1].value = os.path.join(arcpy.env.workspace,"streams")
        
        parameters += [arcpy.Parameter(
        displayName="Impervious Cover",
        name="impcov",
        datatype="DERasterDataset",
        parameterType="Required",
        direction="Input")]
        parameters[-1].value = os.path.join(arcpy.env.workspace,"impcov")
        
        parameters += [arcpy.Parameter(
        displayName="Cumulative Impervious Cover with Lakes",
        name="cumimpcovlakes",
        datatype="DERasterDataset",
        parameterType="Required",
        direction="Input")]
        parameters[-1].value = os.path.join(arcpy.env.workspace,"cumimpcovlakes")
        
        parameters += [arcpy.Parameter(
        displayName="Undeveloped Discharge",
        name="undevQ",
        datatype="DERasterDataset",
        parameterType="Required",
        direction="Input")]
        parameters[-1].value = os.path.join(arcpy.env.workspace,"undevq")
        
        parameters += [arcpy.Parameter(
        displayName="Lakes",
        name="lakes",
        datatype="DERasterDataset",
        parameterType="Required",
        direction="Input")]
        parameters[-1].value = os.path.join(arcpy.env.workspace,"lakes")
        
        
        parameters += [arcpy.Parameter(
        displayName="Upland Production",
        name="p",
        datatype="DERasterDataset",
        parameterType="Required",
        direction="Output")]
        parameters[-1].value = os.path.join(arcpy.env.workspace,"pProd")
        
        parameters += [arcpy.Parameter(
        displayName="Combined production",
        name="q",
        datatype="DERasterDataset",
        parameterType="Required",
        direction="Output")]
        parameters[-1].value = os.path.join(arcpy.env.workspace,"qProd")
        
        parameters += [
        arcpy.Parameter(
        displayName="Basin",
        name="basin",
        datatype="String",
        parameterType="Required",
        direction="Input")]
        parameters[-1].filter.type = "ValueList"
        parameters[-1].filter.list = [
            "Georgia Region 1", 
            "Chattahoochee  GA (Rural and Urban)", 
            "Altamaha GA (Rural and Urban)", 
            "Region 1  2006 (Rural) - Blue Ridge NC 2002 (Urban)", 
            "Blue Ridge Piedmont  NC 2002 (Rural and Urban)",
            "SC Piedmont",
            'SC Blue Ridge', 
            'SC Sand Hills',
            'SC Coastal'
        ]
        
        return parameters

    def updateParameters(self, parameters):
        if parameters[0].value:
            fields = arcpy.ListFields(parameters[0].value)
            l = [f.name for f in fields]
            for p in [1, 2, 3, 4, 5, 6, 7, 8, 9]:
                parameters[p].filter.list = l
                
        if parameters[10].value:
            fields = arcpy.ListFields(parameters[10].value)
            l = [f.name for f in fields]
            parameters[11].filter.list = l
            parameters[12].filter.list = l
            parameters[13].filter.list = l
            
        if parameters[14].value:
            fields = arcpy.ListFields(parameters[14].value)
            l = [f.name for f in fields]
            parameters[15].filter.list = l
        
        if parameters[12].value:
            parameters[30].value = os.path.join(arcpy.env.workspace,"p"+ GetAlias(parameters[12].valueAsText))
            parameters[31].value = os.path.join(arcpy.env.workspace,"q"+ GetAlias(parameters[12].valueAsText))
            
        return

    def execute(self, parameters, messages):
        try:
            tool.execute(self)
            # for i, p in enumerate(parameters):
                # log("%s: %s" % (i, p.valueAsText))
            if not arcpy.env.mask:
                raise Exception("Geoprocessing env variable Mask is not set")
                
            # Script arguments...
            StrInvPts_preclip = parameters[0].valueAsText
            RB_Ero = parameters[1].valueAsText
            RB_Hgt = parameters[2].valueAsText
            RB_Len = parameters[3].valueAsText
            LB_Ero = parameters[4].valueAsText
            LB_Hgt = parameters[5].valueAsText
            LB_Len = parameters[6].valueAsText
            n_channel = parameters[7].valueAsText
            BankWidth = parameters[8].valueAsText
            BankDepth = parameters[9].valueAsText
            
            LU_file = parameters[10].valueAsText
            if 'existing' in LU_file.lower():
                LU_code = "E"
            elif 'future' in LU_file.lower():
                LU_code = "F"
            else:
                LU_code = ""
            
            LU_fld  = parameters[11].valueAsText
            Export_fld  = parameters[12].valueAsText
            Mannings_fld = parameters[13].valueAsText
            pn = Export_fld.split('.')[-1]
           
            pointsources = parameters[14].valueAsText
            point_fld    = parameters[15].valueAsText
            
            K = parameters[16].valueAsText
            slope = parameters[17].valueAsText
            
            BankHydCoe = float(parameters[18].valueAsText)
            BankHydExp = float(parameters[19].valueAsText)
            n_default = float(parameters[20].valueAsText)
            defEro = float(parameters[21].valueAsText)
            defProd = float(parameters[22].valueAsText)
            
            flowdir = Raster(parameters[23].valueAsText) * arcpy.env.mask 
            cumda = Raster(parameters[24].valueAsText)
            Streams_nd = Raster(parameters[25].valueAsText)
            streams = RemoveNulls(Streams_nd)
            Impervious_Cover = Raster(parameters[26].valueAsText)
            Cumulative_Impervious = Raster(parameters[27].valueAsText)
            Rural_1yrQ = Raster(parameters[28].valueAsText)
            lakes = Raster(parameters[29].valueAsText)
            
            pPath = parameters[30].valueAsText
            qPath = parameters[31].valueAsText
            Basin = parameters[32].valueAsText
            
            Units = flowdir.meanCellWidth
            
            vecmask = os.path.join(arcpy.env.scratchFolder, "vecmask.shp")
            arcpy.RasterToPolygon_conversion(arcpy.env.mask, vecmask, "SIMPLIFY", "Value")
            
            StrInvPts = os.path.join(arcpy.env.scratchFolder, "StrInvPts.shp")
            arcpy.Clip_analysis(StrInvPts_preclip, vecmask, StrInvPts)
            count = int(arcpy.GetCount_management(StrInvPts).getOutput(0))
            if count < 1:
                raise Exception("No stream inventory points in the study area")
            
            log("Reclassify flowdirection to find straight paths...")
            Flowdirs = Reclassify(flowdir, "VALUE", "1 1;2 0;4 1;8 0;16 1;32 0;64 1;128 0", "DATA")
            
            log("Reclassify flowdirection to find diagonal paths...")
            Flowdird = Reclassify(flowdir, "VALUE", "1 0;2 1;4 0;8 1;16 0;32 1;64 0;128 1", "DATA")
            
            log("Calculate distance grid...")
            Dist = (Flowdirs + Flowdird * 1.4142)* Units
            Dist.save(os.path.join(arcpy.env.scratchFolder, "dist"))
            
            log("Create Export Coefficient (washoff rate) rasters")
            log( '  Parameter: %s from field %s' % (pn, Export_fld))
            arcpy.PolygonToRaster_conversion(LU_file, Export_fld, os.path.join(arcpy.env.scratchFolder,"LUacres"), "MAXIMUM_AREA", None, Units)
            LU2 = Raster(os.path.join(arcpy.env.scratchFolder,"LUacres")) * (Units*Units/43560.00)
            LU2.save(os.path.join(arcpy.env.scratchFolder, "lu2"))
            
            log("Create roughness grid")  ######
            arcpy.PolygonToRaster_conversion(LU_file, Mannings_fld, os.path.join(arcpy.env.scratchFolder,"MANNINGSN"), "MAXIMUM_AREA", None, Units)
            
            log("Calculate overland flow velocity")
            MANNINGSN = Raster(os.path.join(arcpy.env.scratchFolder,"MANNINGSN"))
            UplandVel = MANNINGSN * Power(slope, 0.5 )
            UplandVel.save(os.path.join(arcpy.env.scratchFolder, "uplandvel"))
            
            log("Calculate overland flow detention time")
            Detovrlndt = Dist / UplandVel
            Detovrlndt.save(os.path.join(arcpy.env.scratchFolder, "detovrlndt"))
            Detovrlnd = RemoveNulls(Detovrlndt)
            Detovrlnd.save(os.path.join(arcpy.env.scratchFolder, "detovrlnd"))
            
            log("Calculate Hydraulic geometry...")
            BankHt = Power(cumda, BankHydExp) * BankHydCoe
            
            log("Stream Assessment points to raster...")
            fields = [RB_Ero, RB_Hgt, RB_Len, LB_Ero, LB_Hgt, LB_Len,n_channel, BankWidth, BankDepth]
            for field in fields:
                
                f = os.path.join(arcpy.env.scratchFolder, "f" + field)
                arcpy.FeatureToRaster_conversion(StrInvPts, field, f, flowdir)
                ras = Raster(f)
                AttributeRaster = Float(ras) * arcpy.env.mask
                
                # AttributeRaster.save(os.path.join(arcpy.env.scratchFolder, "f" + field +""))
                # flowdir.save(os.path.join(arcpy.env.scratchFolder, "flowdir"))
                # streams.save(os.path.join(arcpy.env.scratchFolder, "streams"))
                
                if field == RB_Len or field == LB_Len:
                    log("\tExtract %s attribute with cellsize %s..." % (field, Units))
                    extract = AttExtract(AttributeRaster, flowdir, streams, os.path.join(arcpy.env.scratchFolder, field+"e"))
                
                    log("\t\tReclassify Bank length attribute...")
                    #~ rrange = RemapRange([[-10000000000,0,0], [0.00001,1000000000000,1]]) # this does not work 
                    reclass = Reclassify(extract, "Value", ".00001 100000 1;-100000 0 0; NoData 0", "DATA")
                    #~ reclass = RemoveNulls(reclass_step1)
                    reclass.save(os.path.join(arcpy.env.scratchFolder, field + "rc"))
                
                else: 
                    log("\tExtract %s attribute..." % field)
                    extract = AttExtract(AttributeRaster, flowdir, streams, os.path.join(arcpy.env.scratchFolder, field+"e"))
            
            
            log("Calculate Right bank stream production...")
            RBL = Raster(os.path.join(arcpy.env.scratchFolder, RB_Len+"rc"))
            RBHT = Raster(os.path.join(arcpy.env.scratchFolder, RB_Hgt+"e"))
            RBE = Raster(os.path.join(arcpy.env.scratchFolder, RB_Ero+"e"))
            rt = RBL * streams * defProd * RBHT * RBE / 100 
            rt.save(os.path.join(arcpy.env.scratchFolder, "rt"+pn+""))
            RB = RemoveNulls(rt) 
            RB.save(os.path.join(arcpy.env.scratchFolder, "rb"+pn+""))

            
            log("Calculate Left bank stream production...")
            LBL = Raster(os.path.join(arcpy.env.scratchFolder,LB_Len+"rc"))
            LBHT = Raster(os.path.join(arcpy.env.scratchFolder, LB_Hgt+"e"))
            LBE = Raster(os.path.join(arcpy.env.scratchFolder, LB_Ero+"e"))
            lt = LBL * streams * defProd * LBHT* LBE/ 100
            lt.save(os.path.join(arcpy.env.scratchFolder, "lt"+pn+""))
            LB = RemoveNulls(lt) 
            LB.save(os.path.join(arcpy.env.scratchFolder, "lb"+pn+""))
            
            log("Calculate remaining stream production...")
            B = streams * BankHt * defProd * defEro / 100
            B.save(os.path.join(arcpy.env.scratchFolder, "B"+pn+""))
            
            log("Combine Stream production...")
            APPF = ( BooleanNot(RB) * B + RB ) + ( BooleanNot(LB) * B + LB )
            APPF.save(os.path.join(arcpy.env.scratchFolder, "appf"))
            
            # lakes = Raster(os.path.join(hp.Workspace + "\\WIPoutput.mdb", "lakes"))
            log("Calculate APPS production...")
            APPS = APPF * Dist * BooleanNot(lakes)
            APPS.save(os.path.join(arcpy.env.scratchFolder, "apps"))
            
            log("Combining washoff rate and stream production...")
            PStream = APPS * BooleanNot(Impervious_Cover)
            impcovrc = Reclassify(Impervious_Cover, "Value", "NoData 0;-10000000 0 0;0.00001 1000000 1", "DATA")
            impcovrc.save("impcovrc")
            
            # LU2 =  Raster(os.path.join(hp.Workspace + "\\WIPoutput.mdb", LU_code + pn))
            Ptemp = PStream + LU2 * impcovrc * streams
            LU2.save(os.path.join(arcpy.env.scratchFolder, "lu2"))
            Ptemp.save(os.path.join(arcpy.env.scratchFolder, "ptemp"))
            PStream.save(os.path.join(arcpy.env.scratchFolder, "pstream"))
            streams.save(os.path.join(arcpy.env.scratchFolder, "streams"))
            impcovrc.save(os.path.join(arcpy.env.scratchFolder, "impcovrc"))
            
            production = Ptemp + LU2 * BooleanNot(streams)
            # production.save(pPath)
            arcpy.CopyRaster_management(production, pPath)

            log("Determine stream roughness")
            n_channele1 = Raster(os.path.join(arcpy.env.scratchFolder, n_channel+ "e") )
            n_channele = RemoveNulls(n_channele1)
            n_channele.save(os.path.join(arcpy.env.scratchFolder, "n_channele"))
            
            nstream = streams * BooleanNot(n_channele)* n_default + n_channele
            nstream.save(os.path.join(arcpy.env.scratchFolder, "nstream"))

            
            log("Calculate Hydraulic Radius")
            rb_Lenrc = Raster(os.path.join(arcpy.env.scratchFolder, RB_Len+"rc.tif") )
            lb_Lenrc = Raster(os.path.join(arcpy.env.scratchFolder, LB_Len+"rc.tif") )
            
            # create stream segment mask where data exists 
            #~ rbgreater = GreaterThan(rb_Lenrc, lb_Lenrc)
            #~ rbgreater.save(os.path.join(arcpy.env.scratchFolder, "rbgreater"))
            #~ rbgreater1 = rbgreater * rb_Lenrc
            #~ rbgreater1.save(os.path.join(arcpy.env.scratchFolder, "rbgreater1"))
            #~ lbgreater = GreaterThan(lb_Lenrc, rb_Lenrc)
            #~ lbgreater.save(os.path.join(arcpy.env.scratchFolder, "lbgreater"))
            #~ lbgreater1 = lbgreater * lb_Lenrc
            #~ lbgreater1.save(os.path.join(arcpy.env.scratchFolder, "lbgreater1"))
            #~ totalgt = rbgreater1 +lbgreater1
            #~ totalgt.save(os.path.join(arcpy.env.scratchFolder, "totalgt"))
            #~ dataclip = streams * totalgt
            
            dataclip = streams * CellStatistics([rb_Lenrc, lb_Lenrc], "MAXIMUM", "DATA")
            dataclip.save(os.path.join(arcpy.env.scratchFolder, "dataclip"))
            
            # fill in bank width where values are missing along stream
            widthdef = 20.9 * Power ( ( Float(cumda) / 640 ), 0.376 )
            BankWidthe = Raster(os.path.join(arcpy.env.scratchFolder, BankWidth+"e.tif") )
            widthtemp = dataclip * BankWidthe
            widthtemp.save(os.path.join(arcpy.env.scratchFolder, "widthtemp")) 
            width = streams * BooleanNot(widthtemp) * widthdef + widthtemp
            width.save(os.path.join(arcpy.env.scratchFolder, "width"))

            
            # fill in bank depth where values are missing along stream
            depthdef = 3.02 * Power ( ( Float(cumda) / 640 ), 0.258 )
            BankDepthe = Raster(os.path.join(arcpy.env.scratchFolder, BankDepth+ "e.tif") )
            depthtemp = dataclip * BankDepthe
            depth = streams * BooleanNot(depthtemp) * depthdef + depthtemp
            depth.save(os.path.join(arcpy.env.scratchFolder, "depth"))

            
            hydradiusC = (Float(width) * Float(depth)) / (Float(width) + 2 * Float(depth))
            hydradiusC.save(os.path.join(arcpy.env.scratchFolder, "hydradiusC"))
            hydradius = RemoveNulls(hydradiusC)
            hydradius.save(os.path.join(arcpy.env.scratchFolder, "hydradius"))
            
            log("Calculate normal stream velocity")
            tempvel = Power (hydradius, 0.6667) *  Power (Float(slope), 0.5) / nstream
            tempvel.save(os.path.join(arcpy.env.scratchFolder, "tempvel"))
            
            streamvel = RemoveNulls(tempvel)
            streamvel.save(os.path.join(arcpy.env.scratchFolder, "streamvel"))
                
            log("Calculate in-stream flow detention time")
            Detstreamt = Dist / streamvel
            Detstreamt.save(os.path.join(arcpy.env.scratchFolder, "detstreamt"))
            Detstream = RemoveNulls(Detstreamt)
            Detstream.save(os.path.join(arcpy.env.scratchFolder, "detstream"))
            
            log("Calculate total flow detention time")
            Dettime =  Detstream + Detovrlnd * BooleanNot (Detstream)  
            Dettime.save(os.path.join(arcpy.env.scratchFolder, "dettime"))    
                    
            ##    usgs_calcs = Helper.USGSVars(hp.Basin)
            uQcp = urbanQcp(Basin, cumda, Cumulative_Impervious)
            uQcp.save("UrbanQ1")
            # hp.saveRasterOutput(urbanQcp, "UrbanQ1")
            
            log("Calculate Urban/Rural ratio...")
            URratio = uQcp / Rural_1yrQ
            URratio.save("urbrurratio")
            # hp.saveRasterOutput(URratio, "urbrurratio")
            
            log("Clip to streams...")
            # and round
            URratiocl = Int( RoundUp( RoundDown( Streams_nd* URratio * 20000 ) / 2))
            
            log("Vectorize...")
            
            URRatio_Vector = os.path.join(arcpy.env.scratchFolder, "urratiovec.shp")
            StreamToFeature(URratiocl, flowdir, URRatio_Vector, "NO_SIMPLIFY") 
            ConvertGRIDCODEatt(URRatio_Vector)
            # arcpy.CopyFeatures_management(os.path.join(arcpy.env.scratchFolder, "urratiovec.shp"), os.path.join(hp.Workspace + "\\WIPoutput.mdb", "urratiovec"))
            # hp.models[hp.current_tool]["output"].append(os.path.join(hp.Workspace + "\\WIPoutput.mdb", "urratiovec"))
            
            # for LU in Landuses:
                # for p in params:
            # pn = p[:10].strip()
            # output = os.path.join(hp.Workspace + "\\WIPoutput.mdb", "q" + LU[2] + pn)
            # defProd = params[p]['DefEro']
            # production = os.path.join(hp.Workspace + "\\WIPoutput.mdb", "P" + LU[2] + pn)    
            
            pointsrc = ""
            if pointsources:
                log("Create point source input raster")
                
                pointsrcshp = os.path.join(arcpy.env.scratchFolder, "pointsrc.shp")
                arcpy.Clip_analysis(pointsources, vecmask, pointsrcshp)
                
                count = int(arcpy.GetCount_management(pointsrcshp).getOutput(0))
                if count > 0:
                    log("  found %i points source inputs in study area" % count)
                    temppt = os.path.join(arcpy.env.scratchFolder, "temppt")
                    arcpy.FeatureToRaster_conversion(pointsrcshp, point_fld, temppt, arcpy.env.mask)
                    
                    pointsrc = RemoveNulls(temppt)
                    pointsrc.save("pt" + LU_code + pn)
            
            log("Add erosivity and point sources to %s production..." % (LU_code + pn))
            data_ero = CalcErosivity(defProd, production, pointsrc, URratio, streams)
            # log(qPath)
            arcpy.CopyRaster_management(data_ero, qPath)
            
            # data_ero.save(qPath)
            
            if K:
                Koutput = Exp( K * Dettime / -86400) 
                arcpy.CopyRaster_management(Koutput, 'K'+LU_code+pn)
                # Koutput.save('K'+LU_code+pn)
            
            tool.close(self)
            
        except:       
            i, j, k = sys.exc_info()
            EH(i, j, k)

class Baseline(tool):
    def __init__(self):
        self.label = "Baseline"
        self.description = "Baseline"
        
    def __del__(self):
        super(tool, self).__del__()
        
    def getParameterInfo(self):
    
        parameters = []
        parameters += [arcpy.Parameter(
        displayName="Project Points",
        name="bmppts",
        datatype="GPFeatureLayer",
        parameterType="Required",
        direction="Input")]
        parameters[-1].filter.list = ["Point"]
        
        parameters += [arcpy.Parameter(
        displayName="Project Type field",
        name="bmptype",
        datatype="GPString",
        parameterType="Required",
        direction="Input")]
        parameters[-1].filter.type = "ValueList"
        
        parameters += [arcpy.Parameter(
        displayName="BMP Efficiency field",
        name="bmpeff",
        datatype="GPString",
        parameterType="Required",
        direction="Input")]
        parameters[-1].filter.type = "ValueList"
        
        parameters += [arcpy.Parameter(
        displayName="Summary Points",
        name="summarypts",
        datatype="GPFeatureLayer",
        parameterType="Optional",
        direction="Input")]
        parameters[-1].filter.list = ["Point"]
        
        parameters += [arcpy.Parameter(
        displayName="Input Combined Production",
        name="tssprod",
        datatype="DERasterDataset",
        parameterType="Required",
        direction="Input")]
        
        parameters += [arcpy.Parameter(
        displayName="K raster from Production",
        name="K",
        datatype="DERasterDataset",
        parameterType="Required",
        direction="Input")]
        
        parameters += [arcpy.Parameter(
        displayName="Output Load",
        name="load",
        datatype="DERasterDataset",
        parameterType="Required",
        direction="Output")]
        parameters[-1].parameterDependencies = [parameters[4].name]
        
        parameters += [arcpy.Parameter(
        displayName="Output Yield",
        name="yield",
        datatype="DERasterDataset",
        parameterType="Required",
        direction="Output")]
        parameters[-1].parameterDependencies = [parameters[4].name]
        
        parameters += [arcpy.Parameter(
        displayName="Output Yield Vector",
        name="yieldvec",
        datatype="GPFeatureLayer",
        parameterType="Required",
        direction="Output")]
        parameters[-1].parameterDependencies = [parameters[4].name]
        
        parameters += [arcpy.Parameter(
        displayName="Flow Direction",
        name="flowdir",
        datatype="DERasterDataset",
        parameterType="Required",
        direction="Input")]
        parameters[-1].value = os.path.join(arcpy.env.workspace,"flowdir")
        
        parameters += [arcpy.Parameter(
        displayName="Cumulative Drainage Area",
        name="cumda",
        datatype="DERasterDataset",
        parameterType="Required",
        direction="Input")]
        parameters[-1].value = os.path.join(arcpy.env.workspace,"Cumda")
        
        parameters += [arcpy.Parameter(
        displayName="Streams",
        name="streams",
        datatype="DERasterDataset",
        parameterType="Required",
        direction="Input")]
        parameters[-1].value = os.path.join(arcpy.env.workspace,"streams")
        
        return parameters

    def updateParameters(self, parameters):
        if parameters[0].value:
            fields = arcpy.ListFields(parameters[0].valueAsText)
            l = [f.name for f in fields]
            parameters[1].filter.list = l
            parameters[2].filter.list = l
        return

    def execute(self, parameters, messages):
        try:
            tool.execute(self)
            log("\nBaseline run started at %s" % time.asctime())
            
            bmp_noclip = parameters[0].valueAsText
            bmp_type = parameters[1].valueAsText
            bmp_eff = parameters[2].valueAsText
            summary_pt_input = parameters[3].valueAsText
            TSSProd = Raster(parameters[4].valueAsText)
            K = Raster(parameters[5].valueAsText)
            TSSLoadOutputPath = parameters[6].valueAsText
            TSSYieldPath = parameters[7].valueAsText
            TSSYldvecPath = parameters[8].valueAsText
            flowdir = Raster(parameters[9].valueAsText)
            Cum_da = Raster(parameters[10].valueAsText)
            Streams_nd = Raster(parameters[11].valueAsText)
            
            streams = RemoveNulls(Streams_nd)
            Units = flowdir.meanCellWidth
            
            log("Clipping BMP points to work area (or mask)...")
            vecmask = os.path.join(arcpy.env.scratchFolder, "vectmask.shp")
            BMPpts = os.path.join(arcpy.env.scratchFolder, "BMPpts.shp")
            arcpy.RasterToPolygon_conversion(arcpy.env.mask, vecmask, "SIMPLIFY", "Value")
            arcpy.Clip_analysis(bmp_noclip, vecmask, BMPpts)
            
            log("Finding BMP projects...")
            ExBMPpts = os.path.join(arcpy.env.scratchFolder, "ExBMPpts.shp")
            count = GetSubset(BMPpts, ExBMPpts, " \"%s\" = 'BMP' " % bmp_type)
            
            if count < 1:
                raise Exception("No BMP points in project area")

            log("Convert BMPs to Raster...")
            BMPs = arcpy.FeatureToRaster_conversion(ExBMPpts, bmp_eff, os.path.join(arcpy.env.scratchFolder,"ExBMPpts"), flowdir)
            
            log("Combine decay function with BMP reduction")
            bmptemp = RemoveNulls(BMPs)
            weightred = 1 - ( K * ( 1 - (bmptemp / 100.0 ) ) ) * arcpy.env.mask
            weightred.save(os.path.join(arcpy.env.scratchFolder,"weightred"))
            
            log("Calculate Reduction...")
            Existingtss = BMP2DA(flowdir, "bmp2da", TSSProd, weightred)
            
            log("Clip...")
            TSSLoadOutput = Existingtss * arcpy.env.mask
            TSSLoadOutput.save(TSSLoadOutputPath)
            
            log("Calculate Yield...")
            TSSYield = TSSLoadOutput / Cum_da
            TSSYield.save(TSSYieldPath)
            
            log("Clip to streams...")
            # and round
            TSSYieldcl = Int(RoundUp( RoundDown( Streams_nd * TSSYield * 20000 ) / 2 ))
            
            log("Vectorize...")
            StreamToFeature(TSSYieldcl, flowdir, TSSYldvecPath, "NO_SIMPLIFY")
            
            ConvertGRIDCODEatt(TSSYldvecPath)
                
            if summary_pt_input:
                summary_pts = os.path.join(arcpy.env.workspace, "summarypts")
                arcpy.Clip_analysis(summary_pt_input, vecmask, summary_pts)
                SetPIDs(summary_pts)
                Summarize(TSSLoadOutput, summary_pts)        
            
            tool.close(self)
            
        except:       
            i, j, k = sys.exc_info()
            EH(i, j, k)
            
class CIP(tool):
    def __init__(self):
        self.label = "CIP"
        self.description = "CIP"
        
    def __del__(self):
        super(tool, self).__del__()
        
    def getParameterInfo(self):
    
        parameters = []
        
        parameters += [
        arcpy.Parameter(
        displayName="Project Points",
        name="bmppts",
        datatype="GPFeatureLayer",
        parameterType="Required",
        direction="Input")]
        parameters[-1].filter.list = ["Point"]
        
        parameters += [
        arcpy.Parameter(
        displayName="Project Type field",
        name="bmptype",
        datatype="GPString",
        parameterType="Required",
        direction="Input")]
        parameters[-1].filter.type = "ValueList"
        
        parameters += [
        arcpy.Parameter(
        displayName="Active CIP Projects",
        name="cip",
        datatype="GPString",
        parameterType="Required",
        direction="Input")]
        parameters[-1].filter.type = "ValueList"
        
        parameters += [
        arcpy.Parameter(
        displayName="Existing 1-yr Discharge field",
        name="Q1ex",
        datatype="GPString",
        parameterType="Required",
        direction="Input")]
        parameters[-1].filter.type = "ValueList"
        
        parameters += [
        arcpy.Parameter(
        displayName="Proposed 1-yr Discharge field",
        name="Q1",
        datatype="GPString",
        parameterType="Required",
        direction="Input")]
        parameters[-1].filter.type = "ValueList"
        
        parameters += [
        arcpy.Parameter(
        displayName="Stream Project Length field",
        name="strleng",
        datatype="GPString",
        parameterType="Required",
        direction="Input")]
        parameters[-1].filter.type = "ValueList"
        
        parameters += [
        arcpy.Parameter(
        displayName="Existing efficiency field",
        name="effex",
        datatype="GPString",
        parameterType="Required",
        direction="Input")]
        parameters[-1].filter.type = "ValueList"
        
        parameters += [
        arcpy.Parameter(
        displayName="Proposed efficiency field",
        name="effprop",
        datatype="GPString",
        parameterType="Required",
        direction="Input")]
        parameters[-1].filter.type = "ValueList"
        
        parameters += [
        arcpy.Parameter(
        displayName="Stream length field",
        name="strlen",
        datatype="GPString",
        parameterType="Optional",
        direction="Input")]
        parameters[-1].filter.type = "ValueList"
        
        parameters += [
        arcpy.Parameter(
        displayName="Default Erosion",
        name="defero",
        datatype="Double",
        parameterType="Required",
        direction="Input")]
        
        parameters += [
        arcpy.Parameter(
        displayName="Basin",
        name="basin",
        datatype="String",
        parameterType="Required",
        direction="Input")]
        parameters[-1].filter.type = "ValueList"
        parameters[-1].filter.list = [
            "Georgia Region 1", 
            "Chattahoochee  GA (Rural and Urban)", 
            "Altamaha GA (Rural and Urban)", 
            "Region 1  2006 (Rural) - Blue Ridge NC 2002 (Urban)", 
            "Blue Ridge Piedmont  NC 2002 (Rural and Urban)",
            "SC Piedmont",
            'SC Blue Ridge', 
            'SC Sand Hills',
            'SC Coastal'
        ]
        
        parameters += [
        arcpy.Parameter(
        displayName="Summary Points",
        name="summarypts",
        datatype="GPFeatureLayer",
        parameterType="Optional",
        direction="Input")]
        parameters[-1].filter.list = ["Point"]
        
        parameters += [arcpy.Parameter(
        displayName="Input Stream Production",
        name="q",
        datatype="DERasterDataset",
        parameterType="Required",
        direction="Input")]
        
        parameters += [arcpy.Parameter(
        displayName="Input Combined Production",
        name="p",
        datatype="DERasterDataset",
        parameterType="Required",
        direction="Input")]
        
        parameters += [arcpy.Parameter(
        displayName="Input K Die-off",
        name="K",
        datatype="DERasterDataset",
        parameterType="Required",
        direction="Input")]
        
        parameters += [arcpy.Parameter(
        displayName="Point Source Input",
        name="pt",
        datatype="DERasterDataset",
        parameterType="Required",
        direction="Input")]
        
        parameters += [arcpy.Parameter(
        displayName="Output Load",
        name="load",
        datatype="DERasterDataset",
        parameterType="Required",
        direction="Output")]
        
        parameters += [arcpy.Parameter(
        displayName="Output Yield",
        name="yield",
        datatype="DERasterDataset",
        parameterType="Required",
        direction="Output")]
        
        parameters += [arcpy.Parameter(
        displayName="Output Yield Vector",
        name="yieldvec",
        datatype="GPFeatureLayer",
        parameterType="Required",
        direction="Output")]
        
        parameters += [arcpy.Parameter(
        displayName="Flow Direction",
        name="flowdir",
        datatype="DERasterDataset",
        parameterType="Required",
        direction="Input")]
        parameters[-1].value = os.path.join(arcpy.env.workspace,"flowdir")
        
        parameters += [arcpy.Parameter(
        displayName="Cumulative Drainage Area",
        name="cumda",
        datatype="DERasterDataset",
        parameterType="Required",
        direction="Input")]
        parameters[-1].value = os.path.join(arcpy.env.workspace,"Cumda")
        
        parameters += [arcpy.Parameter(
        displayName="Streams",
        name="streams",
        datatype="DERasterDataset",
        parameterType="Required",
        direction="Input")]
        parameters[-1].value = os.path.join(arcpy.env.workspace,"streams")
        
        parameters += [arcpy.Parameter(
        displayName="Cumulative Impervious Area (including Lakes)",
        name="cumimpcov",
        datatype="DERasterDataset",
        parameterType="Required",
        direction="Input")]
        parameters[-1].value = os.path.join(arcpy.env.workspace,"cumimpcovlakes")
        
        parameters += [arcpy.Parameter(
        displayName="Rural 1-yr Q",
        name="Rural1yrQ",
        datatype="DERasterDataset",
        parameterType="Required",
        direction="Input")]
        parameters[-1].value = os.path.join(arcpy.env.workspace,"UndevQ")
        
        return parameters
        
    def updateParameters(self, parameters, bmpptsfield=0):
        if parameters[bmpptsfield].value:
            fields = arcpy.ListFields(parameters[bmpptsfield].valueAsText)
            l = [f.name for f in fields]
            for i in range(bmpptsfield+1, bmpptsfield+9):
                parameters[i].filter.list = l
        return

    def execute(self, parameters, messages):
        try:
            tool.execute(self)
            
            bmp_noclip = parameters[0].valueAsText
            bmp_type = parameters[1].valueAsText
            bmp_CIPproj = parameters[2].valueAsText
            bmp_Ex1yr = parameters[3].valueAsText
            bmp_Prop1yr = parameters[4].valueAsText
            streamLinearRed = parameters[5].valueAsText #optional
            bmp_eeff = parameters[6].valueAsText
            bmp_peff = parameters[7].valueAsText
            StreamLength_fld = parameters[8].valueAsText
            defEro = parameters[9].value
            Basin = parameters[10].valueAsText
            summary_pt_input = parameters[11].valueAsText
            
            
            TSSprod = Raster(parameters[12].valueAsText)
            TSSP_ero_ext = Raster(parameters[13].valueAsText)
            K = Raster(parameters[14].valueAsText)
            pointsrc = parameters[15].valueAsText
            if pointsrc:
                pointsrc = Raster(parameters[15].valueAsText)
            
            TSSLoadOutputPath = parameters[16].valueAsText
            CIPYldPath = parameters[17].valueAsText
            CIPYldVecPath = parameters[18].valueAsText
            
            flowdir = Raster(parameters[19].valueAsText)
            Cum_da = Raster(parameters[20].valueAsText)
            Streams_nd = Raster(parameters[21].valueAsText)
            Stream_Raster = RemoveNulls(Streams_nd)
            
            Cumulative_Impervious = Raster(parameters[22].valueAsText)
            Rural_1yrQ = Raster(parameters[23].valueAsText)
            URratio_vec = os.path.join(arcpy.env.scratchFolder, "URratio_CIP")
            
            log("\nCIP run started at %s" % (time.asctime()))
            
            pn = GetAlias(bmp_eeff)[:10]
            Units = flowdir.meanCellWidth
            
            vectmask = os.path.join(arcpy.env.scratchFolder, "vectmask.shp")
            BMPpts = os.path.join(arcpy.env.scratchFolder, "BMPpts.shp")
            arcpy.RasterToPolygon_conversion(arcpy.env.mask, vectmask, "SIMPLIFY", "Value")
            arcpy.Clip_analysis(bmp_noclip, vectmask, BMPpts)
            
            if summary_pt_input:
                summary_pts = os.path.join(arcpy.env.workspace, "summaryptsCIP")
                arcpy.Clip_analysis(summary_pt_input, vectmask, summary_pts)
                SetPIDs(summary_pts)
            
            log("Finding CIP projects...")
            CIPBMPpts = os.path.join(arcpy.env.scratchFolder, "CIPpts.shp")
            CIP_found = GetSubset(BMPpts, CIPBMPpts, " \"%s\" = 'TRUE' " % bmp_CIPproj)
            if not CIP_found:
                raise Exception("Did not find any CIP Projects in the study area, stopping")
                
            log("Finding Channel Protection projects...")  # From CIP points only
            ChanBMPpts = os.path.join(arcpy.env.scratchFolder, "ChanBMPpts.shp")
            CP_found = GetSubset(CIPBMPpts, ChanBMPpts , " \"%s\" < \"%s\" " % (bmp_Prop1yr, bmp_Ex1yr))
            
            log("Finding Stream Restoration projects...")    
            strBMPs2 = os.path.join(arcpy.env.scratchFolder, "strBMPs2.shp")
            SR_found = GetSubset(CIPBMPpts, strBMPs2 , " \"%s\" = 'Stream Restoration' " % bmp_type)
            
            log("Finding Existing BMPs...")
            ExistingBMPs = os.path.join(arcpy.env.scratchFolder, "ExistingBMPs.shp")
            existing_found = GetSubset(BMPpts, ExistingBMPs, "NOT ( \"%s\" = 'TRUE' AND ( \"%s\" = 'BMP' OR \"%s\" = 'New BMP' ) ) AND \"%s\" > 0 " % \
                                                            (bmp_CIPproj, bmp_type, bmp_type, bmp_eeff) )
            log("Finding CIP BMPs...")
            CIPBMPs = os.path.join(arcpy.env.scratchFolder, "CIPBMPpts.shp")
            cipbmps_found = GetSubset(CIPBMPpts, CIPBMPs, " \"%s\" = 'BMP' OR \"%s\" = 'New BMP' " % (bmp_type, bmp_type))

                
            if CP_found > 0:
                
                
                CumMod_da, RasBMPpts2, uQcp = ChannelProtection(Basin, ChanBMPpts, bmp_Prop1yr, flowdir, Cum_da, Cumulative_Impervious) 
                
                # uQcp = urbanQcp(CumMod_da, Cumulative_Impervious, Basin)
                
                log("Calculate Urban/Rural ratio...")
                
                URratio = uQcp / Rural_1yrQ
                
                log("Add erosivity to production...")# % param)
                TSSP_ero_ext = CalcErosivity(defEro, TSSprod, pointsrc, URratio, Stream_Raster)
                # TSSP_ero_ext.save(os.path.join(arcpy.env.scratchFolder, "TSSP_ero_ext"))
                log("Clip to streams...")
                # and round
                UrbRurratc = Int(RoundUp( RoundDown( Streams_nd * URratio * 20000 ) / 2 ))
                
                log("Vectorize...")
                StreamToFeature(UrbRurratc, flowdir, URratio_vec, "NO_SIMPLIFY")
                ConvertGRIDCODEatt(URratio_vec)
            
            else:
                log("  Did not find any Channel Protection Projects in the study area, skipping this part")
                CumMod_da = Cum_da
                URratio = os.path.join(arcpy.env.workspace, "UrbRurratio")
                
            
            if SR_found < 1:
                log("  Did not find any Stream Restoration Projects in the study area, skipping this part")
                TSS_reduc = TSSP_ero_ext
            else:
                log("Convert Stream Lengths to Raster...")
                len = arcpy.FeatureToRaster_conversion(strBMPs2, StreamLength_fld, os.path.join(arcpy.env.scratchFolder, "len.tif"), flowdir)
                BMPlengths = Float(len)
                 
                lengths = AttExtract(BMPlengths, flowdir, Stream_Raster, pn+'len.tif')
                
                log("Remove background values...")
                lengthsmask = Reclassify(lengths, "VALUE", ".00001 100000 1;-100000 0 0; NoData 0", "DATA")
                
                log("Convert Stream Restoration Projects to Raster...")
                srp = GetTempRasterPath("srp")
                arcpy.FeatureToRaster_conversion(strBMPs2, bmp_peff, srp, flowdir)
                strBMPs3 = Float(Raster(srp))
                
                PropEffnd = AttExtract(strBMPs3, flowdir, Stream_Raster, pn+'attx.tif')
                
                log("Remove background values...")
                PropEff = RemoveNulls(PropEffnd)
                
                log("Production for Stream Restoration Projects...")
                StrTSSRed = lengthsmask * TSSprod * PropEff / 100
                
                log("Reduce production for Stream Restoration Projects...")
                TSS_reduc = TSSP_ero_ext - StrTSSRed
                
                if streamLinearRed:
                    
                    log("Convert Stream Projects to Raster...")
                    #~ print bmp_peff
                    slpf = arcpy.FeatureToRaster_conversion(strBMPs2, streamLinearRed, os.path.join(arcpy.env.scratchFolder, "slpf.tif"), flowdir)
                    strBMPs3 = Float(slpf)
                    
                    log("Stream reduction per length...")
                    srlength = AttExtract(strBMPs3, flowdir, Stream_Raster, pn[0:5]+'srLen')
                    
                    log("Remove background values...")
                    srlengthm = RemoveNulls(srlength)
                    
                    log("Reclassify flowdirection to find straight paths...")
                    Flowdirs = Reclassify(flowdir, "VALUE", "1 1;2 0;4 1;8 0;16 1;32 0;64 1;128 0", "DATA")
                    
                    log("Reclassify flowdirection to find diagonal paths...")
                    Flowdird = Reclassify(flowdir, "VALUE", "1 0;2 1;4 0;8 1;16 0;32 1;64 0;128 1", "DATA")
                    
                    log("Calculate distance grid...")
                    Dist = ( Flowdirs + Flowdird * 1.4142) * Units
                    
                    log("Stream Length Reduction...")
                    
                    StrLenRed = srlengthm * Dist * lengthsmask
                    TSS_reduc = TSS_reduc - StrLenRed
                
            # Get and combine all the efficiencies used
            if existing_found > 0: 
                log("Convert Existing Efficiency to Raster...")
                arcpy.FeatureToRaster_conversion(ExistingBMPs, bmp_eeff, os.path.join(arcpy.env.scratchFolder, "ExistingBMPs"), flowdir)
                ExistingBMPs = Raster(os.path.join(arcpy.env.scratchFolder, "ExistingBMPs"))
                ExistingBrc = RemoveNulls(ExistingBMPs)
                
            if cipbmps_found > 0:
                log("Convert CIP Efficiency to Raster...")
                CIPBMPpt_temp = GetTempRasterPath("CIPBMPs")
                arcpy.FeatureToRaster_conversion(CIPBMPs, bmp_peff, CIPBMPpt_temp, flowdir)
                CIPBMPptsRas = Raster(CIPBMPpt_temp)
                CIPBMPrc = RemoveNulls(CIPBMPptsRas)
            
            if existing_found and cipbmps_found:
                log("Combine reduction efficiencies...")
                redvar = ExistingBrc + CIPBMPrc
            elif existing_found:
                redvar = ExistingBrc
            elif cipbmps_found:
                redvar = CIPBMPrc
            else:
                redvar = None
                log("  WARNING: Did not find any Existing OR CIP projects, so not reducing accumulation")
                
            log("Calculate Load Reduction...")
            if type(redvar) == Raster:
                wtredvar = 1 - ( K * ( 1 - (redvar / 100.0 ) ) ) * arcpy.env.mask
                wtredvar.save(os.path.join(arcpy.env.scratchFolder, "wtredvar"))
                TSSLoadcip = BMP2DA(flowdir, "TSSLoadcip", TSS_reduc, wtredvar)
            else:
                TSSLoadcip = BMP2DA(flowdir, "TSSLoadcip", TSS_reduc)
            
            log("Clip...")
            TSSLoadOutput = TSSLoadcip * arcpy.env.mask
            TSSLoadOutput.save(TSSLoadOutputPath)
            
            log("Calculate Yield...")
            CIPYield = TSSLoadcip / Cum_da
            CIPYield.save(CIPYldPath)
            
            log("Clip to streams...")
            # and round
            TSSYield_cl = Int(RoundUp( RoundDown( Streams_nd * CIPYield * 20000 ) / 2 ))
            TSSYield_cl.save(os.path.join(arcpy.env.scratchFolder, "YieldStream"))
            
            log("Vectorize...")
            StreamToFeature(TSSYield_cl, flowdir, CIPYldVecPath, "NO_SIMPLIFY")
            
            ConvertGRIDCODEatt(CIPYldVecPath)
     
            if summary_pt_input:
                log("Summarizing results...")
                alias = pn + " Load"
                Summarize(TSSLoadOutput, summary_pts, alias)    
            
            tool.close(self)
            
        except:       
            i, j, k = sys.exc_info()
            EH(i, j, k)

class SingleBMP(CIP):
    def __init__(self):
        self.label = "SingleBMP"
        self.description = "SingleBMP"
        
    def __del__(self):
        super(tool, self).__del__()
        
    def getParameterInfo(self):        
        parameters = super(SingleBMP, self).getParameterInfo()
        return parameters
        
    def updateParameters(self, parameters):
        super(SingleBMP, self).updateParameters(parameters, 0)
    
    def execute(self, parameters, messages):
        try:
            tool.execute(self)
            bmp_noclip = parameters[0].valueAsText
            bmp_type_fld = parameters[1].valueAsText
            bmp_CIPproj_fld = parameters[2].valueAsText
            bmp_Ex1yr_fld = parameters[3].valueAsText
            bmp_Prop1yr_fld = parameters[4].valueAsText
            streamLinearRed_fld = parameters[5].valueAsText #optional
            bmp_eeff_fld = parameters[6].valueAsText
            bmp_peff_fld = parameters[7].valueAsText
            StreamLength_fld = parameters[8].valueAsText
            defEro = parameters[9].value
            Basin = parameters[10].valueAsText
            summary_pt_input = parameters[11].valueAsText
            
            
            TSSprod = Raster(parameters[12].valueAsText)
            TSSP_ero_ext = Raster(parameters[13].valueAsText)
            K = Raster(parameters[14].valueAsText)
            pointsrc = parameters[15].valueAsText
            if pointsrc:
                pointsrc = Raster(parameters[15].valueAsText)
            
            TSSLoadOutputPath = parameters[16].valueAsText
            CIPTSSYldPath = parameters[17].valueAsText
            CIPTSSYldVecPath = parameters[18].valueAsText
            
            flowdir = Raster(parameters[19].valueAsText)
            Cum_da = Raster(parameters[20].valueAsText)
            Streams_nd = Raster(parameters[21].valueAsText)
            Stream_Raster = RemoveNulls(Streams_nd)
            
            Cumulative_Impervious = Raster(parameters[22].valueAsText)
            Rural_1yrQ = Raster(parameters[23].valueAsText)
            URratio_vec = os.path.join(arcpy.env.scratchFolder, "URratio_Sin")
            
            Units = flowdir.meanCellWidth
            pn = GetAlias(bmp_eeff_fld)[:10]
            
            log("Clipping BMP points to work area (or mask)...")
            vecmask = os.path.join(arcpy.env.scratchFolder, "vectmask.shp")
            BMPpts = os.path.join(arcpy.env.scratchFolder, "BMPpts.shp")
            arcpy.RasterToPolygon_conversion(arcpy.env.mask, vecmask, "SIMPLIFY", "Value")
            arcpy.Clip_analysis(bmp_noclip, vecmask, BMPpts)
            
            log("Calculate Urban/Rural ratio...")
            urbanQcpbas = urbanQcp(Basin, Cum_da, Cumulative_Impervious)
            URratio = urbanQcpbas / Rural_1yrQ
            
            log("Add erosivity to existing production...")
            TSSP_ero_ext = CalcErosivity(defEro, TSSprod, pointsrc, URratio, Stream_Raster) 
            # TSSP_ero_ext.save(os.path.join(arcpy.env.scratchFolder,"EroExt"))
            
            # log("Checking for input BMPs in your area...")    
            all = arcpy.GetCount_management(BMPpts)
            # if all <= 1:
                # raise Exception("You must have more than one point to run this tool!")
            
            log("Looping through input BMPs...")  
            SetPIDs(BMPpts)            
            BMProws = arcpy.SearchCursor(BMPpts)
            counter = 0
            count = 1
            
            for BMProw in BMProws:
                
                BMP_FID = BMProw.getValue("PID") 
                
                log("  Processing point %s of %s..." % (count, all)) 
                
                bmp_type = BMProw.getValue(bmp_type_fld)
                bmp_Ex1yr = float(BMProw.getValue(bmp_Ex1yr_fld))
                bmp_Prop1yr = float(BMProw.getValue(bmp_Prop1yr_fld))
                log("  Found bmp type of %s, existing Q1 of %s, and proposed Q1 of %s for PID %s" % (bmp_type, bmp_Ex1yr, bmp_Prop1yr, BMP_FID))
                
                SinBMPpts = os.path.join(arcpy.env.scratchFolder, "SinBMPpts.shp")
                GetSubset(BMPpts, SinBMPpts, " \"%s\" = %s " % ("PID", BMP_FID))
                
                SingleBMP = os.path.join(arcpy.env.scratchFolder, "SingleBMP")
                log("  Convert this project to a raster mask...")
                arcpy.FeatureToRaster_conversion(os.path.join(arcpy.env.scratchFolder,SinBMPpts), "PID", SingleBMP, flowdir)
                SinBMPmask = Reclassify(SingleBMP, "VALUE", "NoData 0; 0.001 100000 1", "DATA")
                SinBMPmask.save(os.path.join(arcpy.env.scratchFolder,"SinBMPmask"))
                
                # K = os.path.join(arcpy.env.scratchFolder, "K" + pn)    
                sum, chanp_red, washoff_red = 0, 0, 0
                
                bmp_eeff = float(BMProw.getValue(bmp_eeff_fld))
                bmp_peff = float(BMProw.getValue(bmp_peff_fld))
                stream_red_per_ft = float(BMProw.getValue(streamLinearRed_fld)) 
                log("  Found existing bmp efficiency of %s, proposed bmp efficiency of %s, and stream reduction of %s for PID %s" % (bmp_eeff, bmp_peff, stream_red_per_ft, BMP_FID))
                
                if bmp_type.lower() in ['bmp', 'new bmp']:
                    if bmp_Prop1yr < bmp_Ex1yr:
                        Channel_Prot = 1
                    else:
                        Channel_Prot = 0
                        
                    if not defEro:
                        log("   No Default erosivity for this BMP")
                        Channel_Prot = 0
                    
                    if not Channel_Prot:
                        log("   No Channel Protection from this BMP")
                    else:
                        
                        log("   Calculating Channel Protection from this BMP")
                        ModCumDa, thisBMPras, this_ds = ChannelProtection(Basin, SinBMPpts, bmp_Prop1yr_fld, flowdir, Cum_da, Cumulative_Impervious) 
                        # ModCumDa.save(os.path.join(arcpy.env.scratchFolder,"modcumda"))
                        this_ds.save(os.path.join(arcpy.env.scratchFolder,"this_ds"))
                        
                        log("  Calculate Future Urban/Rural ratio...")
                        URratio = this_ds / Rural_1yrQ
                        URratio.save(os.path.join(arcpy.env.scratchFolder,"urratio"))
                        
                        TSSP_ero = CalcErosivity(defEro, TSSprod, pointsrc, URratio, Stream_Raster)
                        # TSSP_ero.save(os.path.join(arcpy.env.scratchFolder,"tssp_ero"))
                        
                        log("  %s reduction..." % pn)
                        TSSred = TSSP_ero_ext - TSSP_ero
                        # TSSred.save(os.path.join(arcpy.env.scratchFolder,"tssred.tif"))
                        
                        log("  Tabulating %s reduction..." % pn)
                        chanp_red = Zonal(TSSred)
                        
                        log( "    %s Reduction component from Channel protection = %s\n" % (pn, chanp_red) )
                                
                    if bmp_peff > bmp_eeff:
                        WQ_benefit = 1
                    else: 
                        WQ_benefit = 0
                        
                    if not WQ_benefit:
                        log("  No Water Quality Benefit from this BMP")
                    else:
                        log("  Calculating Water Quality Benefit from this BMP")
                        REMBMPpts = os.path.join(arcpy.env.scratchFolder,"RemBMPpts.shp")
                        GetSubset(BMPpts, REMBMPpts, " \"%s\" <> %s AND %s > 0" % ("PID", BMP_FID, bmp_eeff_fld))
                        
                        log("   Adding erosivity to %s production..." % pn)
                        REMBMPs = (os.path.join(arcpy.env.scratchFolder, "REMBMPs"))
                        log("    Convert all other BMPs to Raster...")
                        arcpy.FeatureToRaster_conversion(REMBMPpts, bmp_eeff_fld, REMBMPs, flowdir)
                        BMPs = RemoveNulls(REMBMPs)
                        wtredBMPs =  ExtractByMask(BMPs / 100.0,  arcpy.env.mask)
                        wtredBMPs.save( os.path.join(arcpy.env.scratchFolder,"wtredBMPs"))
                         
                        counter +=1
                        TSSLoad = BMP2DA(flowdir, pn+str(counter), TSSP_ero_ext, wtredBMPs)
                                          
                        log("    %s reduction..." % pn)
                        TSSLoadpt = TSSLoad * (bmp_peff - bmp_eeff) * SinBMPmask / 100
                        TSSLoadpt.save( os.path.join(arcpy.env.scratchFolder,"TSSLoadpt"))
                        
                        log("    Tabulating %s reduction..." % pn)
                        washoff_red = Zonal(TSSLoadpt)                    
                        log( "    %s Reduction component from Washoff benefit = %s\n" % (pn, washoff_red) )
                        WQ = washoff_red
                        
                    sum = chanp_red + washoff_red
                    SetAtt(BMP_FID, pn[:4] + "red", sum, bmp_noclip)
                
                if bmp_type.lower() in ['stream restoration']: 
                    log("Convert Stream Lengths to Raster...")
                    arcpy.FeatureToRaster_conversion(os.path.join(arcpy.env.scratchFolder, "SinBMPpts.shp"), StreamLength_fld, "len", flowdir)
                    slengths = Float(Raster("len"))
                    
                    thisstream = AttExtract(slengths, flowdir, Stream_Raster, "thisstream")
                    
                    log("Make mask...")
                    ThisBMPmask = Reclassify(thisstream, "Value", ".00001 100000 1;-100000 0 0; NoData 0", "DATA")
                    ThisBMPmask.save(os.path.join(arcpy.env.scratchFolder,"ThisBMPmask"))
                    
                    log("Calculate reduction...")
                    streamprod = (bmp_peff/ 100) * TSSprod * ThisBMPmask * Power(URratio, 1.5)
                    streamprod.save(os.path.join(arcpy.env.scratchFolder,"streamprod"))
                    
                    log("Reclassify flowdirection to find straight paths...")
                    Flowdirs = Reclassify(flowdir, "VALUE", "1 1;2 0;4 1;8 0;16 1;32 0;64 1;128 0", "DATA")
                        
                    log("Reclassify flowdirection to find diagonal paths...")
                    Flowdird = Reclassify(flowdir, "VALUE", "1 0;2 1;4 0;8 1;16 0;32 1;64 0;128 1", "DATA")
                        
                    log("Calculate distance grid...")
                    Dist = (Flowdirs + Flowdird * 1.4142) * Units
                    g
                    log("Calculate length")
                    thislen = Dist * ThisBMPmask
                    dist_red = Zonal(thislen) * stream_red_per_ft
                    
                    log("Summarize Stream reduction from point...")
                    stream_red = Zonal(streamprod) + dist_red
                    
                    log( "  Stream reduction = %s" % stream_red )
                    
                    log("Writing attributes")
                    SetAtt(BMP_FID, pn[:4] + "red", stream_red, bmp_noclip)
            
                count += 1   
            
            tool.close(self)
            
        except:       
            i, j, k = sys.exc_info()
            EH(i, j, k)    