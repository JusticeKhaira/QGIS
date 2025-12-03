"""
Reports module for Proximity Feature Finder
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
        
        # Create complete HTML
        html = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Proximity Analysis Report</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
        }}
        .container {{
            max-width: 1400px;
            margin: 0 auto;
            background-color: white;
            padding: 30px;
            box-shadow: 0 0 10px rgba(0,0,0,0.1);
        }}
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            border-radius: 5px;
            margin-bottom: 30px;
        }}
        .header h1 {{
            margin: 0 0 10px 0;
        }}
        .header p {{
            margin: 5px 0;
            opacity: 0.9;
        }}
        .summary-box {{
            background: #f8f9fa;
            border-left: 4px solid #667eea;
            padding: 20px;
            margin: 20px 0;
        }}
        .summary-box h2 {{
            margin-top: 0;
            color: #333;
        }}
        .feature-count {{
            font-size: 48px;
            font-weight: bold;
            color: #667eea;
            margin: 10px 0;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
        }}
        th, td {{
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }}
        th {{
            background-color: #667eea;
            color: white;
            font-weight: 600;
        }}
        tr:hover {{
            background-color: #f5f5f5;
        }}
        .count {{
            font-weight: bold;
            color: #667eea;
        }}
        .detail-section {{
            margin: 30px 0;
            padding: 20px;
            background: #f8f9fa;
            border-radius: 5px;
            border-left: 4px solid #667eea;
        }}
        .detail-section h3 {{
            color: #667eea;
            margin-top: 0;
        }}
        .detail-table {{
            font-size: 14px;
            background: white;
        }}
        .footer {{
            margin-top: 40px;
            padding-top: 20px;
            border-top: 1px solid #ddd;
            text-align: center;
            color: #666;
            font-size: 14px;
        }}
        strong {{
            color: #667eea;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🗺️ Proximity Analysis Report</h1>
            <p><strong>Generated:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            <p><strong>Analysis:</strong> {self.metadata['analysis_name']}</p>
            <p><strong>Source Layer:</strong> {self.metadata['source_layer']}</p>
            <p><strong>Date:</strong> {self.metadata['analysis_date']}</p>
        </div>
        
        <div class="summary-box">
            <h2>📊 Summary Statistics</h2>
            <p>Total Source Features Analyzed: 
                <span class="feature-count">{self.metadata['total_source_features']}</span>
            </p>
            <p>Total Features Identified: 
                <span class="feature-count">{total_features}</span>
            </p>
        </div>
        
        <h2>📈 Features by Category and Distance</h2>
        <table>
            <thead>
                <tr>
                    <th>Target Layer</th>
                    <th>Buffer Distance (m)</th>
                    <th>Count</th>
                    <th>Min Distance (m)</th>
                    <th>Max Distance (m)</th>
                    <th>Avg Distance (m)</th>
                    <th>Total Area (m²)</th>
                    <th>Total Length (m)</th>
                </tr>
            </thead>
            <tbody>
                {summary_rows}
            </tbody>
        </table>
        
        <h2>📋 Detailed Results (with Feature Names)</h2>
        <p style="color: #666; font-style: italic;">Feature names are automatically extracted when available in the source data</p>
        {detailed_section}
        
        <div class="footer">
            <p>Report generated by Proximity Feature Finder Plugin for QGIS</p>
            <p>© {datetime.now().year} - Proximity Analysis Tool</p>
        </div>
    </div>
</body>
</html>
        """
        
        return html