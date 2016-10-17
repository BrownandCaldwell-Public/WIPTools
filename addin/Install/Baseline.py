
# Import system modules
import sys, os
# import Helper
import arcpy
from arcpy import env
arcpy.env.extent = "MAXOF"
from arcpy.sa import *

# hp = Helper.Helper(sys.argv)
try:
    arcpy.env.overwriteOutput = True
    
    # Local variables
    Cum_da = Raster(os.path.join(env.Workspace + "\\WIPoutput.mdb", "cumda"))
    arcpy.env.extent = os.path.join(env.Workspace + "\\WIPoutput.mdb", "flowacc")
    
    bmp_noclip = sys.argv[1]
    bmp_type = sys.argv[2]
    bmp_eff = sys.argv[3].split(';')
    
    landuses = []
    use_existing = sys.argv[5]
    use_future = sys.argv[6]
    # prod_existing = hp.models['ProdTrans']['input'][15].strip()
    # prod_future = hp.models['ProdTrans']['input'][17].strip()
    if use_existing.lower() == "true":
        landuses.append("E")
    if use_future.lower() == "true":
        landuses.append("F")
    
    # print "use_existing.lower(): %s, use_future.lower(): %s" % (use_existing.lower(), use_future.lower())
    
    # error = ""
    # if not landuses:
        # error = "You must select Existing and/or Future Landuse conditions"
    # if use_existing.lower() == "true" and not prod_existing:
        # error = "You must run Existing in Production Transport first"
    # if use_future.lower() == "true" and not prod_future:
        # error = "You must run Future in Production Transport first"
    # if error:
        # hp.log(error)
        # raise Exception, error
    
    # parameters = hp.GetAlias(bmp_eff)
    # exec(hp.models['ProdTrans']['input'][-1])
    
    hp.log("Clipping BMP points to work area (or mask)...")
    # Rasters
    flowdir = os.path.join(env.Workspace + "\\WIPoutput.mdb", "flowdir")* hp.Mask 
    flowdir.save(os.path.join(hp.SWorkspace, "flowdir")) 
    
    Streams_nd = Raster(os.path.join(env.Workspace + "\\WIPoutput.mdb", "streams"))
    streams = hp.RemoveNulls(Streams_nd)
    #~ streams.save(os.path.join(hp.SWorkspace, "streams1"))
    
    vecmask = os.path.join(hp.SWorkspace, "vectmask.shp")
    BMPpts = os.path.join(hp.SWorkspace, "BMPpts.shp")
    arcpy.RasterToPolygon_conversion(hp.Mask, vecmask, "SIMPLIFY", "Value")
    arcpy.Clip_analysis(bmp_noclip, vecmask, BMPpts)
    
    hp.log("Finding BMP projects...")
    ExBMPpts = os.path.join(hp.SWorkspace, "ExBMPpts.shp")
    count = hp.GetSubset(BMPpts, ExBMPpts, " \"%s\" = 'BMP' " % bmp_type)
    
    if count < 1:
        raise Exception("No BMP points, stopping")
        
    for LU in landuses:
        for param in parameters:
            pn = param[:10].strip()
            TSSProd = os.path.join(hp.SWorkspace, "q" + LU + pn)
            arcpy.CopyRaster_management(os.path.join(env.Workspace + "\\WIPoutput.mdb", "q" + LU + pn), TSSProd)
            
            #~ TSSP_ero = "t" + LU + pn
            K = os.path.join(env.Workspace, "WIPoutput.mdb\\K" + LU[0] + pn)
            
            TSSLoadOutput = (os.path.join(env.Workspace + "\\WIPoutput.mdb", "L" + LU + pn))
            TSSYield = (os.path.join(env.Workspace + "\\WIPoutput.mdb", "Y" +LU + pn))
            TSSYldvec = (os.path.join(env.Workspace + "\\WIPoutput.mdb", pn + LU+ "yield"))
            
            hp.log("Convert BMPs to Raster...")
            arcpy.FeatureToRaster_conversion(ExBMPpts, parameters[param], os.path.join(hp.SWorkspace,"b" + LU + pn), flowdir)
            BMPs = Raster(os.path.join(hp.SWorkspace,"b" + LU + pn))
            
            hp.log("Combine decay function with BMP reduction")
            bmptemp = hp.RemoveNulls(BMPs)
            weightred = 1 - ( K * ( 1 - (bmptemp / 100.0 ) ) )
            weightred.save(os.path.join(hp.SWorkspace,"weightred"))
            
            hp.log("Calculate Reduction...")
            #~ fromv10 args = '"%s" "%s" "%s" "%s" "%s"' % (flowdir, hp.SWorkspace + "\\TSSLoad.txt", hp.SWorkspace + "\\flowdir.asc", os.path.join(hp.SWorkspace, data_ero), hp.SWorkspace + "\\weightred")
            #~ from 931 args = '"%s" "%s" "%s" "%s" "%s"' % (flowdir, hp.SWorkspace + "\\TSSLoad.txt", hp.SWorkspace + "\\flowdir.asc", os.path.join(hp.SWorkspace, TSSProd), hp.SWorkspace + "\\weightred")
           
            Existingtss = hp.BMP2DA(flowdir, "Existingtss", Raster(TSSProd), weightred)
            
            hp.log("Clip...")
            TSSLoadOutput = hp.Mask * Existingtss
            hp.saveRasterOutput(TSSLoadOutput, "L" + LU + pn)
            
            hp.log("Calculate Yield...")
            TSSYield = TSSLoadOutput / Cum_da
            hp.saveRasterOutput(TSSYield, "Y" +LU + pn)
            
            hp.log("Clip to streams...")
            # and round
            TSSYieldcl = Int(RoundUp( RoundDown( Streams_nd * TSSYield * 20000 ) / 2 ))
            
            TSSYldvec = os.path.join(env.Workspace + "\\WIPoutput.mdb", pn + LU+ "yield")
            hp.log("Vectorize...")
            StreamToFeature(TSSYieldcl, flowdir, TSSYldvec, "NO_SIMPLIFY")
            hp.models[hp.current_tool]["output"].append(TSSYldvec)
            
            hp.ConvertGRIDCODEatt(TSSYldvec)
            
    summary_pts = (os.path.join(env.Workspace + "\\WIPoutput.mdb", "summarypts"))
    arcpy.Clip_analysis(sys.argv[4], vecmask, summary_pts)
    hp.SetPIDs(summary_pts)
    hp.models[hp.current_tool]["output"].append(summary_pts)
    
    for LU in landuses:
        for param in parameters:
            pn = param[:10].strip()
            TSSLoadOutput = Raster(os.path.join(env.Workspace + "\\WIPoutput.mdb", "L" + LU[0] + pn))
            hp.Summarize(TSSLoadOutput, summary_pts)        
            
    hp.Close()
    
except:       
    i, j, k = sys.exc_info()
    hp.EH(i, j, k)
    