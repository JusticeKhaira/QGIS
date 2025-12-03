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

             return True
        except Exception as e:
            print(f"Error generating CSV report: {str(e)}")
            return False

    def generate_html_report(self, output_path):
        """Generate HTML report"""
        try:
            html_content = self._create_html_content()
            
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            return True
        except Exception as e:
            print(f"Error generating HTML report: {str(e)}")
            return False
     def _create_html_content(self):
        """Create HTML content for report"""
        # Calculate totals
        total_features = sum(stat['total_count'] for stat in self.summary_stats)
        
        # Build summary table rows
        summary_rows = ""
        for stat in self.summary_stats:
            summary_rows += f"""
                <tr>
                    <td>{stat['target_layer']}</td>
                    <td>{stat['buffer_distance']:.2f}</td>
                    <td class="count">{stat['total_count']}</td>
                    <td>{stat['min_distance']:.2f}</td>
                    <td>{stat['max_distance']:.2f}</td>
                    <td>{stat['avg_distance']:.2f}</td>
                    <td>{stat['total_area']:.2f}</td>
                    <td>{stat['total_length']:.2f}</td>
                </tr>
            """

         # Build detailed results section - UPDATED to include feature_name
        detailed_section = ""
        current_source = None
        detailed_results = self.db_manager.get_detailed_results(
            self.analysis_id, 
            limit=1000  # Limit for performance
        )
        
        for result in detailed_results:
            if current_source != result['source_id']:
                if current_source is not None:
                    detailed_section += "</tbody></table></div>"
                
                current_source = result['source_id']
                detailed_section += f"""
                    <div class="detail-section">
                        <h3>Source Feature ID: {current_source}</h3>
                        <table class="detail-table">
                            <thead>
                                <tr>
                                    <th>Target Layer</th>
                                    <th>Target ID</th>
                                    <th>Feature Name</th>
                                    <th>Distance (m)</th>
                                    <th>Buffer (m)</th>
                                    <th>Area (m²)</th>
                                    <th>Length (m)</th>
                                </tr>
                            </thead>
                            <tbody>
                """

             feature_name = result.get('feature_name', '-')
            detailed_section += f"""
                <tr>
                    <td>{result['target_layer']}</td>
                    <td>{result['target_id']}</td>
                    <td><strong>{feature_name}</strong></td>
                    <td>{result['distance']:.2f}</td>
                    <td>{result['buffer_distance']:.2f}</td>
                    <td>{result['area']:.2f}</td>
                    <td>{result['length']:.2f}</td>
                </tr>
            """
        
        if current_source is not None:
            detailed_section += "</tbody></table></div>"

