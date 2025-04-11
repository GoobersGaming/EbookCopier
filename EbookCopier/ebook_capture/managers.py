import sys
import time
import logging
import keyboard
import threading
from threading import Event
from PIL import ImageGrab, Image
from utils import pdf_maker
from ui import popup_windows
from utils import image_manipulation
logger = logging.getLogger(__name__)

# -------------------------------------------------------------------
# Helper Classes
# -------------------------------------------------------------------


class CaptureConfig():
    def __init__(self, capture_area):
        self.bbox, self.multi_monitor = self._process_capture_area(capture_area)

    def _process_capture_area(self, capture_area):
        bounding_box_keys = list(capture_area.keys())
        bounding_box_values = []
        multi_monitor = False
        for key in bounding_box_keys:
            if key != "monitor":
                bounding_box_values.append(capture_area[key])
            elif key == "monitor" and capture_area[key] > 1:
                multi_monitor = True
        return bounding_box_values, multi_monitor
# -------------------------------------------------------------------
# Manager  Classes
# -------------------------------------------------------------------


class PDFManager:
    def __init__(self, max_img, max_memory, output_pdf):
        self.max_img = max_img
        self.max_memory = max_memory
        self.batch = []
        self.output_pdf = output_pdf

    def add_to_batch(self, image, force_save=False):
        """Add image to batch, optionally forceing save"""
        if not isinstance(image, Image.Image):
            raise ValueError("Invalid image type")

        self.batch.append(image)

        if force_save or self._check_limits():
            return self.save_batch_to_pdf()
        logging.info("Image added to batch")
        return True

    def save_batch_to_pdf(self):
        if not self.batch:
            return True
        try:
            success = pdf_maker.add_image_to_pdf(self.batch, self.output_pdf)
            if not success:
                raise RuntimeError("PDF maker failed")
            self.batch.clear()
            logging.info("Batch saved to pdf")
            return True
        except Exception as e:
            raise RuntimeError(f"Failed to save PDF batch: {str(e)}") from e

    def _check_limits(self):
        if len(self.batch) >= self.max_img or self._get_memory_usage() >= self.max_memory:
            logging.debug(f"Limit Check, Images: {len(self.batch)}/{self.max_img}, Memory: {self._get_memory_usage()}/{self.max_memory} MB's")
            return True
        return False

    def finalize(self):
        logging.info("Finalizing book.")
        if self.batch:
            return self.save_batch_to_pdf()
        return True

    def _get_memory_usage(self):
        return sum(sys.getsizeof(img.tobytes()) for img in self.batch) / (1024 * 1024)  # Convert to MB

# -------------------------------------------------------------------
# PauseManager
# -------------------------------------------------------------------


class PauseManager():
    def __init__(self, timer=None, extra_delay=1.0):
        self.timer = timer
        self.extra_delay = extra_delay
        self.cancel_event = Event()
        self.pause_event = Event()
        self.listener_thread = None
        self._running = False

    def start_listener(self):
        if self._running:
            return

        self._running = True
        self.listener_thread = threading.Thread(
            target=self._keyboard_listener,
            daemon=True)
        self.listener_thread.start()
        logging.debug("Listener started")

    def stop_listener(self):
        """Stop keyboard listener"""
        self._running = False
        self.cancel_event.set()
        if self.listener_thread:
            self.listener_thread.join(timeout=1)
        logging.debug("Listener stopped, pause manager reset")

    def _keyboard_listener(self):
        """Background thread looking for pause key"""
        while self._running and not self.cancel_event.is_set():
            if keyboard.is_pressed("esc"):
                self.pause_event.set()
                logging.info("Pause event set")
                while keyboard.is_pressed("esc") and self._running:
                    time.sleep(0.1)
            time.sleep(0.1)

    def check_for_pause(self, interval=0.1, delay=False):
        """
        replaces time.sleep with a wait that checks for pause event at every interval.

        """
        if delay:
            timer = self.extra_delay
        else:
            timer = self.timer

        if not timer:
            return False

        end_time = time.time() + timer
        while time.time() < end_time:
            if self.pause_event.is_set():
                return self._handle_pause_request()
            time.sleep(interval)
        return False

    def _handle_pause_request(self):
        """Shows pause dialog and return user's choice"""
        self.pause_event.clear()

        response = popup_windows.ask_yes_no(
            "Processing Pause",
            "Do you want to cancel the current operation",
            btn_focus="No",
            ebook_running=True,
            delay=self.extra_delay)
        logging.debug(f"User pause response: {response}")
        if response:  # User choce to cancel
            self.cancel_event.set()
            return True

        logging.info("User resumed run")
        # Extra wait due to ui window stealing focus, check for pause while we wait
        self.check_for_pause(delay=True)
        return False

    def is_cancelled(self):
        """checks if cancellation was requesting"""
        return self.cancel_event.is_set()

    def is_paused(self):
        return self.pause_event.is_set()

# -------------------------------------------------------------------
# Screenshot Manager
# -------------------------------------------------------------------


class ScreenshotManger:
    def __init__(self, capture_config, pause_manager=None, blank_attempts=2, threshold=0.006, extra_delay=1.0, retry_delay=5.0):
        self.capture_config = capture_config
        self.pause_manager = pause_manager
        self.blank_attempts = blank_attempts
        self.threshold = threshold
        self.extra_delay = extra_delay
        self.retry_delay = retry_delay
        self.attempt = 0
        self.current_screenshot = None
        self.previous_screenshot = None

    def capture_valid_screenshot(self):
        """Main Method to capture screenshot"""
        while True:
            result = self._attempt_capture()
            logging.debug(f"Capture valid screenshot result: {result}")
            if result == "valid":
                return self.current_screenshot
            elif result == "cancelled":
                return "cancelled"
            elif result == "blank" and self.attempt >= self.blank_attempts:
                return self._handle_max_blank_attempts()

    def _attempt_capture(self):
        "Single Capture Attempt"
        try:
            self.current_screenshot = self._take_screenshot()

            if self._pause_check():
                return "cancelled"

            if not image_manipulation.is_blank(self.current_screenshot, self.threshold):
                self.attempt = 0
                return "valid"
            self.attempt += 1
            logging.debug(f"Screenshot is blank attempt: {self.attempt}")
            return "blank"

        except Exception as e:
            logging.error(f"Screenshot attempt failed: {str(e)}")
            self.attempt += 1
            return "blank"

    def _take_screenshot(self, max_retries=2):
        """screenshot capture"""
        for attempt in range(max_retries + 1):
            try:
                screenshot = ImageGrab.grab(bbox=self.capture_config.bbox, all_screens=self.capture_config.multi_monitor)
                if screenshot.size == (0, 0):
                    logging.warning("Empty screenshot captured")
                    raise ValueError("Empty screenshot captured")
                return screenshot
            except Exception:
                if attempt == max_retries:
                    logging.error(f"Max attempts reached in taking screenshot attempts: {attempt}")
                    raise RuntimeError("Max Attempts reached for taking a screenshot")
                time.sleep(self.retry_delay)

    def _handle_max_blank_attempts(self):
        """Handle when max blank attempts reached"""
        # TODO: Do I want a popup for again, telling them to fix the page??
        response = popup_windows.ask_user_keep_blank(self.current_screenshot, ebook_running=True, delay=self.extra_delay)
        logging.debug(f"Handle blank image response: {response}")
        # Extra wait due to ui window stealing focus, check for pause while we wait
        self._pause_check(True)
        if response is True:
            self.attempt = 0
            return self.current_screenshot
        elif response == "again":  # User wishes to try again.
            self.attempt = 0
            return self.capture_valid_screenshot()
        else:   # Discard
            return None

    def _pause_check(self, extra_delay=False):
        if self.pause_manager:
            return self.pause_manager.check_for_pause(delay=extra_delay)
        return False

    def get_previous_screenshot(self):
        return self.previous_screenshot

    def add_previous_screenshot(self, prev_screenshot):
        self.previous_screenshot = prev_screenshot

# -------------------------------------------------------------------
# Processor
# -------------------------------------------------------------------


class PageProcessor:
    def __init__(self, screenshot_manager, pause_manager, pdf_manager, extra_delay=1.0):
        self.screenshot_manager = screenshot_manager
        self.pause_manager = pause_manager
        self.pdf_manager = pdf_manager
        self.extra_delay = extra_delay
        self.end_of_book = False

    def process_page(self, end_of_book_mode=False):
        try:
            # Capture screenshot
            logging.info("Taking screenshot")
            screenshot = self.screenshot_manager.capture_valid_screenshot()
            if screenshot == "cancelled":
                return "cancelled"
            if screenshot is None:
                return False if not end_of_book_mode else True

            # Process Screenshot
            should_process = self._evaluate_screenshot(screenshot, end_of_book_mode)
            logging.debug(f"should process screenshot: {should_process}")
            if should_process is True:
                self.pdf_manager.add_to_batch(screenshot)
                self.screenshot_manager.add_previous_screenshot(screenshot)

            if should_process == "End":
                self.end_of_book = True

            return self._determine_completion_status()

        except Exception as e:
            raise RuntimeError(f"Page proocessing failed {str(e)}") from e

    def _evaluate_screenshot(self, screenshot, end_of_book_mode):
        """Should screenshot be processed"""
        prev = self.screenshot_manager.get_previous_screenshot()
        if not prev:
            return True
        logging.info("Checking screenshot for duplication")
        is_duplicate = self._is_image_duplicate(screenshot, prev)
        logging.debug(f"Is screenshot duplicate: {is_duplicate}")
        if end_of_book_mode:
            # If True and enf of book, a duplicate means we are done, dont ask for user input
            if is_duplicate:
                logging.info("End of book mode, duplicate found. Ending copying.")
                self.end_of_book = True
            return not is_duplicate

        # normal mode - User handles duplicates
        if is_duplicate:
            return self._handle_duplicate(screenshot, prev)
        logging.info("Screenshot is not a duplicate.")
        return True

    def _determine_completion_status(self):
        """determine if book processing is done"""
        if self.end_of_book:
            return "End"
        return True

    def _pause_check(self, extra_delay=False):
        # TODO: Need to add in periodic checks.
        return self.pause_manager.check_for_pause(delay=extra_delay)

    def cleanup(self):
        # TODO: No longer needed?
        self.pause_manager.stop_listener()

    def _is_image_duplicate(self, screenshot, previous_screenshot):
        # If true image is duplicate
        return image_manipulation.compare_images(screenshot, previous_screenshot)

    def _handle_duplicate(self, screenshot, previous_screenshot):
        response = popup_windows.ask_user_keep_dupe(previous_screenshot, screenshot, ebook_running=True, delay=self.extra_delay)
        logging.debug(f"User duplicate response: {response}")
        # Extra wait due to ui window stealing focus, check for pause while we wait
        self._pause_check(True)
        return response

    def set_end_of_book(self, value):
        # TODO: No longer needed?
        self.end_of_book = value
