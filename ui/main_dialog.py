"""
Main dialog for Proximity Feature Finder - WITH LOG VIEWER
Shows analysis log and keeps dialog open after completion
"""
import os
from qgis.PyQt.QtCore import Qt, pyqtSignal
from qgis.PyQt.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                                 QComboBox, QCheckBox, QSpinBox, QDoubleSpinBox,
                                 QLineEdit, QPushButton, QListWidget, QGroupBox,
                                 QFileDialog, QListWidgetItem, QMessageBox,
                                 QProgressBar, QTextEdit, QTabWidget, QWidget, QApplication)
from qgis.core import QgsProject, QgsVectorLayer, QgsWkbTypes, QgsMessageLog, Qgis, QgsVectorFileWriter
from ..database.db_manager import DatabaseManager


class ProximityDialog(QDialog):
    """Dialog for configuring proximity analysis with log viewer"""
    
    accepted = pyqtSignal()
    rejected = pyqtSignal()

    def __init__(self, iface, parent=None):
        """Constructor"""
        super(ProximityDialog, self).__init__(parent)
        self.iface = iface
        self.saved_state = {}
        self.analysis_running = False
        self.db = None
        self.setup_ui()
        self.populate_layers()
        self.restore_last_state()

    def setup_ui(self):
        """Set up the user interface with tabs for config and log"""
        self.setWindowTitle("Proximity Feature Finder")
        self.resize(700, 900)
        
        # Enable minimize and maximize buttons
        self.setWindowFlags(
            Qt.Window |
            Qt.WindowMinimizeButtonHint |
            Qt.WindowMaximizeButtonHint |
            Qt.WindowCloseButtonHint
        )
        
        main_layout = QVBoxLayout()
        
        # Create tab widget
        self.tab_widget = QTabWidget()
        
        # Tab 0: Database Configuration
        db_config_tab = QWidget()
        db_config_layout = QVBoxLayout()
        
        db_group = QGroupBox("🗄️ Database Configuration")
        db_group_layout = QVBoxLayout()
        
        db_type_layout = QHBoxLayout()
        db_type_layout.addWidget(QLabel("Database Type:"))
        self.db_type_combo = QComboBox()
        self.db_type_combo.addItems(["SQLite (GeoPackage)", "PostGIS"])
        self.db_type_combo.currentTextChanged.connect(self.on_db_type_changed)
        db_type_layout.addWidget(self.db_type_combo)
        db_type_layout.addStretch()
        db_group_layout.addLayout(db_type_layout)
        
        # SQLite options (put layout inside a QWidget so it can be shown/hidden)
        self.sqlite_widget = QWidget()
        self.sqlite_layout = QHBoxLayout(self.sqlite_widget)
        self.sqlite_layout.addWidget(QLabel("Database File:"))
        self.sqlite_path_edit = QLineEdit()
        self.sqlite_path_edit.setPlaceholderText("proximity_analysis.gpkg")
        self.sqlite_layout.addWidget(self.sqlite_path_edit)
        
        sqlite_browse_btn = QPushButton("Browse...")
        sqlite_browse_btn.clicked.connect(self.browse_sqlite_database)
        self.sqlite_layout.addWidget(sqlite_browse_btn)
        db_group_layout.addWidget(self.sqlite_widget)
        
        # PostGIS options (wrap in a QWidget so it can be shown/hidden)
        self.postgis_widget = QWidget()
        self.postgis_layout = QVBoxLayout(self.postgis_widget)
        
        host_layout = QHBoxLayout()
        host_layout.addWidget(QLabel("Host:"))
        self.postgis_host = QLineEdit()
        self.postgis_host.setText("localhost")
        host_layout.addWidget(self.postgis_host)
        host_layout.addWidget(QLabel("Port:"))
        self.postgis_port = QSpinBox()
        self.postgis_port.setValue(5432)
        self.postgis_port.setRange(1, 65535)
        host_layout.addWidget(self.postgis_port)
        host_layout.addStretch()
        self.postgis_layout.addLayout(host_layout)
        
        db_layout = QHBoxLayout()
        db_layout.addWidget(QLabel("Database:"))
        self.postgis_database = QLineEdit()
        self.postgis_database.setPlaceholderText("proximity_db")
        db_layout.addWidget(self.postgis_database)
        self.postgis_layout.addLayout(db_layout)
        
        user_layout = QHBoxLayout()
        user_layout.addWidget(QLabel("User:"))
        self.postgis_user = QLineEdit()
        self.postgis_user.setText("postgres")
        user_layout.addWidget(self.postgis_user)
        user_layout.addWidget(QLabel("Password:"))
        self.postgis_password = QLineEdit()
        self.postgis_password.setEchoMode(QLineEdit.Password)
        user_layout.addWidget(self.postgis_password)
        user_layout.addStretch()
        self.postgis_layout.addLayout(user_layout)
        
        self.postgis_widget.setVisible(False)
        db_group_layout.addWidget(self.postgis_widget)
        
        # Connection button
        test_conn_btn = QPushButton("🔌 Test Connection")
        test_conn_btn.clicked.connect(self.test_database_connection)
        db_group_layout.addWidget(test_conn_btn)
        
        self.conn_status_label = QLabel("Not connected")
        self.conn_status_label.setStyleSheet("QLabel { color: red; font-style: italic; }")
        db_group_layout.addWidget(self.conn_status_label)
        
        db_group.setLayout(db_group_layout)
        db_config_layout.addWidget(db_group)
        
        # Layer management section
        layer_mgmt_group = QGroupBox("📚 Layer Management")
        layer_mgmt_layout = QVBoxLayout()
        
        save_load_layout = QHBoxLayout()
        self.save_layer_btn = QPushButton("💾 Save Current Layer to DB")
        self.save_layer_btn.clicked.connect(self.save_layer_to_db)
        self.save_layer_btn.setEnabled(False)
        save_load_layout.addWidget(self.save_layer_btn)
        
        self.load_layer_btn = QPushButton("📥 Load Layer from DB")
        self.load_layer_btn.clicked.connect(self.load_layer_from_db)
        self.load_layer_btn.setEnabled(False)
        save_load_layout.addWidget(self.load_layer_btn)
        
        layer_mgmt_layout.addLayout(save_load_layout)
        layer_mgmt_group.setLayout(layer_mgmt_layout)
        db_config_layout.addWidget(layer_mgmt_group)
        
        db_config_layout.addStretch()
        db_config_tab.setLayout(db_config_layout)
        self.tab_widget.addTab(db_config_tab, "🗄️ Database")
        
        # Tab 1: Configuration
        config_tab = QWidget()
        config_layout = QVBoxLayout()
        
        # ===== Source Layer Section =====
        source_group = QGroupBox("📍 Source Layer (What to search around)")
        source_layout = QVBoxLayout()
        
        self.source_combo = QComboBox()
        source_layout.addWidget(QLabel("Select Layer:"))
        source_layout.addWidget(self.source_combo)
        
        self.selected_only_check = QCheckBox("Use selected features only")
        source_layout.addWidget(self.selected_only_check)
        
        source_group.setLayout(source_layout)
        config_layout.addWidget(source_group)
        
        # ===== Distance Section =====
        distance_group = QGroupBox("📏 Search Distance (Exclusive Zones)")
        distance_layout = QVBoxLayout()
        
        info_label = QLabel("ℹ️ Features appear only in their CLOSEST zone (no duplicates)")
        info_label.setStyleSheet("QLabel { color: #0066cc; font-style: italic; padding: 5px; background: #e6f2ff; border-radius: 3px; }")
        distance_layout.addWidget(info_label)
        
        dist_input_layout = QHBoxLayout()
        self.distance_spin = QDoubleSpinBox()
        self.distance_spin.setRange(0.1, 1000000)
        self.distance_spin.setValue(1000)
        self.distance_spin.setDecimals(2)
        self.distance_spin.setSuffix(" m")
        
        dist_input_layout.addWidget(QLabel("Distance:"))
        dist_input_layout.addWidget(self.distance_spin)
        dist_input_layout.addStretch()
        
        distance_layout.addLayout(dist_input_layout)
        
        self.multi_distance_check = QCheckBox("Create multiple distance zones (different colors)")
        distance_layout.addWidget(self.multi_distance_check)
        
        multi_dist_layout = QHBoxLayout()
        multi_dist_layout.addWidget(QLabel("Distances (comma-separated):"))
        self.multi_distance_edit = QLineEdit()
        self.multi_distance_edit.setPlaceholderText("e.g., 100, 200, 500")
        self.multi_distance_edit.setEnabled(False)
        multi_dist_layout.addWidget(self.multi_distance_edit)
        distance_layout.addLayout(multi_dist_layout)
        
        self.multi_distance_check.toggled.connect(self.multi_distance_edit.setEnabled)
        
        distance_group.setLayout(distance_layout)
        config_layout.addWidget(distance_group)
        
        # ===== Target Layers Section =====
        target_group = QGroupBox("🎯 Target Layers (Features to identify)")
        target_layout = QVBoxLayout()
        
        self.target_list = QListWidget()
        self.target_list.setSelectionMode(QListWidget.MultiSelection)
        target_layout.addWidget(self.target_list)
        
        button_layout = QHBoxLayout()
        select_all_btn = QPushButton("Select All")
        deselect_all_btn = QPushButton("Deselect All")
        
        select_all_btn.clicked.connect(self.select_all_targets)
        deselect_all_btn.clicked.connect(self.deselect_all_targets)
        
        button_layout.addWidget(select_all_btn)
        button_layout.addWidget(deselect_all_btn)
        button_layout.addStretch()
        
        target_layout.addLayout(button_layout)
        target_group.setLayout(target_layout)
        config_layout.addWidget(target_group)
        
        # ===== Analysis Options Section =====
        options_group = QGroupBox("⚙️ Analysis Options")
        options_layout = QVBoxLayout()
        
        self.count_check = QCheckBox("Count features")
        self.count_check.setChecked(True)
        options_layout.addWidget(self.count_check)
        
        self.distance_check = QCheckBox("Calculate distances to nearest feature")
        self.distance_check.setChecked(True)
        options_layout.addWidget(self.distance_check)
        
        self.attributes_check = QCheckBox("Include feature attributes")
        self.attributes_check.setChecked(True)
        options_layout.addWidget(self.attributes_check)
        
        self.area_check = QCheckBox("Calculate area covered (for polygons)")
        self.area_check.setChecked(False)
        options_layout.addWidget(self.area_check)
        
        self.length_check = QCheckBox("Calculate length (for lines)")
        self.length_check.setChecked(False)
        options_layout.addWidget(self.length_check)
        
        self.neighbor_check = QCheckBox("Find neighboring polygons (for polygon sources)")
        self.neighbor_check.setChecked(True)
        options_layout.addWidget(self.neighbor_check)
        
        options_group.setLayout(options_layout)
        config_layout.addWidget(options_group)
        
        config_tab.setLayout(config_layout)
        self.tab_widget.addTab(config_tab, "⚙️ Configuration")
        
        # Tab 2: Analysis Log
        log_tab = QWidget()
        log_layout = QVBoxLayout()
        
        log_header = QLabel("📋 Analysis Log")
        log_header.setStyleSheet("QLabel { font-size: 14px; font-weight: bold; padding: 5px; }")
        log_layout.addWidget(log_header)
        
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setStyleSheet("""
            QTextEdit {
                background-color: #1e1e1e;
                color: #d4d4d4;
                font-family: 'Courier New', monospace;
                font-size: 10pt;
            }
        """)
        log_layout.addWidget(self.log_text)
        
        log_button_layout = QHBoxLayout()
        self.clear_log_btn = QPushButton("Clear Log")
        self.clear_log_btn.clicked.connect(self.clear_log)
        self.copy_log_btn = QPushButton("Copy Log")
        self.copy_log_btn.clicked.connect(self.copy_log)
        log_button_layout.addWidget(self.clear_log_btn)
        log_button_layout.addWidget(self.copy_log_btn)
        log_button_layout.addStretch()
        log_layout.addLayout(log_button_layout)
        
        log_tab.setLayout(log_layout)
        self.tab_widget.addTab(log_tab, "📋 Analysis Log")
        
        main_layout.addWidget(self.tab_widget)
        
        # ===== Progress Bar =====
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        main_layout.addWidget(self.progress_bar)
        
        # ===== Status Label =====
        self.status_label = QLabel("")
        self.status_label.setStyleSheet("QLabel { color: blue; font-style: italic; padding: 5px; }")
        main_layout.addWidget(self.status_label)
        
        # ===== Buttons =====
        button_layout = QHBoxLayout()
        
        self.run_btn = QPushButton("▶️ Run Analysis")
        self.run_btn.setStyleSheet("QPushButton { background-color: #4CAF50; color: white; font-weight: bold; padding: 10px; }")
        
        self.new_analysis_btn = QPushButton("🔄 New Analysis")
        self.new_analysis_btn.setStyleSheet("QPushButton { background-color: #2196F3; color: white; font-weight: bold; padding: 10px; }")
        self.new_analysis_btn.setVisible(False)
        
        self.close_btn = QPushButton("✖ Close")
        self.close_btn.setStyleSheet("QPushButton { padding: 10px; }")
        
        self.run_btn.clicked.connect(self.accept_dialog)
        self.new_analysis_btn.clicked.connect(self.reset_for_new_analysis)
        self.close_btn.clicked.connect(self.reject_dialog)
        
        button_layout.addStretch()
        button_layout.addWidget(self.new_analysis_btn)
        button_layout.addWidget(self.run_btn)
        button_layout.addWidget(self.close_btn)
        
        main_layout.addLayout(button_layout)
        
        self.setLayout(main_layout)

    def on_db_type_changed(self):
        """Handle database type change"""
        is_postgis = self.db_type_combo.currentText() == "PostGIS"
        # show/hide the container widgets (layouts themselves can't be shown/hidden)
        self.sqlite_widget.setVisible(not is_postgis)
        self.postgis_widget.setVisible(is_postgis)

    def browse_sqlite_database(self):
        """Browse for SQLite database file location"""
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save GeoPackage Database",
            "",
            "GeoPackage (*.gpkg);;All Files (*)"
        )
        if file_path:
            if not file_path.endswith('.gpkg'):
                file_path += '.gpkg'
            self.sqlite_path_edit.setText(file_path)

    def test_database_connection(self):
        """Test database connection"""
        try:
            if self.db_type_combo.currentText() == "PostGIS":
                # Validate PostGIS inputs
                if not self.postgis_database.text().strip():
                    self.conn_status_label.setText("❌ Database name required")
                    self.conn_status_label.setStyleSheet("QLabel { color: red; }")
                    return
                
                db_config = {
                    'type': 'postgis',
                    'host': self.postgis_host.text(),
                    'port': self.postgis_port.value(),
                    'database': self.postgis_database.text(),
                    'user': self.postgis_user.text(),
                    'password': self.postgis_password.text()
                }
            else:
                # SQLite
                db_path = self.sqlite_path_edit.text().strip()
                if not db_path:
                    db_path = os.path.join(
                        QgsProject.instance().homePath() or os.path.expanduser("~"),
                        "proximity_analysis.gpkg"
                    )
                    self.sqlite_path_edit.setText(db_path)
                
                if not db_path.endswith('.gpkg'):
                    db_path += '.gpkg'
                
                db_config = db_path
            
            # Close old connection if exists
            if self.db:
                self.db.close()
            
            # Create new connection
            self.db = DatabaseManager(db_config)
            
            self.conn_status_label.setText("✅ Connected successfully")
            self.conn_status_label.setStyleSheet("QLabel { color: green; font-weight: bold; }")
            self.save_layer_btn.setEnabled(True)
            self.load_layer_btn.setEnabled(True)
            
            QMessageBox.information(self, "Success", "Database connected successfully!")
            
        except Exception as e:
            error_msg = str(e)
            self.conn_status_label.setText(f"❌ Connection failed: {error_msg[:50]}")
            self.conn_status_label.setStyleSheet("QLabel { color: red; }")
            self.save_layer_btn.setEnabled(False)
            self.load_layer_btn.setEnabled(False)
            QMessageBox.critical(self, "Connection Error", f"Failed to connect to database:\n{error_msg}")

    def save_layer_to_db(self):
        """Save selected layer to database"""
        if not self.db:
            QMessageBox.warning(self, "Error", "Please connect to a database first")
            return
        
        try:
            layer = self.source_combo.currentData()
            if not layer:
                QMessageBox.warning(self, "Error", "Please select a layer")
                return
            
            # Use QGIS native function to save layer
            options = QgsVectorFileWriter.SaveVectorOptions()
            options.driverName = "GPKG" if isinstance(self.db.db_config, str) else "PostgreSQL"
            
            if isinstance(self.db.db_config, str):
                # SQLite/GeoPackage
                output_path = self.db.db_config
            else:
                # PostGIS
                connection_string = (
                    f"postgresql://{self.db.db_config['user']}:"
                    f"{self.db.db_config['password']}@"
                    f"{self.db.db_config['host']}:"
                    f"{self.db.db_config['port']}/{self.db.db_config['database']}"
                )
                output_path = connection_string
            
            error = QgsVectorFileWriter.writeAsVectorFormatV2(
                layer,
                output_path,
                QgsProject.instance().transformContext(),
                options
            )
            
            if error[0] == QgsVectorFileWriter.NoError:
                self.append_log(f"✅ Layer '{layer.name()}' saved to database")
                QMessageBox.information(self, "Success", f"Layer '{layer.name()}' saved successfully!")
            else:
                self.append_log(f"❌ Error saving layer: {error[1]}")
                QMessageBox.critical(self, "Error", f"Failed to save layer:\n{error[1]}")
            
        except Exception as e:
            error_msg = str(e)
            self.append_log(f"❌ Error: {error_msg}")
            QMessageBox.critical(self, "Error", f"Failed to save layer:\n{error_msg}")

    def load_layer_from_db(self):
        """Load layer from database"""
        if not self.db:
            QMessageBox.warning(self, "Error", "Please connect to a database first")
            return
        
        try:
            if isinstance(self.db.db_config, str):
                # SQLite/GeoPackage
                db_path = self.db.db_config
                layer = QgsVectorLayer(db_path, "Loaded Layer", "ogr")
            else:
                # PostGIS
                connection_string = (
                    f"postgresql://{self.db.db_config['user']}:"
                    f"{self.db.db_config['password']}@"
                    f"{self.db.db_config['host']}:"
                    f"{self.db.db_config['port']}/{self.db.db_config['database']}"
                )
                layer = QgsVectorLayer(connection_string, "Loaded Layer", "postgres")
            
            if not layer.isValid():
                QMessageBox.critical(self, "Error", "Failed to load layer from database")
                return
            
            QgsProject.instance().addMapLayer(layer)
            self.append_log(f"✅ Layer loaded from database")
            self.populate_layers()
            QMessageBox.information(self, "Success", "Layer loaded successfully!")
            
        except Exception as e:
            error_msg = str(e)
            self.append_log(f"❌ Error: {error_msg}")
            QMessageBox.critical(self, "Error", f"Failed to load layer:\n{error_msg}")

    def append_log(self, message):
        """Append message to log viewer"""
        self.log_text.append(message)
        # Auto-scroll to bottom
        scrollbar = self.log_text.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    def clear_log(self):
        """Clear the log viewer"""
        self.log_text.clear()

    def copy_log(self):
        """Copy log to clipboard"""
        clipboard = QApplication.clipboard()
        clipboard.setText(self.log_text.toPlainText())
        self.status_label.setText("✅ Log copied to clipboard")

    def show_log_tab(self):
        """Switch to log tab"""
        self.tab_widget.setCurrentIndex(2)

    def reset_for_new_analysis(self):
        """Reset dialog for a new analysis"""
        self.analysis_running = False
        self.run_btn.setVisible(True)
        self.new_analysis_btn.setVisible(False)
        self.tab_widget.setCurrentIndex(1)
        self.status_label.setText("Ready for new analysis")
        self.populate_layers()

    def populate_layers(self):
        """Populate layer dropdowns with available vector layers"""
        self.source_combo.clear()
        self.target_list.clear()
        
        layers = QgsProject.instance().mapLayers().values()
        vector_layers = [layer for layer in layers 
                        if isinstance(layer, QgsVectorLayer)]
        
        if not vector_layers:
            QMessageBox.warning(
                self,
                "No Layers",
                "No vector layers found in project. Please add some layers first."
            )
            return
        
        for layer in vector_layers:
            self.source_combo.addItem(layer.name(), layer)
            item = QListWidgetItem(layer.name())
            item.setData(Qt.UserRole, layer)
            self.target_list.addItem(item)

    def select_all_targets(self):
        """Select all target layers"""
        for i in range(self.target_list.count()):
            self.target_list.item(i).setSelected(True)

    def deselect_all_targets(self):
        """Deselect all target layers"""
        self.target_list.clearSelection()

    def save_current_state(self):
        """Save current dialog state"""
        try:
            self.saved_state = {
                'db_type': self.db_type_combo.currentText(),
                'sqlite_path': self.sqlite_path_edit.text(),
                'postgis_host': self.postgis_host.text(),
                'postgis_port': self.postgis_port.value(),
                'postgis_database': self.postgis_database.text(),
                'postgis_user': self.postgis_user.text(),
                'source_index': self.source_combo.currentIndex(),
                'selected_only': self.selected_only_check.isChecked(),
                'distance': self.distance_spin.value(),
                'multi_distance': self.multi_distance_check.isChecked(),
                'multi_distance_text': self.multi_distance_edit.text(),
                'target_indices': [i for i in range(self.target_list.count()) 
                                  if self.target_list.item(i).isSelected()],
            }
        except Exception as e:
            QgsMessageLog.logMessage(f"Error saving state: {str(e)}", "Proximity Finder", Qgis.Warning)

    def restore_last_state(self):
        """Restore last saved state"""
        try:
            if not self.saved_state:
                return
            
            if 'db_type' in self.saved_state:
                idx = self.db_type_combo.findText(self.saved_state['db_type'])
                if idx >= 0:
                    self.db_type_combo.setCurrentIndex(idx)
            
            if 'sqlite_path' in self.saved_state:
                self.sqlite_path_edit.setText(self.saved_state['sqlite_path'])
            
            if 'postgis_host' in self.saved_state:
                self.postgis_host.setText(self.saved_state['postgis_host'])
                self.postgis_port.setValue(self.saved_state.get('postgis_port', 5432))
                self.postgis_database.setText(self.saved_state.get('postgis_database', ''))
                self.postgis_user.setText(self.saved_state.get('postgis_user', ''))
            
            if 'source_index' in self.saved_state:
                self.source_combo.setCurrentIndex(self.saved_state['source_index'])
            
            if 'selected_only' in self.saved_state:
                self.selected_only_check.setChecked(self.saved_state['selected_only'])
            
            if 'distance' in self.saved_state:
                self.distance_spin.setValue(self.saved_state['distance'])
            
            if 'multi_distance' in self.saved_state:
                self.multi_distance_check.setChecked(self.saved_state['multi_distance'])
            
            if 'multi_distance_text' in self.saved_state:
                self.multi_distance_edit.setText(self.saved_state['multi_distance_text'])
            
            if 'target_indices' in self.saved_state:
                for idx in self.saved_state['target_indices']:
                    if idx < self.target_list.count():
                        self.target_list.item(idx).setSelected(True)
            
        except Exception as e:
            QgsMessageLog.logMessage(f"Error restoring state: {str(e)}", "Proximity Finder", Qgis.Warning)

    def get_parameters(self):
        """Get all parameters from the dialog with validation"""
        self.save_current_state()
        
        try:
            # Validate source layer
            source_layer = self.source_combo.currentData()
            if not source_layer:
                self.show_error("Please select a source layer")
                return None
            
            # Validate target layers
            selected_targets = self.target_list.selectedItems()
            if not selected_targets:
                self.show_error("Please select at least one target layer")
                return None
            
            target_layers = [item.data(Qt.UserRole) for item in selected_targets]
            
            # Validate and get distance(s)
            distances = []
            if self.multi_distance_check.isChecked():
                distance_text = self.multi_distance_edit.text().strip()
                if not distance_text:
                    self.show_error("Please enter distance values or uncheck 'Create multiple distance zones'")
                    return None
                
                try:
                    distances = [float(d.strip()) for d in distance_text.split(',') if d.strip()]
                    if not distances:
                        self.show_error("Please enter valid distance values")
                        return None
                    
                    if any(d <= 0 for d in distances):
                        self.show_error("All distances must be greater than 0")
                        return None
                        
                except ValueError:
                    self.show_error("Invalid distance values. Please use numbers separated by commas (e.g., 100, 200, 500)")
                    return None
            else:
                distance_value = self.distance_spin.value()
                if distance_value <= 0:
                    self.show_error("Distance must be greater than 0")
                    return None
                distances = [distance_value]
            
            # Check if using selected features only
            if self.selected_only_check.isChecked():
                if source_layer.selectedFeatureCount() == 0:
                    reply = QMessageBox.question(
                        self,
                        "No Selection",
                        "No features are selected in the source layer. Do you want to use all features instead?",
                        QMessageBox.Yes | QMessageBox.No,
                        QMessageBox.No
                    )
                    if reply == QMessageBox.Yes:
                        self.selected_only_check.setChecked(False)
                    else:
                        return None
            
            # Build parameters dictionary
            params = {
                'source_layer': source_layer,
                'target_layers': target_layers,
                'distances': sorted(distances),
                'use_selected_only': self.selected_only_check.isChecked(),
                'count_features': self.count_check.isChecked(),
                'calculate_distances': self.distance_check.isChecked(),
                'include_attributes': self.attributes_check.isChecked(),
                'calculate_area': self.area_check.isChecked(),
                'calculate_length': self.length_check.isChecked(),
                'find_neighbors': self.neighbor_check.isChecked(),
                'add_to_map': self.add_to_map_check.isChecked() if hasattr(self, 'add_to_map_check') else True,
                'generate_csv': self.csv_check.isChecked() if hasattr(self, 'csv_check') else True,
                'generate_html': self.html_check.isChecked() if hasattr(self, 'html_check') else True
            }
            
            # Show confirmation
            feature_count = source_layer.selectedFeatureCount() if params['use_selected_only'] else source_layer.featureCount()
            self.status_label.setText(
                f"✅ Ready: {feature_count} source feature(s) • {len(target_layers)} target layer(s) • {len(distances)} exclusive zone(s)"
            )
            
            return params
            
        except Exception as e:
            self.show_error(f"Error getting parameters: {str(e)}")
            QgsMessageLog.logMessage(
                f"Error in get_parameters: {str(e)}",
                "Proximity Finder",
                Qgis.Critical
            )
            return None

    def show_error(self, message):
        """Show error message"""
        self.status_label.setText("")
        QMessageBox.warning(self, "Validation Error", message)
        self.status_label.setStyleSheet("QLabel { color: red; font-style: italic; }")
        self.status_label.setText(f"❌ {message}")

    def accept_dialog(self):
        """Handle dialog acceptance - but don't close"""
        params = self.get_parameters()
        if params:
            # ADD THIS: Include database configuration in params
            if self.db_type_combo.currentText() == "PostGIS":
                params['database_config'] = {
                    'type': 'postgis',
                    'host': self.postgis_host.text(),
                    'port': self.postgis_port.value(),
                    'database': self.postgis_database.text(),
                    'user': self.postgis_user.text(),
                    'password': self.postgis_password.text()
                }
            else:
                # SQLite/GeoPackage
                db_path = self.sqlite_path_edit.text().strip()
                if not db_path:
                    db_path = os.path.join(
                        QgsProject.instance().homePath() or os.path.expanduser("~"),
                        "proximity_analysis.gpkg"
                    )
                if not db_path.endswith('.gpkg'):
                    db_path += '.gpkg'
                params['database_path'] = db_path
            
            self.analysis_running = True
            self.clear_log()
            self.show_log_tab()
            self.append_log("Starting proximity analysis...")
            self.accepted.emit()

    def analysis_completed(self, success, message, log_messages):
        """Called when analysis completes"""
        # Display all log messages
        for log_msg in log_messages:
            self.append_log(log_msg)
        
        if success:
            self.status_label.setStyleSheet("QLabel { color: green; font-weight: bold; }")
            self.status_label.setText(f"✅ {message}")
            self.run_btn.setVisible(False)
            self.new_analysis_btn.setVisible(True)
        else:
            self.status_label.setStyleSheet("QLabel { color: red; font-weight: bold; }")
            self.status_label.setText(f"❌ {message}")
        
        self.analysis_running = False

    def reject_dialog(self):
        """Handle dialog rejection"""
        if self.analysis_running:
            reply = QMessageBox.question(
                self,
                "Analysis Running",
                "Analysis is currently running. Are you sure you want to close?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            if reply == QMessageBox.No:
                return
        
        self.rejected.emit()
        self.close()

    def closeEvent(self, event):
        """Handle window close event"""
        if self.analysis_running:
            reply = QMessageBox.question(
                self,
                "Analysis Running",
                "Analysis is currently running. Are you sure you want to close?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            if reply == QMessageBox.No:
                event.ignore()
                return
        
        self.save_current_state()
        if self.db:
            self.db.close()
        event.accept()