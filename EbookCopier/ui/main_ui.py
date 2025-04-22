from PySide6.QtWidgets import (

    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QComboBox,
    QLineEdit,
    QPushButton,
    QFileDialog,
    QSizePolicy,
    QApplication



)
from PySide6.QtCore import (
    Qt,
)
from PySide6.QtGui import (
    QIntValidator
)
import logging
# from ui.styles import pyside_styles
from utils.logs import setup_logging
from settings.config import Book
from update.update_manager import UpdateManger
from ui.popup_windows import MessageBox
from ui.popup_windows import DialogResult
from pathlib import Path

logger = logging.getLogger(__name__)


class BookCopierUI(QMainWindow):
    """
    Main application window for BookCopier
    Handles all UI components and user interactions
    """

    def __init__(self, settings, start_command=None):
        super().__init__()
        self.settings = settings
        self.start_command = start_command
        self._setup_logger()
        self._init_ui()
        # self._check_for_update()

        # connect signals
        self.site_selector.currentTextChanged.connect(self._handle_site_change)

    def _init_ui(self):
        """Initialize the main UI components"""
        self.setWindowTitle("Book Copier")
        self.setFixedSize(450, 260)

        # center widget and main layouot
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(10, 10, 10, 10)

        # Create form widgets
        self._create_form_widgets(main_layout)

        # Start button
        start_btn = QPushButton("Start Processing")
        start_btn.clicked.connect(lambda: self.start_command(self.get_book_params()))
        main_layout.addWidget(start_btn)

    def _create_form_widgets(self, layout):
        """Create all the form widgetse and their layouots"""
        """Create all the form widgets and their layouts"""
        # Site Selector - Centered
        site_layout = QHBoxLayout()
        site_layout.addWidget(QLabel("Select Site:"))

        # Add stretchable space before and after the combobox
        site_layout.addStretch(1)  # Left stretch

        self.site_selector = QComboBox()
        self.site_selector.addItems(["", "Libby", "Hoopla"])
        self.site_selector.setCurrentIndex(0)
        self.site_selector.setFixedWidth(200)
        site_layout.addWidget(self.site_selector, alignment=Qt.AlignCenter)  # Center alignment

        site_layout.addStretch(1)  # Right stretch
        layout.addLayout(site_layout)

        # Page View Selector - Centered
        page_view_layout = QHBoxLayout()
        page_view_layout.addWidget(QLabel("Page View:"))

        page_view_layout.addStretch(1)  # Left stretch

        self.page_view_selector = QComboBox()
        self.page_view_selector.addItems(["One Page", "Two Pages"])
        self.page_view_selector.setCurrentIndex(0)
        self.page_view_selector.setFixedWidth(200)
        self.page_view_selector.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)  # Allow horizontal expansion
        page_view_layout.addWidget(self.page_view_selector, alignment=Qt.AlignCenter)

        page_view_layout.addStretch(1)  # Right stretch
        layout.addLayout(page_view_layout)

        # Page Count and Timer
        count_timer_layout = QHBoxLayout()

        # Page Count
        count_layout = QHBoxLayout()
        count_layout.addWidget(QLabel("Page Count:"))
        self.page_count = QLineEdit()
        self.page_count.setValidator(QIntValidator())  # Only allow ints
        self.page_count.setFixedWidth(80)
        count_layout.addWidget(self.page_count)
        count_timer_layout.addLayout(count_layout)

        # Timer
        timer_layout = QHBoxLayout()
        timer_layout.addWidget(QLabel("Timer (sec):"))
        self.timer_entry = QLineEdit("5")
        self.timer_entry.setValidator(QIntValidator())
        self.timer_entry.setFixedWidth(80)
        timer_layout.addWidget(self.timer_entry)
        count_timer_layout.addLayout(timer_layout)

        layout.addLayout(count_timer_layout)

        # Tooltip for timer
        self.timer_entry.setToolTip("How long to wait for a page to load before taking a screenshot")

        # File Selection
        file_layout = QHBoxLayout()
        file_layout.addWidget(QLabel("Save PDF As:"))
        self.path_label = QLineEdit()
        self.path_label.setReadOnly(True)
        file_layout.addWidget(self.path_label)

        browse_btn = QPushButton("...")
        browse_btn.setFixedWidth(30)
        browse_btn.clicked.connect(self._ask_user_save_location)
        file_layout.addWidget(browse_btn)
        layout.addLayout(file_layout)

    def get_book_params(self):
        """Returns all parameters as a Book Object"""
        book = Book()
        book.file_path = self.path_label.text()
        book.selected_site = self.site_selector.currentText()
        book.timer = self.timer_entry.text()
        book.book_length = self.page_count.text()
        book.page_view = self.page_view_selector.currentText()
        return book

    def reset_ui(self):
        """Reset all UI fields to their default values"""
        self.path_label.clear()
        self.page_count.clear()
        self.site_selector.setCurrentIndex(0)

    def hide_window(self):
        self.hide()
        # self.showMinimized()

    def restore_window(self):
        self.show()
        self.showNormal()
        self.activateWindow()
        self.raise_()

    def set_start_command(self, value):
        self.start_command = value

    def closeEvent(self, event):
        logger.info("Application shutting down...")
        QApplication.instance().quit()
        event.accept()

    def _handle_site_change(self, selected_site):
        """Handles changes to site selector"""
        if selected_site == "Hoopla":
            self.page_view_selector.setCurrentIndex(0)
            self.page_view_selector.setEnabled(False)
            self.page_count.setToolTip("Please Make Sure You Are Getting The Page Count When In Full Screen On The Webpage, FN + F11")
        else:
            self.page_view_selector.setEnabled(True)
            self.page_count.setToolTip("")

    def _check_for_update(self):
        """check for application updates"""
        if not self.settings.auto_update:
            return False

        update_manager = UpdateManger()
        try:
            if not update_manager.check_for_update():
                return False
            logger.info("Update available")
            response = MessageBox.question("Update Available", "Would you like to download and install the new update?")
            logger.debug(f"User update response: {response}")
            if response != DialogResult.ACCEPT:
                return False
            if not update_manager.download_repo():
                return False
            logger.info("Update downloaded")
            update_manager.start_install()
        except Exception as e:
            logger.error(f"Update Failed {str(e)}")
            MessageBox.error("Update Failed", "Unable to update, please try again later")

    def _ask_user_save_location(self):
        last_path = self.settings.last_save_dir
        if not Path(last_path).exists() or not Path(last_path).is_dir():
            last_path = ""
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save PDF As",
            last_path,
            "PDF files (*.pdf);;All files (*.*)"
        )
        if file_path:
            if self.settings.last_save_dir != str(Path(file_path).parent):
                logger.info("Updating last save directory")
                self.settings.last_save_dir = str(Path(file_path).parent)
                self.settings.save_user_settings()
            self.path_label.setText(file_path)

    def _setup_logger(self):
        log_level = []
        console_level = None
        if self.settings.console_level == "INFO":
            console_level = logging.INFO
        elif self.settings.console_level == "DEBUG":
            console_level = logging.DEBUG
        elif self.settings.console_level == "WARNING":
            console_level = logging.WARNING
        elif self.settings.console_level == "ERROR":
            console_level = logging.ERROR
        elif self.settings.console_level == "CRITICAL":
            console_level = logging.CRITICAL

        if not self.settings.info:
            log_level.append(logging.INFO)
        if not self.settings.debug:
            log_level.append(logging.DEBUG)

        setup_logging(
            log_dir="logs",
            console_logging=self.settings.console_logging,
            console_level=console_level
        )
        logger.info("Logger configured")
        logging.getLogger("PIL").setLevel(logging.WARNING)

    def run(self):
        """Show and run app"""
        self.show()
