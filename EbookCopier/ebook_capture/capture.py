from ebook_capture.managers import CaptureConfig, PauseManager, PDFManager, ScreenshotManger, PageProcessor, Process
import keyboard
from utils import browser
import logging
logger = logging.getLogger(__name__)


"""Logic For Copying The Book"""
# TODO: Collect Blank Data Per Site
# TODO: Check Raises
# TODO: Maximum second pass length? To avoit endless run


def capture_ebook(book, settings):
    """Main function to capture an ebook and convert it to PDF"""
    logger.info(f"Starting ebook capture for {book.selected_site}")

    # Setup components with detailed configuration logging
    logger.debug("Initializing capture components...")
    capture_config = CaptureConfig(book.capture_box)
    pause_manager = PauseManager(timer=int(book.timer))
    pause_manager.start_listener()

    screenshot_manager = ScreenshotManger(capture_config=capture_config,
                                          blank_attempts=2,
                                          threshold=settings.thresholds[book.selected_site],
                                          retry_delay=int(book.timer))

    pdf_manager = PDFManager(max_img=settings.max_images,
                             max_memory=settings.max_memory_mb,
                             output_pdf=book.file_path)

    processor = PageProcessor(screenshot_manager,
                              pause_manager,
                              pdf_manager,
                              )
    logger.info(
        f"Components initialized with settings:\n"
        f"- Site: {book.selected_site}\n"
        f"- Timer: {book.timer}\n"
        f"- Threshold: {settings.thresholds[book.selected_site]}\n"
        f"- Max images: {settings.max_images}\n"
        f"- Max memory: {settings.max_memory_mb}MB\n"
        f"- Output path: {book.file_path}"
    )
    try:
        # Initial wait before starting capture
        logger.info("Starting initial wait period...")
        pause_manager.check_for_pause(timer=float(book.timer))
        logger.info("Initial wait completed, beginning capture process")

        # First pass - user declared book length
        logger.info(f"Starting first pass for {book.book_length} pages")
        first_pass_result = _process_initial_pages(book, processor, pause_manager, int(book.timer))

        if first_pass_result != Process.COMPLETED:
            logger.warning(f"Capture cancelled during first pass with result: {first_pass_result}")
            return False

        # Second pass - process remaining pages until duplicate found
        if not processor.end_of_book:
            logger.info("Starting remaining pages processing")
            second_pass_result = _process_remaining_pages(processor, pause_manager, int(book.timer))
            if second_pass_result != Process.COMPLETED:
                logger.warning(f"Capture cancelled during remaining pages with result: {second_pass_result}")
                return False

        logger.info("Ebook capture completed successfully")
        return True

    except Exception as e:
        # TODO: Ensure we are raising run cancelling errors back to main, for popup_window.messagebox
        logger.critical(f"Fatal error during ebook capture: {str(e)}", exc_info=True)
        raise RuntimeError(f"Runtime Error during capture: {str(e)}") from e
    finally:
        logger.info("Beginning cleanup process")
        _cleanup_resources(pause_manager, pdf_manager)
        logger.info("Cleanup completed, book finished")


def _process_initial_pages(book, processor: PageProcessor, pause_manager: PauseManager, timer):
    """Process pages up to user declared book length"""
    logger.info(f"Processing initial {book.book_length} pages")

    for page in range(int(book.book_length)):
        if _should_cancel(pause_manager):
            logger.warning(f"Cancellation detected at page {page}")
            return Process.CANCELLED

        logger.debug(f"Processing page {page + 1}/{book.book_length}")
        result = processor.process_page()
        logger.debug(f"Page processing result: {result}")

        if result == Process.CANCELLED:
            logger.warning("User cancelled during initial pages processing")
            return Process.CANCELLED

        if result == Process.END:
            logger.info("Early book end detected during initial processing")
            return Process.COMPLETED

        if result == Process.NEXT:
            logger.debug("Navigating to next page")
            navigate_to_next_page(timer, pause_manager)
        else:
            logger.error(f"Unexpected processing result: {result}")
            raise RuntimeError(f"Error processing initial pages: {result}")

    logger.info("Completed all initial pages")
    return Process.COMPLETED


def _process_remaining_pages(processor: PageProcessor, pause_manager: PauseManager, timer: float):
    """Continue processing pages until duplicate found (auto end of book detection)"""

    # TODO: Conisder adding a maximum length to run.
    logger.info("Starting remaining pages processing")
    page_count = 0

    while True:
        if _should_cancel(pause_manager):
            logger.warning("Cancellation detected during remaining pages processing")
            return Process.CANCELLED

        page_count += 1
        logger.debug(f"Processing remaining page {page_count}")
        result = processor.process_page(end_of_book_mode=True)
        logger.info(f"Remaining page processing result: {result}")

        if result == Process.CANCELLED:
            logger.warning("User cancelled during remaining pages processing")
            return Process.CANCELLED

        if result == Process.END:  # Found final duplicate
            logger.info("Auto-detected book end during remaining pages processing")
            return Process.COMPLETED

        logger.debug("Navigating to next remaining page")
        navigate_to_next_page(timer, pause_manager)


def _should_cancel(pause_manager):
    """Check if processing should be cancelled"""
    cancelled = pause_manager.is_cancelled()
    paused = pause_manager.check_for_pause()

    if cancelled or paused:
        logger.debug(f"Cancellation check - cancelled: {cancelled}, paused: {paused}")
    return cancelled or paused


def _cleanup_resources(pause_manager, pdf_manager):
    """Clean up all resources"""
    logger.debug("Starting resource cleanup")
    try:
        pause_manager.stop_listener()
        logger.debug("Pause manager stopped")
        pdf_manager.finalize()
        logger.debug("PDF manager finalized")
    except Exception as e:
        logger.error(f"Error during cleanup: {str(e)}", exc_info=True)
        raise


def navigate_to_next_page(timer, pause_manager):
    """Navigate to next page and wait for page to load"""
    logger.debug("Attempting to navigate to next page")

    if browser.check_environment():
        logger.debug("Browser environment adjustment detected - applying extended wait")
        pause_manager.check_for_pause(timer=30)

    try:
        keyboard.press_and_release("right")
        logger.info("Navigated to next page")
        pause_manager.check_for_pause(timer=1)
        return True
    except Exception as e:
        logger.error(f"Navigation failed: {str(e)}")
        raise
