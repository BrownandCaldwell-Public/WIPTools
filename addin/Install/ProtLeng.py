
# Import system modules
import sys, os
import Helper
import regression
import arcpy
from arcpy import env
arcpy.env.extent = "MAXOF"
from arcpy.sa import *

hp = Helper.Helper(sys.argv)
try:
    # Local variables
    bmp_noclip = sys.argv[1]
          
    # Vectors
    vecMask = os.path.join(hp.SWorkspace, "vectMask.shp")
    BMPpts = os.path.join(hp.SWorkspace, "BMPptsPL.shp")
    arcpy.RasterToPolygon_conversion(hp.Mask, vecMask, "SIMPLIFY", "Value")
    hp.SetPIDs(bmp_noclip)
    arcpy.Clip_analysis(bmp_noclip, vecMask, BMPpts)
    OID = "PID"
    
    # Setup output field
    ProtLen_fld  = "ProtLeng"
        
    hp.log("Calculate Existing Urban and Rural discharges...")
    
    Cumulative_Impervious = Raster(os.path.join(hp.Workspace + "\\WIPoutput.mdb", "cumimpcovlake") )
    Cum_da = Raster(os.path.join(hp.Workspace + "\\WIPoutput.mdb", "cumda"))
##    usgs_calcs = Helper.USGSVars(hp.Basin)
    U1yr_ext = regression.urbanQcp(hp.Basin, Cum_da, Cumulative_Impervious)
    U1yr_ext.save(os.path.join(hp.SWorkspace, "U1yr_ext"))
    
    hp.log("Looping through input BMPs...")    
    BMProws = arcpy.UpdateCursor(BMPpts)
    
    all = arcpy.GetCount_management(BMPpts)
    count = 1
    for BMProw in BMProws:
        BMP_FID = BMProw.getValue(OID)
        
        hp.log("  Processing point %s of %s..." % (count, all)) 
        #~ print "   %s %s: %s" % (BMPpts, OID, BMP_FID), 
        bmp_Ex1yr = float(BMProw.getValue(sys.argv[2]))
        bmp_Prop1yr = float(BMProw.getValue(sys.argv[3]))
        
        if not (bmp_Prop1yr < bmp_Ex1yr):
            hp.log("   No Channel Protection from this BMP")
        else:
            hp.log("   Found Channel Protection BMP")            
            
            hp.log("   Creating new dataset for this point")
            SinBMPpts = os.path.join(hp.SWorkspace, "PLBMPpts%s.shp" % BMP_FID)
            hp.GetSubset(BMPpts, SinBMPpts, " \"PID\" = %s " % BMP_FID)
            
            hp.log("   Calculating Urban 1yr Flow")
            ModCumDa, thisBMPras, Urban_1yrQ = regression.ChannelProtection(hp, SinBMPpts, sys.argv[3])
            # we don't need these rasters at all
            #~ ModCumDa.save(os.path.join(hp.SWorkspace, "ModCumDa"))  
            #~ thisBMPras.save(os.path.join(hp.SWorkspace, "thisBMPras"))
            Urban_1yrQ.save(os.path.join(hp.SWorkspace, "Urban_1yrQ"))
            
          
            flowdir = os.path.join(hp.Workspace + "\\WIPoutput.mdb", "flowdir")* hp.Mask 
            flowdir.save(os.path.join(hp.SWorkspace, "flowdir")) 
            
            ans = hp.ProtLength(thisBMPras, flowdir, Urban_1yrQ, U1yr_ext)
            hp.log ("   The cell distance calculated by protleng.exe is: %s" % ans)
            hp.SetAtt(BMP_FID, ProtLen_fld, ans * hp.units['size'], bmp_noclip)
            
        count += 1
        
    hp.Close()
    
except:       
    i, j, k = sys.exc_info()
    hp.EH(i, j, k)
    
