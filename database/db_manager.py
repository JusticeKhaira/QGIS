"""
Database manager for storing proximity analysis results
Supports both SQLite (GeoPackage) and PostGIS databases
"""
import sqlite3
from datetime import datetime
from qgis.core import QgsMessageLog, Qgis  # type: ignore

# Try to import psycopg2
try:
    import psycopg2  # type: ignore
    PSYCOPG2_AVAILABLE = True
except ImportError:
    PSYCOPG2_AVAILABLE = False


class DatabaseManager:
    """Manage database for proximity analysis"""

    def __init__(self, db_config):
        self.db_config = db_config
        self.connection = None
        self.is_postgis = isinstance(db_config, dict) and db_config.get('type') == 'postgis'
        
        if self.is_postgis and not PSYCOPG2_AVAILABLE:
            raise ImportError("PostGIS requires psycopg2. Install via QGIS Python Console.")
        
        self.initialize_database()

    def initialize_database(self):
        """Initialize database connection"""
        try:
            if self.is_postgis:
                self.connection = psycopg2.connect(
                    host=self.db_config['host'],
                    port=self.db_config.get('port', 5432),
                    database=self.db_config['database'],
                    user=self.db_config['user'],
                    password=self.db_config['password']
                )
            else:
                self.connection = sqlite3.connect(self.db_config)
            
            self.create_tables()
            QgsMessageLog.logMessage("Database connected", "Proximity Finder", Qgis.Info)
        except Exception as e:
            QgsMessageLog.logMessage(f"DB Error: {str(e)}", "Proximity Finder", Qgis.Critical)
            raise

    def create_tables(self):
        """Create tables if they don't exist"""
        cursor = self.connection.cursor()
        
        if self.is_postgis:
            cursor.execute("CREATE EXTENSION IF NOT EXISTS postgis")
        
        # Placeholder - add actual table creation later
        self.connection.commit()

    def create_new_analysis(self, params):
        """Create analysis record"""
        return 1

    def insert_proximity_results(self, analysis_id, results):
        """Insert results"""
        pass

    def insert_summary(self, analysis_id, summary):
        """Insert summary"""
        pass

    def get_total_count(self, analysis_id):
        """Get count"""
        return 0

    def get_analysis_metadata(self, analysis_id):
        """Get metadata"""
        return None

    def get_summary_statistics(self, analysis_id):
        """Get stats"""
        return []

    def get_detailed_results(self, analysis_id, limit=None):
        """Get results"""
        return []

    def close(self):
        """Close connection"""
        if self.connection:
            self.connection.close()

    def __del__(self):
        self.close()