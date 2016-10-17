import arcpy
import pythonaddins

class CIP(object):
    """Implementation for CIP_addin.button (Button)"""
    def __init__(self):
        self.enabled = True
        self.checked = False
    def onClick(self):
        try:
            pythonaddins.GPToolDialog("WatershedImprovementPlanningTools.pyt", "ScenarioAnalysis")
        except TypeError:
            pass

class ImpCov(object):
    """Implementation for ImpCov_addin.button (Button)"""
    def __init__(self):
        self.enabled = True
        self.checked = False
    def onClick(self):
        try:
            pythonaddins.GPToolDialog("WatershedImprovementPlanningTools.pyt", "ImpCov")
        except TypeError:
            pass

class Runoff(object):
    """Implementation for Runoff_addin.button (Button)"""
    def __init__(self):
        self.enabled = True
        self.checked = False
    def onClick(self):
                try:
            pythonaddins.GPToolDialog("WatershedImprovementPlanningTools.pyt", "Runoff")
        except TypeError:
            pass

class TopoHydro(object):
    """Implementation for TopoHydro_addin.button (Button)"""
    def __init__(self):
        self.enabled = True
        self.checked = False
    def onClick(self):
        try:
            pythonaddins.GPToolDialog("WatershedImprovementPlanningTools.pyt", "TopoHydro")
        except TypeError:
            pass
