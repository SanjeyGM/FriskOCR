from pathlib import Path
from PIL import Image
import threading
import keyboard
import pyperclip
import json
import os
import sys
import subprocess
import importlib.util
from PyQt5.QtCore import Qt, QRect, QSize, QTimer, QThread, pyqtSignal, QPropertyAnimation, QEasingCurve, QPointF, pyqtProperty
from PyQt5.QtGui import QCursor, QPixmap, QIcon, QPalette, QColor, QKeySequence
from PyQt5.QtWidgets import (QApplication, QLabel, QSystemTrayIcon, QMenu, 
                           QRubberBand, QMainWindow, QDialog, QPushButton, 
                           QVBoxLayout, QHBoxLayout, QComboBox, QProgressBar,
                           QMessageBox, QLineEdit, QWidget, QGraphicsOpacityEffect)
import multiprocessing

def format_shortcut_display(shortcut):
    """Convert shortcut string to camel notation (e.g., 'shift+r' to 'Shift+R')"""
    parts = shortcut.split('+')
    formatted_parts = []
    for part in parts:
        if part in ['shift', 'ctrl', 'alt']:
            formatted_parts.append(part.capitalize())
        else:
            formatted_parts.append(part.upper())
    return '+'.join(formatted_parts)

class ModelInstallWorker(QThread):
    progress = pyqtSignal(str)
    finished = pyqtSignal(bool, str)
    
    def __init__(self, model_name):
        super().__init__()
        self.model_name = model_name
    
    def run(self):
        try:
            # Placeholder for future development if needed
            self.finished.emit(True, "Model check completed")
        except Exception as e:
            self.finished.emit(False, str(e))



class BaseOCRView(QMainWindow):
    def __init__(self):
        super().__init__(None, Qt.Window | Qt.WindowMinimizeButtonHint | Qt.WindowCloseButtonHint)
        self.first_hide = True
        self.setWindowTitle("Screenshot OCR")
        self.setWindowIcon(QIcon(self.get_resource_path("assets/icon.ico")))
        self.apply_theme()
        self.config_file = "ocr_config.json"
        self.load_config()
        self.ocr = None
        self.current_hotkey = None
        self.hotkey_callback = None
        self.settings_dialog = None  # Initialize settings_dialog to None

        self.screenshotLabel = QLabel(self)
        self.screenshotLabel.setAlignment(Qt.AlignCenter)
        self.pixmap = QPixmap()
        
        self.rubberBand = QRubberBand(QRubberBand.Rectangle, self)
        self.startPoint = None
        
        self.screen_geometry = None
        self.original_width = None
        self.original_height = None
        
        self.setup_tray()
        
        # Replace immediate initialization with just showing settings
        QTimer.singleShot(0, self.show_initial_settings)
        
        self.hide()

    def apply_theme(self):
        self.setStyleSheet("""
            QMainWindow {
                background-color: #1a1a1a;
                color: #ffffff;
            }
            QMenu {
                background-color: #2d2d2d;
                color: #ffffff;
                border: 1px solid #0078d7;
            }
            QMenu::item {
                padding: 5px 20px;
            }
            QMenu::item:selected {
                background-color: #0078d7;
            }
            QSystemTrayIcon {
                background-color: #2d2d2d;
            }
            QRubberBand {
                background-color: rgba(0, 120, 215, 0.2);
                border: 1px solid #0078d7;
            }
            QMessageBox {
                background-color: #1a1a1a;
                color: #ffffff;
            }
            QMessageBox QPushButton {
                background-color: #0078d7;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                min-width: 80px;
            }
            QMessageBox QPushButton:hover {
                background-color: #1e90ff;
            }
            QMessageBox QLabel {
                color: #ffffff;
            }
        """)

    def load_stylesheet(self):
        return """
        QMainWindow {
            background-color: #1e1e1e;
            color: #ffffff;
        }
        QLabel {
            font-size: 16px;
            color: #ffffff;
        }
        QPushButton {
            background-color: #0078d7;
            color: white;
            border: none;
            padding: 10px 20px;
            text-align: center;
            font-size: 16px;
            margin: 4px 2px;
            border-radius: 8px;
        }
        QPushButton:hover {
            background-color: #005a9e;
        }
        QLineEdit {
            padding: 5px;
            border: 1px solid #0078d7;
            border-radius: 4px;
            color: #ffffff;
            background-color: #333333;
        }
        QComboBox {
            padding: 5px;
            border: 1px solid #0078d7;
            border-radius: 4px;
            color: #ffffff;
            background-color: #333333;
        }
        QSystemTrayIcon {
            icon-size: 24px;
        }
        QMenu {
            background-color: #1e1e1e;
            border: 1px solid #0078d7;
            color: #ffffff;
        }
        QMenu::item {
            padding: 5px 30px;
        }
        QMenu::item:selected {
            background-color: #0078d7;
            color: white;
        }
        """

    def load_config(self):
        try:
            config_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ocr_config.json")
            if os.path.exists(config_file):
                with open(config_file, 'r') as f:
                    config = json.load(f)
            else:
                config = {"shortcut": "shift+r", "model": "manga-ocr"}
                with open(config_file, 'w') as f:
                    json.dump(config, f)

            self.shortcut = config.get("shortcut", "shift+r")
            self.current_model = config.get("model", "manga-ocr")
        except Exception as e:
            self.shortcut = "shift+r"
            self.current_model = "manga-ocr"
            print(f"Error loading config: {e}")

    
    def save_config(self):
        try:
            config = {
                "shortcut": self.shortcut,
                "model": self.current_model  # Ensure this saves the currently selected model
            }
            with open(self.config_file, 'w') as f:
                json.dump(config, f)
        except Exception as e:
            print(f"Error saving config: {e}")

    def check_ocr_models(self):
    # """Check and return the first available OCR model"""
        manga_ocr_spec = importlib.util.find_spec('manga_ocr')
        easyocr_spec = importlib.util.find_spec('easyocr')
        
        # Return the first available model
        if manga_ocr_spec:
            return "manga-ocr"
        elif easyocr_spec:
            return "easyocr"
        return None

    def initialize_ocr(self, loading_dialog=None):
        try:
            # Clean up existing OCR instance
            if hasattr(self, 'ocr') and self.ocr:
                del self.ocr
                self.ocr = None
            
            os.environ['PYTHONIOENCODING'] = 'utf-8'
            # Force console to use utf-8
            if sys.platform.startswith('win'):
                import ctypes
                kernel32 = ctypes.windll.kernel32
                kernel32.SetConsoleOutputCP(65001)
            
            if self.current_model == "manga-ocr":
                try:
                    from manga_ocr import MangaOcr
                    if loading_dialog:
                        loading_dialog.setText("Initializing Manga OCR model...")
                    QApplication.processEvents()
                    
                    self.ocr = MangaOcr()
                    return True
                    
                except Exception as e:
                    if "DLL load failed" in str(e):
                        QMessageBox.critical(
                            self,
                            "Python Installation Error",
                            "This error occurs because Python was installed from Microsoft Store.\n\n"
                            "Please:\n"
                            "1. Uninstall the Microsoft Store version of Python\n"
                            "2. Download and install Python from python.org\n"
                            "3. Restart the application"
                        )
                    else:
                        QMessageBox.critical(
                            self,
                            "Error",
                            f"Error initializing Manga OCR: {str(e)}\n\n"
                            "Try restarting the application."
                        )
                    return False
            
            elif self.current_model == "easyocr":
                try:
                    # Suppress stdout during import to avoid encoding errors
                    old_stdout = sys.stdout
                    sys.stdout = open(os.devnull, 'w', encoding='utf-8')
                    
                    import easyocr
                    sys.stdout = old_stdout
                    
                    if loading_dialog:
                        loading_dialog.setText("Initializing EasyOCR model...")
                    QApplication.processEvents()
                    
                    # Suppress stdout during Reader initialization
                    sys.stdout = open(os.devnull, 'w', encoding='utf-8')
                    self.ocr = easyocr.Reader(['en'], gpu=False, download_enabled=True, verbose=False)
                    sys.stdout = old_stdout
                    
                    return True
                    
                except ImportError:
                    sys.stdout = old_stdout
                    QMessageBox.critical(
                        self,
                        "Import Error",
                        "EasyOCR is not properly installed.\n\n"
                        "Please install it using:\n"
                        "pip install easyocr"
                    )
                    return False
                except Exception as e:
                    sys.stdout = old_stdout
                    if 'model' in str(e).lower():
                        QMessageBox.critical(
                            self,
                            "Model Error",
                            "EasyOCR models not found. Please download them manually:\n\n"
                            "1. Open command prompt as administrator\n"
                            "2. Run: python -m pip install --upgrade easyocr\n"
                            "3. Run: python -c \"import easyocr; easyocr.Reader(['en'])\"\n"
                            "4. Restart the application"
                        )
                    else:
                        QMessageBox.critical(
                            self,
                            "Error",
                            f"Error initializing EasyOCR: {str(e)}\n\n"
                            "Try restarting the application."
                        )
                    return False
                finally:
                    sys.stdout = old_stdout
            
            return False
        except Exception as e:
            QMessageBox.critical(
                self,
                "Error",
                f"Error initializing OCR: {str(e)}\n\n"
                "Try restarting the application."
            )
            return False
        finally:
            if loading_dialog:
                loading_dialog.close()

    def get_resource_path(self, relative_path):
    # """Get absolute path to resource, works for dev and for PyInstaller."""
        try:
            # PyInstaller creates a temp folder and stores path in _MEIPASS
            base_path = sys._MEIPASS
        except Exception:
            # Use the directory where the script is located
            base_path = os.path.dirname(os.path.abspath(__file__))

        return os.path.join(base_path, relative_path)
            
    def setup_tray(self):
        self.tray_icon = QSystemTrayIcon(self)

        # Get the absolute path to the icon
        icon_path = self.get_resource_path("assets/icon.ico")
        print(f"Looking for icon at: {icon_path}")  # Debug print

        if not os.path.exists(icon_path):
            print(f"Warning: Icon file not found at {icon_path}")
            # Try an alternative path
            alt_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", "icon.ico")
            print(f"Trying alternative path: {alt_path}")  # Debug print
            if os.path.exists(alt_path):
                icon_path = alt_path

        self.tray_icon.setIcon(QIcon(icon_path))

    # Rest of the setup_tray function remains the same

        tray_menu = QMenu()
        settings_action = tray_menu.addAction("Settings")
        tray_menu.addSeparator()
        quit_action = tray_menu.addAction("Quit")
        
        settings_action.triggered.connect(lambda: self.show_settings(first_run=False))
        quit_action.triggered.connect(self.quit_app)
        
        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.setVisible(True)
        
        tooltip = "OCR Tool (No model installed)" if not self.ocr else f"OCR Tool (Shortcut: {format_shortcut_display(self.shortcut)})"
        self.tray_icon.setToolTip(tooltip)
    def start_hotkey_listener(self):
        try:
            # Remove existing hotkey if it exists
            if self.hotkey_callback:
                keyboard.remove_hotkey(self.hotkey_callback)
                self.hotkey_callback = None
            
            # Register new hotkey and store the callback
            self.hotkey_callback = keyboard.add_hotkey(self.shortcut, self.trigger_screenshot_display)
            self.current_hotkey = self.shortcut
            
            # Update tray tooltip
            if hasattr(self, 'tray_icon'):
                self.tray_icon.setToolTip(f"OCR Tool (Shortcut: {format_shortcut_display(self.shortcut)})")
        except Exception as e:
            QMessageBox.warning(
                self,
                "Hotkey Error",
                f"Error setting shortcut: {str(e)}\nPlease try a different shortcut."
            )
            # Revert to default if there's an error
            self.shortcut = "shift+r"
            self.save_config()
            self.start_hotkey_listener()

    def restart_hotkey_listener(self):
        try:
            # Remove existing hotkey
            if self.hotkey_callback:
                keyboard.remove_hotkey(self.hotkey_callback)
                self.hotkey_callback = None
            
            # Add a small delay before registering the new hotkey
            QTimer.singleShot(100, self.start_hotkey_listener)
            
        except Exception as e:
            QMessageBox.warning(
                self,
                "Hotkey Error",
                f"Error updating shortcut: {str(e)}\nPlease try a different shortcut."
            )
            # Revert to the previous shortcut if there's an error
            self.shortcut = self.current_hotkey if self.current_hotkey else "shift+r"
            self.save_config()
            self.start_hotkey_listener()

    def show_settings(self, first_run=False, show_loading=False):
        if self.settings_dialog is None:
            self.settings_dialog = SettingsDialog(
                self,
                current_shortcut=self.shortcut,
                current_model=self.current_model,
                first_run=first_run
            )
        if first_run:
            result = self.settings_dialog.exec_()
            if result == QDialog.Accepted and show_loading:
                loading_dialog = LoadingDialog(self)
                loading_dialog.show()
                
                # Use QTimer to allow the loading dialog to show
                QTimer.singleShot(100, lambda: self.initialize_model_with_loading(loading_dialog))
        else:
            if self.settings_dialog.exec_() == QDialog.Accepted:
                new_shortcut = self.settings_dialog.new_shortcut
                if new_shortcut != self.shortcut:
                    old_shortcut = self.shortcut
                    self.shortcut = new_shortcut
                    self.save_config()
                    
                    try:
                        if self.ocr:
                            self.restart_hotkey_listener()
                    except Exception as e:
                        self.shortcut = old_shortcut
                        self.save_config()
                        self.restart_hotkey_listener()
                        QMessageBox.warning(
                            self,
                            "Shortcut Error",
                            f"Could not set new shortcut: {str(e)}\nReverted to previous shortcut."
                        )
                
                new_model = self.settings_dialog.model_combo.currentData()
                if new_model != self.current_model:
                    self.current_model = new_model
                    self.save_config()
                    
                    loading_dialog = LoadingDialog(self)
                    loading_dialog.show()
                    QTimer.singleShot(100, lambda: self.initialize_model_with_loading(loading_dialog))
        self.settings_dialog = None  # Reset settings_dialog after closing

    def initialize_model_with_loading(self, loading_dialog):
        if self.initialize_ocr(loading_dialog):
            if not self.current_hotkey:
                self.start_hotkey_listener()
            self.tray_icon.setToolTip(f"OCR Tool (Shortcut: {format_shortcut_display(self.shortcut)})")
        else:
            loading_dialog.close()
            QMessageBox.warning(
                self,
                "Model Not Available",
                "The selected model could not be initialized. Please check if it's properly installed."
            )

    def process_image(self, pil_image):
        try:
            if not self.ocr or self.current_model not in ["manga-ocr", "easyocr"]:
                if not self.initialize_ocr():
                    QMessageBox.warning(self, "No OCR Model", "Please install an OCR model first.")
                    return ""

            if self.current_model == "manga-ocr":
                return self.ocr(pil_image)
            elif self.current_model == "easyocr":
                import numpy as np
                # Convert image to RGB before processing
                numpy_image = np.array(pil_image.convert('RGB'))
                result = self.ocr.readtext(numpy_image)
                return ' '.join([text for _, text, _ in result])
        except Exception as e:
            QMessageBox.critical(self, "OCR Error", f"Error processing image: {str(e)}")
            return ""

    def trigger_screenshot_display(self):
        if not self.ocr:
            QMessageBox.warning(
                self,
                "No OCR Model",
                "Please install and initialize an OCR model from the Settings first."
            )
            return
        QTimer.singleShot(0, self.capture_and_display_screenshot)

    def capture_and_display_screenshot(self):
        screen = QApplication.primaryScreen()
        self.screen_geometry = screen.geometry()
        self.pixmap = screen.grabWindow(0)
        
        # Store the original screen dimensions
        self.original_width = self.screen_geometry.width()
        self.original_height = self.screen_geometry.height()
        
        # Scale the screenshot to fit the display
        scaled_pixmap = self.pixmap.scaled(
            self.screen_geometry.width(),
            self.screen_geometry.height(),
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation
        )
        
        self.screenshotLabel.setPixmap(scaled_pixmap)
        self.screenshotLabel.setGeometry(0, 0, self.screen_geometry.width(), self.screen_geometry.height())
        self.setWindowFlag(Qt.WindowStaysOnTopHint)
        QApplication.setOverrideCursor(Qt.CrossCursor)
        self.showFullScreen()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.startPoint = event.pos()
            self.rubberBand.setGeometry(QRect(self.startPoint, QSize()))
            self.rubberBand.show()

    def mouseMoveEvent(self, event):
        if self.startPoint and event.buttons() & Qt.LeftButton:
            self.rubberBand.setGeometry(QRect(self.startPoint, event.pos()).normalized())

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton and self.startPoint:
            self.finalize_selection()
            QApplication.restoreOverrideCursor()
            self.hide()
            self.startPoint = None

    def finalize_selection(self):
        if self.rubberBand.isVisible():
            rect = self.rubberBand.geometry()
            
            # Calculate the scaling factors
            scale_x = self.pixmap.width() / self.screen_geometry.width()
            scale_y = self.pixmap.height() / self.screen_geometry.height()
            
            # Apply scaling to get the actual coordinates in the original image
            scaled_rect = QRect(
                int(rect.x() * scale_x),
                int(rect.y() * scale_y),
                int(rect.width() * scale_x),
                int(rect.height() * scale_y)
            )
            
            cropped_pixmap = self.pixmap.copy(scaled_rect)
            image = cropped_pixmap.toImage()
            
            buffer = image.bits().asstring(image.sizeInBytes())
            pil_image = Image.frombytes(
                "RGBA", 
                (image.width(), image.height()), 
                buffer
            )
            
            ocr_result = self.process_image(pil_image)
            if ocr_result:
                pyperclip.copy(ocr_result)
                self.tray_icon.showMessage(
                    "OCR Complete",
                    "Text has been copied to clipboard",
                    QSystemTrayIcon.Information,
                    2000
                )
            
            self.rubberBand.hide()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            QApplication.restoreOverrideCursor()
            self.hide()
            if self.first_hide:
                self.tray_icon.showMessage(
                    "OCR Tool",
                    "Application is now minimized to system tray.\nYou can access it through the tray icon.",
                    QSystemTrayIcon.Information,
                    3000
                )
                self.first_hide = False
        super().keyPressEvent(event)

    def quit_app(self):
        try:
            if self.hotkey_callback:
                keyboard.remove_hotkey(self.hotkey_callback)
                self.hotkey_callback = None
        except Exception:
            pass  # Ignore errors during cleanup
            
        self.tray_icon.hide()
        QApplication.quit()
        
    def show_initial_settings(self):
        """Show settings dialog on startup without auto-initializing model"""
        self.settings_dialog = SettingsDialog(
            self,
            current_shortcut=self.shortcut,
            current_model=self.current_model,
            first_run=True
        )
        self.settings_dialog.show()

class LoadingOverlay(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setParent(parent)
        self.resize(parent.size())
        self.setAttribute(Qt.WA_TransparentForMouseEvents)
        
        # Initialize angle
        self._current_angle = 0
        
        # Create semi-transparent dark background
        self.background_effect = QGraphicsOpacityEffect()
        self.background_effect.setOpacity(0.7)
        self.setGraphicsEffect(self.background_effect)
        self.setStyleSheet("background-color: #000000;")
        
        # Create loading label with 'F' animation
        self.loading_label = QLabel("Loading...", self)
        self.loading_label.setStyleSheet("""
            QLabel {
                color: #0078d7;
                font-size: 24px;
                font-weight: bold;
                background-color: transparent;
                padding: 20px;
            }
        """)
        self.loading_label.setAlignment(Qt.AlignCenter)
        
        # Center the loading label
        layout = QVBoxLayout(self)
        layout.addWidget(self.loading_label, alignment=Qt.AlignCenter)
        
        # Create loading animation
        self.animation = QTimer(self)
        self.animation.timeout.connect(self.update_text)
        self.animation.start(500)  # Update every 500ms
        self.dots = 0

    def update_text(self):
        self.dots = (self.dots + 1) % 4
        self.loading_label.setText("Loading" + "." * self.dots)

    def showEvent(self, event):
        self.resize(self.parent().size())
        super().showEvent(event)

    def hideEvent(self, event):
        super().hideEvent(event)
        # Stop animation when hidden
        self.animation.stop()

class SettingsDialog(QDialog):
    def __init__(self, parent=None, current_shortcut="shift+r", current_model="manga-ocr", first_run=False):
        super().__init__(parent, Qt.Window | Qt.WindowMinimizeButtonHint | Qt.WindowCloseButtonHint)
        self.setWindowTitle("OCR Settings")
        self.setWindowIcon(QIcon(self.get_resource_path("assets/icon.ico")))
        self.setFixedSize(400, 250)  # Reduced height to fit content better
        self.new_shortcut = current_shortcut
        self.current_model = current_model
        self.first_run = first_run
        self.setup_ui()
        self.apply_theme()
        self.is_loading = False  # Add this line
        self.loading_overlay = LoadingOverlay(self)
        self.loading_overlay.hide()
        # Format the initial shortcut display
        self.shortcut_input.setText(format_shortcut_display(current_shortcut))

    def apply_theme(self):
        self.setStyleSheet("""
            QDialog {
                background-color: #1a1a1a;
                color: #ffffff;
            }
            QLabel {
                color: #ffffff;
                font-size: 12px;
                margin-bottom: 2px;
            }
            QPushButton {
                background-color: #0078d7;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-size: 12px;
                min-width: 80px;
            }
            QPushButton:hover {
                background-color: #1e90ff;
            }
            QPushButton:pressed {
                background-color: #005fb8;
            }
            QLineEdit {
                background-color: #2d2d2d;
                border: 1px solid #0078d7;
                border-radius: 4px;
                padding: 6px;
                color: white;
                font-size: 12px;
                min-height: 20px;
            }
            QComboBox {
                background-color: #2d2d2d;
                border: 1px solid #0078d7;
                border-radius: 4px;
                padding: 6px;
                color: white;
                font-size: 12px;
                min-height: 20px;
            }
            QComboBox::drop-down {
                border: none;
                padding-right: 10px;
            }
            QComboBox::down-arrow {
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 5px solid #0078d7;
                margin-right: 5px;
            }
            QComboBox QAbstractItemView {
                background-color: #2d2d2d;
                border: 1px solid #0078d7;
                selection-background-color: #0078d7;
            }
        """)

    def setup_ui(self):
        main_layout = QVBoxLayout()
        main_layout.setSpacing(15)
        main_layout.setContentsMargins(20, 20, 20, 20)

        # Create form layout for better alignment
        form_layout = QVBoxLayout()
        form_layout.setSpacing(15)

        # Shortcut section
        shortcut_label = QLabel("Keyboard Shortcut")
        self.shortcut_input = QLineEdit(self.new_shortcut)
        self.shortcut_input.setReadOnly(True)
        
        # Add shortcut widgets
        form_layout.addWidget(shortcut_label)
        form_layout.addWidget(self.shortcut_input)

        # Model section
        model_label = QLabel("OCR Language")
        self.model_combo = QComboBox()
        self.model_combo.addItem("Japanese", "manga-ocr")
        self.model_combo.addItem("English", "easyocr")
        
        # Set current model
        index = self.model_combo.findData(self.current_model)
        if index >= 0:
            self.model_combo.setCurrentIndex(index)

        # Add model widgets
        form_layout.addWidget(model_label)
        form_layout.addWidget(self.model_combo)

        # Add form layout to main layout
        main_layout.addLayout(form_layout)

        # Button section
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)
        
        self.save_button = QPushButton("Load")  # Changed from "Save" to "Load"
        self.cancel_button = QPushButton("Cancel")
        
        button_layout.addStretch()
        button_layout.addWidget(self.save_button)
        button_layout.addWidget(self.cancel_button)

        main_layout.addStretch()
        main_layout.addLayout(button_layout)

        self.setLayout(main_layout)

        # Connect signals
        self.shortcut_input.installEventFilter(self)
        self.save_button.clicked.connect(self.accept)
        self.cancel_button.clicked.connect(self.reject)

    def get_resource_path(self, relative_path):
        try:
            base_path = sys._MEIPASS
        except Exception:
            base_path = os.path.dirname(os.path.abspath(__file__))
        return os.path.join(base_path, relative_path)

    def apply_dark_palette(self):
        dark_palette = QPalette()
        dark_palette.setColor(QPalette.Window, QColor(43, 43, 43))
        dark_palette.setColor(QPalette.WindowText, Qt.white)
        dark_palette.setColor(QPalette.Base, QColor(61, 61, 61))
        dark_palette.setColor(QPalette.AlternateBase, QColor(43, 43, 43))
        dark_palette.setColor(QPalette.ToolTipBase, Qt.white)
        dark_palette.setColor(QPalette.ToolTipText, Qt.white)
        dark_palette.setColor(QPalette.Text, Qt.white)
        dark_palette.setColor(QPalette.Button, QColor(61, 61, 61))
        dark_palette.setColor(QPalette.ButtonText, Qt.white)
        dark_palette.setColor(QPalette.BrightText, Qt.red)
        dark_palette.setColor(QPalette.Link, QColor(0, 120, 215))
        dark_palette.setColor(QPalette.Highlight, QColor(0, 120, 215))
        dark_palette.setColor(QPalette.HighlightedText, Qt.white)
        self.setPalette(dark_palette)

    def load_stylesheet(self):
        return """
        QDialog {
            background-color: #2B2B2B;
            color: #FFFFFF;
        }
        QLabel {
            font-size: 14px;
            color: #FFFFFF;
            padding: 5px;
        }
        QPushButton {
            background-color: #3D3D3D;
            color: white;
            border: 1px solid #505050;
            padding: 8px 16px;
            text-align: center;
            font-size: 14px;
            border-radius: 4px;
            min-width: 80px;
        }
        QPushButton:hover {
            background-color: #505050;
            border: 1px solid #666666;
        }
        QPushButton:pressed {
            background-color: #666666;
        }
        QLineEdit {
            padding: 8px;
            background-color: #3D3D3D;
            border: 1px solid #505050;
            border-radius: 4px;
            color: #FFFFFF;
            selection-background-color: #0078D7;
        }
        QLineEdit:focus {
            border: 1px solid #0078D7;
        }
        QComboBox {
            padding: 8px;
            background-color: #3D3D3D;
            border: 1px solid #505050;
            border-radius: 4px;
            color: #FFFFFF;
            min-width: 200px;
        }
        QComboBox:hover {
            border: 1px solid #666666;
        }
        QComboBox:focus {
            border: 1px solid #0078D7;
        }
        QComboBox::drop-down {
            border: none;
            width: 20px;
            padding-right: 4px;
        }
        QComboBox::down-arrow {
            image: none;
            border: none;
            width: 0;
        }
        QComboBox QAbstractItemView {
            background-color: #3D3D3D;
            border: 1px solid #505050;
            selection-background-color: #505050;
            selection-color: #FFFFFF;
            color: #FFFFFF;
        }
        QGroupBox {
            background-color: #2B2B2B;
            border: 1px solid #505050;
            border-radius: 4px;
            margin-top: 8px;
            padding-top: 16px;
        }
        QGroupBox::title {
            color: #FFFFFF;
            subcontrol-origin: margin;
            left: 8px;
            padding: 0 3px;
        }
        """

    def eventFilter(self, obj, event):
        if obj == self.shortcut_input and event.type() == event.KeyPress:
            key = event.key()
            if key != Qt.Key_Escape:
                modifiers = []
                if event.modifiers() & Qt.ShiftModifier:
                    modifiers.append("shift")
                if event.modifiers() & Qt.ControlModifier:
                    modifiers.append("ctrl")
                if event.modifiers() & Qt.AltModifier:
                    modifiers.append("alt")
                
                key_text = QKeySequence(key).toString().lower()
                if key_text:
                    if modifiers:
                        self.new_shortcut = "+".join(modifiers + [key_text])
                    else:
                        self.new_shortcut = key_text
                    # Format the display text while keeping the internal value lowercase
                    self.shortcut_input.setText(format_shortcut_display(self.new_shortcut))
                    event.accept()
                return True
        return super().eventFilter(obj, event)

    def install_model(self):
        model_name = self.model_combo.currentData()
        self.install_button.setEnabled(False)
        self.progress_bar.setRange(0, 0)
        self.progress_bar.show()
        self.progress_label.show()
        
        self.worker = ModelInstallWorker(model_name)
        self.worker.progress.connect(self.update_progress)
        self.worker.finished.connect(self.installation_finished)
        self.worker.start()

    def update_progress(self, message):
        self.progress_label.setText(message)

    def installation_finished(self, success, message):
        self.install_button.setEnabled(True)
        self.progress_bar.hide()
        self.progress_label.hide()
        
        if success:
            QMessageBox.information(self, "Success", "Model installed successfully!")
        else:
            QMessageBox.critical(self, "Error", f"Installation failed: {message}")
    
    def on_model_changed(self, model_name):
        self.current_model = model_name  # Update the current model
        self.save_config()  # Save immediately after change

    def accept(self):
        """Handle save button click"""
        self.is_loading = True
        self.loading_overlay.show()
        QApplication.processEvents()
        
        changes_made = False
        parent = self.parent()
        new_shortcut = self.shortcut_input.text()
        new_model = self.model_combo.currentData()

        # Update shortcut if changed
        if new_shortcut != parent.shortcut:
            changes_made = True
            parent.shortcut = new_shortcut
            parent.save_config()
            try:
                if parent.ocr:
                    parent.restart_hotkey_listener()
            except Exception as e:
                QMessageBox.warning(
                    self,
                    "Shortcut Error",
                    f"Could not set new shortcut: {str(e)}"
                )

        # Initialize model on first run or when model changes
        if self.first_run or new_model != parent.current_model:
            changes_made = True
            parent.current_model = new_model
            parent.save_config()
            
            # Always initialize on first run
            if parent.initialize_ocr():
                if not parent.current_hotkey:
                    parent.start_hotkey_listener()
                QMessageBox.information(self, "Success", "Model initialized successfully!")
            else:
                QMessageBox.warning(
                    self,
                    "Model Not Available",
                    "The selected model could not be initialized. Please check if it's properly installed."
                )
        
        # Show success message if changes were made and not first run
        elif changes_made:
            QMessageBox.information(self, "Success", "Settings saved successfully!")

        self.loading_overlay.hide()
        self.is_loading = False
        
        # Close dialog after successful save/initialization if not first run
        if not self.first_run:
            super().accept()

    def reject(self):
        if not self.is_loading:
            super().reject()
            parent = self.parent()
            parent.hide()
            if parent.first_hide:
                parent.tray_icon.showMessage(
                    "OCR Tool",
                    "Application is now minimized to system tray.\nYou can access it through the tray icon.",
                    QSystemTrayIcon.Information,
                    3000
                )
                parent.first_hide = False

    def keyPressEvent(self, event):
        # Only allow Escape when not loading
        if event.key() == Qt.Key_Escape and not self.is_loading:
            self.reject()
        else:
            super().keyPressEvent(event)
            
def main():
    app = QApplication.instance()
    if not app:
        app = QApplication(sys.argv)
    
    # Set application-wide dark theme
    app.setStyle("Fusion")
    
    dark_palette = QPalette()
    dark_palette.setColor(QPalette.Window, QColor(26, 26, 26))
    dark_palette.setColor(QPalette.WindowText, Qt.white)
    dark_palette.setColor(QPalette.Base, QColor(45, 45, 45))
    dark_palette.setColor(QPalette.AlternateBase, QColor(26, 26, 26))
    dark_palette.setColor(QPalette.ToolTipBase, Qt.white)
    dark_palette.setColor(QPalette.ToolTipText, Qt.white)
    dark_palette.setColor(QPalette.Text, Qt.white)
    dark_palette.setColor(QPalette.Button, QColor(45, 45, 45))
    dark_palette.setColor(QPalette.ButtonText, Qt.white)
    dark_palette.setColor(QPalette.BrightText, Qt.red)
    dark_palette.setColor(QPalette.Link, QColor(0, 120, 215))
    dark_palette.setColor(QPalette.Highlight, QColor(0, 120, 215))
    dark_palette.setColor(QPalette.HighlightedText, Qt.white)
    
    app.setPalette(dark_palette)
    
    if not QSystemTrayIcon.isSystemTrayAvailable():
        QMessageBox.critical(None, "OCR Tool", "System tray is not available on this system.")
        sys.exit(1)
    
    QApplication.setQuitOnLastWindowClosed(False)
    window = BaseOCRView()
    
    try:
        sys.exit(app.exec_())
    except SystemExit:
        try:
            if window.hotkey_callback:
                keyboard.remove_hotkey(window.hotkey_callback)
        except Exception:
            pass
        if hasattr(window, 'tray_icon'):
            window.tray_icon.hide()

if __name__ == "__main__":
    multiprocessing.freeze_support()
    
    main()
