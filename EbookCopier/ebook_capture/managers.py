import sys
import time
import logging
import keyboard
import threading
from threading import Event
from PIL import ImageGrab, Image
from utils import pdf_maker
from ui.popup_windows import MessageBox, ImageWindow
from ui.popup_windows import DialogResult
from utils import image_manipulation
from enum import Enum, auto
logger = logging.getLogger(__name__)


class Process(Enum):
    VALID = auto()
    CANCELLED = auto()
    END = auto()
    BLANK = auto()
    DISCARD = auto()
    CONTINUE = auto()
    DONT_CONTINUE = auto()
    NEXT = auto()
    COMPLETED = auto()

    def __str__(self):
        return self.name.title()  # "Accept", "Reject", etc.

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
        logger.debug(f"PDFManager initialized with max_img={max_img}, max_memory={max_memory}MB, output_pdf={output_pdf}")

    def add_to_batch(self, image, force_save=False):
        """Add image to batch, optionally forceing save"""
        if not isinstance(image, Image.Image):
            raise ValueError("Invalid image type")

        self.batch.append(image)
        logger.debug(f"Image added to batch (current size: {len(self.batch)}/{self.max_img})")

        if force_save or self._check_limits():
            return self.save_batch_to_pdf()
        logger.info("Image added to batch")
        return True

    def save_batch_to_pdf(self):
        if not self.batch:
            logger.debug("Attempted to save empty batch - skipping")
            return True
        try:
            logger.info(f"Saving batch of {len(self.batch)} images to PDF")
            success = pdf_maker.add_image_to_pdf(self.batch, self.output_pdf)
            if not success:
                logger.error("PDF maker reported failure")
                raise RuntimeError("PDF maker failed")
            self.batch.clear()
            logger.info(f"Successfully saved {len(self.batch)} images to PDF")
            return True
        except Exception as e:
            logger.error(f"Failed to save PDF batch: {str(e)}", exc_info=True)
            raise RuntimeError(f"Failed to save PDF batch: {str(e)}") from e

    def _check_limits(self):
        current_images = len(self.batch)
        current_memory = self._get_memory_usage()
        if current_images >= self.max_img or current_memory >= self.max_memory:
            logger.debug(f"Batch limits reached - Images: {current_images}/{self.max_img}, Memory: {current_memory:.2f}/{self.max_memory} MB")
            return True
        return False

    def finalize(self):
        logger.info(f"Finalizing PDF with {len(self.batch)} remaining images")
        if self.batch:
            return self.save_batch_to_pdf()
        logger.debug("No remaining images to finalize")
        return True

    def _get_memory_usage(self):
        return sum(sys.getsizeof(img.tobytes()) for img in self.batch) / (1024 * 1024)  # Convert to MB

# -------------------------------------------------------------------
# PauseManager
# -------------------------------------------------------------------


class PauseManager():
    def __init__(self, timer=None):
        self.timer = timer
        self.cancel_event = Event()
        self.pause_event = Event()
        self.listener_thread = None
        self._running = False
        logger.debug(f"PauseManager initialized with timer={timer}")

    def start_listener(self):
        if self._running:
            logger.debug("Listener already running - ignoring start request")
            return

        self._running = True
        self.listener_thread = threading.Thread(
            target=self._keyboard_listener,
            daemon=True)
        self.listener_thread.start()
        logger.info("Keyboard listener thread started (ESC to pause)")

    def stop_listener(self):
        """Stop keyboard listener"""
        if not self._running:
            logger.debug("Stop requested but listener not running")
            return

        self._running = False
        self.cancel_event.set()
        if self.listener_thread:
            logger.debug("Joining listener thread...")
            self.listener_thread.join(timeout=1)
            if self.listener_thread.is_alive():
                logger.warning("Listener thread did not terminate cleanly")
            else:
                logger.info("Listener thread stopped successfully")
        self.cancel_event.clear()  # Reset for next run
        logger.debug("Pause manager reset")

    def _keyboard_listener(self):
        """Background thread looking for pause key"""
        logger.debug("Keyboard listener thread running")
        while self._running and not self.cancel_event.is_set():
            try:
                if keyboard.is_pressed("esc"):
                    self.pause_event.set()
                    logger.info("Pause triggered by ESC key")
                    # Wait for key release to prevent multi triggers
                    while keyboard.is_pressed("esc") and self._running:
                        time.sleep(0.1)
            except Exception as e:
                logger.error(f"Error in keyboard listener: {str(e)}", exc_info=True)
                raise RuntimeError(f"Error in keyboard listener: {str(e)}") from e

            time.sleep(0.1)

    def check_for_pause(self, interval=0.1, timer=None):
        """
        replaces time.sleep with a wait that checks for pause event at every interval.

        """
        if timer is None:
            timer = self.timer
        logger.debug(f"Starting check for pause for {timer} seconds")
        end_time = time.time() + timer
        while time.time() < end_time:
            if self.pause_event.is_set():
                logger.debug("Pause detected during wait period")
                return self._handle_pause_request()
            time.sleep(interval)
        return False

    def _handle_pause_request(self):
        """Shows pause dialog and return user's choice"""
        self.pause_event.clear()
        logger.info("Processing pause request - showing dialog")
        response = MessageBox.question(
            title="Processing Paused",
            message="Do you want to stop and cancel the current book?",
        )
        logger.info(f"User pause response: {response}")
        if response == DialogResult.ACCEPT:
            logger.warning("User requested cancellation")
            self.cancel_event.set()
            return True

        logger.info("User chose to continue processing")
        # small wait for recheck
        self.check_for_pause(timer=1.0)
        return False

    def is_cancelled(self):
        """checks if cancellation was requested"""
        cancelled = self.cancel_event.is_set()
        if cancelled:
            logger.debug("Cancellation status check: True")
        return cancelled

    def is_paused(self):
        paused = self.pause_event.is_set()
        if paused:
            logger.debug("Pause status check: True")
        return paused

# -------------------------------------------------------------------
# Screenshot Manager
# -------------------------------------------------------------------


class ScreenshotManger:
    def __init__(self, capture_config, pause_manager=None, blank_attempts=2, threshold=0.006, retry_delay=5.0):
        self.capture_config = capture_config
        self.pause_manager = pause_manager
        self.blank_attempts = blank_attempts
        self.threshold = threshold
        self.retry_delay = retry_delay
        self.attempt = 0
        self.current_screenshot = None
        self.previous_screenshot = None
        logger.info(
            f"ScreenshotManager initialized with blank_attempts={blank_attempts}, "
            f"threshold={threshold}, retry_delay={retry_delay}, "
            f"monitor_config={capture_config}"
        )

    def capture_valid_screenshot(self, end_of_book_mode=False):
        """Main Method to capture screenshot"""
        logger.debug(f"Starting screenshot capture (end_of_book_mode={end_of_book_mode})")
        while True:
            result = self._attempt_capture(end_of_book_mode=end_of_book_mode)
            if result == Process.VALID:
                logger.info("Valid screenshot captured")
                return self.current_screenshot
            elif result == Process.CANCELLED:
                logger.warning("Screenshot capture cancelled by user")
                return Process.CANCELLED
            elif result == Process.BLANK:
                if self.attempt >= self.blank_attempts:
                    logger.warning(f"Max blank attempts reached ({self.blank_attempts})")
                    return self._handle_max_blank_attempts()
                logger.debug(f"Blank screenshot detected (attempt {self.attempt}/{self.blank_attempts})")

    def _attempt_capture(self, end_of_book_mode=False):
        """Attempts a single screenshot capture with pause checking"""
        try:
            logger.debug("Attempting screenshot capture")
            self.current_screenshot = self._take_screenshot()

            if self._pause_check():
                return Process.CANCELLED
            # HACK: Setting threshold to 0 for end of book, so if the book ends on a blank page, we dont 2 popups in a row
            threshold = 0.000 if end_of_book_mode else self.threshold
            logger.debug(f"Checking for blank screenshot (threshold={threshold})")

            if not image_manipulation.is_blank(self.current_screenshot, threshold):
                logger.debug("Screenshot is valid")
                self.attempt = 0
                return Process.VALID
            self.attempt += 1
            logger.warning(f"Blank screenshot detected (attempt {self.attempt})")
            return Process.BLANK

        except Exception as e:
            logger.error(f"Screenshot attempt failed: {str(e)}", exc_info=True)
            self.attempt += 1
            return Process.BLANK

    def _take_screenshot(self, max_retries: int = 2) -> Image.Image:
        """Takes a screenshot, with a maximum rety value of max_retries"""
        for attempt in range(max_retries + 1):
            try:
                logger.debug(f"Taking screenshot (attempt {attempt + 1}/{max_retries + 1})")
                screenshot = ImageGrab.grab(
                    bbox=self.capture_config.bbox,
                    all_screens=self.capture_config.multi_monitor)

                if screenshot.size == (0, 0):
                    logger.error("Empty screenshot captured (0x0 pixels)")
                    raise ValueError("Empty screenshot captured")

                logger.debug(f"Screenshot captured successfully: {screenshot.size} pixels")
                return screenshot

            except Exception as e:
                if attempt == max_retries:
                    logger.critical(f"Failed after {max_retries} retries: {str(e)}")
                    raise RuntimeError(f"Max attempts reached for taking a screenshot: {str(e)}")

                logger.warning(f"Screenshot attempt {attempt + 1} failed: {str(e)}")
                time.sleep(self.retry_delay)

    def _handle_max_blank_attempts(self):
        """Handles the case when maximum blank screenshot attempts are reached.

        Presents the user with options to accept the blank screenshot, retry capturing,
        or discard the screenshot entirely.

        Returns:
                Image.Image | None:
                    - Returns the current screenshot if user accepts (DialogResult.ACCEPT)
                    - Returns a new screenshot from capture_valid_screenshot() if retry (DialogResult.RETRY)
                    - Returns None if user discards (any other response)

        Note:
            Resets the attempt counter to 0 when user chooses ACCEPT or RETRY.
    """
        # TODO: Do I want a popup for again, telling them to fix the page??
        logger.info("Showing blank screenshot dialog to user")
        response = ImageWindow.blank(self.current_screenshot)
        logger.info(f"User response to blank screenshot: {response}")

        self._pause_check()
        if response == DialogResult.ACCEPT:
            logger.info("User accepted blank screenshot")
            self.attempt = 0
            return self.current_screenshot
        elif response == DialogResult.RETRY:
            logger.info("User requested retry for blank screenshot")
            self.attempt = 0
            return self.capture_valid_screenshot()
        else:   # Discard
            logger.info("User discarded blank screenshot")
            return Process.DISCARD

    def _pause_check(self, timer=1.0):
        if self.pause_manager:
            logger.debug("Checking for pause state")
            return self.pause_manager.check_for_pause(timer=timer)
        return False

    def get_previous_screenshot(self):
        logger.debug("Retrieving previous screenshot")
        return self.previous_screenshot

    def add_previous_screenshot(self, prev_screenshot):
        logger.debug("Storing previous screenshot")
        self.previous_screenshot = prev_screenshot

# -------------------------------------------------------------------
# Processor
# -------------------------------------------------------------------


class PageProcessor:
    def __init__(self, screenshot_manager: ScreenshotManger, pause_manager: PauseManager, pdf_manager: PDFManager):
        self.screenshot_manager = screenshot_manager
        self.pause_manager = pause_manager
        self.pdf_manager = pdf_manager
        self.end_of_book = False
        logger.info(
            f"PageProcessor initialized with end_of_book={self.end_of_book}")

    def process_page(self, end_of_book_mode: bool = False) -> Process:
        """Captures and processes a single page screenshot for PDF generation.
            The complete workflow:
        1. Captures a validated screenshot
        2. Checks for duplicates (unless in end-of-book mode)
        3. Adds valid screenshots to PDF batch
        4. Determines whether processing should continue

        Args:
            end_of_book_mode: If True, enables automatic book-ending behavior on duplicates.
                            If False (default), allows user interaction for duplicates.

        Returns:
            Process:
                - CANCELLED: If user cancelled screenshot capture
                - DISCARD: If screenshot was discarded
                - CONTINUE: If processing should continue to next page
                - END: If processing should stop (book complete)

        Raises:
            RuntimeError: If any unrecoverable error occurs during processing

        Side Effects:
            - Adds valid screenshots to pdf_manager's batch
            - Updates screenshot_manager's previous screenshot reference
            - Sets end_of_book flag when appropriate
        """
        try:
            logger.info(f"Starting page processing (end_of_book_mode={end_of_book_mode})")

            # Capture screenshot
            logger.debug("Initiating screenshot capture")
            screenshot = self.screenshot_manager.capture_valid_screenshot(end_of_book_mode=end_of_book_mode)
            if screenshot == Process.CANCELLED:
                logger.warning("Processing cancelled during screenshot capture")
                return Process.CANCELLED

            if screenshot == Process.DISCARD and not end_of_book_mode:
                logger.info("Screenshot discarded by user in normal mode")
                return Process.NEXT

            logger.info("Screenshot validation successful")
            # Process Screenshot
            should_process = self._evaluate_screenshot(screenshot, end_of_book_mode)
            logger.debug(f"Screenshot evaluation result: {should_process}")

            if should_process == Process.CONTINUE:
                logger.debug("Adding valid screenshot to PDF batch")
                self.pdf_manager.add_to_batch(screenshot)
                self.screenshot_manager.add_previous_screenshot(screenshot)
                logger.debug("Updated previous screenshot reference")

            if should_process == Process.END:
                logger.info("End of book detected")
                self.end_of_book = True

            completion_status = self._determine_completion_status()
            logger.info(f"Processing complete, status: {completion_status}")
            return completion_status

        except Exception as e:
            logger.critical(f"Page processing failed: {str(e)}", exc_info=True)
            raise RuntimeError(f"Page processing failed: {str(e)}") from e

    def _evaluate_screenshot(self, screenshot: Image.Image, end_of_book_mode: bool) -> Process:
        """Evaluates whether a screenshot should be processed or considered a duplicate.

        Handles two distinct modes:
        1. Normal mode: User interacts with duplicate screenshots (keep/discard/end book)
        2. End-of-book mode: First duplicate automatically ends book processing

        Args:
            screenshot: The PIL Image to evaluate
            end_of_book_mode: If True, uses automated end-of-book detection logic

        Returns:
            Process:
                - CONTINUE if screenshot should be processed
                - DONT_CONTINUE if screenshot is duplicate (in end-of-book mode)
                - Result from _handle_duplicate() in normal mode

        Behavior:
            - In normal mode: Duplicates trigger user interaction via _handle_duplicate()
            - In end-of-book mode: First duplicate sets end_of_book flag and stops processing
            - Non-duplicates always continue processing
        """
        prev = self.screenshot_manager.get_previous_screenshot()
        if prev is None:
            logger.debug("No previous screenshot - processing first page")
            return Process.CONTINUE

        logger.debug("Checking for duplicate screenshot")
        is_duplicate = self._is_image_duplicate(screenshot, prev)
        logger.info(f"Duplicate check result: {is_duplicate}")

        # If True and end of book, a duplicate means we are done, dont ask for user input
        # Applies to capture._process_remaining_pages()
        if end_of_book_mode:
            if is_duplicate:
                self.end_of_book = True
                logger.info("End-of-book mode: duplicate detected as book end")
            return Process.DONT_CONTINUE if is_duplicate else Process.CONTINUE
            # if is_duplicate is True:
            #     return Process.DONT_CONTINUE
            # else:
            #     return Process.CONTINUE
            # return Process.CONTINUE if not is_duplicate else Process.DONT_CONTINUE
            # return not is_duplicate

        # Normal mode, user handles duplicates
        if is_duplicate:
            logger.info("Normal mode: handling duplicate screenshot")
            return self._handle_duplicate(screenshot, prev)

        logger.debug("Screenshot is unique - continuing processing")
        return Process.CONTINUE

    def _determine_completion_status(self):
        """Determins if book processing is done or should continue on to a new page"""
        status = Process.END if self.end_of_book else Process.NEXT
        logger.debug(f"Determined completion status: {status}")
        return status

    def _pause_check(self, timer=1.0):
        """Checks for pause state during wait period."""
        logger.debug(f"Checking for pause state (timeout={timer})")
        return self.pause_manager.check_for_pause(timer=timer)

    def cleanup(self):
        """Cleans up keyboard listener"""
        logger.info("Initiating processor cleanup")
        self.pause_manager.stop_listener()
        logger.debug("Cleanup completed")

    def _is_image_duplicate(self, screenshot: Image.Image, previous_screenshot: Image.Image) -> Process:
        """Compares current screenshot with previous one."""
        logger.debug("Performing image comparison for duplicates")
        try:
            result = image_manipulation.compare_images(screenshot, previous_screenshot)
            logger.debug(f"Image comparison result: {result}")
            return result
        except Exception as e:
            logger.error(f"Image comparison failed: {str(e)}", exc_info=True)
            raise

    def _handle_duplicate(self, screenshot: Image.Image, previous_screenshot: Image.Image) -> Process:
        """Handles user interaction when a duplicate screenshot is detected.

        Opens a dialog window allowing the user to choose between:
        - Keeping the duplicate image
        - Discarding the duplicate image
        - Ending the book processing

        Args:
            screenshot: The current screenshot that was detected as a duplicate
            previous_screenshot: The previously accepted screenshot for comparison

        Returns:
            Process:
                - CONTINUE: If user kept screenshot
                - DONT_CONTINUE: If user discarded screenshot
                - END: If user declares end of book.

        Raises:
            RunTimerError: If not a non valid response is returned from ImageWindow.duplicate
        """
        logger.info("Presenting duplicate screenshot dialog to user")
        try:
            response = ImageWindow.duplicate(previous_img=previous_screenshot, current_img=screenshot)
            logger.info(f"User response to duplicate: {response}")

            self._pause_check()

            if response == DialogResult.ACCEPT:
                logger.debug("User chose to keep duplicate")
                return Process.CONTINUE
            elif response == DialogResult.REJECT:
                logger.debug("User chose to discard duplicate")
                return Process.DONT_CONTINUE
            elif response == DialogResult.TERMINATE:
                logger.info("User chose to end book processing")
                return Process.END
            else:
                logger.error(f"Invalid dialog response received: {response}")
                raise RuntimeError(f"Unknown duplicate response: {response}")

        except Exception as e:
            logger.error(f"Duplicate handling failed: {str(e)}", exc_info=True)
            raise

    # def set_end_of_book(self, value):
    #     # TODO: No longer needed?
    #     self.end_of_book = value
