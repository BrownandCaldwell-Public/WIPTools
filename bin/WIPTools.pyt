import arcpy
from arcpy.sa import *
import sys, os, time, traceback
import numpy

logfname   = __file__+".log"
    
def CalcErosivity(DefEro, TSSprod, pointSrcRaster, URratio, Streams_rc):
    
    if type(pointSrcRaster) == Raster:
        pointsrc = True
    else:
        pointsrc = False
    
    log("Adding erosivity (%s and %s)..." % ((DefEro != 0), pointsrc))
    if DefEro and not pointsrc:
        output = ( Streams_rc * Power(URratio, 1.5 ) + BooleanNot( Streams_rc)) * TSSprod 
    elif not DefEro and pointsrc:
        output = TSSprod + pointSrcRaster
    elif not DefEro and not pointsrc:
        output = TSSprod 
    else: 
        output = (( Streams_rc * Power( URratio, 1.5 ) + BooleanNot( Streams_rc)) * TSSprod  ) + pointSrcRaster
    return output
    
def log(message):
    ''' Logging function that write to the log file, and ArcGIS geoprocessor messages'''
    # if not message.startswith("  "):
        # message = " Step %s: %s" % (Step(), message)
    message = str(message)
    if arcpy: arcpy.AddMessage(message)
    with file(logfname, 'a') as logfile:
        logfile.write(message+"\n")
    
def GetBasin():
    try:
        bf = open("Basin.dat", "r")
        Basin = bf.readline().strip()
        bf.close()
        return Basin
    except Exception, e:
        raise e

def EH(i, j, k):
    data = traceback.format_exception(i,j,k)
    for l in data:
        log("\t" + l.strip())
        # arcpy.AddError(l)
        
    # arcpy.AddError("*"*50+'''\nExtended error output has been recorded in the log file''')
    raise Exception(arcpy.GetMessages())
     
def BMP2DA(flowdir, outputname=None, weightsInput=None, bmpsInput=None):
    import bmpFlowModFast
    log("\tRunning BMP2DA...")
    
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
            raise Exception("Input weight raster (%s) is not the same size (%s) as flow direction raster size (%s)" % (bmpsInput.catalogPath, nbmppts.size, nflowdir.size))
    else:
        nbmppts = None
        
    arr = bmpFlowModFast.flowAccumulate(nflowdir, nweight, nbmppts)

    newRaster = arcpy.NumPyArrayToRaster(arr, lowerLeft, cellSize, value_to_nodata=0)
    if outputname != None:
        newRaster.save(os.path.join(arcpy.env.scratchFolder, outputname))
        # log("\tOutput: " + os.path.join(arcpy.env.scratchFolder, outputname))
        # stats = arr.flatten()
        # log("\t\tMax: %s Min: %s Avg: %s Med: %s Std: %s Var: %s" % (numpy.amax(stats), numpy.amin(stats), numpy.average(stats), numpy.median(stats), numpy.std(stats), numpy.var(stats)))
    log( "\tBMP2DA took %6.2f seconds" % (time.time()-start) )
    
    return newRaster

def AttExtract(streamInvPts, flowdir, streams, outputname=None, cellsize=None):
    import AttributeExtract
    log("\tRunning AttExtract...")
    
    lowerLeft = arcpy.Point(flowdir.extent.XMin,flowdir.extent.YMin)
    cellSize = flowdir.meanCellWidth

    start = time.time()
    nStreamInv = arcpy.RasterToNumPyArray(streamInvPts, nodata_to_value=-1).astype(numpy.double)
    nflowdir = arcpy.RasterToNumPyArray(flowdir, nodata_to_value=0).astype(numpy.int)
    nStream  = arcpy.RasterToNumPyArray(streams, nodata_to_value=0).astype(numpy.int)
    if not cellsize: cellsize = 0
    
    
    arr = AttributeExtract.extractAlongStream(nStreamInv, nflowdir, nStream, cellsize)

    newRaster = arcpy.NumPyArrayToRaster(arr, lowerLeft, cellSize, value_to_nodata=0)
    if outputname != None:
        newRaster.save(outputname)
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
    LoadTable = os.path.join(self.arcpy.env.scratchFolder, 'load.dbf')
    
    outZSaT  = ZonalStatisticsAsTable(self.Mask, "Value", raster, LoadTable, "DATA")
    rows = arcpy.UpdateCursor(LoadTable)
    computation = rows.next().getValue(stat)
    
    return computation
    
def SetAtt(PID, att, val, lyr, alias=None):
    # log("\t\tPID: %s\n\t\tAttribute: %s\n\t\tValue: %s\n\t\tLayer: %s" % (PID, att, val, lyr) )
    
    if not alias: alias = att
    
    if not att in ListofFields(lyr):
        log( "\tAdding field: %s (%s)" % (att, alias) )
        arcpy.AddField_management(lyr, att, "DOUBLE", "", "", "", alias, "NULLABLE", "NON_REQUIRED", "")
        
    rows = arcpy.UpdateCursor(lyr)
    
    for row in rows:
        if row.getValue('PID') == PID:
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
    newname = os.path.join(arcpy.env.scratchFolder, outputname+".tif")
    i = 1
    while os.path.exists(newname):
        newname = os.path.join(arcpy.env.scratchFolder, outputname+str(i)+".tif")
        i+=1
    return newname
    
def SetPIDs(vec):
    if ".mdb" in vec:
        OID = "OBJECTID"
    else:
        OID = "FID"
        

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
    arcpy.SelectLayerByAttribute_management('subset', "NEW_SELECTION", query)
    arcpy.CopyFeatures_management('subset', output)
    count = int(arcpy.GetCount_management(output).getOutput(0))
    log("  %s, found %s" % (query, count))
    return count

def ruralQcp(Basin, cum_da):
    if Basin == 'SC Piedmont':
         return ( Power( ( cum_da / 640 ) , 0.649 ) ) * (158 * 0.875)
    if Basin == 'SC Blue Ridge':
         return ( Power( ( cum_da / 640 ) , 0.779 ) ) * (110 * 0.875)
    if Basin == 'SC Sand Hills':
         return ( Power( ( cum_da / 640 ) , 0.758 ) ) * (25.7 * 0.875)
    if Basin == 'SC Coastal':
         return ( Power( ( cum_da / 640 ) , 0.649 ) ) * (60.3 * 0.875)
    if Basin == 'Chattahoochee  GA (Rural and Urban)':
         return ( Power( ( cum_da / 640 ) , 0.654 ) ) * 181
    if Basin == 'Altamaha GA (Rural and Urban)':
         return ( Power( ( cum_da / 640 ) , 0.622 ) ) * 159
    if Basin == 'Region 1  2006 (Rural) - Blue Ridge NC 2002 (Urban)':
         return ( Power( ( cum_da / 640 ) , 0.649 ) ) * 135.4
    if Basin == 'Blue Ridge Piedmont  NC 2002 (Rural and Urban)':
         return ( Power( ( cum_da / 640 ) , 0.702 ) ) * 115.7
    if Basin == 'Georgia Region 1':
         return ( Power( ( cum_da / 640 ) , 0.649 ) ) * 138.25
    
def rural2yrQ(Basin, cum_da):
    if Basin == 'SC Piedmont':
                return ( Power( ( cum_da / 640 ) , 0.649 ) ) * 158
    if Basin == 'SC Blue Ridge':
         return ( Power( ( cum_da / 640 ) , 0.779 ) ) * 110
    if Basin == 'SC Sand Hills':
         return ( Power( ( cum_da / 640 ) , 0.758 ) ) * 25.7
    if Basin == 'SC Coastal':
         return ( Power( ( cum_da / 640 ) , 0.649 ) ) * 60.3

def rural5yrQ(Basin, cum_da):
    if Basin == 'SC Piedmont':
         return ( Power( ( cum_da / 640 ) , 0.627 ) ) * 295
    if Basin == 'SC Blue Ridge':
         return ( Power( ( cum_da / 640 ) , 0.747 ) ) * 209
    if Basin == 'SC Sand Hills':
         return ( Power( ( cum_da / 640 ) , 0.744) ) * 44.7
    if Basin == 'SC Coastal':
         return ( Power( ( cum_da / 640 ) , 0.627) ) * 1233
    
def rural10yrQ(Basin, cum_da):
    if Basin == 'SC Piedmont':
         return ( Power( ( cum_da / 640 ) , 0.617 ) ) * 398
    if Basin == 'SC Blue Ridge':
         return ( Power( ( cum_da / 640 ) , 0.736 ) ) * 288
    if Basin == 'SC Sand Hills':
         return ( Power( ( cum_da / 640 ) , 0.74 ) ) * 58.9
    if Basin == 'SC Coastal':
         return ( Power( ( cum_da / 640 ) , 0.617 ) ) * 174
    
def rural25yrQ(Basin, cum_da):
    if Basin == 'SC Piedmont':
         return ( Power( ( cum_da / 640 ) , 0.606 ) ) * 537
    if Basin == 'SC Blue Ridge':
         return ( Power( ( cum_da / 640 ) , 0.724 ) ) * 398
    if Basin == 'SC Sand Hills':
         return ( Power( ( cum_da / 640 ) , 0.736 ) ) * 77.6
    if Basin == 'SC Coastal':
         return ( Power( ( cum_da / 640 ) , 0.606 ) ) * 245
         
def urbanQcp(cum_da, impcov, Basin='Region 1  2006 (Rural) - Blue Ridge NC 2002 (Urban)'):
    if Basin == 'SC Piedmont':
        return (Power( ( cum_da / 640 ) , 0.554 ) * (1.36 * 0.875)) * ( Power( impcov, 1.241 )) * ( Power( rural2yrQ(Basin,cum_da), 0.323))
    if Basin == 'SC Blue Ridge':
        return (Power( ( cum_da / 640 ) , 0.554 ) * (1.36 * 0.875)) * ( Power( impcov, 1.241 )) * ( Power( rural2yrQ(Basin,cum_da), 0.323))      
    if Basin == 'SC Sand Hills':
        return (Power( ( cum_da / 640 ) , 0.554 ) * (1.36 * 0.875)) * ( Power( impcov, 1.241 )) * ( Power( rural2yrQ(Basin,cum_da), 0.323))      
    if Basin == 'SC Coastal':
        return (Power( ( cum_da / 640 ) , 0.554 ) * (1.36 * 0.875)) * ( Power( impcov, 1.241 )) * ( Power( rural2yrQ(Basin,cum_da), 0.323))
    if Basin == 'Chattahoochee  GA (Rural and Urban)':
         return ( Power( ( cum_da / 640 ), 0.73 ) ) * ( Power( impcov, 0.31 ) ) * 146
    if Basin == 'Altamaha GA (Rural and Urban)':
         return ( Power( ( cum_da / 640 ), 0.7 ) ) * ( Power( impcov, 0.31 ) ) * 127
    if Basin == 'Region 1  2006 (Rural) - Blue Ridge NC 2002 (Urban)':
         return ( Power( ( cum_da / 640 ), 0.739 ) ) * ( Power( impcov, 0.686 ) ) * 28.5
    if Basin == 'Blue Ridge Piedmont  NC 2002 (Rural and Urban)':
         return ( Power( ( cum_da / 640 ), 0.739 ) ) * ( Power( impcov, 0.686 ) ) * 28.5
    if Basin == 'Georgia Region 1':
         return ((190 * 0.875) * Power( ( cum_da / 640 ), 0.751 ) )  * ( Power( 10 , ( 0.0116 * impcov ) ) )

def urban2yrQ(Basin, cum_da, impcov):
    if Basin == 'SC Piedmont':
        return (Power( ( cum_da / 640 ) , 0.554 ) * 1.36 ) * ( Power( impcov, 1.241 )) * ( Power( rural2yrQ(Basin,cum_da), 0.323))
    if Basin == 'SC Blue Ridge':
         return (Power( ( cum_da / 640 ) , 0.554 ) * 1.36 ) * ( Power( impcov, 1.241 )) * ( Power( rural2yrQ(Basin,cum_da), 0.323))      
    if Basin == 'SC Sand Hills':
         return (Power( ( cum_da / 640 ) , 0.554 ) * 1.36 ) * ( Power( impcov, 1.241 )) * ( Power( rural2yrQ(Basin,cum_da), 0.323))      
    if Basin == 'SC Coastal':
         return (Power( ( cum_da / 640 ) , 0.554 ) * 1.36 ) * ( Power( impcov, 1.241 )) * ( Power( rural2yrQ(Basin,cum_da), 0.323))
    if Basin == 'Chattahoochee  GA (Rural and Urban)':
         return ( Power( ( cum_da / 640 ) , 0.73 ) ) * ( Power( impcov, 0.31 ) ) * 167
    if Basin == 'Altamaha GA (Rural and Urban)':
         return ( Power( ( cum_da / 640 ) , 0.7 ) ) * ( Power( impcov, 0.31 ) ) * 145
    if Basin == 'Region 1  2006 (Rural) - Blue Ridge NC 2002 (Urban)':
         return ( Power( ( cum_da / 640 ) , 0.739 ) ) * ( Power( impcov, 0.686 ) ) * 33.3
    if Basin == 'Blue Ridge Piedmont  NC 2002 (Rural and Urban)':
         return ( Power( ( cum_da / 640 ) , 0.739 ) ) * ( Power( impcov, 0.686 ) ) * 33.3
    if Basin == 'Georgia Region 1':
         return (190* Power( ( cum_da / 640 ), 0.751 ) )  * ( Power( 10 , ( 0.0116 * impcov ) ) )

def urban5yrQ(Basin, cum_da, impcov):
    if Basin == 'SC Piedmont':
        return (Power( ( cum_da / 640 ) , 0.554 ) * 2.58) * ( Power( impcov, 1.17 )) * ( Power( rural5yrQ(Basin,cum_da), 0.299))
    if Basin == 'SC Blue Ridge':
        return (Power( ( cum_da / 640 ) , 0.554 ) * 2.58) * ( Power( impcov, 1.17 )) * ( Power( rural5yrQ(Basin,cum_da), 0.299))        
    if Basin == 'SC Sand Hills':
        return (Power( ( cum_da / 640 ) , 0.554 ) * 2.58) * ( Power( impcov, 1.17 )) * ( Power( rural5yrQ(Basin,cum_da), 0.299))    
    if Basin == 'SC Coastal':
        return (Power( ( cum_da / 640 ) , 0.554 ) * 2.58) * ( Power( impcov, 1.17 )) * ( Power( rural5yrQ(Basin,cum_da), 0.299))   

def urban10yrQ(Basin, cum_da, impcov):
    if Basin == 'SC Piedmont':
        return (Power( ( cum_da / 640 ) , 0.536 ) * 3.77) * ( Power( impcov, 1.115 )) * ( Power( rural10yrQ(Basin,cum_da), 0.291))
    if Basin == 'SC Blue Ridge':
        return (Power( ( cum_da / 640 ) , 0.536 ) * 3.77) * ( Power( impcov, 1.115 )) * ( Power( rural10yrQ(Basin,cum_da), 0.291))       
    if Basin == 'SC Sand Hills':
        return (Power( ( cum_da / 640 ) , 0.536 ) * 3.77) * ( Power( impcov, 1.115 )) * ( Power( rural10yrQ(Basin,cum_da), 0.291))  
    if Basin == 'SC Coastal':
        return (Power( ( cum_da / 640 ) , 0.536 ) * 3.77) * ( Power( impcov, 1.115 )) * ( Power( rural10yrQ(Basin,cum_da), 0.291))
    if Basin == 'Chattahoochee  GA (Rural and Urban)':
         return ( Power( ( cum_da / 640 ) , 0.7 ) ) * ( Power( impcov, 0.21) ) * 405
    if Basin == 'Altamaha GA (Rural and Urban)':
         return ( Power( ( cum_da / 640 ) , 0.7 ) ) * ( Power( impcov, 0.21 ) ) * 351 
    if Basin == 'Region 1  2006 (Rural) - Blue Ridge NC 2002 (Urban)':
         return ( Power( ( cum_da / 640 ) , 0.655 ) ) * ( Power( impcov, 0.515 ) ) * 122
    if Basin == 'Blue Ridge Piedmont  NC 2002 (Rural and Urban)':
         return ( Power( ( cum_da / 640 ) , 0.655 ) ) * ( Power( impcov, 0.515 ) ) * 122
    if Basin == 'Georgia Region 1':
         return (399 * Power( ( cum_da / 640 ), 0.767 ) )  * ( Power( 10 , ( 0.0071 * impcov ) ) )
    
def urban25yrQ(Basin, cum_da, impcov):
    if Basin == 'SC Piedmont':
        return (Power( ( cum_da / 640 ) , 0.524 ) * 5.84) * ( Power( impcov, 1.041 )) * ( Power( rural25yrQ(Basin,cum_da), 0.284))
    if Basin == 'SC Blue Ridge':
        return (Power( ( cum_da / 640 ) , 0.524 ) * 5.84) * ( Power( impcov, 1.041 )) * ( Power( rural25yrQ(Basin,cum_da), 0.284))       
    if Basin == 'SC Sand Hills':
         return (Power( ( cum_da / 640 ) , 0.524 ) * 5.84) * ( Power( impcov, 1.041 )) * ( Power( rural25yrQ(Basin,cum_da), 0.284))  
    if Basin == 'SC Coastal':
         return (Power( ( cum_da / 640 ) , 0.524 ) * 5.84) * ( Power( impcov, 1.041 )) * ( Power( rural25yrQ(Basin,cum_da), 0.284))
    if Basin == 'Chattahoochee  GA (Rural and Urban)':
         return ( Power( ( cum_da / 640 ) , 0.7 ) ) * ( Power( impcov, 0.2 ) ) * 527 
    if Basin == 'Altamaha GA (Rural and Urban)':
          return ( Power( ( cum_da / 640 ) , 0.7 ) ) * ( Power( impcov, 0.2 ) ) * 452 
    if Basin == 'Region 1  2006 (Rural) - Blue Ridge NC 2002 (Urban)':
         return ( Power( ( cum_da / 640 ) , 0.611 ) ) * ( Power( impcov, 0.436 ) ) * 228 
    if Basin == 'Blue Ridge Piedmont  NC 2002 (Rural and Urban)':
         return ( Power( ( cum_da / 640 ) , 0.611 ) ) * ( Power( impcov, 0.436 ) ) * 228
    if Basin == 'Georgia Region 1':
         return (526 * Power( ( cum_da / 640 ), 0.773 ) )  * ( Power( 10 , ( 0.00539 * impcov ) ) )

def ChannelProtection(BMP_pts, fld):
        # Flow reduction calcs

        flowdir = ExtractByMask(Raster(os.path.join(hp.Workspace + "\\WIPoutput.mdb", "flowdir")), arcpy.env.mask )
        Cum_da = Raster(os.path.join(hp.Workspace + "\\WIPoutput.mdb", "cumda"))
        Cumulative_Impervious = Raster(os.path.join(hp.Workspace + "\\WIPoutput.mdb", "cumimpcovlake"))
        flowdir.save(os.path.join(arcpy.env.scratchFolder, "flowdir")) 

        arcpy.CopyRaster_management (os.path.join(hp.Workspace + "\\WIPoutput.mdb", "mask"), os.path.join(arcpy.env.scratchFolder, "mask"))
        mask = Raster(os.path.join(arcpy.env.scratchFolder, "mask"))

        log("Convert Single BMP Project to Raster...")
        RasBMPpts = hp.GetTempRasterPath("RasBMPpts")
        arcpy.FeatureToRaster_conversion(BMP_pts, fld, RasBMPpts, flowdir)
        thisBMPras = Raster(RasBMPpts)

        if hp.Basin == 'Georgia Region 1':
                Mod_da = 640 * Power( ( thisBMPras / ((190 * 0.875) * Power( 10,(Cumulative_Impervious * 0.0116 )) )), ( 1 / 0.751) )
        elif hp.Basin == 'Chattahoochee  GA (Rural and Urban)':
                Mod_da = 640 * Power( ( thisBMPras / ( 146 * Power( Cumulative_Impervious, 0.31 ) ) ), ( 1 / 0.73 ) )
        elif hp.Basin == 'Altamaha GA (Rural and Urban)':
                Mod_da = 640 * Power( ( thisBMPras / ( 127 * Power( Cumulative_Impervious, 0.31 ) ) ), ( 1 / 0.7 ) )
        elif hp.Basin in ['Region 1  2006 (Rural) - Blue Ridge NC 2002 (Urban)', 'Blue Ridge Piedmont  NC 2002 (Rural and Urban)']:
                Mod_da = 640 * Power( ( thisBMPras / ( 28.5 * Power( Cumulative_Impervious, 0.686 ) ) ), ( 1 / 0.739 ) )
                
##             for below use inverse of: (Power( ( cum_da / 640 ) , 0.554 ) * (1.36 * 0.875)) * ( Power( impcov, 1.241 )) * ( Power( rural2yrQ(Basin,cum_da), 0.323))

        elif hp.Basin in ['SC Piedmont', 'SC Blue Ridge', 'SC Sand Hills' 'SC Coastal']:
                Mod_da = 640 * Power( ( thisBMPras / ( ( (1.36 * 0.875) * Power( rural2yrQ(hp.Basin,Cum_da), 0.323) ) * Power( Cumulative_Impervious, 1.241 ) ) ), ( 1 / 0.554 ) )

        else: raise Exception("Unknown basin: " + hp.Basin)
                

        log("Convert to percent reduction in accumulation...")
        acc_red = ExtractByMask(1 - ( Mod_da / Cum_da), mask)
        acc_red.save(os.path.join(arcpy.env.scratchFolder,"acc_red_cp"))

        ModCumDa_u = hp.BMP2DA(flowdir, "ModCumDa_asc", mask, acc_red)

        log("Convert units...")
        conv = hp.units['cellsqft'] / 43560
        ModCumDa = ModCumDa_u * conv
    
        log("Calculating urbanQcp...")
        uQcp = urbanQcp(ModCumDa, Cumulative_Impervious)

        return ModCumDa, thisBMPras, uQcp
        
class Toolbox(object):
    def __init__(self):
        self.label = "WIP Tools"
        self.alias = "WIP Tools"
        # self.tools = [Baseline, CIP]
        self.tools = [TopoHydro, ImpCov, Runoff, ProdTrans, Baseline, CIP]
        if arcpy.env.scratchWorkspace == "" or arcpy.env.scratchWorkspace.endswith('Default.gdb'):
            arcpy.env.scratchWorkspace = os.path.split(arcpy.env.workspace)[0]

class TopoHydro(object):
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
        
        parameters += [arcpy.Parameter(
        displayName="Flow Accumulation",
        name="flowacc",
        datatype="DERasterDataset",
        parameterType="Derived",
        direction="Output")]
        parameters[-1].value = os.path.join(arcpy.env.workspace,"Flow_acc")
        
        parameters += [arcpy.Parameter(
        displayName="Cumulative Drainage Area",
        name="cumda",
        datatype="DERasterDataset",
        parameterType="Derived",
        direction="Output")]
        parameters[-1].value = os.path.join(arcpy.env.workspace,"Cumda")
        
        parameters += [arcpy.Parameter(
        displayName="Streams",
        name="output streams",
        datatype="DERasterDataset",
        parameterType="Derived",
        direction="Output")]
        parameters[-1].value = os.path.join(arcpy.env.workspace,"Streams")
        
        return parameters

    def updateParameters(self, parameters):
        return

    def execute(self, parameters, messages):
        try:
              
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
            CumDA = Flow_Acc * cellSize / 43560
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

        except:       
            i, j, k = sys.exc_info()
            EH(i, j, k)
            
class ImpCov(object):
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
        
        parameters += [arcpy.Parameter(
        displayName="Cumulative Impervious Cover",
        name="cumimpcov",
        datatype="DERasterDataset",
        parameterType="Derived",
        direction="Output")]
        parameters[-1].value = os.path.join(arcpy.env.workspace,"cumimpcov")
        
        parameters += [arcpy.Parameter(
        displayName="Cumulative Impervious Cover with Lakes",
        name="cumimpcovlakes",
        datatype="DERasterDataset",
        parameterType="Derived",
        direction="Output")]
        parameters[-1].value = os.path.join(arcpy.env.workspace,"cumimpcovlakes")
        
        parameters += [arcpy.Parameter(
        displayName="Cumulative Impervious Vector",
        name="cumimpcovvec",
        datatype="DEFeatureDataset",
        parameterType="Derived",
        direction="Output")]
        parameters[-1].value = os.path.join(arcpy.env.workspace,"cumimpcovvec")
        
        parameters += [arcpy.Parameter(
        displayName="Raster Lakes",
        name="lakes",
        datatype="DERasterDataset",
        parameterType="Derived",
        direction="Output")]
        parameters[-1].value = os.path.join(arcpy.env.workspace,"lakes")
        
        return parameters

    def updateParameters(self, parameters):
        return

    def execute(self, parameters, messages):
        try:
            
            # Script arguments...
            Impervious_Polygons_Vector_preclip = parameters[0].valueAsText
            Lakes_Polygon_Vector_preclip = parameters[1].valueAsText
            Flow_Direction_Raster = Raster(parameters[2].valueAsText)
            Flow_Accumulation = Raster(parameters[3].valueAsText)
            Cum_da = Raster(parameters[4].valueAsText)
            Streams = Raster(parameters[5].valueAsText)
            impcovPath = parameters[6].valueAsText
            cumimpcovPath = parameters[7].valueAsText
            cumimpcovlakesPath = parameters[8].valueAsText
            vector = parameters[9].valueAsText
            lakesPath = parameters[10].valueAsText
            
            # Cum_da = os.path.join(hp.Workspace, "cumda")
            # Streams = os.path.join(hp.Workspace + "\\WIPoutput.mdb", "streams")
            # Lakes_Polygon_Vector_preclip = sys.argv[2]
            # Impervious_Polygons_Vector_preclip = sys.argv[1]
            
            # Local variables...
            # Flow_Accumulation = os.path.join(hp.Workspace + "\\WIPoutput.mdb", "flowacc")
            Impervious_Cover_pc = os.path.join(arcpy.env.scratchFolder, "impcovpc")
            # demximp = os.path.join(hp.Workspace, "demximp")
            
            # Flow_Direction_Raster = os.path.join(hp.Workspace + "\\WIPoutput.mdb", "flowdir")* arcpy.env.mask 
            # Flow_Direction_Raster.save(os.path.join(arcpy.env.scratchFolder, "flowdir")) 
            
            # cellSize = hp.units['cellsqft']**0.5
        ##    arcpy.env.cellSize = "MINOF"
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
                raise Exception, "No impervious areas in the study area"
            count = int(arcpy.GetCount_management(Lakes_Polygon_Vector).getOutput(0))
            if count < 1:
                raise Exception, "No lakes in the study area"
            
            log("Converting impervious polygons to raster...")
            impid = 'NewId'
            AddID(Impervious_Polygons_Vector, impid)
            Feature_Impe1 = os.path.join(arcpy.env.scratchFolder,"Feature_Impe1")
            arcpy.PolygonToRaster_conversion(Impervious_Polygons_Vector, impid, (os.path.join(arcpy.env.scratchFolder,"Feature_Impe1")),"MAXIMUM_AREA","None", float(cellSize)/10)
            
            
            log("Reclassifying impervious raster...")
            Reclass_Feat1 = RemoveNulls(Feature_Impe1)
            # Reclass_Feat1.save(os.path.join(arcpy.env.scratchFolder,"Reclass_Feat1"))
            
            # Mask = os.path.join(hp.Workspace+ "\\WIPoutput.mdb","Mask")
            
            # arcpy.env.extent = Mask
            log("Computing block statistics...")
            BlockSt_Recl1 = BlockStatistics(Reclass_Feat1, NbrRectangle(10, 10, "CELL"), "SUM", "DATA")
        ##    BlockSt_Recl1.save(os.path.join(arcpy.env.scratchFolder,"BlockSt_Recl1"))
            
            log("Aggregate...")
            Imp_Cover_pc = Aggregate(BlockSt_Recl1,10, "MEAN", "EXPAND", "DATA")
            Imp_Cover = ExtractByMask(Imp_Cover_pc, arcpy.env.mask)
            
        ##    Imp_Cover_pc = arcpy.env.mask * Imp_Cover  ## DOES NOT WORK
            Imp_Cover.save(impcovPath)
            
            Flow_Accumulation_weighted = BMP2DA(Flow_Direction_Raster,"flow_accw.tif", Imp_Cover)
            
            # hp.saveRasterOutput(Imp_Cover, "Impcov")
            
        ##    if os.path.exists(demximp):
        ##        demximp_clip = demximp*arcpy.env.mask
        ##        args = '"%s" "%s" "%s"' % (Flow_Direction_Raster, demximp_asc, demximp_clip.catalogPath)
        ##        hp.RunScript("BMP2DA", args)
        ##
        ##        demximp_extr = Raster(demximp_asc)
        ##    else:
            demximp_extr = 0
                
            log("Divide...")
            cumimpcov=arcpy.env.mask * (Flow_Accumulation_weighted + demximp_extr ) / Flow_Accumulation
            # hp.saveRasterOutput(cumimpcov, "cumimpcov")
            cumimpcov.save(cumimpcovPath)
            
            log("Clip output to streams...")
            Clipped_ = Int(RoundUp(RoundDown(cumimpcov * Streams * 20000 ) / 2))
            
            log("Vectorize...")
            # vector = os.path.join(hp.Workspace + "\\WIPoutput.mdb", "cumimpcovvec")
            StreamToFeature(Clipped_, Flow_Direction_Raster, vector, "NO_SIMPLIFY")
            # hp.models[hp.current_tool]["output"].append(vector)
            
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
            cumimpcovlake = Flow_Accumulation_lakes/Flow_Accumulation
            cumimpcovlake.save(cumimpcovlakesPath)
                
            # hp.Close()

        except:       
            i, j, k = sys.exc_info()
            EH(i, j, k)
            
class Runoff(object):
    def __init__(self):
        self.label = "Runoff"
        self.description = "Runoff"

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
        displayName="Storm Recurrance Intervals",
        name="pdepth",
        datatype="GPValueTable",
        parameterType="Required",
        direction="Input")]
        parameters[-1].columns = [['String', 'Storm'], ['Double', 'Rain depth']]
        parameters[-1].filters[0].type = "ValueList"
        parameters[-1].filters[0].list = ['Channel Protection', '1yr', '2yr', '5yr', '10yr', '25yr']
        
        parameters += [arcpy.Parameter(
        displayName="Soils CN Table (LUT.csv)",
        name="lut",
        datatype=["DETable","GPTableView"],
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
        displayName="Cumulative Impervious Cover with Lakes",
        name="cumimpcovlake",
        datatype="DERasterDataset",
        parameterType="Required",
        direction="Input")]
        parameters[-1].value = os.path.join(arcpy.env.workspace,"cumimpcovlake")
        
        parameters += [arcpy.Parameter(
        displayName="Output Flood Storage",
        name="outputvols",
        datatype="DERasterDataset",
        parameterType="Derived",
        direction="Output")]
        
        parameters += [arcpy.Parameter(
        displayName="Output Undeveloped Discharge",
        name="undevq",
        datatype="DERasterDataset",
        parameterType="Derived",
        direction="Output")]
        parameters[-1].value = os.path.join(arcpy.env.workspace,"undevQ")
        
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
            Landuse = parameters[0].valueAsText
            LanduseAtt = parameters[1].valueAsText
            Soils = parameters[2].valueAsText
            SoilsAtt = parameters[3].valueAsText
            pname, pdepth = parameters[4].valueAsText.split(" ")
            lutFile = parameters[5].valueAsText
            flowdir = Raster(parameters[6].valueAsText)
            cum_da = Raster(parameters[7].valueAsText)
            flowacc = Raster(parameters[8].valueAsText)
            cumimpcovlake = Raster(parameters[9].valueAsText)
            volflood = parameters[10].valueAsText
            undevqPath = parameters[11].valueAsText
            
            Units = flowdir.meanCellWidth
             
            
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
            print LUcodes
            
            arcpy.AddField_management(os.path.join(arcpy.env.scratchFolder,"union.shp"), "CN", "LONG", "", "", "", "", "NON_NULLABLE", "NON_REQUIRED", "")
            rows = arcpy.UpdateCursor(os.path.join(arcpy.env.scratchFolder,"union.shp"))
            row = rows.next()
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
                row = rows.next()
            del row, rows
            
            # cum_da = Raster(os.path.join(hp.Workspace + "\\WIPoutput.mdb", "cumda"))
            
            log("Convert union to raster...")
            arcpy.PolygonToRaster_conversion(os.path.join(arcpy.env.scratchFolder,"union.shp"), "CN", os.path.join(arcpy.env.scratchFolder,"CurveN"),"MAXIMUM_AREA","None", cum_da)
            CurveN = Raster(os.path.join(arcpy.env.scratchFolder,"CurveN"))
            
            # log("Get precipitation contants for %s ..." % (hp.Basin))
            # f = open(os.path.join(hp.AppPath, r'../ToolData/Precipdepth.csv'), 'r')
                
            # header = f.readline().strip().replace('"', "").split(",")
            # pdepth = {}
            # for i in f.readlines():
                # data = i.strip().replace('"', "").split(',')
                # if hp.Basin in data[0]:
                    # for j in range(1, len(header)):
                        # pdepth[header[j]] = float(data[j])
            # f.close()
            
            # if not pdepth: raise ValueError, "Why is this empty?!"
            # else: print pdepth
            
            #   WQV ----------------------------------------------------------------------------------------------------------------------------------------------------------------------
            log("Volume Calc...")
            # flowacc = Raster(os.path.join(hp.Workspace + "\\WIPoutput.mdb", "flowacc"))
            Convraster = (cum_da * 43560)/12 
            # cumimpcovlake = Raster(os.path.join(hp.Workspace + "\\WIPoutput.mdb", "cumimpcovlake"))
            WQVin = ((cumimpcovlake * 0.009) + 0.05) * float(pdepth)#["WQdepth"]
            WQVin.save('vol'+pname)

            # log("WQ Vol Conv Calc...")

            
            WQV = WQVin * Convraster
            # hp.saveRasterOutput(WQV, "WQV") 
            # WQV.save(volflood)
            #~ CurveN = (((1000 / (16 + (10 * WQVin) - (10 * Power((Power(WQVin, 2)) + (1.25 * 1.2 * WQVin), 0.5)))) - 73.852036) / 25.632621) * 38 + 60
            
            #   1-yr ----------------------------------------------------------------------------------------------------------------------------------------------------------------------
            log("1-yr Vol Calc...")
            # should pull out precip value to tool data table...
            V1in = Power( ( float(pdepth) - 0.2 * (( 1000.00 / CurveN ) - 10) ), 2) / ( float(pdepth) + (0.8 * (( 1000.00 / CurveN ) - 10)))
            # V1in.save(os.path.join(arcpy.env.scratchFolder, "V1in"))
            
            log("1-yr Vol Conv...")
            V1ft = V1in * Units * Units / 12 * arcpy.env.mask
            
            log("Flow Accum...")
            vol1yr = BMP2DA(flowdir, "V1.tif", V1ft)
                
            chnnl_prot = arcpy.env.mask * vol1yr
            # hp.saveRasterOutput(chnnl_prot,"chnnlprot")

            ##   10-yr ----------------------------------------------------------------------------------------------------------------------------------------------------------------------
            # log("10yr Urban Vol Calc...")
            # _V10U = Power((pdepth["depth10yr"] - 0.2 * (( 1000.00 / CurveN ) - 10)) , 2) / (pdepth["depth10yr"] + (0.8 * (( 1000.00 / CurveN ) - 10)))
            
            # log("10yr Conv...")
            # V10Uft = _V10U * hp.units['cellsqft'] / 12 * arcpy.env.mask
            
            # log("Flow Accum...")
           
            # V10U = hp.BMP2DA(flowdir, "V10U", V10Uft)
            
            # log("10yr Rural Vol Calc...")
            # _V10R = (pdepth["depth10yr"] - 0.2 * (( 1000.00 / pdepth["baseCN"]) - 10))** 2 / (pdepth["depth10yr"] + (0.8 * (( 1000.00 / pdepth["baseCN"]) - 10)))
            
            # log("10yr Rural Vol Conv...")
            # V10Rft = _V10R * hp.units['cellsqft'] / 12 * arcpy.env.mask
            
            # log("Flow Accum...")
            # V10R = hp.BMP2DA(flowdir,"V10R", V10Rft)
            
            # log("10yr Flood storage...")
            # V10Flood = arcpy.env.mask * (V10U - V10R)
            # hp.saveRasterOutput(V10Flood, "V10Flood")
            
            # log("10yr Discharge...")
            # cumimpcov = Raster(os.path.join(hp.Workspace + "\\WIPoutput.mdb", "cumimpcov"))


            
            ##   25-yr ----------------------------------------------------------------------------------------------------------------------------------------------------------------------
            # log("25yr Urban Vol Calc...")
            # _V25U = Power((pdepth["depth25yr"] - 0.2 * (( 1000.00 / CurveN ) - 10)) , 2) / (pdepth["depth25yr"] + (0.8 * (( 1000.00 / CurveN ) - 10)))

            # log("25yr Conv...")
            # V25_U_ft= _V25U * hp.units['cellsqft'] / 12 * arcpy.env.mask
            
            # log("Flow Accum...")
            
            # V25U = hp.BMP2DA(flowdir, "V25U", V25_U_ft)
            
            # log("25yr Rural Vol Calc...")
            # _V25R = (pdepth["depth25yr"] - 0.2 * (( 1000.00 / pdepth["baseCN"]) - 10))** 2 / (pdepth["depth25yr"] + (0.8 * (( 1000.00 / pdepth["baseCN"]) - 10)))

            # log("25yr Rural Vol Conv...")
            # V25_R_ft = _V25R * hp.units['cellsqft'] / 12 * arcpy.env.mask
            
            # log("Flow Accum...")
            
            # V25R = hp.BMP2DA(flowdir, "V25R", V25_R_ft)
            
            # log("25yr Flood storage...")
            # V25Flood = arcpy.env.mask * (V25U - V25R)
            # hp.saveRasterOutput(V25Flood, "V25Flood")
            
             
        ##    usgs_calcs = Helper.USGSVars(hp.Basin)
        ##    usgs_calcs = Helper.newregression(hp.Basin)
            
            log("Calculating Undeveloped Discharge...")
                
            UndevQ = ( Power( ( cum_da / 640 ) , 0.649 ) ) * (158 * 0.875)
            UndevQ.save(undevqPath)
                
            # urban2yrQ_var = (Power( ( cum_da / 640 ) , 0.554 ) * 1.36 ) * ( Power( impcov, 1.241 )) * ( Power( rural2yrQ(Basin,cum_da), 0.323))
            # hp.saveRasterOutput(urban2yrQ_var, "urban2yrQ")
            # urban10yrQ_var = urban10yrQ(hp.Basin,cum_da,cumimpcovlake)
            # hp.saveRasterOutput(urban10yrQ_var, "urban10yrQ")    
            # urban25yrQ_var = urban25yrQ(hp.Basin,cum_da,cumimpcovlake)
            # hp.saveRasterOutput(urban25yrQ_var, "urban25yrQ")
          
            # hp.Close()

        except:       
            i, j, k = sys.exc_info()
            EH(i, j, k)

class ProdTrans(object):
    def __init__(self):
        self.label = "ProdTrans"
        self.description = "Production and Transport Setup"

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
        displayName="Cumulative Impervious Cover",
        name="cumimpcov",
        datatype="DERasterDataset",
        parameterType="Required",
        direction="Input")]
        parameters[-1].value = os.path.join(arcpy.env.workspace,"cumimpcov")
        
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
        displayName="Output Production",
        name="p",
        datatype="DERasterDataset",
        parameterType="Required",
        direction="Output")]
        
        parameters += [arcpy.Parameter(
        displayName="Output Load",
        name="q",
        datatype="DERasterDataset",
        parameterType="Required",
        direction="Output")]
        
        return parameters

    def updateParameters(self, parameters):
        if parameters[0].value:
            fields = arcpy.ListFields(parameters[0].value)
            l = [f.name for f in fields]
            for p in [1, 2, 3, 4, 5, 6, 7, 8, 9]:
                parameters[p].filter.list = l
                
        for p in [11,13]:
            param = parameters[p]
            if parameters[p-1].value:
                fields = arcpy.ListFields(parameters[p-1].value)
                l = [f.name for f in fields]
                param.filter.list = l
                
        return

    def execute(self, parameters, messages):
        try:
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
            pn = LU_fld.split('.')[-1]
           
            pointsources = parameters[12].valueAsText
            point_fld    = parameters[13].valueAsText
            
            K = parameters[14].valueAsText
            slope = parameters[15].valueAsText
            
            BankHydCoe = float(parameters[16].valueAsText)
            BankHydExp = float(parameters[17].valueAsText)
            n_default = float(parameters[18].valueAsText)
            defEro = float(parameters[19].valueAsText)
            defProd = float(parameters[20].valueAsText)
            
            flowdir = Raster(parameters[21].valueAsText) * arcpy.env.mask 
            cumda = Raster(parameters[22].valueAsText)
            Streams_nd = Raster(parameters[23].valueAsText)
            streams = RemoveNulls(Streams_nd)
            Impervious_Cover = Raster(parameters[24].valueAsText)
            Cumulative_Impervious = Raster(parameters[25].valueAsText)
            Rural_1yrQ = Raster(parameters[26].valueAsText)
            lakes = Raster(parameters[27].valueAsText)
            
            qPath = parameters[28].valueAsText
            pPath = parameters[29].valueAsText
            
            Units = flowdir.meanCellWidth
            
            vecmask = os.path.join(arcpy.env.scratchFolder, "vecmask.shp")
            arcpy.RasterToPolygon_conversion(arcpy.env.mask, vecmask, "SIMPLIFY", "Value")
            
            StrInvPts = os.path.join(arcpy.env.scratchFolder, "StrInvPts.shp")
            arcpy.Clip_analysis(StrInvPts_preclip, vecmask, StrInvPts)
            count = int(arcpy.GetCount_management(StrInvPts).getOutput(0))
            if count < 1:
                raise Exception, "No stream inventory points in the study area"
            
            log("Reclassify flowdirection to find straight paths...")
            Flowdirs = Reclassify(flowdir, "VALUE", "1 1;2 0;4 1;8 0;16 1;32 0;64 1;128 0", "DATA")
            
            log("Reclassify flowdirection to find diagonal paths...")
            Flowdird = Reclassify(flowdir, "VALUE", "1 0;2 1;4 0;8 1;16 0;32 1;64 0;128 1", "DATA")
            
            log("Calculate distance grid...")
            Dist = (Flowdirs + Flowdird * 1.4142)* Units
            Dist.save(os.path.join(arcpy.env.scratchFolder, "dist.tif"))

            # params = {}
            # exec(sys.argv[21])
            # if not params:
                # log("   \nThere are no parameters selected to calculate production for!!")
                # raise Exception
                
            # Landuses = []
            # if LU_existing_file != "":
                # Landuses.append( ( LU_existing_file, LU_existing_fld, "E" ) )
            # if LU_future_file != "":
                # Landuses.append( ( LU_future_file, LU_future_fld, "F" ) )
            # if Landuses == []:   
                # log("   \nThere are no parameters selected to calculate production for!!")
                # raise Exception
            
            # for LU in Landuses:
            log("Join LUT to landuse layer")
            arcpy.MakeFeatureLayer_management(LU_file, "LULyr")
            
            # input = file(os.path.join(hp.AppPath, r"..\Tooldata\LUT.csv"), 'r')
            # output = file(os.path.join(arcpy.env.scratchFolder, "LUT.txt"), 'w')
            # output.write(input.read().replace(",", "\t"))
            # input.close()
            # output.close()
            
            # arcpy.MakeTableView_management(os.path.join(arcpy.env.scratchFolder, "LUT.txt"), "LUTview")
            # arcpy.AddJoin_management("LULyr" , LU[1], "LUTview", "TABLE_MATC")

            
            log("Create Export Coefficient (washoff rate) rasters")
            # for param in params:
            # pn = param[:10].strip()
            log( '  Parameter: ' + pn)
            arcpy.PolygonToRaster_conversion("LULyr", LU_fld, os.path.join(arcpy.env.scratchFolder,"LUacres.tif"), "MAXIMUM_AREA", None, Units)
            LU2 = Raster(os.path.join(arcpy.env.scratchFolder,"LUacres.tif")) * float(Units*Units/43560)
            # hp.saveRasterOutput(lu2temp, LU[2] + pn) ######################
            
            log("Create roughness grid")
            arcpy.PolygonToRaster_conversion("LULyr", 'Lut.csv.MANNINGSN', os.path.join(arcpy.env.scratchFolder,"MANNINGSN.tif"), "MAXIMUM_AREA", None, Units)
            
            log("Calculate overland flow velocity")
            MANNINGSN = Raster(os.path.join(arcpy.env.scratchFolder,"MANNINGSN.tif"))
            UplandVel = MANNINGSN * Power(slope, 0.5 )
            UplandVel.save(os.path.join(arcpy.env.scratchFolder, "uplandvel.tif"))
            
            log("Calculate overland flow detention time")
            Detovrlndt = Dist / UplandVel
            Detovrlndt.save(os.path.join(arcpy.env.scratchFolder, "detovrlndt.tif"))
            Detovrlnd = RemoveNulls(Detovrlndt)
            Detovrlnd.save(os.path.join(arcpy.env.scratchFolder, "detovrlnd.tif"))
            
            log("Calculate Hydraulic geometry...")
            BankHt = Power(cumda, BankHydExp) * BankHydCoe
            
            log("Stream Assessment points to raster...")
            fields = [RB_Ero, RB_Hgt, RB_Len, LB_Ero, LB_Hgt, LB_Len,n_channel, BankWidth, BankDepth]
            for field in fields:
                
                #~ ras = os.path.join(arcpy.env.scratchFolder, field.replace("_","") + "ras")
                #~ extract = field+"e"
                #~ asc = os.path.join(arcpy.env.scratchFolder, field+"ras.asc")
                
                f = os.path.join(arcpy.env.scratchFolder, "f" + field)
                arcpy.FeatureToRaster_conversion(StrInvPts, field, f, flowdir)
                ras = Raster(f)
                AttributeRaster = Float(ras) * arcpy.env.mask
                
                # AttributeRaster.save(os.path.join(arcpy.env.scratchFolder, "f" + field +".tif"))
                # flowdir.save(os.path.join(arcpy.env.scratchFolder, "flowdir.tif"))
                # streams.save(os.path.join(arcpy.env.scratchFolder, "streams.tif"))
                
                if field == RB_Len or field == LB_Len:
                    log("\tExtract %s attribute with cellsize %s..." % (field, Units))
                    extract = AttExtract(AttributeRaster, flowdir, streams, os.path.join(arcpy.env.scratchFolder, field+"e.tif"), Units)
                
                    log("\t\tReclassify Bank length attribute...")
                    #~ rrange = RemapRange([[-10000000000,0,0], [0.00001,1000000000000,1]]) # this does not work 
                    reclass = Reclassify(extract, "Value", ".00001 100000 1;-100000 0 0; NoData 0", "DATA")
                    #~ reclass = RemoveNulls(reclass_step1)
                    reclass.save(os.path.join(arcpy.env.scratchFolder, field + "rc.tif"))
                
                else: 
                    log("\tExtract %s attribute..." % field)
                    extract = AttExtract(AttributeRaster, flowdir, streams, os.path.join(arcpy.env.scratchFolder, field+"e.tif"), None)
            
            
            log("Calculate Right bank stream production...")
            RBL = Raster(os.path.join(arcpy.env.scratchFolder, RB_Len+"rc.tif"))
            RBHT = Raster(os.path.join(arcpy.env.scratchFolder, RB_Hgt+"e.tif"))
            RBE = Raster(os.path.join(arcpy.env.scratchFolder, RB_Ero+"e.tif"))
            rt = RBL * streams * defProd * RBHT * RBE / 100 
            rt.save(os.path.join(arcpy.env.scratchFolder, "rt"+pn+".tif"))
            RB = RemoveNulls(rt) 
            RB.save(os.path.join(arcpy.env.scratchFolder, "rb"+pn+".tif"))

            
            log("Calculate Left bank stream production...")
            LBL = Raster(os.path.join(arcpy.env.scratchFolder,LB_Len+"rc.tif"))
            LBHT = Raster(os.path.join(arcpy.env.scratchFolder, LB_Hgt+"e.tif"))
            LBE = Raster(os.path.join(arcpy.env.scratchFolder, LB_Ero+"e.tif"))
            lt = LBL * streams * defProd * LBHT* LBE/ 100
            lt.save(os.path.join(arcpy.env.scratchFolder, "lt"+pn+".tif"))
            LB = RemoveNulls(lt) 
            LB.save(os.path.join(arcpy.env.scratchFolder, "lb"+pn+".tif"))
            
            log("Calculate remaining stream production...")
            B = streams * BankHt * defProd * defEro / 100
            B.save(os.path.join(arcpy.env.scratchFolder, "B"+pn+".tif"))
            
            log("Combine Stream production...")
            APPF = ( BooleanNot(RB) * B + RB ) + ( BooleanNot(LB) * B + LB )
            APPF.save(os.path.join(arcpy.env.scratchFolder, "appf.tif"))
            
            # lakes = Raster(os.path.join(hp.Workspace + "\\WIPoutput.mdb", "lakes"))
            log("Calculate APPS production...")
            APPS = APPF * Dist * BooleanNot(lakes)
            APPS.save(os.path.join(arcpy.env.scratchFolder, "apps.tif"))
            
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
            n_channele1 = Raster(os.path.join(arcpy.env.scratchFolder, n_channel+ "e.tif") )
            n_channele = RemoveNulls(n_channele1)
            n_channele.save(os.path.join(arcpy.env.scratchFolder, "n_channele.tif"))
            
            nstream = streams * BooleanNot(n_channele)* n_default + n_channele
            nstream.save(os.path.join(arcpy.env.scratchFolder, "nstream.tif"))

            
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
            dataclip.save(os.path.join(arcpy.env.scratchFolder, "dataclip.tif"))
            
            # fill in bank width where values are missing along stream
            widthdef = 20.9 * Power ( ( Float(cumda) / 640 ), 0.376 )
            BankWidthe = Raster(os.path.join(arcpy.env.scratchFolder, BankWidth+"e.tif") )
            widthtemp = dataclip * BankWidthe
            widthtemp.save(os.path.join(arcpy.env.scratchFolder, "widthtemp")) 
            width = streams * BooleanNot(widthtemp) * widthdef + widthtemp
            width.save(os.path.join(arcpy.env.scratchFolder, "width.tif"))

            
            # fill in bank depth where values are missing along stream
            depthdef = 3.02 * Power ( ( Float(cumda) / 640 ), 0.258 )
            BankDepthe = Raster(os.path.join(arcpy.env.scratchFolder, BankDepth+ "e.tif") )
            depthtemp = dataclip * BankDepthe
            depth = streams * BooleanNot(depthtemp) * depthdef + depthtemp
            depth.save(os.path.join(arcpy.env.scratchFolder, "depth.tif"))

            
            hydradiusC = (Float(width) * Float(depth)) / (Float(width) + 2 * Float(depth))
            hydradiusC.save(os.path.join(arcpy.env.scratchFolder, "hydradiusC"))
            hydradius = RemoveNulls(hydradiusC)
            hydradius.save(os.path.join(arcpy.env.scratchFolder, "hydradius.tif"))
            
            log("Calculate normal stream velocity")
            tempvel = Power (hydradius, 0.6667) *  Power (Float(slope), 0.5) / nstream
            tempvel.save(os.path.join(arcpy.env.scratchFolder, "tempvel.tif"))
            
            streamvel = RemoveNulls(tempvel)
            streamvel.save(os.path.join(arcpy.env.scratchFolder, "streamvel.tif"))
                
            log("Calculate in-stream flow detention time")
            Detstreamt = Dist / streamvel
            Detstreamt.save(os.path.join(arcpy.env.scratchFolder, "detstreamt.tif"))
            Detstream = RemoveNulls(Detstreamt)
            Detstream.save(os.path.join(arcpy.env.scratchFolder, "detstream.tif"))
            
            log("Calculate total flow detention time")
            Dettime =  Detstream + Detovrlnd * BooleanNot (Detstream)  
            Dettime.save(os.path.join(arcpy.env.scratchFolder, "dettime.tif"))    
                    
            ##    usgs_calcs = Helper.USGSVars(hp.Basin)
            uQcp = urbanQcp(cumda, Cumulative_Impervious)
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
            
            # hp.Close()
            
        except:       
            i, j, k = sys.exc_info()
            EH(i, j, k)

class Baseline(object):
    def __init__(self):
        self.label = "Baseline"
        self.description = "Baseline"
        arcpy.env.overwriteOutput = True
        # arcpy.env.extent = os.path.join(arcpy.env.workspace, "flowacc")

    def getParameterInfo(self):
    
        parameters = []
        
        parameters += [arcpy.Parameter(
        displayName="Use Production developed for Existing Landuse",
        name="existingLU",
        datatype="GPBoolean",
        parameterType="Optional",
        direction="Input")]
        
        parameters += [arcpy.Parameter(
        displayName="Use Production developed for Future Landuse",
        name="futureLU",
        datatype="GPBoolean",
        parameterType="Optional",
        direction="Input")]
        
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
        displayName="Summary Points output field ",
        name="summaryptsfield",
        datatype="Field",
        parameterType="Required",
        direction="Input")]
        parameters[-1].parameterDependencies = [parameters[-2].name]
        
        parameters += [arcpy.Parameter(
        displayName="Output Load",
        name="load",
        datatype="GPRasterDataLayer",
        parameterType="Derived",
        direction="Output")]
        parameters[-1].parameterDependencies = [parameters[4].name]
        
        parameters += [arcpy.Parameter(
        displayName="Output Yield",
        name="yield",
        datatype="GPFeatureLayer",
        parameterType="Derived",
        direction="Output")]
        parameters[-1].parameterDependencies = [parameters[4].name]
        
        
        
        return parameters

    def updateParameters(self, parameters):
        if parameters[2].value:
            fields = arcpy.ListFields(parameters[2].valueAsText)
            l = [f.name for f in fields]
            parameters[3].filter.list = l
            parameters[4].filter.list = l
        return

    def execute(self, parameters, messages):
        try:
            log("\nBaseline run started at %s" % time.asctime())
            
            bmp_noclip = parameters[2].valueAsText
            bmp_type = parameters[3].valueAsText
            bmp_eff = parameters[4].valueAsText
            summary_pt_input = parameters[5].valueAsText
            
            landuses = []
            use_existing = parameters[0].value
            use_future = parameters[1].value
            if use_existing:
                landuses.append("E")
            if use_future:
                landuses.append("F")
            if not landuses: raise Exception("You must select at least one type of landuse")
            
            Cum_da = Raster(os.path.join(arcpy.env.workspace, "cumda"))
            flowdir = Raster(os.path.join(arcpy.env.workspace, "flowdir"))
            Streams_nd = Raster(os.path.join(arcpy.env.workspace, "streams"))
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
                raise Exception("No BMP points, stopping")
            
            if summary_pt_input:
                summary_pts = os.path.join(arcpy.env.workspace, "summarypts")
                arcpy.Clip_analysis(summary_pt_input, vecmask, summary_pts)
                SetPIDs(summary_pts)
                
            pn = GetAlias(bmp_eff)[:10]
            for LU in landuses:
                TSSProd = Raster(os.path.join(arcpy.env.workspace, "q" + LU + pn)) * arcpy.env.mask
                
                K = os.path.join(arcpy.env.workspace, "K" + LU[0] + pn)
                
                TSSLoadOutput = (os.path.join(arcpy.env.workspace, "L" + LU + pn))
                TSSYield = (os.path.join(arcpy.env.workspace, "Y" +LU + pn))
                TSSYldvec = (os.path.join(arcpy.env.workspace, pn + LU+ "yield"))
                
                log("Convert BMPs to Raster...")
                BMPs = arcpy.FeatureToRaster_conversion(ExBMPpts, bmp_eff, os.path.join(arcpy.env.scratchFolder,"b" + LU + pn + ".tif"), flowdir)
                
                log("Combine decay function with BMP reduction")
                bmptemp = RemoveNulls(BMPs)
                weightred = 1 - ( K * ( 1 - (bmptemp / 100.0 ) ) ) * arcpy.env.mask
                weightred.save(os.path.join(arcpy.env.scratchFolder,"weightred.tif"))
                
                log("Calculate Reduction...")
                Existingtss = BMP2DA(flowdir, "bmp2da.tif", TSSProd, weightred)
                
                log("Clip...")
                TSSLoadOutput = Existingtss * arcpy.env.mask
                TSSLoadOutput.save("L" + LU + pn)
                
                log("Calculate Yield...")
                TSSYield = TSSLoadOutput / Cum_da
                TSSYield.save("Y" +LU + pn)
                
                log("Clip to streams...")
                # and round
                TSSYieldcl = Int(RoundUp( RoundDown( Streams_nd * TSSYield * 20000 ) / 2 ))
                
                log("Vectorize...")
                TSSYldvec = pn + LU+ "yield"
                StreamToFeature(TSSYieldcl, flowdir, TSSYldvec, "NO_SIMPLIFY")
                
                ConvertGRIDCODEatt(TSSYldvec)
                    
                if summary_pt_input:
                    TSSLoadOutput = Raster(os.path.join(arcpy.env.workspace, "L" + LU[0] + pn))
                    Summarize(TSSLoadOutput, summary_pts)        
            
        except:       
            i, j, k = sys.exc_info()
            EH(i, j, k)
            
class CIP(object):
    def __init__(self):
        self.label = "CIP"
        self.description = "CIP"

    def getParameterInfo(self):
    
        parameters = []
        
        parameters += [
        arcpy.Parameter(
        displayName="Scenario Name",
        name="scenarioName",
        datatype="GPString",
        parameterType="Required",
        direction="Input")]
        
        parameters += [
        arcpy.Parameter(
        displayName="Use Production developed for Existing Landuse",
        name="existingLU",
        datatype="GPBoolean",
        parameterType="Optional",
        direction="Input")]
        
        parameters += [
        arcpy.Parameter(
        displayName="Use Production developed for Future Landuse",
        name="futureLU",
        datatype="GPBoolean",
        parameterType="Optional",
        direction="Input")]
        
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
        displayName="Summary Points",
        name="summarypts",
        datatype="GPFeatureLayer",
        parameterType="Optional",
        direction="Input")]
        parameters[-1].filter.list = ["Point"]
       
        
        return parameters

    def updateParameters(self, parameters):
        if parameters[3].value:
            fields = arcpy.ListFields(parameters[3].valueAsText)
            l = [f.name for f in fields]
            for i in [4, 5, 6, 7, 8, 9, 10, 11]:
                parameters[i].filter.list = l
        return

    def execute(self, parameters, messages):
        try:
            ScenName = parameters[0].valueAsText
            use_existing = parameters[1].value
            use_future = parameters[2].value
            bmp_noclip = parameters[3].valueAsText
            bmp_type = parameters[4].valueAsText
            bmp_CIPproj = parameters[5].valueAsText
            bmp_Ex1yr = parameters[6].valueAsText
            bmp_Prop1yr = parameters[7].valueAsText
            bmp_strlngth = parameters[8].valueAsText
            bmp_eeff = parameters[9].valueAsText
            bmp_peff = parameters[10].valueAsText
            StreamLength = parameters[11].valueAsText
            defEro = parameters[12].value
            summary_pt_input = parameters[13].valueAsText
            
            log("\nCIP run %s started at %s" % (ScenName, time.asctime()))
            
            landuses = []
            if use_existing:
                landuses.append("E")
            if use_future:
                landuses.append("F")
            if not landuses: raise Exception("You must select at least one type of landuse")
            
            pn = GetAlias(bmp_eeff)[:10]
            
            gdb = "CIP_%s.mdb" % ScenName.replace(" ", "_")
            arcpy.CreatePersonalGDB_management(os.path.split(arcpy.env.workspace)[0], gdb)
            cipWorkspace = os.path.join(os.path.split(arcpy.env.workspace)[0], gdb)
            
            vectmask = os.path.join(arcpy.env.scratchFolder, "vectmask.shp")
            BMPpts = os.path.join(arcpy.env.scratchFolder, "BMPpts.shp")
            arcpy.RasterToPolygon_conversion(arcpy.env.mask, vectmask, "SIMPLIFY", "Value")
            arcpy.Clip_analysis(bmp_noclip, vectmask, BMPpts)
            
            Cum_da = Raster(os.path.join(arcpy.env.workspace, "cumda"))
            flowdir = Raster(os.path.join(arcpy.env.workspace, "flowdir"))
            Streams_nd = Raster(os.path.join(arcpy.env.workspace, "streams"))
            Stream_Raster = RemoveNulls(Streams_nd)
            Units = flowdir.meanCellWidth
            
            if summary_pt_input:
                summary_pts = os.path.join(cipWorkspace, "summaryptsCIP")
                arcpy.Clip_analysis(summary_pt_input, vectmask, summary_pts)
                SetPIDs(summary_pts)
            
            log("Finding CIP projects...")
            CIPBMPpts = os.path.join(arcpy.env.scratchFolder, "CIPpts.shp")
            CIP_found = GetSubset(BMPpts, CIPBMPpts, " \"%s\" = 'TRUE' " % bmp_CIPproj)
            if not CIP_found:
                raise Exception, "Did not find any CIP Projects in the study area, stopping"
                
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
            
            for LU in landuses:
                TSSprod = Raster(os.path.join(arcpy.env.workspace, "p" + LU + pn))
                K = Raster(os.path.join(arcpy.env.workspace, "K" + LU + pn))
                
                pointsrc = ""
                if "pt" + LU + pn in arcpy.ListRasters(arcpy.env.workspace):
                    pointsrc = Raster(os.path.join(arcpy.env.workspace, "pt" + LU + pn))
                    
                if CP_found > 0:
                    CumMod_da, RasBMPpts2, throwout = ChannelProtection(ChanBMPpts, bmp_Prop1yr)
                    
                    Cumulative_Impervious = Raster(os.path.join(arcpy.env.workspace, "cumimpcovlake") )
                    urbanQcp = urbanQcp(CumMod_da, Cumulative_Impervious)
                    
                    log("Calculate Urban/Rural ratio...")
                    Rural_1yrQ = Raster(os.path.join(arcpy.env.workspace, "UndevQ"))
                    URratio = urbanQcp / Rural_1yrQ
                    
                    log("Add erosivity to production...")# % param)
                    TSSP_ero_ext = CalcErosivity(defEro, TSSprod, pointsrc, URratio, Stream_Raster)
                    # TSSP_ero_ext.save(os.path.join(arcpy.env.scratchFolder, "TSSP_ero_ext"))
                    log("Clip to streams...")
                    # and round
                    UrbRurratc = Int(RoundUp( RoundDown( Streams_nd * URratio * 20000 ) / 2 ))
                    
                    URratio_vec = os.path.join(cipWorkspace, LU + "rv" + pn)#
                    log("Vectorize...")
                    StreamToFeature(UrbRurratc, flowdir, URratio_vec, "NO_SIMPLIFY")
                    ConvertGRIDCODEatt(URratio_vec)
                
                else:
                    log("  Did not find any Channel Protection Projects in the study area, skipping this part")
                    CumMod_da = Cum_da
                    URratio = os.path.join(arcpy.env.workspace, "UrbRurratio")
                    TSSP_ero_ext = Raster(os.path.join(arcpy.env.workspace, "q" + LU + pn)) * arcpy.env.mask
                
                if SR_found < 1:
                    log("  Did not find any Stream Restoration Projects in the study area, skipping this part")
                    TSS_reduc = TSSP_ero_ext
                else:
                    log("Convert Stream Lengths to Raster...")
                    len = arcpy.FeatureToRaster_conversion(strBMPs2, bmp_strlngth, os.path.join(arcpy.env.scratchFolder, "len.tif"), flowdir)
                    BMPlengths = Float(len)
                     
                    lengths = AttExtract(BMPlengths, flowdir,"lengths", Stream_Raster, Units)
                    
                    log("Remove background values...")
                    lengthsmask = Reclassify(lengths, "VALUE", ".00001 100000 1;-100000 0 0; NoData 0", "DATA")
                    
                    log("Convert Stream Restoration Projects to Raster...")
                    srp = GetTempRasterPath("srp")
                    arcpy.FeatureToRaster_conversion(strBMPs2, bmp_peff, srp, flowdir)
                    strBMPs3 = Float(Raster(srp))
                    
                    PropEffnd = AttExtract(strBMPs3, flowdir, "PropEffnd", Stream_Raster)
                    
                    log("Remove background values...")
                    PropEff = RemoveNulls(PropEffnd)
                    
                    log("Production for Stream Restoration Projects...")
                    StrTSSRed = lengthsmask * TSSprod * PropEff / 100
                    
                    log("Reduce production for Stream Restoration Projects...")
                    TSS_reduc = TSSP_ero_ext - StrTSSRed
                    
                    if StreamLength:
                        
                        log("Convert Stream Projects to Raster...")
                        #~ print bmp_peff
                        slpf = arcpy.FeatureToRaster_conversion(strBMPs2, StreamLength, os.path.join(arcpy.env.scratchFolder, "slpf.tif"), flowdir)
                        strBMPs3 = Float(slpf)
                        
                        log("Stream reduction per length...")
                        srlength = AttExtract(strBMPs3, flowdir,"lengths", Stream_Raster)
                        
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
                    arcpy.FeatureToRaster_conversion(ExistingBMPs, bmp_eeff, os.path.join(arcpy.env.scratchFolder, "ExistingBMPs.tif"), flowdir)
                    ExistingBMPs = Raster(os.path.join(arcpy.env.scratchFolder, "ExistingBMPs.tif"))
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
                TSSLoadOutput.save(os.path.join(cipWorkspace, "L" + LU[0] + pn))
                
                log("Calculate Yield...")
                CIPTSSYield = TSSLoadcip / Cum_da
                CIPTSSYield.save(os.path.join(cipWorkspace, "Y" + LU[0] + pn))
                
                log("Clip to streams...")
                # and round
                TSSYield_cl = Int(RoundUp( RoundDown( Streams_nd * CIPTSSYield * 20000 ) / 2 ))
                TSSYield_cl.save(os.path.join(cipWorkspace, LU[0] + "y2" + pn))
                
                TSSYldvec = os.path.join(cipWorkspace, LU[0] + "yV" + pn)#
                log("Vectorize...")
                StreamToFeature(TSSYield_cl, flowdir, TSSYldvec, "NO_SIMPLIFY")
                
                ConvertGRIDCODEatt(TSSYldvec)
     
            if summary_pt_input:
                log("Summarizing results...")
                alias = LU + " " + pn + " Load"
                Summarize(TSSLoadOutput, summary_pts, alias)    
        
        except:       
            i, j, k = sys.exc_info()
            EH(i, j, k)
            
