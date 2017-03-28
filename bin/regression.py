

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
