"""
Utilities module for Proximity Feature Finder
"""
import csv
import os
from datetime import datetime


class ReportGenerator:
    """Generate various report formats from analysis results"""

    def __init__(self, db_manager, analysis_id):
        """Constructor"""
        self.db_manager = db_manager
        self.analysis_id = analysis_id
        self.metadata = db_manager.get_analysis_metadata(analysis_id)
        self.summary_stats = db_manager.get_summary_statistics(analysis_id)

    def generate_csv_report(self, output_path):
        """Generate CSV report"""
        try:
            with open(output_path, 'w', newline='', encoding='utf-8') as csvfile:
                # Write header information
                csvfile.write("Proximity Analysis Report\n")
                csvfile.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                csvfile.write(f"Analysis: {self.metadata['analysis_name']}\n")
                csvfile.write(f"Source Layer: {self.metadata['source_layer']}\n")
                csvfile.write(f"Date: {self.metadata['analysis_date']}\n")
                csvfile.write("\n")