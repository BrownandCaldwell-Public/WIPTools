# WIPTools
ArcGIS-based geoprocessing tools for Watershed Improvement Plans 

## Deploying
Because WIP Tools is implemented as a python toolbox, you can place the .pyt file in any location and access it via your ArcCatalog window in ArcMap. However, it does require the (2) .pyd files to be placed in the same location. Additionaly there are a collection of text files used for specifying project-specific modeling parameters taht should be kept with the .pyt. Therefore, it will usually be sensible to have a copy of all these files in the project directory.

Because WIP Tools is implemented as a python toolbox, it can run in any version of ArcGIS (YMMV and testing should be done for versions prior to 10.3)

## Compiled Cython libs
There are 2 tools that for performance can be compiled to C as .pyd files using Cython:
- AttributeExtract.pyx
- bmpFlowModFast.pyx
To recompile these, cython and a C compiler must be installed. There is a batch file (compile.bat) to act as a makefile to run Cython and make the .pyd files from them.

## Running
There are a large number of inputs and outputs for some of the tools, therefore it is simplest to place them in a new model builder specific for a project. This way outputs from one tool can be linked as inputs for multiple other tools, and the geoporcessing lineage is graphically documented. The model should make use the the following geoprocessing environment variables for consistency across all mdoels:
- workspace
- processing extents
- cell size
- snap raster (optional)

Some tools, like Topohydro, will benefit from setting overrides on these values for that tool. Using model builder also allows intermediate files to be preserved in a scratch folder

## Documenting
Using a model builder is the best way to both customize parameters for a project and to document what has been run using which inputs. Also, the geoprocessing history in the results window in ArcMap is useful for tracking previous runs, therefore the .mxd file should be preserved for the life of the project. Multiple .mxd map documents can be used to make branched modeling workflows, but they should be made by using "save as" in the mxd to preserve the complete parent history.

A log file is also produced, in the same location as the .pyt file, for duplicate and comprehensive documentation.

## Addin
An addin has been made for convenience of locating the individual tools, if that workflow is desired over using model builder. The addin simply references the tools in the .pyt python toolbox, so the geoprocessing lineage in the results window will be preserved.