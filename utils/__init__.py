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
                
                # Write summary statistics
                csvfile.write("Summary Statistics\n")
                writer = csv.writer(csvfile)
                writer.writerow([
                    'Target Layer',
                    'Buffer Distance (m)',
                    'Total Count',
                    'Min Distance (m)',
                    'Max Distance (m)',
                    'Avg Distance (m)',
                    'Total Area (m²)',
                    'Total Length (m)'
                ])
                
                for stat in self.summary_stats:
                    writer.writerow([
                        stat['target_layer'],
                        f"{stat['buffer_distance']:.2f}",
                        stat['total_count'],
                        f"{stat['min_distance']:.2f}",
                        f"{stat['max_distance']:.2f}",
                        f"{stat['avg_distance']:.2f}",
                        f"{stat['total_area']:.2f}",
                        f"{stat['total_length']:.2f}"
                    ])
                
                csvfile.write("\n\n")

                 # Write detailed results - UPDATED to include feature_name
                csvfile.write("Detailed Results\n")
                writer.writerow([
                    'Source Feature ID',
                    'Target Layer',
                    'Target Feature ID',
                    'Feature Name',
                    'Distance (m)',
                    'Buffer Distance (m)',
                    'Area (m²)',
                    'Length (m)'
                ])

                detailed_results = self.db_manager.get_detailed_results(self.analysis_id)
                for result in detailed_results:
                    writer.writerow([
                        result['source_id'],
                        result['target_layer'],
                        result['target_id'],
                        result.get('feature_name', ''),
                        f"{result['distance']:.2f}",
                        f"{result['buffer_distance']:.2f}",
                        f"{result['area']:.2f}",
                        f"{result['length']:.2f}"
                    ])

