"""
Tab components for NFACT Graphical User Interface.
"""

from NFACT.gui.tabs.base_tab import BaseModuleTab
from NFACT.gui.tabs.config_tab import ConfigTab
from NFACT.gui.tabs.decomp_tab import DecompTab
from NFACT.gui.tabs.dr_tab import DRTab
from NFACT.gui.tabs.pipeline_tab import PipelineTab
from NFACT.gui.tabs.pp_tab import PPTab
from NFACT.gui.tabs.qc_tab import QcTab
from NFACT.gui.tabs.stats_tab import StatsTab

__all__ = [
    "BaseModuleTab",
    "ConfigTab",
    "DecompTab",
    "DRTab",
    "PipelineTab",
    "PPTab",
    "QcTab",
    "StatsTab",
]
