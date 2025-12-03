"""
Main analysis engine for proximity analysis - ENHANCED VERSION
With EXCLUSIVE distance zones (features only appear in their closest zone)
"""
import os
import sys
import traceback
from datetime import datetime

from qgis.core import (
    QgsProject, QgsVectorLayer, QgsFeature, QgsGeometry,
    QgsDistanceArea, QgsCoordinateReferenceSystem,
    QgsWkbTypes, QgsMessageLog, Qgis, QgsSpatialIndex,
    QgsVectorFileWriter, QgsFields, QgsField, QgsPointXY,
    QgsSymbol, QgsRendererCategory, QgsCategorizedSymbolRenderer,
    QgsMarkerSymbol, QgsLineSymbol, QgsFillSymbol,
    QgsGraduatedSymbolRenderer, QgsRendererRange
)
from qgis.PyQt.QtCore import QVariant
from qgis.PyQt.QtGui import QColor

# Lazy imports - avoid circular imports
def get_database_manager():
    """Lazy import to avoid circular dependency"""
    try:
        from ..database.db_manager import DatabaseManager
        return DatabaseManager
    except ImportError as e:
        QgsMessageLog.logMessage(f"Import error: {str(e)}", "Proximity Finder", Qgis.Critical)
        return None

def get_report_generator():
    """Lazy import to avoid circular dependency"""
    try:
        from ..reports.report_generator import ReportGenerator
        return ReportGenerator
    except ImportError as e:
        QgsMessageLog.logMessage(f"Import error: {str(e)}", "Proximity Finder", Qgis.Critical)
        return None


class ProximityAnalyzer:
    """Main class for performing proximity analysis"""

    def __init__(self, iface, params):
        """Constructor"""
        self.iface = iface
        self.params = params
        self.db_manager = None
        self.analysis_id = None
        self.results = []
        self.found_features_layer = None
        self.processed_features = {}  # Changed to dict to track distance zones
        self.source_features_layer = None
        self.analysis_log = []  # Store log messages

    def log_message(self, message, level=Qgis.Info):
        """Log message to both QGIS log and internal log"""
        QgsMessageLog.logMessage(message, "Proximity Finder", level)
        timestamp = datetime.now().strftime('%H:%M:%S')
        self.analysis_log.append(f"[{timestamp}] {message}")

    def run_analysis(self):
        """Execute the complete analysis workflow"""
        try:
            self.analysis_log = []
            self.log_message("=" * 60)
            self.log_message("STARTING PROXIMITY ANALYSIS")
            self.log_message("=" * 60)
            
            # Get DatabaseManager class
            DatabaseManager = get_database_manager()
            if not DatabaseManager:
                return False, "Failed to load database manager", self.analysis_log
            
            # Get database config - support both SQLite and PostGIS
            if 'database_config' in self.params:
                # PostGIS
                db_config = self.params['database_config']
                self.log_message(f"Connecting to PostGIS: {db_config.get('database')}")
                self.db_is_postgis = True
                self.db_path = None
            else:
                # SQLite/GeoPackage
                db_config = self.params.get('database_path', 'proximity_analysis.gpkg')
                self.log_message(f"Using GeoPackage: {db_config}")
                self.db_is_postgis = False
                self.db_path = db_config

            self.db_manager = DatabaseManager(db_config)
            self.analysis_id = self.db_manager.create_new_analysis(self.params)
            
            self.log_message(f"Analysis ID: {self.analysis_id}")
            
            # Get source layer and features
            source_layer = self.params['source_layer']
            
            # Get features based on selection
            if self.params.get('use_selected_only', False):
                if source_layer.selectedFeatureCount() == 0: