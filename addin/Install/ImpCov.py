
# Import system modules
import sys, os 
import Helper
import arcpy
from arcpy import env
from arcpy.sa import *

hp = Helper.Helper(sys.argv)
try:
    
    # Script arguments...
   
    Cum_da = os.path.join(hp.Workspace, "cumda")
    Streams = os.path.join(hp.Workspace + "\\WIPoutput.mdb", "streams")
    Lakes_Polygon_Vector_preclip = sys.argv[2]
    Impervious_Polygons_Vector_preclip = sys.argv[1]
    
    # Local variables...
    Flow_Accumulation = os.path.join(hp.Workspace + "\\WIPoutput.mdb", "flowacc")
    Impervious_Cover_pc = os.path.join(hp.SWorkspace, "impcovpc")
    demximp = os.path.join(hp.Workspace, "demximp")
    
    Flow_Direction_Raster = os.path.join(hp.Workspace + "\\WIPoutput.mdb", "flowdir")* hp.Mask 
    Flow_Direction_Raster.save(os.path.join(hp.SWorkspace, "flowdir")) 
    
    
    # Reset raster env variables for cell size to prevent impcov calc from crashing
    
    cellSize = hp.units['cellsqft']**0.5
##    arcpy.env.cellSize = "MINOF"
    
    hp.log(" Clipping input vectors to work area (or mask)")
    vecMask = os.path.join(hp.SWorkspace,"vectMask.shp")
    arcpy.RasterToPolygon_conversion(hp.Mask, vecMask, "SIMPLIFY", "Value")
    
    Lakes_Polygon_Vector = os.path.join(hp.SWorkspace, "lakespolyvec.shp")
    arcpy.Clip_analysis(Lakes_Polygon_Vector_preclip, vecMask, Lakes_Polygon_Vector)
    Impervious_Polygons_Vector = os.path.join(hp.SWorkspace, "imppolyvec.shp")
    arcpy.Clip_analysis(Impervious_Polygons_Vector_preclip, vecMask, Impervious_Polygons_Vector)
    
    # Data Validation
    count = int(arcpy.GetCount_management(Impervious_Polygons_Vector).getOutput(0))
    if count < 1:
        raise Exception, "No impervious areas in the study area"
    count = int(arcpy.GetCount_management(Lakes_Polygon_Vector).getOutput(0))
    if count < 1:
        raise Exception, "No lakes in the study area"
    
    hp.log("Converting impervious polygons to raster...")
    impid = 'NewId'
    hp.AddID(Impervious_Polygons_Vector, impid)
    Feature_Impe1 = os.path.join(hp.SWorkspace,"Feature_Impe1")
    arcpy.PolygonToRaster_conversion(Impervious_Polygons_Vector, impid, (os.path.join(hp.SWorkspace,"Feature_Impe1")),"MAXIMUM_AREA","None", float(cellSize)/10)
    
    
    hp.log("Reclassifying impervious raster...")
    Reclass_Feat1 = hp.RemoveNulls(Feature_Impe1)
    Reclass_Feat1.save(os.path.join(hp.SWorkspace,"Reclass_Feat1"))
    
    Mask = os.path.join(hp.Workspace+ "\\WIPoutput.mdb","Mask")
    
    arcpy.env.extent = Mask
    hp.log("Computing block statistics...")
    BlockSt_Recl1 = BlockStatistics(Reclass_Feat1, NbrRectangle(10, 10, "CELL"), "SUM", "DATA")
##    BlockSt_Recl1.save(os.path.join(hp.SWorkspace,"BlockSt_Recl1"))
    
    hp.log("Aggregate...")
    Imp_Cover_pc = Aggregate(BlockSt_Recl1,10, "MEAN", "EXPAND", "DATA")
    Imp_Cover = ExtractByMask(Imp_Cover_pc, Mask)
    
##    Imp_Cover_pc = hp.Mask * Imp_Cover  ## DOES NOT WORK
    Imp_Cover.save(os.path.join(hp.SWorkspace,"Imp_Cover"))
    
    Flow_Accumulation_weighted = hp.BMP2DA(Flow_Direction_Raster,"flow_accw", Imp_Cover)
    
    hp.saveRasterOutput(Imp_Cover, "Impcov")
    
##    if os.path.exists(demximp):
##        demximp_clip = demximp*hp.Mask
##        args = '"%s" "%s" "%s"' % (Flow_Direction_Raster, demximp_asc, demximp_clip.catalogPath)
##        hp.RunScript("BMP2DA", args)
##
##        demximp_extr = Raster(demximp_asc)
##    else:
    demximp_extr = 0
        
    hp.log("Divide...")
    cumimpcov=hp.Mask * (Flow_Accumulation_weighted + demximp_extr ) / Flow_Accumulation
    hp.saveRasterOutput(cumimpcov, "cumimpcov")
    
    hp.log("Clip output to streams...")
    Clipped_ = Int(RoundUp(RoundDown(cumimpcov * Streams * 20000 ) / 2))
    
    hp.log("Vectorize...")
    vector = os.path.join(hp.Workspace + "\\WIPoutput.mdb", "cumimpcovvec")
    StreamToFeature(Clipped_, Flow_Direction_Raster, vector, "NO_SIMPLIFY")
    hp.models[hp.current_tool]["output"].append(vector)
    
    hp.ConvertGRIDCODEatt(vector)
    
    # Add lakes for other tools that use it
    hp.log("Lake features to Raster...")
    lakeid = "NewId"
    hp.AddID(Lakes_Polygon_Vector, lakeid)
    lakes_temp = os.path.join(hp.SWorkspace, "lakes_temp")
    arcpy.PolygonToRaster_conversion(Lakes_Polygon_Vector, lakeid, lakes_temp,"MAXIMUM_AREA","None", Flow_Direction_Raster)
    Lakes = Reclassify(lakes_temp, "VALUE", "-10000000000 10000000000 1;NODATA 0", "DATA")
    Lakes.save(os.path.join(hp.Workspace,"WIPoutput.mdb\\Lakes"))
        
    
    hp.log("Add lakes to Impervious Cover...")
    Impervious_Cover_Lakes = (Imp_Cover*(BooleanNot(Lakes))+(Lakes*100))
    
    hp.log("Flow Accum with Lakes...")
    Flow_Accumulation_lakes=hp.BMP2DA(Flow_Direction_Raster, "LFlowacc", Impervious_Cover_Lakes)
    
    hp.log("Divide...")
    cumimpcovlake = Flow_Accumulation_lakes/Flow_Accumulation
    cumimpcovlake.save(os.path.join(hp.Workspace,"WIPoutput.mdb\\cumimpcovlake"))
        
    hp.Close()

except:       
    i, j, k = sys.exc_info()
    hp.EH(i, j, k)
    
