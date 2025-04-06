import time
import sys
import keyboard
import pyautogui
from PIL import ImageGrab
from threading import Thread, Event
from ui import popup_windows
from utils import logs
from utils.browser import activate_edge, enter_fullscreen_if_needed, is_edge_fullscreen
from utils import image_manipulation, pdf_maker


"""Logic For Copying The Book"""
#TODO:  # Better Solution For Hoopla Reloading When Losing Focus
        # Custom Thresholds Per Site
        # Collect Blank Data Per Site
        # Move Mouse Based On Display
        # Move Mouse Based On Capture Area
        # Move capture and validate into PageProcessor
        # Remove These Global Vars
        
pause_event = Event()
cancel_event = Event()
HOOPLA = 20


def move_mouse():
    cur_x, cur_y = pyautogui.position()
    width, height = pyautogui.size()
    if (cur_x, cur_y) != (width // 2, height):
        pyautogui.moveTo(width // 2, height)  # Center-bottom
        logs.LOGGER.debug("Mouse moved to bottom center")

def keyboard_listener():
    """Background Thread that sets pause event when ESC key is pressed"""
    while not cancel_event.is_set():
        if keyboard.is_pressed('esc'):
            pause_event.set()
            logs.LOGGER.info("Esc key detected")
            # Prevents multiple triggers
            while keyboard.is_pressed('esc') and not cancel_event.is_set():
                time.sleep(0.1)
        time.sleep(0.1) # Reduce cpu usage

def start_keyboard_listener():
    listner_thread = Thread(target=keyboard_listener, daemon=True)
    listner_thread.start()
    logs.LOGGER.info("Keyboard listener started")
    return listner_thread

def handle_pause_request(listener_thread, site):
    """User initiated pause, ask user if they wish to stop"""
    if pause_event.is_set():
            logs.LOGGER.info("User Paused")
            response = popup_windows.ask_yes_no("Cancel Run", "Do You Wish To Cancel Run?", btn_focus="No")
            if response: # User Wants To Cancel Run
                cancel_event.set()
                listener_thread.join(timeout=1) # Wait for clean exit
                logs.LOGGER.info("User paused and cancelled run.")
                pause_event.clear()
                return True
            elif not response: # User Resumes Run
                logs.LOGGER.info("User Resumed")
                #activate_edge()
                activate_edge()
                if not is_edge_fullscreen:
                    enter_fullscreen_if_needed()
                pause_event.clear()
                if site == "Hoopla":
                    time.sleep(HOOPLA)
                move_mouse()
                return False
    else:
        return False

def get_memory_usage(image_list):
    logs.LOGGER.debug(f"Memory usage of screenshot_batch MB: {sum(sys.getsizeof(img.tobytes()) for img in image_list) / (1024 * 1024)}")
    logs.LOGGER.debug(f"Batch Size: {len(image_list)}")
    return sum(sys.getsizeof(img.tobytes()) for img in image_list) / (1024 * 1024)  # Convert to MB

def capture_ebook(timer, total_pages, capture_area, max_img, max_mem, selected_site, output_pdf):
    listener = start_keyboard_listener()
    capture_config = CaptureConfig(capture_area)
    processor = PageProcessor(max_img, max_mem, output_pdf)
    #Restablish Edge As Active Window, Move Mouse And Wait If Needed
    activate_edge()
    move_mouse()
    if selected_site == "Hoopla":
        # Hoopla seems to want to reload if you switch focus from edge.
        time.sleep(HOOPLA)
    try:
        for page in range(total_pages):
            # Check If We Have A Pause Request
            logs.LOGGER.info(f"Page: {page} of {total_pages}")
            if handle_pause_request(listener, selected_site):
                return "cancelled"
            #Take Screenshot, and check for being blank
            screenshot = capture_and_validate_page(timer, listener, capture_config, selected_site)
            if screenshot == "cancelled":
                return "cancelled"
            elif not screenshot:
                # No screenshot, so we move to next page
                navigate_to_next_page(selected_site)
                continue
            page_process = processor.process_page(screenshot, selected_site)
            if page_process is False:
                navigate_to_next_page(selected_site)
                continue
            elif page_process == "End":
                logs.LOGGER.info("User declared end of book")
                return True
            if not processor.save_image(screenshot):
                logs.LOGGER.error("Unable To Save Screenshot")
                return "cancelled"
            navigate_to_next_page(selected_site)
        return True
    finally:
        """Clean up listener thread, and add any remaning images in batch to pdf"""
        #cancel_event.set() #Exit Thread, Should Be Needed, Believe dameon=True should terminate it.
        cancel_event.clear()
        pause_event.clear()
        listener.join(timeout=1) # Wait for clean exit
        # Take Edge Out Of Full Screen
        activate_edge()
        keyboard.press_and_release("f11")
        pdf_maker.add_image_to_pdf(processor.batch, processor.output_pdf)
        processor.batch.clear() # Not needed
        #cleanup(listener, processor)

#Helper Classes/functions
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
        logs.LOGGER.debug(f"process_capture_area, bbox: {bounding_box_values}, multi_monitor: {multi_monitor}")
        return bounding_box_values, multi_monitor 

class PageProcessor:
    def __init__(self, max_img, max_mem, output_pdf):
        self.max_img = max_img
        self.max_mem = max_mem
        self.output_pdf = output_pdf
        self.batch = []
        self.previous_image = None

    def process_page(self, screenshot, site):
        """Process a captured page"""
        #No Previous Image to Check Against
        if not self.previous_image:
            logs.LOGGER.info("No previous image to compare to")
            return True
        # Check Against Previous Image
        if self._is_duplicate(screenshot):
            response = self._handle_duplicate(screenshot)
            if site == "Hoopla":
                time.sleep(HOOPLA)
            return response

    
    def save_image(self, screenshot):
        """Add Image To Batch"""
        self._add_to_batch(screenshot)
        logs.LOGGER.info("Image added to batch")
        if len(self.batch) >= self.max_img or get_memory_usage(self.batch) >= self.max_mem:
            return self._save_batch_to_pdf()
        else:
            return True
    
    def _save_batch_to_pdf(self):
        logs.LOGGER.info("Saving batch...")
        if pdf_maker.add_image_to_pdf(self.batch, self.output_pdf):
            logs.LOGGER.info("Batch cleared")
            self.batch.clear()
            return True

    def _is_duplicate(self, screenshot):
        #If True, Image Is Duplicate
        return image_manipulation.compare_images(screenshot, self.previous_image)
    
    def _handle_duplicate(self, screenshot):
        #True we keep duplicate, False we dont, End end the book
        return popup_windows.ask_user_keep_dupe(self.previous_image, screenshot)
    
    def _add_to_batch(self, screenshot):
        # add batch and check limits
        self.previous_image = screenshot
        self.batch.append(screenshot)

def capture_and_validate_page(timer, listener, capture_config, site):
        """Capture and validate a single page"""
        max_attempts = 3
        attempt = 0
        while attempt < max_attempts:
            # Listen For Pause, If Pause 
            logs.LOGGER.debug(f"capture_and_validate_page, Attempt: {attempt}")
            pause = pause_check(timer, listener, site)
            if pause:
                return "cancelled"
            #time.sleep(timer)
            screenshot = take_screenshot(capture_config)

            if not image_manipulation.is_blank(screenshot): # If False Image is not blank so we return
                logs.LOGGER.info("Image is not blank")
                return screenshot
            
            if attempt == 2:
                # Ask User To Keep Image Detected As Blank, True = Keep
                response = popup_windows.ask_user_keep_blank(screenshot)
                if response is True:
                    if site == "Hoopla":
                        time.sleep(HOOPLA)
                    return screenshot
                elif response == "again":
                    if site == "Hoopla":
                        time.sleep(HOOPLA)
                    #Reset Attempts And Try Again
                    attempt = -1
                else:
                    break
            attempt +=1
        logs.LOGGER.info("Image Is Blank And Skipped")   
        return None

def pause_check(total_wait_time, listener, site, interval=0.1):

    end_time = time.time() + total_wait_time
    while time.time() < end_time:
        remaining = min(interval, end_time, time.time())
        if remaining > 0:
            time.sleep(remaining)

        if handle_pause_request(listener, site):
            return True
    return False

def navigate_to_next_page(site):
    activate_edge()
    if not is_edge_fullscreen():
        enter_fullscreen_if_needed()
        if site == "Hoopla":
            time.sleep(HOOPLA)
    move_mouse()
    logs.LOGGER.info("Navigate to next page")
    keyboard.press_and_release("right")

def take_screenshot(capture_config):
    logs.LOGGER.debug(f"take_screenshot, bbox: {capture_config.bbox}, all_screens = {capture_config.multi_monitor}")
    return ImageGrab.grab(bbox=capture_config.bbox, all_screens=capture_config.multi_monitor)
