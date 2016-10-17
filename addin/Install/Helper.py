import time
import traceback
import os
import sys
import string 
import subprocess
import pprint
pp = pprint.PrettyPrinter()
from shutil import rmtree
import arcpy
from arcpy import env
arcpy.env.extent = "MAXOF"
from arcpy.sa import *
import random
import regression
import numpy

class Helper:
    def __init__(self, args):
        
        os.chdir(os.path.split(args[0])[0])
        self.step = 0
        self.ExecPath = os.getcwd()
        self.Logfilename = os.path.join(self.ExecPath, "tempLog.log")
        
        self.log( "    " + file("rev.txt").read() )
        #~ self.SysInfo()
            
        # Check out necessary licenses
        if arcpy.CheckExtension("spatial") == "Available":
            arcpy.CheckOutExtension("Spatial")
        else:
            self.log("    No Spatial Analyst license available, bailing")
            raise Exception("No Spatial Analyst license available")
        
        arcpy.env.overwriteOutput = True
        
        # Load required toolboxes...
        if os.path.exists("C:\Program Files (x86)\ArcGIS\Desktop10.4\ArcToolbox\Toolboxes"):
            basepath = "C:\Program Files (x86)\ArcGIS\Desktop10.4\ArcToolbox\Toolboxes"
        elif os.path.exists("C:\Program Files\ArcGIS\Desktop10.4\ArcToolbox\Toolboxes"):
            basepath = "C:\Program Files\ArcGIS\Desktop10.4\ArcToolbox\Toolboxes"
        else:
            raise Exception, "Could not locate the spatial analyst toolbox, stopping"
            
        arcpy.AddToolbox(os.path.join(basepath, "Spatial Analyst Tools.tbx"))
        arcpy.AddToolbox(os.path.join(basepath, "Conversion Tools.tbx"))
        arcpy.AddToolbox(os.path.join(basepath, "Data Management Tools.tbx"))
        
        self.Basin = ""
        self.units = {}
        self.models = {}
        
        lastmodelpath = os.path.join(os.getcwd(), "LastModel.wip")
        self.log( "    Looking for " + lastmodelpath )
        if os.path.exists(lastmodelpath):
            self.log( "    Found LastModel.wip" )
            l = open(lastmodelpath, "r")                
            self.Workspace = l.readline().split(',')[0]
            l.close()
            
            self.log( "    Working in %s" % self.Workspace )
        
        else:
            self.log( "    LastModel.wip not found" )
            self.Workspace = self.ExecPath
            
        if string.count(args[0], "TopoHydro") == 0:
            self.SetEnvVar()
        else:
            self.log( "    Not calling SetEnv for TopoHydro" )
      
        
        
    def log(self, message):
        ''' Logging function that logs to sys.stdout, the log file, and ArcGIS messages all at the same time'''
        if not message.startswith("  "):
            message = " Step %s: %s" % (self.Step(), message)
        
        if arcpy: arcpy.AddMessage(message)
        
        
        try:
            log = file(self.Logfilename, 'a')
        except:
            time.sleep(1000)
            log = file(self.Logfilename, 'a')
        log.write(message + "\n")
        log.close()
        
       
        
    def SetEnvVar(self):
        '''Set the geoprocessing environment variables stored in the WIP.dat config file that is stored in each dataset folder.'''
        #~ self.log("calling Set GPEnvironment")
        self.Mask = ""
        
        
        self.AppPath= os.path.split(sys.argv[0])[0]
        thiswip = os.path.join(self.Workspace, "WIP.dat")
        if os.path.exists(thiswip):
            execfile(thiswip)
        else:
            self.log( '    Did not find this WIP.dat %s ' %thiswip )
            ######
        self.valid = True
            ######
        if not self.valid:
            self.log( "    Skipping this tool run since a previous tool run was invalid" )
            sys.exit(1)
        
        # Find out which tool is running
        self.current_tool = os.path.split(sys.argv[0])[1].replace(".pyc","").replace(".py","")
        if self.current_tool == "CIP":
            self.current_tool = "CIP_%s" % sys.argv[1].replace(" ", "_")
            
        self.models[self.current_tool] = {}
        self.models[self.current_tool]["input"] = sys.argv[1:]
        self.models[self.current_tool]["output"] = []
        
        self.SWorkspace = os.path.join(self.Workspace, "Scratch")
        if not os.path.exists(self.SWorkspace): 
            os.mkdir(self.SWorkspace)  
        
        arcpy.env.Workspace = self.SWorkspace
        
        self.Logfilename=os.path.join(self.Workspace, self.current_tool+".log")
            
        self.VWorkspace = os.path.join(self.Workspace, "WIPoutput.mdb")
        if not os.path.exists(self.VWorkspace): 
            arcpy.CreatePersonalGDB_management(self.Workspace, "WIPoutput.mdb","CURRENT") 
            
        if type(self.Mask) != type(""):
            dsc = arcpy.Describe(self.Mask)
            arcpy.env.extent = dsc.Extent
            arcpy.env.snapRaster = self.Mask.catalogPath
            arcpy.cellSize = dsc.MeanCellHeight
            self.cellSize = dsc.MeanCellHeight
            #~ self.log(" Extent has been set to %s" % arcpy.extent)
            self.log("    Cell size has been set to %s %s" % (arcpy.cellSize, self.units['type']))
            
        
        # f = open(os.path.join(self.AppPath, r'../ToolData/Metadatainfo.csv'), 'r')
        # header = f.readline().split(',')
        # tags = f.readline().split(',')
        # self.tags = {}
        # for k, v in zip(header, tags):
            # self.tags[k] = v
        
        # self.metadata = {}
        # for i in f.readlines():
            # d = i.split(',')
            # self.metadata[d[0].lower()] = {}
            # for j in range(1, len(d)-1):
                # self.metadata[d[0].lower()][header[j]] = d[j]
        # f.close()
        
        # for i in self.metadata.keys():
            # self.metadata[i]['Citation Originator'] = "%s\\%s" % (os.environ['USERDOMAIN'], os.environ['USERNAME'])
            
        self.log( "    Finished loading env vars" )
        
    def GetBasin(self):
        try:
            bf = open("Basin.dat", "r")
            Basin = bf.readline().strip()
            bf.close()
            return Basin
        except Exception, e:
            raise e
    
    def EH(self, i, j, k):
        #~ traceback.print_exc(file = logfile)
        #~ i, j, k = sys.exc_info()
        data = traceback.format_exception(i,j,k)
        for l in data:
            #~ gp.AddError(l)
            self.log("  " + l)
            
        #~ self.log('\n%s\n' % arcpy.GetMessages())
        arcpy.AddError(arcpy.GetMessages())        
        arcpy.AddError("*"*50+'''\nExtended error output has been recorded in the log file''')
        self.Close(0)
        raise 
        
    def RunScript(self, script, args, returnOutput=False):
        if '.mdb' in args and script != 'MetadataExport':
            raise Exception, "Can not use a path to the geodatabase from the custom geoprocessing tools: " + args
        scriptvar=os.path.join(self.AppPath,script)
        command = '"%s" %s' % (scriptvar, args)
        
        pipe = subprocess.Popen(command,stdout=subprocess.PIPE).stdout
        scriptdata = pipe.readlines()
        pipe.close()
        
        # Give the script time to close the dataset and log
        time.sleep(1)
        if len(scriptdata) == 0 or scriptdata[-1].strip() != "Done!":
            for i in scriptdata:
                self.log( '    ' + i.strip() )
            raise Exception, "Error in running this command:\n\t" + command
        
        if returnOutput:
            return scriptdata
         
    def BMP2DA(self, flowdir, outputname=None, weightsInput=None, bmpsInput=None):
        
        import bmpFlowModFast
        
        lowerLeft = arcpy.Point(flowdir.extent.XMin,flowdir.extent.YMin)
        cellSize = flowdir.meanCellWidth

        start = time.time()
        nflowdir = arcpy.RasterToNumPyArray(flowdir, nodata_to_value=0).astype(numpy.int)
        if type(weightsInput) != arcpy.Raster:
            nweight = arcpy.RasterToNumPyArray(weightsInput, nodata_to_value=0).astype(numpy.double)
        else:
            nweight = None
        if type(bmpsInput) != arcpy.Raster:
            nbmppts = arcpy.RasterToNumPyArray(bmpsInput, nodata_to_value=0).astype(numpy.double)
        else:
            nbmppts = None
            
        arr = bmpFlowModFast.flowAccumulate(nflowdir, nweight, nbmppts)

        newRaster = arcpy.NumPyArrayToRaster(arr, lowerLeft, cellSize, value_to_nodata=0)
        if outputname != None:
            newRaster.save(os.path.join(self.Workspace, outputname))
            
        self.log( "BMP2DA took %6.2f seconds" % (time.time()-start) )
        
        return newRaster

    def AttExtract(self, streamInvPts, flowdir, outputname, streams, cellsize=None):
        
        #~ outputname = self.GetTempRasterPath(outputname) # this leads to mass confusion as, we re-use the name passed, so we expect it to be the same shen we go to use the outputs
        output = self.GetTempRasterPath(outputname)
        if os.path.exists(output):
            self.log("    Warning: %s already exists, overwriting" % output)
            arcpy.Delete_management(output)
            while os.path.exists(output):
                time.sleep(100)
        streamInvPts = self.MakeTempRaster(streamInvPts, "sip")
        streams = self.MakeTempRaster(streams, "str")
        
        args = '"%s" "%s" "%s" "%s"' % (streamInvPts.catalogPath, flowdir.catalogPath, output, streams.catalogPath)
        if cellsize: args += " %s" % cellsize
        #~ else: self.log("  Warning: you are using AttExtract without a cellsize, which usually results in incorrect results for Stream projects")
        self.RunScript("AttExtract.exe", args)
        
        return self.RemoveNulls(output)
    
    def ProtLength(self, pt, flowdir, singleQ, existingQ):
        
        #for r in [pt, flowdir, singleQ, existingQ]:
        pt = self.MakeTempRaster(pt, "protleng")
        flowdir = self.MakeTempRaster(flowdir, "protleng")
        singleQ = self.MakeTempRaster(singleQ, "protleng")
        existingQ = self.MakeTempRaster(existingQ, "protleng")
        
        args = '"%s" "%s" "%s" "%s"' % (pt.catalogPath, flowdir.catalogPath, singleQ.catalogPath, existingQ.catalogPath)
        Csharpdata = self.RunScript("ProtLen.exe", args, True)
       
        substring = "Length computed as: "
        ans = 0
        for line in Csharpdata:
            if substring in line:
                ans = float(line.strip().replace(substring, ""))
       
        if not ans:
            raise Exception("Invalid result from ProtLen.exe: %s" % Csharpdata)
        return ans
    
    def saveRasterOutput(self, output, name, giveDetails=False):
                
        output_mdb = os.path.join(self.Workspace, "WIPoutput.mdb")
        env.workspace = output_mdb
        rasterList = arcpy.ListRasters("*", "GRID")
        env.workspace = self.Workspace
        
        if not type(output) == Raster:
            raise Exception, "%s is not a Raster object, could not save"
        # if name in rasterList:
            # raise Exception, "%s already exists, could not save" % name
        
        path = os.path.join(output_mdb, name)
        self.log("  Saving output raster: %s" % (path))
        if giveDetails:
            self.log("    Band count:       %s" % output.bandCount)
            self.log("    Compression type: %s" % output.compressionType)
            self.log("    Format:           %s" % output.format)
            self.log("    Has Attributes:   %s" % output.hasRAT)
            self.log("    Extent:           %s" % output.extent)
            self.log("    Rows:             %s" % output.height)
            self.log("    Columns:          %s" % output.width)
            self.log("    Minimum:          %s" % output.minimum)
            self.log("    Maximum:          %s" % output.maximum)
            self.log("    NoData Value:     %s" % output.noDataValue)
            self.log("    Data Type:        %s" % output.pixelType)
            self.log("    Size (Mb):        %s" % (output.uncompressedSize/1048576))
        output.save(path)
        
        #~ if not "scratch" in path:
        self.models[self.current_tool]["output"].append(path)
        
        # return path
        return path
        
        
    def MakeMeta(self):
        
        for output in self.models[self.current_tool]['output']:
            dataset = os.path.split(output)[1].lower()
            db = "WIPoutput.mdb"
            if self.current_tool.lower().startswith("cip"):
                db = self.current_tool + ".mdb"
                
            if dataset in self.metadata.keys():
                self.log("    Found metadata for %s" % (dataset))
                
                args = '"%s" %s' % (os.path.join(self.Workspace, db), dataset)
                self.RunScript("MetadataExport", args)
                
                
            else:
                self.log("    Could not find metadata for %s" % (dataset))
        
    def MemStatus(self, apps=["ArcCatalog","ArcMap","python","cmd","BMP2DA","MetadataExport","AttExtract","ProtLen"]):
        
        for i in apps:
            stat = os.popen('tasklist /FI "IMAGENAME eq %s.exe" /NH' % i)
            data = stat.read().strip()
            stat.close()
            if data: self.log( data )
        
    def SysInfo(self):
        info = os.popen('systeminfo')
        self.log( info.read() )
        info.close()
        
    def AddID(self, vec, id):
                
        if not id in self.ListofFields(vec):
            arcpy.AddField_management(vec, id, "LONG", "", "", "", "", "NON_NULLABLE", "NON_REQUIRED", "")
            
        rows = arcpy.UpdateCursor(vec)
        
        for row in rows:
            row.setValue(id, 1)
            rows.updateRow(row)
            
                
        
    def Close(self, clean=1):
        #~ if clean: self.MakeMeta()
        self.RecordLastModel()
        self.SerializeDAT(clean)
        if clean: 
            #~ rmtree(self.SWorkspace)
            self.log("  Done successfully!")
            
        self.log(time.asctime() + "\n" + "_"*45)
    
    def SerializeDAT(self, valid):
        # serialize persistent parts for future model runs
        truth = {1:True, 0:False}
        model = open(os.path.join(self.Workspace, "WIP.dat"), "w")
        model.write('self.units = %s\n' % self.units)
        model.write("self.Basin = '%s'\n" % self.Basin)
        model.write("self.Workspace = '%s'\n" % self.Workspace.replace("\\", "\\\\"))
        model.write("self.Mask = Raster('%s')\n" % self.Mask.catalogPath.replace("\\", "\\\\"))
        model.write('self.models = {\n')
        for k in self.models:
            model.write("\t'%s': {\n" % k)
            for l in self.models[k]:
                model.write("\t\t'%s': %s,\n" % (l, self.models[k][l]))
            model.write("\t},\n")
        model.write("}\n")
        model.write("self.valid = %s" % (truth[valid]))
        model.close()

    def RecordLastModel(self):
        lmr_fname = os.path.join(self.ExecPath, "LastModel.wip")
        path = {}
        
        # Write the current model out first, as AddData only reads the first line
        lmr = open(lmr_fname, "w")
        lmr.write("%s,%s\n" % (self.Workspace, str(sys.argv)[1:-1]))
        lmr.close()    
    
    def GetDataTable(self, table):
        
        if not table.endswith(".csv"): self.log( "Warning, your data table does not appear to be comma-seprated" )
            
        table = os.path.join(os.path.join(self.AppPath, r"..\Tooldata"), table)
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
        
    def Step(self):
        self.step += 1
        return self.step
        

        
    def Zonal(self, raster, stat='SUM'):
        LoadTable = os.path.join(self.SWorkspace, 'load.dbf')
        
        outZSaT  = ZonalStatisticsAsTable(self.Mask, "Value", raster, LoadTable, "DATA")
        rows = arcpy.UpdateCursor(LoadTable)
        computation = rows.next().getValue(stat)
        
        return computation
        
    def SetAtt(self, PID, att, val, lyr, alias=None):
        self.log("\t\tPID: %s\n\t\tAttribute: %s\n\t\tValue: %s\n\t\tLayer: %s" % (PID, att, val, lyr) )
        
        if not alias: alias = att
        
        if not att in self.ListofFields(lyr):
            self.log( "\tAdding field: %s (%s)" % (att, alias) )
            arcpy.AddField_management(lyr, att, "DOUBLE", "", "", "", alias, "NULLABLE", "NON_REQUIRED", "")
            
        rows = arcpy.UpdateCursor(lyr)
        
        for row in rows:
            if row.getValue('PID') == PID:
                row.setValue(att, val)
                rows.updateRow(row)
            
        
        
    def Summarize(self, raster, points, alias=None, PID=-1):
        name = os.path.split(raster.catalogPath)[1][:8].strip()
        temp_vec = os.path.join(self.SWorkspace, name + ".shp")
        arcpy.sa.ExtractValuesToPoints(points, raster, temp_vec)
       
        
        rows = arcpy.SearchCursor(temp_vec)
        
        for row in rows:
            thisPID = row.getValue("PID")
            if PID == thisPID or PID < 0:
                self.SetAtt(thisPID, name, row.getValue("RASTERVALU"), points, alias)
        
    def GetAlias(self, input_list):
        aliases = {}
        a = file(os.path.join(self.AppPath, r'..\ToolData\alias.txt'))
        for i in a.readlines():
            d = i.strip().split('\t')
            aliases[d[0].strip()] = d[1].replace('"', '').replace(' ', '').split(',')
        a.close()
        
        parameter_dict = {}
        for this_input in input_list:
            for alias in aliases:
                for substring in aliases[alias]:
                    if substring in this_input.lower():
                        parameter_dict[alias] = this_input
        if not parameter_dict:
            self.log("    No parameters found in %s, stopping" % input_list)
            raise Exception
        
        return parameter_dict
        
    def ShortName(self, name):
        shortname = "uh-oh"
        
        a = file(os.path.join(self.AppPath, r'..\ToolData\alias.txt'))
        for i in a.readlines():
            d = i.strip().split('\t')
            if name == d[0].strip():
                shortname = d[1].replace('"', '').replace(' ', '').split(',')[0]
                
        return shortname
        
    def SetPIDs(self, vec):
        if ".mdb" in vec:
            OID = "OBJECTID"
        else:
            OID = "FID"
            

        if not 'PID' in self.ListofFields(vec):
            self.log( "Adding PID field" )
            arcpy.AddField_management(vec, 'PID', "SHORT", "", "", "", "", "NULLABLE", "REQUIRED", "")

        rows = arcpy.UpdateCursor(vec)
        
        for row in rows:     
            val = row.getValue(OID)
            row.setValue("PID", int(val))
            rows.updateRow(row)
            
        
        
    def ListofFields(self, lyr):
        fields = arcpy.ListFields(lyr)
        return fields

    def ConvertGRIDCODEatt(self,lyr):
        arcpy.AddField_management(lyr, "Ratio", "DOUBLE", "", "", "", "", "", "NON_REQUIRED", "")
        rows = arcpy.UpdateCursor(lyr)
         
        for row in rows:
            val = row.getValue('GRID_CODE')
            row.setValue("Ratio", val/10000.0)
            rows.updateRow(row)
            
    def GetTempRasterPath(self, outputname):
        
        if not ("\\" in outputname or "/" in outputname):
            p = self.SWorkspace
            f = outputname[:min(len(outputname), 13)]
        else:
            p, f = os.path.split(outputname)
            f = f[:min(len(f), 13)]
        
        newname = os.path.join(p, f)
        basename = os.path.join(p, f[:min(len(f), 9)])
        i = 1
        while os.path.exists(newname):
            newname = "%s%04i" % (basename, i)
            i+=1
        return newname
        
    def MakeTempRaster(self, r, prefix):
        
        if len(prefix) > 3:
            prefix = prefix[:3]
            
        if type(r) == Raster:
            result = ExtractByMask(r, self.Mask)
##            print "\t\t**", r
##            print "\t\t**", self.Mask
##            print "\t\t**", result
##            print "\t\t**", prefix
##            print "\t\t**", self.GetTempRasterPath(prefix)
##            if not r.catalogPath:
            result.save(self.GetTempRasterPath(prefix))
            return result
        else:
            if r:
                raise Exception("%s is not a raster object, it is a %s" % (r, type(r)))
            else:
                return None
            
    def RemoveNulls(self, raster):
        return Con(IsNull(raster),0,raster)
        
    def GetSubset(self, input, output, query):
        arcpy.MakeFeatureLayer_management(input, 'subset')
        arcpy.SelectLayerByAttribute_management('subset', "NEW_SELECTION", query)
        arcpy.CopyFeatures_management('subset', output)
        count = int(arcpy.GetCount_management(output).getOutput(0))
        self.log("  %s, found %s" % (query, count))
        return count
        
class WIP:
    def __init__(self, fname=None):
        if not fname:
            lastmodel = file("LastModel.wip").readline().split(',')[0]
            fname = os.path.join(lastmodel, "WIP.dat")
        execfile(fname)
        models = self.models.keys()
        for m in models:
            if 'CIP' in m:
                thismodel = self.models.pop(m)
                self.models['CIP'] = thismodel
                
    def writebat(self):
        bat = file('..\\BatchRunAll.bat', 'w')
        bat.write('set PYTHONPATH=C:\Program Files\ArcGIS\Desktop10.0;%PYTHONPATH%\nset PATH=C:\Python26\ArcGIS10.0;%PATH%;\n\n')
        bat.write('REM Comment this out if you are not running TopoHydro\ndel "C:\Program Files\WIP Tools\Bin\LastModel.wip"\n\n')
        
        for mod in ['TopoHydro', 'ImpCov', 'Runoff', 'ProdTrans', 'Baseline', 'CIP', 'SingleBMP', 'ProtLeng']:
            print mod + ", %s" % mod in self.models 
                    
            if mod in self.models:
                bat.write('python "C:\Program Files\WIP Tools\Bin\%s.py"' % mod)
                for i in self.models[mod]['input']:
                    if " " in i:
                        i = '"' + i + '"'
                    bat.write(" " + i)
                bat.write('\n')
                
        bat.close()        


class USGSVars:
    def __init__(self, Basin):
        # Read table of parameters and match to the basin being used
        self.Basin = Basin
        pf = None
        f = os.path.join(os.path.split(sys.argv[0])[0], r"../ToolData/USGSvars.csv")
       
        if not os.path.exists(f): raise Exception
        else: pf = open(f, 'r')
        params = pf.readline().split(',')
        
        found = 0
        for i in pf.readlines():
            vals = i.split(',')
            thisBasin = vals[0]
            if thisBasin == Basin:
                found = 1
                for j in range(1, len(params)):
                    code = "self.%s = %f" % ("p"+params[j].strip(), float(vals[j]))
                    exec(code)
        pf.close()

        if not found:
            raise Exception, "Basin not found!"
            
    def urbanQcp(self, cum_da, impcov):
        if self.Basin == 'Georgia Region 1':
                return (self.pcpuUBase* Power( ( cum_da / 640 ), self.pcpuUAExp ) )  * ( Power( 10 , ( self.pcpuUIExp * impcov ) ) )
        else:
                return ( Power( ( cum_da / 640 ), self.pcpuUAExp ) ) * ( Power( impcov, self.pcpuUIExp ) ) * self.pcpuUBase 
        
    def urban2yrQ(self, cum_da, impcov):
        if self.Basin == 'Georgia Region 1':
                return (self.p2UBase* Power( ( cum_da / 640 ), self.p2UAExp ) )  * ( Power( 10 , ( self.p2UIExp * impcov ) ) )
        else:
                return ( Power( ( cum_da / 640 ) , self.p2UAExp ) ) * ( Power( impcov, self.p2UIExp ) ) * self.p2UBase

    def urban10yrQ(self, cum_da, impcov):
        if self.Basin == 'Georgia Region 1':
                return (self.p10UBase* Power( ( cum_da / 640 ), self.p10UAExp ) )  * ( Power( 10 , ( self.p10UIExp * impcov ) ) )
        else:
                return ( Power( ( cum_da / 640 ) , self.p10UAExp ) ) * ( Power( impcov, self.p10UIExp ) ) * self.p10UBase 
        
    def urban25yrQ(self, cum_da, impcov): 
        if self.Basin == 'Georgia Region 1':
                return (self.p25UBase* Power( ( cum_da / 640 ), self.p25UAExp ) )  * ( Power( 10 , ( self.p25UIExp * impcov ) ) )
        else:            
                return ( Power( ( cum_da / 640 ) , self.p25UAExp ) ) * ( Power( impcov, self.p25UIExp ) ) * self.p25UBase 
        
    def ruralQcp(self, cum_da, impcov):
        return ( Power( ( cum_da / 640 ) , self.pcprRAExp ) ) * self.pcprRBase

        

##def ChannelProtection(hp, BMP_pts, fld):
##    # Flow reduction calcs
##    
##    flowdir = Raster(os.path.join(hp.Workspace + "\\WIPoutput.mdb", "flowdir")) * hp.Mask 
##    Cum_da = Raster(os.path.join(hp.Workspace + "\\WIPoutput.mdb", "cumda"))
##    Cumulative_Impervious = Raster(os.path.join(hp.Workspace + "\\WIPoutput.mdb", "cumimpcovlake"))
##    flowdir.save(os.path.join(hp.SWorkspace, "flowdir")) 
##    
##    arcpy.CopyRaster_management (os.path.join(hp.Workspace + "\\WIPoutput.mdb", "mask"), os.path.join(hp.SWorkspace, "mask"))
##    mask = Raster(os.path.join(hp.SWorkspace, "mask"))
##    
##    hp.log("Convert Single BMP Project to Raster...")
##    RasBMPpts = hp.GetTempRasterPath("RasBMPpts")
##    arcpy.FeatureToRaster_conversion(BMP_pts, fld, RasBMPpts, flowdir)
##    thisBMPras = Raster(RasBMPpts)
##    
##    hp.log("Back out modified drainage area...")
##    USGS = hp.GetDataTable("USGSvars.csv")
##    if not hp.Basin in USGS:
##        hp.log("Could not find matching Basin")
##        raise Exception
##    else:
##        
##        if hp.Basin == 'Georgia Region 1':
##            Mod_da = 640 * Power( ( thisBMPras / ( USGS[hp.Basin]['cpuUBase'] * Power( 10,(Cumulative_Impervious * USGS[hp.Basin]['cpuUIExp'] )) ) ), ( 1 / USGS[hp.Basin]['cpuUAExp'] ) )
##        else:
##            Mod_da = 640 * Power( ( thisBMPras / ( USGS[hp.Basin]['cpuUBase'] * Power( Cumulative_Impervious, USGS[hp.Basin]['cpuUIExp'] ) ) ), ( 1 / USGS[hp.Basin]['cpuUAExp'] ) )
##
##            
##    hp.log("Convert to percent reduction in accumulation...")
##    acc_red = (1 - ( Mod_da / Cum_da))* mask
##    acc_red.save(os.path.join(hp.SWorkspace,"acc_red_cp"))
##    
##    ModCumDa_u = hp.BMP2DA(flowdir, "ModCumDa_asc", mask, acc_red)
##    
##    hp.log("Convert units...")
##    conv = hp.units['cellsqft'] / 43560
##    ModCumDa = ModCumDa_u * conv
##    
##    hp.log("Calculating urbanQcp...")
##    usgs_calcs = USGSVars(hp.Basin)
##    urbanQcp = usgs_calcs.urbanQcp(ModCumDa, Cumulative_Impervious)
##    
##    
##    return ModCumDa, thisBMPras, urbanQcp
    
def CalcErosivity(hp, DefEro, TSSprod, pointSrcRaster, URratio, Streams_rc):
    
    if type(pointSrcRaster) == Raster:
        pointsrc = True
    else:
        pointsrc = False
    
    hp.log("Adding erosivity (%s and %s)..." % ((DefEro != 0), pointsrc))
    if DefEro and not pointsrc:
        output = ( Streams_rc * Power(URratio, 1.5 ) + BooleanNot( Streams_rc)) * TSSprod 
    elif not DefEro and pointsrc:
        output = TSSprod + pointSrcRaster
    elif not DefEro and not pointsrc:
        output = TSSprod 
    else: 
        output = (( Streams_rc * Power( URratio, 1.5 ) + BooleanNot( Streams_rc)) * TSSprod  ) + pointSrcRaster
    return output

            
if __name__ == "__main__":

    if len(sys.argv) > 1:
        w = WIP(sys.argv[1])
    else:
        w = WIP()
    w.writebat()

    
