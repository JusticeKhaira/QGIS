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
                       return False, "No features selected in source layer. Please select features or uncheck 'Use selected features only'.", self.analysis_log
                source_features = source_layer.selectedFeatures()
                self.log_message(f"Using {len(source_features)} SELECTED features from {source_layer.name()}")
            else:
                source_features = list(source_layer.getFeatures())
                self.log_message(f"Using ALL {len(source_features)} features from {source_layer.name()}")
            
            if not source_features:
                return False, "No features to analyze in source layer", self.analysis_log
            
            # Log distance zones
            sorted_distances = sorted(self.params['distances'])
            self.log_message(f"Distance zones to analyze: {sorted_distances}")
            self.log_message("NOTE: Features will only appear in their CLOSEST zone (exclusive zones)")
            
            # Create highlighted source features layer
            self.create_source_highlight_layer(source_layer, source_features)
            self.log_message("Created source features highlight layer")
            
            # Create output layer for found TARGET features
            self.create_output_layer(source_layer)
            self.log_message("Created output layer for target features")
            
            # Process each distance - SMALLEST FIRST for exclusive zones
            total_distances = len(sorted_distances)
            for idx, distance in enumerate(sorted_distances):
                progress = int((idx / total_distances) * 100)
                self.log_message("-" * 60)
                self.log_message(f"PROCESSING ZONE {idx+1}/{total_distances}: {distance}m buffer")
                self.analyze_distance(source_features, source_layer, distance)
            
            # Check if any features were found
            if self.found_features_layer.featureCount() == 0:
                self.log_message("WARNING: No features found within any distance zone!", Qgis.Warning)
                return False, "No features found within the specified distance(s). Try increasing the distance.", self.analysis_log
            
            self.log_message("=" * 60)
            self.log_message(f"TOTAL TARGET FEATURES FOUND: {self.found_features_layer.featureCount()}")
            
            # Save outputs
            shp_path = self.save_output_as_shapefile()
            if shp_path:
                self.log_message(f"Saved shapefile: {shp_path}")
            
            # Save results to DB (GeoPackage or PostGIS)
            self.save_output_to_geopackage()
            
            # Generate reports
            if self.params.get('generate_csv', False) or self.params.get('generate_html', False):
                ReportGenerator = get_report_generator()
                if ReportGenerator:
                    report_gen = ReportGenerator(self.db_manager, self.analysis_id)
                    
                    # choose base path for reports
                    if self.db_path:
                        base = self.db_path.replace('.gpkg', '')
                    else:
                        base = os.path.join(
                            QgsProject.instance().homePath() or os.path.expanduser("~"),
                            self.params.get('database_config', {}).get('database', 'proximity_analysis')
                        )

                    if self.params.get('generate_csv', False):
                        csv_path = f"{base}.csv"
                        try:
                            report_gen.generate_csv_report(csv_path)
                            self.log_message(f"Generated CSV report: {csv_path}")
                        except Exception as e:
                            self.log_message(f"Error generating CSV: {str(e)}", Qgis.Warning)
                    
                    if self.params.get('generate_html', False):
                        html_path = f"{base}.html"
                        try:
                            report_gen.generate_html_report(html_path)
                            self.log_message(f"Generated HTML report: {html_path}")
                        except Exception as e:
                            self.log_message(f"Error generating HTML: {str(e)}", Qgis.Warning)
            
            # Add results to map with proper styling
            if self.params.get('add_to_map', True):
                if shp_path:
                    self.add_shapefile_to_map(shp_path)
                    self.log_message("Added results to map canvas")
                if self.source_features_layer:
                    self.add_source_layer_to_map()
                    self.log_message("Added source features to map canvas")
            
            total_found = self.db_manager.get_total_count(self.analysis_id)
            
            self.log_message("=" * 60)
            self.log_message("ANALYSIS COMPLETED SUCCESSFULLY!")
            self.log_message("=" * 60)
            
            return True, f"Analysis complete! Found {total_found} TARGET features within buffer zones. Shapefile: {shp_path}", self.analysis_log
            
        except Exception as e:
            error_details = traceback.format_exc()
            self.log_message(f"ERROR: {str(e)}", Qgis.Critical)
            self.log_message(error_details, Qgis.Critical)
            return False, f"Analysis failed: {str(e)}", self.analysis_log
            
    def create_source_highlight_layer(self, source_layer, source_features):
        """Create a layer to highlight selected source features"""
        crs = source_layer.crs().authid()
        geom_type = QgsWkbTypes.displayString(source_layer.wkbType())
        
        # Create memory layer for source features
        self.source_features_layer = QgsVectorLayer(
            f"{geom_type}?crs={crs}",
            "Source Features (Search Origin)",
            "memory"
        )
        
        # Copy fields from source layer
        provider = self.source_features_layer.dataProvider()
        provider.addAttributes(source_layer.fields())
        self.source_features_layer.updateFields()
        
        # Add features
        features_to_add = []
        for feat in source_features:
            new_feat = QgsFeature(self.source_features_layer.fields())
            new_feat.setGeometry(feat.geometry())
            new_feat.setAttributes(feat.attributes())
            features_to_add.append(new_feat)
        
        provider.addFeatures(features_to_add)
        self.source_features_layer.updateExtents()

    def create_output_layer(self, source_layer):
        """Create memory layer to store found TARGET features with detailed attributes"""
        crs = source_layer.crs().authid()
        
        # Create comprehensive fields for output layer
        fields = QgsFields()
        fields.append(QgsField("result_id", QVariant.Int))
        fields.append(QgsField("source_id", QVariant.Int))
        fields.append(QgsField("src_layer", QVariant.String, len=100))
        fields.append(QgsField("target_lyr", QVariant.String, len=100))
        fields.append(QgsField("target_id", QVariant.Int))
        fields.append(QgsField("feat_name", QVariant.String, len=255))
        fields.append(QgsField("distance_m", QVariant.Double, len=10, prec=2))
        fields.append(QgsField("buffer_m", QVariant.Double, len=10, prec=2))
        fields.append(QgsField("zone", QVariant.String, len=50))
        fields.append(QgsField("found_date", QVariant.String, len=50))
        
        # Determine geometry type
        geom_type = "Point"
        for target_layer in self.params.get('target_layers', []):
            if target_layer.geometryType() == QgsWkbTypes.PolygonGeometry:
                geom_type = "MultiPolygon"
                break
            elif target_layer.geometryType() == QgsWkbTypes.LineGeometry:
                geom_type = "MultiLineString"
        
        self.log_message(f"Output layer geometry type: {geom_type}")
        
        # Create memory layer
        self.found_features_layer = QgsVectorLayer(
            f"{geom_type}?crs={crs}",
            "Proximity Results (Target Features)",
            "memory"
        )
        
        provider = self.found_features_layer.dataProvider()
        provider.addAttributes(fields)
        self.found_features_layer.updateFields()

    def analyze_distance(self, source_features, source_layer, distance):
        """Analyze features at a specific distance"""
        
        self.log_message(f"Analyzing {len(source_features)} source features at {distance}m buffer")
        
        # Distance calculator
        distance_calc = QgsDistanceArea()
        distance_calc.setSourceCrs(
            source_layer.crs(),
            QgsProject.instance().transformContext()
        )
        distance_calc.setEllipsoid(source_layer.crs().ellipsoidAcronym())
        
        zone_feature_count = 0
        
        # Process each source feature
        for source_idx, source_feature in enumerate(source_features):
            source_geom = source_feature.geometry()
            buffer_geom = source_geom.buffer(distance, 16)
            
            # Analyze each target layer
            for target_layer in self.params.get('target_layers', []):
                results = self.find_features_in_buffer(
                    source_feature,
                    source_layer,
                    target_layer,
                    buffer_geom,
                    distance_calc,
                    distance
                )
                
                zone_feature_count += len(results)