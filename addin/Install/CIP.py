
# Import system modules
import sys, os
import Helper
import regression
import arcpy
from arcpy.sa import *

hp = Helper.Helper(sys.argv)
try:
    # Local variables
    Cum_da = Raster(os.path.join(hp.Workspace + "\\WIPoutput.mdb", "cumda"))
    arcpy.env.extent = os.path.join(hp.Workspace + "\\WIPoutput.mdb", "cumda")
    Units = hp.units['size']
    
    ScenName = sys.argv[1]
    bmp_noclip = sys.argv[2]
    bmp_type = sys.argv[3]
    bmp_CIPproj = sys.argv[4]
    bmp_Ex1yr = sys.argv[5]
    bmp_Prop1yr = sys.argv[6]
    bmp_eeff_l= sys.argv[7].split(';')
    bmp_peff_l = sys.argv[8].split(';')
    bmp_strlngth = sys.argv[9]
    stream_len_perft = sys.argv[10].replace("#", "").split(';')
    summary_pt_input = sys.argv[11]
    
    landuses = []
    use_existing = sys.argv[12]
    use_future = sys.argv[13]
    prod_existing = hp.models['ProdTrans']['input'][15].strip()
    prod_future = hp.models['ProdTrans']['input'][17].strip()
    if use_existing.lower() == "true":
        landuses.append("E")
    if use_future.lower() == "true":
        landuses.append("F")
    
    error = ""
    if not landuses:
        error = "You must select Existing and/or Future Landuse conditions"
    if use_existing == "true" and not prod_existing:
        error = "You must run Existing in Production Transport first"
    if use_future == "true" and not prod_future:
        error = "You must run Future in Production Transport first"
    if error:
        hp.log(error)
        raise Exception, error
        
    params = {}
    
    exec(hp.models['ProdTrans']['input'][-1])
    
    OutputRasters = []
    temp = arcpy.env.workspace
    arcpy.env.workspace = os.path.join(hp.Workspace, "WIPoutput.mdb")
    OutputRasters = arcpy.ListRasters()
    arcpy.env.workspace = temp
    
    existing_params = hp.GetAlias(bmp_eeff_l)
    proposed_params = hp.GetAlias(bmp_peff_l)
    streamlen_params = hp.GetAlias(stream_len_perft)
    
    if not existing_params.keys().sort() == proposed_params.keys().sort():
        raise Exception, "Parameters found for Existing efficiencies and Proposed efficiencies do not match"

    gdb = "CIP_%s.mdb" % ScenName.replace(" ", "_")
    arcpy.CreatePersonalGDB_management(hp.Workspace, gdb)
    
    vectmask = os.path.join(hp.SWorkspace, "vectmask.shp")
    BMPpts = os.path.join(hp.SWorkspace, "BMPpts.shp")
    arcpy.RasterToPolygon_conversion(hp.Mask, vectmask, "SIMPLIFY", "Value")
    arcpy.Clip_analysis(bmp_noclip, vectmask, BMPpts)
    
    flowdir = os.path.join(hp.Workspace + "\\WIPoutput.mdb", "flowdir")* hp.Mask 
    flowdir.save(os.path.join(hp.SWorkspace, "flowdir")) 
    
    Streams_nd = Raster(os.path.join(hp.Workspace + "\\WIPoutput.mdb", "streams"))
    streams = hp.RemoveNulls(Streams_nd)
    
    hp.log("Finding CIP projects...")
    CIPBMPpts = os.path.join(hp.SWorkspace, "CIPpts.shp")
    CIP_found = hp.GetSubset(BMPpts, CIPBMPpts, " \"%s\" = 'TRUE' " % bmp_CIPproj)
    
    if CIP_found < 1:
        raise Exception, "Did not find any CIP Projects in the study area, stopping"
    
    for LU in landuses:
        for param in existing_params:
            
            pn = param[:10].strip()
            bmp_eeff = existing_params[param]
            bmp_peff = proposed_params[param]
            
            arcpy.CopyRaster_management(os.path.join(hp.Workspace + "\\WIPoutput.mdb", "p" + LU + pn), os.path.join(hp.SWorkspace, "p" + LU + pn))
            TSSprod = Raster(os.path.join(hp.SWorkspace, "p" + LU + pn))
            K = Raster(os.path.join(hp.Workspace + "\\WIPoutput.mdb", "K" + LU + pn))
            
            pointsrc = ""
            #~ hp.log( "   %s, %s, %s" % ("pt" + LU + pn, OutputRasters, "pt" + LU + pn in OutputRasters))
            if "pt" + LU + pn in OutputRasters:
                pointsrc = Raster(os.path.join(hp.Workspace + "\\WIPoutput.mdb", "pt" + LU + pn))
                
            defEro = 0
            if param in params:
                defEro = params[param]['DefEro']
                
            hp.log("Finding Channel Protection projects...")  # From CIP points only
            ChanBMPpts = os.path.join(hp.SWorkspace, "ChanBMPpts.shp")
            CP_found = hp.GetSubset(CIPBMPpts, ChanBMPpts , " \"%s\" < \"%s\" " % (bmp_Prop1yr, bmp_Ex1yr))
            
            if CP_found > 0:
                CumMod_da, RasBMPpts2, throwout = regression.ChannelProtection(hp, ChanBMPpts, bmp_Prop1yr)
                
                Cumulative_Impervious = Raster(os.path.join(hp.Workspace + "\\WIPoutput.mdb", "cumimpcovlake") )
##                usgs_calcs = Helper.USGSVars(hp.Basin)
                urbanQcp = regression.urbanQcp(hp.Basin, CumMod_da, Cumulative_Impervious)
                
                hp.log("Calculate Urban/Rural ratio...")
                Rural_1yrQ = Raster(os.path.join(hp.Workspace + "\\WIPoutput.mdb", "UndevQ"))
                URratio = urbanQcp / Rural_1yrQ
                
                Streams_nd = Raster(os.path.join(hp.Workspace + "\\WIPoutput.mdb", "streams"))
                Stream_Raster = hp.RemoveNulls(Streams_nd)
                
                hp.log("Add erosivity to %s production..." % param)
                TSSP_ero_ext = Helper.CalcErosivity(hp, defEro, TSSprod, pointsrc, URratio, Stream_Raster)
                TSSP_ero_ext.save(os.path.join(hp.SWorkspace, "TSSP_ero_ext"))
                hp.log("Clip to streams...")
                # and round
                UrbRurratc = Int(RoundUp( RoundDown( Streams_nd * URratio * 20000 ) / 2 ))
                
                URratio_vec = os.path.join(hp.Workspace, gdb, LU + "rv" + pn)#
                hp.log("Vectorize...")
                
                
                StreamToFeature(UrbRurratc, flowdir, URratio_vec, "NO_SIMPLIFY")
                hp.ConvertGRIDCODEatt(URratio_vec)
            
            else:
                hp.log("  Did not find any Channel Protection Projects in the study area")
                CumMod_da = Cum_da
                URratio = os.path.join(os.path.join(hp.Workspace, "WIPoutput.mdb"), "UrbRurratio")
                arcpy.CopyRaster_management(os.path.join(hp.Workspace + "\\WIPoutput.mdb", "q" + LU + pn), os.path.join(hp.SWorkspace, "q" + LU + pn))
                TSSP_ero_ext = Raster(os.path.join(hp.SWorkspace, "q" + LU + pn))
            
            hp.log("Finding Stream Restoration projects...")    
            strBMPs2 = os.path.join(hp.SWorkspace, "strBMPs2.shp")
            found = hp.GetSubset(CIPBMPpts, strBMPs2 , " \"%s\" = 'Stream Restoration' " % bmp_type)
            if found < 1:
                hp.log("  Did not find any Stream Restoration Projects in the study area, skipping this part")
                TSS_reduc = TSSP_ero_ext
            else:
                hp.log("Convert Stream Lengths to Raster...")
                len = arcpy.FeatureToRaster_conversion(strBMPs2, bmp_strlngth, os.path.join(hp.SWorkspace, "len"), flowdir)
                BMPlengths = Float(len)
                 
                lengths = hp.AttExtract(BMPlengths, flowdir,"lengths", streams, Units)
                
                hp.log("Remove background values...")
                lengthsmask = Reclassify(lengths, "VALUE", ".00001 100000 1;-100000 0 0; NoData 0", "DATA")
                
                hp.log("Convert Stream Restoration Projects to Raster...")
                srp = hp.GetTempRasterPath("srp")
                arcpy.FeatureToRaster_conversion(strBMPs2, bmp_peff, srp, flowdir)
                strBMPs3 = Float(Raster(srp))
                
                PropEffnd = hp.AttExtract(strBMPs3, flowdir, "PropEffnd", streams)
                
                hp.log("Remove background values...")
                PropEff = hp.RemoveNulls(PropEffnd)
                
                hp.log("%s production for Stream Restoration Projects..." % param)
                StrTSSRed = lengthsmask * TSSprod * PropEff / 100
                
                hp.log("Reduce %s production for Stream Restoration Projects..." % param)
                TSS_reduc = TSSP_ero_ext - StrTSSRed
                
                if streamlen_params.has_key(param):
                    
                    hp.log("Convert Stream Projects to Raster...")
                    #~ print bmp_peff
                    slpf = arcpy.FeatureToRaster_conversion(strBMPs2, streamlen_params[param], os.path.join(hp.SWorkspace, "slpf"), flowdir)
                    strBMPs3 = Float(slpf)
                    
                    hp.log("Stream reduction per length...")
                    srlength = hp.AttExtract(strBMPs3, flowdir,"lengths", streams)
                    
                    hp.log("Remove background values...")
                    srlengthm = hp.RemoveNulls(srlength)
                    
                    hp.log("Reclassify flowdirection to find straight paths...")
                    Flowdirs = Reclassify(flowdir, "VALUE", "1 1;2 0;4 1;8 0;16 1;32 0;64 1;128 0", "DATA")
                    
                    hp.log("Reclassify flowdirection to find diagonal paths...")
                    Flowdird = Reclassify(flowdir, "VALUE", "1 0;2 1;4 0;8 1;16 0;32 1;64 0;128 1", "DATA")
                    
                    hp.log("Calculate distance grid...")
                    Dist = ( Flowdirs + Flowdird * 1.4142) * Units
                    
                    hp.log("Stream Length Reduction...")
                    
                    StrLenRed = srlengthm * Dist * lengthsmask
                    TSS_reduc = TSS_reduc - StrLenRed
                
                
                
            # Get and combine all the efficiencies used
            
            hp.log("Finding Existing BMPs...")
            ExistingBMPs = os.path.join(hp.SWorkspace, "ExistingBMPs.shp")
            existing_found = hp.GetSubset(BMPpts, ExistingBMPs, "NOT ( \"%s\" = 'TRUE' AND ( \"%s\" = 'BMP' OR \"%s\" = 'New BMP' ) ) AND \"%s\" > 0 " % \
                                                            (bmp_CIPproj, bmp_type, bmp_type, bmp_eeff) )
                
            if existing_found > 0: 
                hp.log("Convert Existing Efficiency to Raster...")
                arcpy.FeatureToRaster_conversion(ExistingBMPs, bmp_eeff, os.path.join(hp.SWorkspace, "ExistingBMPs"), flowdir)
                ExistingBMPs = Raster(os.path.join(hp.SWorkspace, "ExistingBMPs"))
                ExistingBrc = hp.RemoveNulls(ExistingBMPs)
                
                
            hp.log("Finding CIP BMPs...")
            CIPBMPs = os.path.join(hp.SWorkspace, "CIPBMPpts.shp")
            cip_found = hp.GetSubset(CIPBMPpts, CIPBMPs, " \"%s\" = 'BMP' OR \"%s\" = 'New BMP' " % (bmp_type, bmp_type))
            
            if cip_found > 0:
                hp.log("Convert CIP Efficiency to Raster...")
                #~ raise Exception
                CIPBMPpt_temp = hp.GetTempRasterPath("CIPBMPs")
                arcpy.FeatureToRaster_conversion(CIPBMPs, bmp_peff, CIPBMPpt_temp, flowdir)
                CIPBMPptsRas = Raster(CIPBMPpt_temp)
                CIPBMPrc = hp.RemoveNulls(CIPBMPptsRas)
            
            if existing_found and cip_found:
                hp.log("Combine reduction efficiencies...")
                redvar = ExistingBrc + CIPBMPrc
            elif existing_found:
                redvar = ExistingBrc
            elif cip_found:
                redvar = CIPBMPrc
            else:
                redvar = None
                hp.log("  WARNING: Did not find any Existing OR CIP projects, so not reducing accumulation")
                
            redvar.save(os.path.join(hp.SWorkspace, "redvar"))
                
            # TSS Reduction calcs  
            hp.log("Calculate %s Reduction..." % param)
            if type(redvar) == Raster:
                wtredvar = 1 - ( K * ( 1 - (redvar / 100.0 ) ) )
                wtredvar.save(os.path.join(hp.SWorkspace, "wtredvar"))
                TSSLoadcip = hp.BMP2DA(flowdir, "TSSLoadcip", TSS_reduc, wtredvar)
            else:
                TSSLoadcip = hp.BMP2DA(flowdir, "TSSLoadcip", TSS_reduc)
            
            hp.log("Clip...")
            # hp.log("%s: %s" % (hp.Mask, type(hp.Mask)))
            # hp.log("%s: %s" % (TSSLoadcip, type(TSSLoadcip)))
            TSSLoadOutput = ExtractByMask(TSSLoadcip, hp.Mask)
            TSSLoadOutput.save(os.path.join(hp.Workspace, gdb, "L" + LU[0] + pn))
            
            hp.log("Calculate %s Yield..." % param)
            CIPTSSYield = TSSLoadcip / Cum_da
            CIPTSSYield.save(os.path.join(hp.Workspace, gdb, "Y" + LU[0] + pn))
            
            hp.log("Clip to streams...")
            # and round
            TSSYield_cl = Int(RoundUp( RoundDown( Streams_nd * CIPTSSYield * 20000 ) / 2 ))
            TSSYield_cl.save(os.path.join(hp.Workspace, gdb, LU[0] + "y2" + pn))
            
            TSSYldvec = os.path.join(hp.Workspace, gdb, LU[0] + "yV" + pn)#
            hp.log("Vectorize...")
            StreamToFeature(TSSYield_cl, flowdir, TSSYldvec, "NO_SIMPLIFY")
            hp.models[hp.current_tool]["output"].append(TSSYldvec)
            
            hp.ConvertGRIDCODEatt(TSSYldvec)
 
    if summary_pt_input != "#":
                
        hp.log("Summarizing results...")
        summary_pts = os.path.join(os.path.join(hp.Workspace, gdb), "summaryptsCIP")
        arcpy.Clip_analysis(summary_pt_input, vectmask, summary_pts)
        hp.SetPIDs(summary_pts)
        hp.models[hp.current_tool]["output"].append(summary_pts)
        
        for lucode in landuses:
            if lucode == 'E': LU = "Existing"
            if lucode == 'F': LU = "Future"
            for param in existing_params:
                pn = param[:10].strip()
                alias = LU + " " + param + " Load"
                TSSLoadOutput = Raster(os.path.join(hp.Workspace, gdb, "L" + LU[0] + pn))
                hp.Summarize(TSSLoadOutput, summary_pts, alias)    


    hp.Close()
    
except:       
    i, j, k = sys.exc_info()
    hp.EH(i, j, k)
    
