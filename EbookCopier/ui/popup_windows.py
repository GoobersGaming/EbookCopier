from PySide6.QtWidgets import (
    QApplication,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QDialog,
    QStyle,
    QDialogButtonBox,
    QWidget,
    QScrollArea,
    QSizePolicy,
    QFrame,

)
from PySide6.QtCore import (
    Qt,
    QSize,
    QPropertyAnimation,
)
from PySide6.QtGui import (QPixmap, QImage,)
from PIL import Image
from enum import (Enum, auto)
import winsound
import ctypes
import logging

logger = logging.getLogger(__name__)

"""Popup windws for the main GUI App"""


def apply_non_focus_style(hwnd):
    GWL_EXSTYLE = -20
    WS_EX_NOACTIVATE = 0x08000000
    WS_EX_TOPMOST = 0x00000008
    WS_EX_TOOLWINDOW = 0x00000080
    # WS_EX_TRANSPARENT = 0x00000020

    try:
        style = ctypes.windll.user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
        new_style = style | WS_EX_NOACTIVATE | WS_EX_TOPMOST | WS_EX_TOOLWINDOW
        ctypes.windll.user32.SetWindowLongW(hwnd, GWL_EXSTYLE, new_style)

        # Refresh the window
        SWP_NOMOVE = 0x0002
        SWP_NOSIZE = 0x0001
        SWP_NOZORDER = 0x0004
        SWP_FRAMECHANGED = 0x0020
        SWP_NOACTIVATE = 0x0010

        ctypes.windll.user32.SetWindowPos(
            hwnd, -1, 0, 0, 0, 0,
            SWP_NOMOVE | SWP_NOSIZE | SWP_NOZORDER | SWP_FRAMECHANGED | SWP_NOACTIVATE
        )
    except Exception as e:
        logger.error(f"Failed to apply window styles: {e}")
        raise RuntimeError(f"Failed to apply window styles: {e}") from e


def get_styled_text_width(widget, text):
    widget.style().unpolish(widget)  # Clear existing styles
    widget.style().polish(widget)    # Reapply stylesheet
    QApplication.processEvents()     # Force style processing

    # Return width using the widget's CURRENT font
    return widget.fontMetrics().boundingRect(text).width(), widget.fontMetrics().boundingRect(text).height()


def calculate_button_size(button_data: list[dict], padding: int = 20):
    """Measure text using application-styled fonts."""
    temp_button = QPushButton()  # Parent to dialog for style inheritance
    temp_button.ensurePolished()      # Sync styles

    max_width = 0
    max_height = 0

    for data in button_data:
        width, height = get_styled_text_width(temp_button, data["text"])
        max_width = max(max_width, width + padding)
        max_height = height + padding // 2
    temp_button.deleteLater()
    return max_width, max_height


class DialogResult(Enum):
    ACCEPT = auto()
    REJECT = auto()
    TERMINATE = auto()
    RETRY = auto()
    DELETE = auto()
    KEEP = auto()
    HELP = auto()

    def __str__(self):
        return self.name.title()  # "Accept", "Reject", etc.


class NoFocusDialogBase(QDialog):
    """Base QDialog widget for a non focusable interactive window with custom button setup"""
    BUTTON_SPACING = 20
    BUTTON_CONTENTS_MARGIN = (12, 6, 12, 6)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_DeleteOnClose)
        self.setWindowFlags(Qt.WindowType.Window | Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.Tool)

        self._hwnd = None
        self._pending_style_apply = True
        self.response = None

    def showEvent(self, event):
        super().showEvent(event)
        if self._pending_style_apply:
            try:
                self._hwnd = int(self.winId())
                apply_non_focus_style(self._hwnd)
            except Exception as e:
                logger.warning(f"Failed to apply window styles: {e}")
                raise RuntimeError(f"Failed to apply window styles: {e}") from e

    def center_on_screen(self):
        """Center the dialog on the primary screen"""
        screen = QApplication.primaryScreen().availableGeometry()
        self.adjustSize()
        self.move(
            screen.center().x() - self.width() // 2,
            screen.center().y() - self.height() // 2
        )

    def setup_buttons(self, layout, button_options, default_button):
        button_list = []
        button_container = QWidget()

        # Container setup
        button_container.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        # Layout setup with generous margins
        button_layout = QHBoxLayout(button_container)
        button_layout.setSpacing(self.BUTTON_SPACING)
        button_layout.setContentsMargins(*self.BUTTON_CONTENTS_MARGIN)  # * unpacks tuple
        button_layout.addStretch(1)  # Left stretch

        max_width, max_height = calculate_button_size(button_options)

        for data in button_options:
            button = QPushButton(data["text"])

            if default_button == data['text']:
                button.setDefault(True)

            button.setFocusPolicy(Qt.NoFocus)

            # Set initial fixed size and store original
            button.setFixedSize(max_width, max_height)
            # button.original_size = QSize(self.max_width, self.max_height)

            # Set size policy to allow growing
            button.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)

            # Connect hover events
            button.clicked.connect(
                lambda checked, ret=data["return"]: self.handle_response(ret)
            )

            button_layout.addWidget(button)
            button_list.append(button)

        button_layout.addStretch(1)  # Right stretch
        layout.addWidget(button_container)
        return button_list

    def handle_response(self, response):
        self.response = response
        if response == DialogResult.ACCEPT:
            self.accept()
        elif response == DialogResult.REJECT:
            self.reject()
        else:
            self.accept()

    def closeEvent(self, event):
        super().closeEvent(event)
        self.deleteLater()


class MessageBox(NoFocusDialogBase):

    MAIN_LAYOUT_SPACING = 20
    MAIN_LAYOUT_CONTENT_MARGINS = (12, 12, 12, 12)
    CONTENT_LAYOUT_SPACING = 20
    MESSAGE_LAYOUT_CONTENT_MARGINS = (12, 12, 12, 12)

    def __init__(self, title: str, message: str, button_options: list[dict] = None, default_button: str = None,
                 icon: QStyle = None, parent: QWidget = None) -> None:
        """Initialize the message box.

        Args:
            title: Window title for the dialog
            message: Message text to display
            button_options: List of button configurations. Each dict should contain:
                - "text": Button label text
                - "return": Return value when clicked
                Defaults to [{"text": "Ok", "return": DialogResult.ACCEPT}]
            default_button: Text of the button to set as default (None for no default)
            icon: QStyle icon to display (None for no icon)
            parent: Parent widget for the dialog

        Returns:
            DialogResult: The result based on which button was clicked

        Note:
        The actual dialog result is stored in the `response` attribute and returned
        via the static methods, not through the QDialog return value.
        """
        super().__init__(parent)

        # Play sound
        winsound.MessageBeep(winsound.MB_ICONHAND)

        self.setWindowTitle(title)

        # Main layout
        main_layout = QVBoxLayout()
        main_layout.setSpacing(self.MAIN_LAYOUT_SPACING)
        main_layout.setContentsMargins(*self.MAIN_LAYOUT_CONTENT_MARGINS)  # * unpacks tuple

        # Message and Icon
        content_layout = QHBoxLayout()
        content_layout.setSpacing(self.CONTENT_LAYOUT_SPACING)

        # Icon widget - left
        if icon:
            icon_label = QLabel()
            icon_label.setPixmap(icon.pixmap(QSize(48, 48)))
            icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignLeft)
            content_layout.addWidget(icon_label)

        # message
        message_container = QWidget()
        message_layout = QVBoxLayout(message_container)
        message_layout.setContentsMargins(*self.MESSAGE_LAYOUT_CONTENT_MARGINS)

        label = QLabel(message)
        label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        label.setWordWrap(True)

        # strech above and below to center message
        message_layout.addStretch()
        message_layout.addWidget(label)
        message_layout.addStretch()

        content_layout.addWidget(message_container, 1)  # 1 takes remaning space

        main_layout.addLayout(content_layout)
        if button_options is None:
            button_options = [
                {"text": "Ok", "return": DialogResult.ACCEPT}
            ]
        self.setup_buttons(main_layout, button_options, default_button)
        self.setLayout(main_layout)

    @staticmethod
    def show(title: str, message: str, button_options: list[dict] = None, default_button: str = None, icon: QStyle = None, parent: QWidget = None) -> DialogResult:
        """Display the message box and return the user's response.

        Args:
            title: Window title for the dialog
            message: Message text to display
            button_options: List of button configurations (see __init__)
            default_button: Text of the default button
            icon: QStyle icon to display
            parent: Parent widget

        Returns:
            DialogResult: The result based on which button was clicked
            """
        dialog = MessageBox(title, message, button_options, default_button, icon, parent)
        dialog.exec()
        return dialog.response

    @staticmethod
    def error(title: str, message: str, button_options: list[dict] = None, default_button: str = None, parent: QWidget = None) -> DialogResult:
        """Display an error message box with critical icon.

        Args:
            title: Window title for the dialog
            message: Error message text
            button_options: List of button configurations (see __init__)
            default_button: Text of the default button
            parent: Parent widget

        Returns:
            DialogResult: The result based on which button was clicked
        """
        app = QApplication.instance()
        style = app.style()
        error_icon = style.standardIcon(QStyle.SP_MessageBoxCritical)
        return MessageBox.show(title, message, button_options, default_button, error_icon, parent)

    @staticmethod
    def warning(title: str, message: str, button_options: list[dict] = None, default_button: str = None, parent: QWidget = None) -> DialogResult:
        """Display a warning message box with warning icon.

        Args:
            title: Window title for the dialog
            message: Warning message text
            button_options: List of button configurations (see __init__)
            default_button: Text of the default button
            parent: Parent widget

        Returns:
            DialogResult: The result based on which button was clicked
        """
        app = QApplication.instance()
        style = app.style()
        warning_icon = style.standardIcon(QStyle.SP_MessageBoxWarning)
        return MessageBox.show(title, message, button_options, default_button, warning_icon, parent)

    @staticmethod
    def information(title: str, message: str, button_options: list[dict] = None, default_button: str = None, parent: QWidget = None) -> DialogResult:
        """Display an information message box with info icon.

        Args:
            title: Window title for the dialog
            message: Information message text
            button_options: List of button configurations (see __init__)
            default_button: Text of the default button
            parent: Parent widget

        Returns:
            DialogResult: The result based on which button was clicked
        """
        app = QApplication.instance()
        style = app.style()
        info_icon = style.standardIcon(QStyle.SP_MessageBoxInformation)
        return MessageBox.show(title, message, button_options, default_button, info_icon, parent)

    @staticmethod
    def question(title: str, message: str, button_options: list[dict] = None, default_button: str = None, parent: QWidget = None) -> DialogResult:
        """Display a question message box with question icon.

        Args:
            title: Window title for the dialog
            message: Question message text
            button_options: List of button configurations. Defaults to:
                [{"text": "Yes", "return": True}, {"text": "No", "return": False}]
            default_button: Text of the default button
            parent: Parent widget

        Returns:
            DialogResult: The result based on which button was clicked
        """
        app = QApplication.instance()
        style = app.style()
        question_icon = style.standardIcon(QStyle.SP_MessageBoxQuestion)
        if button_options is None:
            button_options = [
                {"text": "Yes", "return": DialogResult.ACCEPT},
                {"text": "No", "return": DialogResult.REJECT}
            ]
        return MessageBox.show(title, message, button_options, default_button, question_icon, parent)


class ImageWindow(NoFocusDialogBase):
    MAIN_LAYOUT_SPACING = 20
    MAIN_CONTENTS_MARGIN = (12, 12, 12, 12)
    MESSAGE_CONTAINER_SPACING = 40
    TRANSPARENCY_BUTTON_SIZE = (30, 30)
    IMAGE_SPACING = 20

    def __init__(self, title: str, message: str, image1: Image.Image, image2: Image.Image = None,
                 button_options: list[dict] = None, default_button: str = None, parent: QWidget = None) -> DialogResult:
        super().__init__(parent)

        # Play sound
        winsound.MessageBeep(winsound.MB_ICONHAND)

        self.setWindowTitle(title)

        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(*self.MAIN_CONTENTS_MARGIN)  # * unpacks tuple

        # Message Container with transparency button - TOP
        message__container = QHBoxLayout()
        message__container.setSpacing(self.MESSAGE_CONTAINER_SPACING)

        message_label = QLabel(message)
        message_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        message__container.addWidget(message_label)

        # Transparency Button
        self.transparency_button = QPushButton(("◐"))
        self.transparency_button.setFixedSize(*self.TRANSPARENCY_BUTTON_SIZE)  # * unpacks tuple
        self.transparency_button.clicked.connect(self._toggle_transparency)
        self.transparency_button.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        message__container.addWidget(self.transparency_button)

        main_layout.addLayout(message__container)

        # Image layout
        image_container = QFrame()
        image_layout = QHBoxLayout(image_container)
        image_layout.setSpacing(self.IMAGE_SPACING)

        # First image
        self.image1_frame = self._create_image_frame(image1[0], image1[1])
        image_layout.addWidget(self.image1_frame)

        # Second image
        if image2 is not None:
            self.image2_frame = self._create_image_frame(image2[0], image2[1])
            image_layout.addWidget(self.image2_frame)

        main_layout.addWidget(image_container)

        if button_options is None:
            button_options = [
                {"text": "Ok", "return": DialogResult.ACCEPT}
            ]

        # Buttons
        self.setup_buttons(main_layout, button_options, default_button)

        # Center dialog
        self.center_on_screen()

    def _toggle_transparency(self):
        """Toggle window opacity between 100% and 50% with animation."""
        target_opacity = 0.50 if self.windowOpacity() == 1.0 else 1.0
        button_text = "◑" if target_opacity == 0.5 else "◐"  # Change button icon

        # Animate the transition
        self.animation = QPropertyAnimation(self, b"windowOpacity")
        self.animation.setDuration(300)  # 300ms animation
        self.animation.setStartValue(self.windowOpacity())
        self.animation.setEndValue(target_opacity)
        self.animation.start()

        self.transparency_button.setText(button_text)

    def _create_image_frame(self, image, title):
        frame = QFrame()
        frame.setObjectName("StyledFrame")
        frame_layout = QVBoxLayout(frame)
        frame_layout.setSpacing(5)

        # title
        title_label = QLabel(title)
        title_label.setObjectName("Title")
        # title_label.setStyleSheet("color: white; font-weight: bold")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        frame_layout.addWidget(title_label)

        # image
        img_label = QLabel()
        img_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # img_label.setStyleSheet("background: white;")

        if image is not None:
            screen = QApplication.primaryScreen().availableGeometry()
            max_width_per_image = int(screen.width() * 0.45)  # 45% of screen width per image
            max_height = (screen.height() * 0.8)  # 80% of screen height

            # Get original image dimensions
            orig_width, orig_height = image.size

            # Calculate the scaling factor while keeping aspect ratio
            width_ratio = max_width_per_image / orig_width
            height_ratio = max_height / orig_height

            # Use the smaller ratio to ensure the image fits entirely
            scale_ratio = min(width_ratio, height_ratio)

            # Apply scaling
            new_width = int(orig_width * scale_ratio)
            new_height = int(orig_height * scale_ratio)

            # Convert to QPixmap and scale smoothly
            qimg = self._pil_to_qimage(image)
            pixmap = QPixmap.fromImage(qimg)
            scaled_pixmap = pixmap.scaled(
                new_width,
                new_height,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )

            img_label.setPixmap(scaled_pixmap)
        else:
            img_label.setPixmap(QPixmap(300, 400))
            img_label.pixmap().fill(Qt.gray)
        frame_layout.addWidget(img_label)
        return frame

    def _pil_to_qimage(self, pil_img):
        try:
            if pil_img is None:
                raise ValueError("PIL image is None")

            if pil_img.mode == "RGB":
                r, g, b = pil_img.split()
                pil_img = Image.merge("RGB", (b, g, r))
                img = QImage(pil_img.tobytes(), pil_img.width, pil_img.height,
                             pil_img.width * 3, QImage.Format_RGB888)
            elif pil_img.mode == "RGBA":
                r, g, b, a = pil_img.split()
                pil_img = Image.merge("RGBA", (b, g, r, a))
                img = QImage(pil_img.tobytes(), pil_img.width, pil_img.height,
                             pil_img.width * 4, QImage.Format_RGBA8888)
            else:
                pil_img = pil_img.convert("RGB")
                return self._pil_to_qimage(pil_img)

            if img.isNull():
                raise ValueError("Failed to create QImage")
            return img
        except Exception as e:
            logger.warning(f"Error converting PIL to QImage: {e}")
            # Return a blank image as fallback
            blank = QImage(100, 100, QImage.Format_RGB888)
            blank.fill(Qt.white)
            return blank

    def handle_response(self, response):
        # Override base, Handles User Response and ensures animation stops
        self.response = response
        if hasattr(self, 'animation'):
            self.animation.stop()
        if response == DialogResult.ACCEPT:
            self.accept()
        elif response == DialogResult.REJECT:
            self.reject()
        else:
            self.accept()

    def closeEvent(self, event):
        # Override Base, cleans up animation and pixmap and widget
        # Clean up animation if it exists
        if hasattr(self, 'animation'):
            self.animation.stop()
            del self.animation
        super().closeEvent(event)
        self.deleteLater()

    @staticmethod
    def show(title: str, message: str, image1: Image.Image, image2: Image.Image = None,
             button_options: list[dict] = None, default_button: str = None, parent: QWidget = None) -> DialogResult:
        dialog = ImageWindow(
            title=title,
            message=message,
            image1=image1,
            image2=image2,
            button_options=button_options,
            default_button=default_button,
            parent=parent
        )
        dialog.exec()
        return dialog.response

    @staticmethod
    def duplicate(previous_img: Image.Image, current_img: Image.Image):
        """static method showing detected duplicate images, and returning user choice"""
        return ImageWindow.show(
            image1=(previous_img, "Previous Image"),
            image2=(current_img, "Current Image"),
            title="Duplicate Image Detected",
            message="A duplicate image has been detected.Would you like to keep the current picture or discard it?",
            button_options=[
                {"text": "Keep Current", "return": DialogResult.ACCEPT},
                {"text": "Discard Current", "return": DialogResult.REJECT},
                {"text": "End Book", "return": DialogResult.TERMINATE}
            ],
        )

    @staticmethod
    def blank(blank_img: Image.Image) -> DialogResult:
        """Statio method for showing detected blank image, and returning user choice"""
        return ImageWindow.show(
            image1=(blank_img, "Blank Image"),
            title="Blank Image Detected",
            message="A blank image has been detected.\nWould you like to keep, discard, or try again",
            button_options=[
                {"text": "Keep Image", "return": DialogResult.ACCEPT},
                {"text": "Discard Image", "return": DialogResult.REJECT},
                {"text": "Try Again", "return": DialogResult.RETRY}
            ],
        )


def continuation(title: str, message: str, help_items: list = None, parent: QWidget = None) -> DialogResult:
    """Display a (Wrapper) confirmation dialog with Continue/Cancel/Help options.

    Args:
        title: Window title
        message: Main message text
        help_items: Optional list of help pages (each with 'label' and optional 'image_path')
        parent: Parent widget

    Returns:
        True if user clicked Continue, False if Canceled or closed
    """
    dialog = ConfirmationDialog(title, message, help_items, parent)
    dialog.exec()
    return dialog.response


class HelpDialog(NoFocusDialogBase):
    def __init__(self, help_items, parent=None):
        super().__init__(parent)

        self.setWindowTitle("Help")
        self.setMinimumSize(600, 500)
        self.help_items = help_items
        self.current_index = 0

        self._setup_ui()
        self._update_content()

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        # Scroll area for content
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        self.content_widget = QWidget()
        self.content_layout = QVBoxLayout(self.content_widget)

        # message label
        self.message_label = QLabel()
        self.message_label.setWordWrap(True)
        self.message_label.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.content_layout.addWidget(self.message_label)

        # image label
        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.content_layout.addWidget(self.image_label)

        # add scroll
        scroll.setWidget(self.content_widget)
        layout.addWidget(scroll)

        # Navigation buttons
        button_box = QDialogButtonBox()
        button_options = [
            {"text": "Previous"},
            {"text": "Next"},
            {"text": "Done"}
        ]
        max_width, max_height = calculate_button_size(button_options)
        self.prev_button = QPushButton("Previous")
        self.prev_button.setAutoDefault(False)
        self.prev_button.setFixedSize(max_width, max_height)
        self.prev_button.clicked.connect(self.show_previous)
        button_box.addButton(self.prev_button, QDialogButtonBox.ActionRole)

        self.next_button = QPushButton("Next")
        self.next_button.setFixedSize(max_width, max_height)
        self.next_button.clicked.connect(self.show_next)
        button_box.addButton(self.next_button, QDialogButtonBox.ActionRole)

        self.done_button = QPushButton("Done")
        self.done_button.setFixedSize(max_width, max_height)
        self.done_button.clicked.connect(self.accept)
        button_box.addButton(self.done_button, QDialogButtonBox.ActionRole)

        layout.addWidget(button_box)

    def _update_content(self):
        # set help item to current index
        item = self.help_items[self.current_index]
        self.message_label.setText(item["label"])
        # If image path, add image
        # TODO: double check image path is valid??
        if "image_path" in item and item["image_path"]:
            pixmap = QPixmap(item["image_path"])
            if not pixmap.isNull():
                self.image_label.setPixmap(pixmap.scaled(
                    400, 300, Qt.KeepAspectRatio, Qt.SmoothTransformation
                ))
            else:
                self.image_label.clear()
        else:
            self.image_label.clear()
        # update prev button state based on current_index
        self.prev_button.setEnabled(self.current_index > 0)
        # add done button on last index
        is_last = self.current_index == len(self.help_items) - 1
        self.next_button.setVisible(not is_last)
        self.done_button.setVisible(is_last)

    def show_next(self):
        if self.current_index < len(self.help_items) - 1:
            self.current_index += 1
            self._update_content()

    def show_previous(self):
        if self.current_index > 0:
            self.current_index -= 1
            self._update_content()


class ConfirmationDialog(NoFocusDialogBase):
    def __init__(self, title: str, message: str, help_items: list, parent: QWidget = None):
        super().__init__(parent)
        self.setWindowTitle(title)

        self.setModal(True)

        self.help_items = help_items
        self._setup_ui(message)

    def _setup_ui(self, message):
        layout = QVBoxLayout(self)

        # message label
        message_label = QLabel(message)
        message_label.setWordWrap(True)
        layout.addWidget(message_label)

        # button box
        button_box = QDialogButtonBox()
        button_options = [
            {"text": "Continue", "return": DialogResult.ACCEPT},
            {"text": "Cancel", "return": DialogResult.REJECT},
            {"text": "Help", "return": DialogResult.HELP}
        ]
        max_width, max_height = calculate_button_size(button_options)
        continue_buton = QPushButton("Continue")
        continue_buton.clicked.connect(lambda checked, ret=button_options[0]["return"]: self.handle_response(ret))
        continue_buton.setFixedSize(max_width, max_height)
        button_box.addButton(continue_buton, QDialogButtonBox.AcceptRole)

        cancel_button = QPushButton("Cancel")
        cancel_button.setFixedSize(max_width, max_height)
        cancel_button.clicked.connect(lambda checked, ret=button_options[1]["return"]: self.handle_response(ret))
        button_box.addButton(cancel_button, QDialogButtonBox.RejectRole)

        if self.help_items:
            help_button = QPushButton("Help")
            help_button.setFixedSize(max_width, max_height)
            help_button.clicked.connect(self.show_help)
            button_box.addButton(help_button, QDialogButtonBox.HelpRole)

        layout.addWidget(button_box)

    def show_help(self):
        help_dialog = HelpDialog(self.help_items, self)
        help_dialog.exec()


if __name__ == "__main__":
    # Themes
    # dark_theme, warm_sand, midnight_theme, solar_cream, moon_parchemnt, autumn_ember, winter_ash,
    # neon_rain, plain_light, plain_dark, forest_theme, forest_bark
    from ui.styles import pyside_themes
    print("Starting UI Test")
    app = QApplication([])
    app.setStyle("Fusion")
    app.setStyleSheet(pyside_themes(theme="forest_bark"))
    style = app.style()
    info_icon = style.standardIcon(QStyle.SP_MessageBoxInformation)

    img1 = Image.new("RGB", (400, 600), color="white")
    img2 = Image.new("RGB", (400, 600), color="gray")

    blank = ImageWindow.blank(img1)
    print(f"Blank response: {blank}")

    duplicate = ImageWindow.duplicate(img1, img2)
    print(f"duplicate response: {duplicate}")

    question = MessageBox.question(title="Delete Pdf",
                                   message="Do you wish to delete the unfinished book?",
                                   button_options=[
                                       {"text": "Delete", "return": DialogResult.DELETE},
                                       {"text": "Keep", "return": DialogResult.KEEP}])

    print(f"Question response: {question}")
    from ui.help import cont_message

    message_content, help_content = cont_message("libby", "one")
    cont = continuation(title="Before Continuing",
                        message=message_content,
                        help_items=help_content)
    print(cont)
