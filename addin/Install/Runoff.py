# Import system modules
import sys, string, os
#~ import win32com.client
#~ from Utils import *
import Helper
import regression
import arcpy
from arcpy import env
from arcpy.sa import *

hp = Helper.Helper(sys.argv)
try:
    os.chdir(os.path.split(sys.argv[0])[0])
    scratch = os.path.join(hp.Workspace, "Scratch")
    
    hp.Basin = sys.argv[1]
    Landuse = sys.argv[2]
    LanduseAtt = sys.argv[3]
    Soils = sys.argv[4]
    SoilsAtt = sys.argv[5]
    
    # Set outputs
    
    impcov = os.path.join(hp.SWorkspace, "impcov")
     
    Mask = os.path.join(hp.Workspace+ "\\WIPoutput.mdb","Mask")
    arcpy.env.extent = Mask
    
    flowdir = os.path.join(hp.Workspace + "\\WIPoutput.mdb", "flowdir")* hp.Mask 
    flowdir.save(os.path.join(hp.SWorkspace, "flowdir")) 
    
    #~ hp.log(" Clipping input vectors to work area (or mask)")
    vecMask = os.path.join(hp.SWorkspace, "vectMask.shp")
    arcpy.RasterToPolygon_conversion(hp.Mask, vecMask, "SIMPLIFY", "Value")
    
    hp.log("Clip inputs to watershed...")
    arcpy.Clip_analysis(Soils,  vecMask, os.path.join(hp.SWorkspace,"Soilsclpd.shp"))
    arcpy.Clip_analysis(Landuse, vecMask, os.path.join(hp.SWorkspace,"LUclpd.shp"))
    
    hp.log("Union of soils and landuse...")
    arcpy.Union_analysis([os.path.join(hp.SWorkspace,"LUclpd.shp"), os.path.join(hp.SWorkspace,"Soilsclpd.shp")], os.path.join(hp.SWorkspace,"union.shp"))
    
    hp.log("Add Curve Number to union...")
    LUcodes = hp.GetDataTable("LUT.csv")
    print LUcodes
    
    arcpy.AddField_management(os.path.join(hp.SWorkspace,"union.shp"), "CN", "LONG", "", "", "", "", "NON_NULLABLE", "NON_REQUIRED", "")
    rows = arcpy.UpdateCursor(os.path.join(hp.SWorkspace,"union.shp"))
    row = rows.next()
    while row:
        CN = 1
        
        SoilType = row.getValue(SoilsAtt)
        if SoilType not in ["A", "B", "C", "D", "W", "BorrowPits", "GulliedLand", "UL"]:
            hp.log("  Soil type " + SoilType + " is not equal to A, B, C, D, W (Water), BorrowPits, GulliedLand, or UL (Urban Land), skipping")
        else:
            
            LUType = row.getValue(LanduseAtt)
            if SoilType in ["A", "B", "C", "D"]:
                SoilType = "CurveN" + SoilType
                
            if not LUType in LUcodes:
                hp.log("  Could not find " + LUType + " in land use table (LUT), skipping")
            else:
                CN = LUcodes[LUType][SoilType]
                
        row.setValue("CN", CN)
        rows.updateRow(row)
        row = rows.next()
    del row, rows
    
    cum_da = Raster(os.path.join(hp.Workspace + "\\WIPoutput.mdb", "cumda"))
    
    hp.log("Convert union to raster...")
    arcpy.PolygonToRaster_conversion(os.path.join(hp.SWorkspace,"union.shp"), "CN", os.path.join(hp.SWorkspace,"CurveN"),"MAXIMUM_AREA","None", cum_da)
    CurveN = Raster(os.path.join(hp.SWorkspace,"CurveN"))
    
    hp.log("Get precipitation contants for %s ..." % (hp.Basin))
    f = open(os.path.join(hp.AppPath, r'../ToolData/Precipdepth.csv'), 'r')
        
    header = f.readline().strip().replace('"', "").split(",")
    pdepth = {}
    for i in f.readlines():
        data = i.strip().replace('"', "").split(',')
        if hp.Basin in data[0]:
            for j in range(1, len(header)):
                pdepth[header[j]] = float(data[j])
    f.close()
    
    if not pdepth: raise ValueError, "Why is this empty?!"
    else: print pdepth
    
    #   WQV ----------------------------------------------------------------------------------------------------------------------------------------------------------------------
    hp.log("WQ Vol Calc...")
    flowacc = Raster(os.path.join(hp.Workspace + "\\WIPoutput.mdb", "flowacc"))
    Convraster = (cum_da*43560)/12 
    cumimpcovlake = Raster(os.path.join(hp.Workspace + "\\WIPoutput.mdb", "cumimpcovlake"))
    WQVin = ((cumimpcovlake * 0.009) + 0.05) * pdepth["WQdepth"]
    WQVin.save(os.path.join(hp.SWorkspace, "WQVin"))

    hp.log("WQ Vol Conv Calc...")

    
    WQV = WQVin * Convraster
    hp.saveRasterOutput(WQV, "WQV") 
            
    #~ CurveN = (((1000 / (16 + (10 * WQVin) - (10 * Power((Power(WQVin, 2)) + (1.25 * 1.2 * WQVin), 0.5)))) - 73.852036) / 25.632621) * 38 + 60
    
    #   1-yr ----------------------------------------------------------------------------------------------------------------------------------------------------------------------
    hp.log("1-yr Vol Calc...")
    # should pull out precip value to tool data table...
    V1in = Power( ( pdepth["depth1yr"] - 0.2 * (( 1000.00 / CurveN ) - 10) ), 2) / (pdepth["depth1yr"] + (0.8 * (( 1000.00 / CurveN ) - 10)))
    V1in.save(os.path.join(hp.SWorkspace, "V1in"))
    
    hp.log("1-yr Vol Conv...")
    V1ft = V1in * hp.units['cellsqft'] / 12 * hp.Mask
    
    hp.log("Flow Accum...")
    vol1yr = hp.BMP2DA(flowdir, "V1", V1ft)
        
    chnnl_prot = hp.Mask * vol1yr
    hp.saveRasterOutput(chnnl_prot,"chnnlprot")

    #~ #   10-yr ----------------------------------------------------------------------------------------------------------------------------------------------------------------------
    hp.log("10yr Urban Vol Calc...")
    _V10U = Power((pdepth["depth10yr"] - 0.2 * (( 1000.00 / CurveN ) - 10)) , 2) / (pdepth["depth10yr"] + (0.8 * (( 1000.00 / CurveN ) - 10)))
    
    hp.log("10yr Conv...")
    V10Uft = _V10U * hp.units['cellsqft'] / 12 * hp.Mask
    
    hp.log("Flow Accum...")
   
    V10U = hp.BMP2DA(flowdir, "V10U", V10Uft)
    
    hp.log("10yr Rural Vol Calc...")
    _V10R = (pdepth["depth10yr"] - 0.2 * (( 1000.00 / pdepth["baseCN"]) - 10))** 2 / (pdepth["depth10yr"] + (0.8 * (( 1000.00 / pdepth["baseCN"]) - 10)))
    
    hp.log("10yr Rural Vol Conv...")
    V10Rft = _V10R * hp.units['cellsqft'] / 12 * hp.Mask
    
    hp.log("Flow Accum...")
    V10R = hp.BMP2DA(flowdir,"V10R", V10Rft)
    
    hp.log("10yr Flood storage...")
    V10Flood = hp.Mask * (V10U - V10R)
    hp.saveRasterOutput(V10Flood, "V10Flood")
    
    hp.log("10yr Discharge...")
    cumimpcov = Raster(os.path.join(hp.Workspace + "\\WIPoutput.mdb", "cumimpcov"))


    
    #~ #   25-yr ----------------------------------------------------------------------------------------------------------------------------------------------------------------------
    hp.log("25yr Urban Vol Calc...")
    _V25U = Power((pdepth["depth25yr"] - 0.2 * (( 1000.00 / CurveN ) - 10)) , 2) / (pdepth["depth25yr"] + (0.8 * (( 1000.00 / CurveN ) - 10)))

    hp.log("25yr Conv...")
    V25_U_ft= _V25U * hp.units['cellsqft'] / 12 * hp.Mask
    
    hp.log("Flow Accum...")
    
    V25U = hp.BMP2DA(flowdir, "V25U", V25_U_ft)
    
    hp.log("25yr Rural Vol Calc...")
    _V25R = (pdepth["depth25yr"] - 0.2 * (( 1000.00 / pdepth["baseCN"]) - 10))** 2 / (pdepth["depth25yr"] + (0.8 * (( 1000.00 / pdepth["baseCN"]) - 10)))

    hp.log("25yr Rural Vol Conv...")
    V25_R_ft = _V25R * hp.units['cellsqft'] / 12 * hp.Mask
    
    hp.log("Flow Accum...")
    
    V25R = hp.BMP2DA(flowdir, "V25R", V25_R_ft)
    
    hp.log("25yr Flood storage...")
    V25Flood = hp.Mask * (V25U - V25R)
    hp.saveRasterOutput(V25Flood, "V25Flood")
    
     
##    usgs_calcs = Helper.USGSVars(hp.Basin)
##    usgs_calcs = Helper.newregression(hp.Basin)
    
    hp.log("Calculating Undeveloped Discharge...")
        
    UndevQ = regression.ruralQcp(hp.Basin, cum_da)
    hp.saveRasterOutput(UndevQ, "UndevQ")
        
    urban2yrQ_var = regression.urban2yrQ(hp.Basin, cum_da,cumimpcovlake)
    hp.saveRasterOutput(urban2yrQ_var, "urban2yrQ")
    urban10yrQ_var = regression.urban10yrQ(hp.Basin,cum_da,cumimpcovlake)
    hp.saveRasterOutput(urban10yrQ_var, "urban10yrQ")    
    urban25yrQ_var = regression.urban25yrQ(hp.Basin,cum_da,cumimpcovlake)
    hp.saveRasterOutput(urban25yrQ_var, "urban25yrQ")
  
    hp.Close()

except:       
    i, j, k = sys.exc_info()
    hp.EH(i, j, k)

    
