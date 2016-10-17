
# Import system modules
import sys, os
import Helper
import regression
import arcpy
from arcpy import env
from arcpy.sa import *

hp = Helper.Helper(sys.argv)
try:
    # Local variables
    
    Rural_1yrQ = Raster(os.path.join(hp.Workspace + "\\WIPoutput.mdb", "UndevQ"))
    BMPpts = os.path.join(hp.SWorkspace, "BMPptsSin.shp")
    Units = hp.units['size']
    wtredBMPs = os.path.join(hp.SWorkspace, "wtredBMPs")
    
    bmp_noclip = sys.argv[1]
    existing_efficiencies = sys.argv[5].split(';')
    proposed_efficiencies = sys.argv[6].split(';')
    landuse = sys.argv[7]
    if sys.argv[8] != "#":
         stream_reductions = sys.argv[8].split(';')
    strlngth = sys.argv[9]
    
    #~ parameters = hp.GetAlias(existing_efficiencies)
    
    Streams_nd = Raster(os.path.join(hp.Workspace + "\\WIPoutput.mdb", "streams"))
    Stream_Raster = hp.RemoveNulls(Streams_nd)
        
    arcpy.CopyRaster_management(hp.Workspace + "\\WIPoutput.mdb\\cumda", os.path.join(hp.SWorkspace, "cumda"))
    Cum_da =  Raster(os.path.join(hp.SWorkspace, "cumda"))
    
    flowdir = ExtractByMask(os.path.join(hp.Workspace + "\\WIPoutput.mdb", "flowdir"), hp.Mask )
    flowdir.save(os.path.join(hp.SWorkspace, "flowdir")) 
    
    if landuse == "Existing": LU = "E" 
    else: LU = "F"
   
    vecMask = os.path.join(hp.SWorkspace, "vectMask.shp")
    arcpy.RasterToPolygon_conversion(hp.Mask, vecMask, "SIMPLIFY", "Value") 
       
    existing_params = hp.GetAlias(existing_efficiencies)
    proposed_params = hp.GetAlias(proposed_efficiencies)
    streamreduc_params = hp.GetAlias(stream_reductions)
    if not existing_params.keys().sort() == proposed_params.keys().sort() == streamreduc_params.keys().sort():
        raise Exception, "Parameters found for Existing efficiencies, Proposed efficiencies, and Stream Reductions does not match"
        
    params = {}
    
    exec(hp.models['ProdTrans']['input'][-1])
    
    hp.log("Preparing input BMPs...")    
    hp.SetPIDs(bmp_noclip)
    arcpy.Clip_analysis(bmp_noclip, vecMask, BMPpts)
    
    for p in existing_params: # If we switch the loops below to be param first point second, then we could include this stuff in the param loop. Right now we don't want to run this calc for every point, hence this bit of code duplication outide the main loops
                    
        pn = p[:10].strip()
        TSSprod = os.path.join(hp.Workspace + "\\WIPoutput.mdb", "p" + LU + pn)
        pointsrc = ""
        if os.path.exists(os.path.join(hp.SWorkspace, "pt" + pn)):
            pointsrc = "pt" + pn
        defEro = 0
        if p in params:
            defEro = params[p]['DefEro']   
            
        hp.log("Calculate Urban/Rural ratio...")
        Cumulative_Impervious = Raster(os.path.join(hp.Workspace + "\\WIPoutput.mdb", "cumimpcovlake"))
##        usgs_calcs = Helper.USGSVars(hp.Basin)
        urbanQcpbas = regression.urbanQcp(hp.Basin, Cum_da, Cumulative_Impervious)
        URratio = urbanQcpbas / Rural_1yrQ
        
        hp.log("Add erosivity to existing %s production..." % p)
        TSSP_ero_ext = Helper.CalcErosivity(hp, defEro, TSSprod, pointsrc, URratio, Stream_Raster) # need this to be here so that is not repeated many times inside CP, even if there are no CP points
        arcpy.CopyRaster_management(TSSP_ero_ext, os.path.join(hp.SWorkspace, "ero") + p[:10].strip())
        
    
    hp.log("Checking for input BMPs in your area...")    
    all = arcpy.GetCount_management(BMPpts)
    if all <= 1:
        raise Exception("You must have more than one point to run this tool!")
    
    
    hp.log("Looping through input BMPs...")    
    BMProws = arcpy.SearchCursor(BMPpts)
    counter = 0
    count = 1
    #~ while BMProw:        
    for BMProw in BMProws:
        
        print "%s\n" % (75*'-')
        print BMPpts
        BMP_FID = BMProw.getValue("PID")
        
        hp.log("  Processing point %s of %s..." % (count, all)) 
        print "   %s BMPID: %s\n" % (BMPpts, BMP_FID)
        
        bmp_type = BMProw.getValue(sys.argv[2])
        bmp_Ex1yr = float(BMProw.getValue(sys.argv[3]))
        bmp_Prop1yr = float(BMProw.getValue(sys.argv[4]))
        hp.log("  Found bmp type of %s, existing Q1 of %s, and proposed Q1 of %s for PID %s" % (bmp_type, bmp_Ex1yr, bmp_Prop1yr, BMP_FID))
        
        SinBMPpts = os.path.join(hp.SWorkspace, "SinBMPpts.shp")
        hp.GetSubset(BMPpts, SinBMPpts, " \"PID\" = %s " % BMP_FID)
        
        SingleBMP = os.path.join(hp.SWorkspace, "SingleBMP")
        hp.log("Convert this project to a raster mask...")
        arcpy.FeatureToRaster_conversion(os.path.join(hp.SWorkspace,SinBMPpts), "PID", SingleBMP, flowdir)
        SinBMPmask = Reclassify(SingleBMP, "VALUE", "NoData 0; 0.001 100000 1", "DATA")
        SinBMPmask.save(os.path.join(hp.SWorkspace,"SinBMPmask"))
        
        for p in existing_params:
            pn = p[:10].strip()
            K = os.path.join(hp.SWorkspace, "K" + pn)

            TSSP_ero_ext = Raster(os.path.join(hp.SWorkspace, "ero" + pn))
            
            sum, chanp_red, washoff_red = 0, 0, 0
            
            bmp_eeff = float(BMProw.getValue(existing_params[p]))
            bmp_peff = float(BMProw.getValue(proposed_params[p]))
            stream_red_per_ft = float(BMProw.getValue(streamreduc_params[p])) 
            hp.log("  Found existing bmp efficiency of %s, proposed bmp efficiency of %s, and stream reduction of %s for PID %s" % (bmp_eeff, bmp_peff, stream_red_per_ft, BMP_FID))
            
            pointsrc = ""
            if os.path.exists(os.path.join(hp.SWorkspace, "pt" + pn)):
                pointsrc = "pt" + pn
            defEro = 0
            
            if p in params:
                defEro = params[p]['DefEro']          
            
            if bmp_type.lower() in ['bmp', 'new bmp']:
                if bmp_Prop1yr < bmp_Ex1yr:
                    Channel_Prot = 1
                else:
                    Channel_Prot = 0
                    
                if not defEro:
                    hp.log("   No Default erosivity for this BMP")
                    Channel_Prot = 0
                
                if not Channel_Prot:
                    hp.log("   No Channel Protection from this BMP")
                else:
                    
                    hp.log("   Calculating Channel Protection from this BMP")
                    #~ arcpy.Merge_management ("ChanBMPpts.shp; SinBMPpts.shp", "merge.shp")
                    ModCumDa, thisBMPras, this_ds = regression.ChannelProtection(hp, SinBMPpts, sys.argv[4])
                    ModCumDa.save(os.path.join(hp.SWorkspace,"modcumda"))
                    this_ds.save(os.path.join(hp.SWorkspace,"this_ds"))
                    
                    hp.log("Calculate Future Urban/Rural ratio...")
                    URratio = this_ds / Rural_1yrQ
                    URratio.save(os.path.join(hp.SWorkspace,"urratio"))
                    
                    TSSP_ero = Helper.CalcErosivity(hp, defEro, TSSprod, pointsrc, URratio, Stream_Raster)
                    TSSP_ero.save(os.path.join(hp.SWorkspace,"tssp_ero"))
                    
                    hp.log("%s reduction..." % p)
                    TSSred = TSSP_ero_ext - TSSP_ero
                    TSSred.save(os.path.join(hp.SWorkspace,"tssred"))
                    
                    hp.log("Tabulating %s reduction..." % p)
                    chanp_red = hp.Zonal(TSSred)
                    
                    print "    %s Reduction component from Channel protection = %s\n" % (p, chanp_red)
                            
                if bmp_peff > bmp_eeff:
                    WQ_benefit = 1
                else: 
                    WQ_benefit = 0
                    
                if not WQ_benefit:
                    hp.log("   No Water Quality Benefit from this BMP")
                else:
                    hp.log("   Calculating Water Quality Benefit from this BMP")
                    REMBMPpts = os.path.join(hp.SWorkspace,"RemBMPpts.shp")
                    hp.GetSubset(BMPpts, REMBMPpts, " \"PID\" <> %s AND %s > 0" % (BMP_FID, existing_params[p]))
                    #~ arcpy.CopyFeatures_management(BMPpts, )
                    #~ rows = arcpy.UpdateCursor(os.path.join(hp.SWorkspace,"RemBMPpts.shp"))
                    #~ row = rows.next()
                    #~ while row:
                        #~ if row.getValue("PID") == BMP_FID or float(row.getValue(existing_params[p])) <= 0:
                            #~ rows.deleteRow(row)
                        #~ row = rows.next()
                    #~ del row, rows
                    
                    #~ hp.log("Adding erosivity to %s production..." % p)
                    data_ero = Helper.CalcErosivity(hp, defEro, TSSprod, pointsrc, URratio, Stream_Raster)
                    
                    REMBMPs = (os.path.join(hp.SWorkspace, "REMBMPs"))
                    hp.log("Convert all other BMPs to Raster...")
                    arcpy.FeatureToRaster_conversion(REMBMPpts, existing_params[p], REMBMPs, flowdir)
                    BMPs = hp.RemoveNulls(REMBMPs)
                    wtredBMPs =  ExtractByMask(BMPs / 100.0,  hp.Mask)
                   
                     
                    arcpy.CopyRaster_management(data_ero, os.path.join(hp.SWorkspace,"data_ero"))
                    data_ero1 = Raster(os.path.join(hp.SWorkspace,"data_ero"))
                    counter +=1
                    TSSLoad = hp.BMP2DA(flowdir, pn+str(counter), data_ero1, wtredBMPs)
                    
                                      
                    hp.log("%s reduction..." % p)
                    TSSLoadpt = TSSLoad * (bmp_peff - bmp_eeff) * SinBMPmask / 100
                    
                    hp.log("Tabulating %s reduction..." % p)
                    washoff_red = hp.Zonal(TSSLoadpt)                    
                    print "    %s Reduction component from Washoff benefit = %s\n" % (p, washoff_red)
                    WQ = washoff_red
                    
                sum = chanp_red + washoff_red
                print TSSprod, sum
            
                hp.log("Writing attributes")
                hp.SetAtt(BMP_FID, hp.ShortName(p) + "red" + LU[0], sum, bmp_noclip)
            
            if bmp_type.lower() in ['stream restoration']: 
                # Calculate in-stream reduction ################################
                hp.log("Convert Stream Lengths to Raster...")
                arcpy.env.extent = os.path.join(hp.SWorkspace, "flowdir")
                arcpy.FeatureToRaster_conversion(os.path.join(hp.SWorkspace, "SinBMPpts.shp"), strlngth, os.path.join(hp.SWorkspace, "len"), flowdir)
                slengths = Float(Raster(os.path.join(hp.SWorkspace, "len")))
                  
                thisstream = hp.AttExtract(slengths, flowdir, "thisstream", Stream_Raster, Units)
                
                hp.log("Make mask...")
                ThisBMPmask = Reclassify(thisstream, "Value", ".00001 100000 1;-100000 0 0; NoData 0", "DATA")
                ThisBMPmask.save(os.path.join(hp.SWorkspace,"ThisBMPmask"))
                
                hp.log("Calculate reduction...")
                streamprod = (bmp_peff/ 100) * Raster(TSSprod) * ThisBMPmask * Power(URratio, 1.5)
                streamprod.save(os.path.join(hp.SWorkspace,"streamprod"))
                
                hp.log("Reclassify flowdirection to find straight paths...")
                Flowdirs = Reclassify(flowdir, "VALUE", "1 1;2 0;4 1;8 0;16 1;32 0;64 1;128 0", "DATA")
                    
                hp.log("Reclassify flowdirection to find diagonal paths...")
                Flowdird = Reclassify(flowdir, "VALUE", "1 0;2 1;4 0;8 1;16 0;32 1;64 0;128 1", "DATA")
                    
                hp.log("Calculate distance grid...")
                Dist = (Flowdirs + Flowdird * 1.4142) * hp.units['size']
                
                hp.log("Calculate length")
                thislen = Dist * ThisBMPmask
                dist_red = hp.Zonal(thislen) * stream_red_per_ft
                print "stream_red_per_ft: %s, dist_red: %s" % (stream_red_per_ft, dist_red)
                
                hp.log("Summarize Stream reduction from point...")
                stream_red = hp.Zonal(streamprod) + dist_red
                
                print "Stream reduction", stream_red
                
                hp.log("Writing attributes")
                hp.SetAtt(BMP_FID, hp.ShortName(p) + "red" + LU[0], stream_red, bmp_noclip)
        
        count += 1

    hp.Close()
    
except:       
    i, j, k = sys.exc_info()
    hp.EH(i, j, k)
    
