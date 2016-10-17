import os, arcpy
from arcpy.sa import *

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
         
def urbanQcp(Basin, cum_da, impcov):
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

def ChannelProtection(hp, BMP_pts, fld):
        # Flow reduction calcs

        flowdir = ExtractByMask(Raster(os.path.join(hp.Workspace + "\\WIPoutput.mdb", "flowdir")), hp.Mask )
        Cum_da = Raster(os.path.join(hp.Workspace + "\\WIPoutput.mdb", "cumda"))
        Cumulative_Impervious = Raster(os.path.join(hp.Workspace + "\\WIPoutput.mdb", "cumimpcovlake"))
        flowdir.save(os.path.join(hp.SWorkspace, "flowdir")) 

        arcpy.CopyRaster_management (os.path.join(hp.Workspace + "\\WIPoutput.mdb", "mask"), os.path.join(hp.SWorkspace, "mask"))
        mask = Raster(os.path.join(hp.SWorkspace, "mask"))

        hp.log("Convert Single BMP Project to Raster...")
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
                

        hp.log("Convert to percent reduction in accumulation...")
        acc_red = ExtractByMask(1 - ( Mod_da / Cum_da), mask)
        acc_red.save(os.path.join(hp.SWorkspace,"acc_red_cp"))

        ModCumDa_u = hp.BMP2DA(flowdir, "ModCumDa_asc", mask, acc_red)

        hp.log("Convert units...")
        conv = hp.units['cellsqft'] / 43560
        ModCumDa = ModCumDa_u * conv
    
        hp.log("Calculating urbanQcp...")
        uQcp = urbanQcp(hp.Basin, ModCumDa, Cumulative_Impervious)

        return ModCumDa, thisBMPras, uQcp
