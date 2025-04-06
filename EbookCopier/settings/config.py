import tomllib
import tomli_w
from pathlib import Path
from utils import logs
import logging

"""Book/User Settings"""

class Book:
    def __init__(self):
        self.file_path = None
        self.timer = None
        self.book_length = None
        self.selected_site = None
        self.page_view = None
        self.capture_box = None
        self.monitor_display = None

    def clear_values(self):
        self.file_path = None
        self.timer = None
        self.book_length = None
        self.selected_site = None
        self.page_view = None
        self.capture_box = None
        self.monitor_display = None
    
    def validate(self):
        if not self.file_path:
            raise ValueError("empty_file_path")
        path = Path(self.file_path)
        if not path.parent.exists():
            raise ValueError(f"invalid_directory")
        if not str(self.timer).isdigit():
            raise ValueError("invalid_timer")
        if not str(self.book_length).isdigit():
            raise ValueError("invalid_length")
        if not self.selected_site:
            raise ValueError("no_site_selected")
        if not self.page_view:
            raise ValueError("invalid_page_view")
        return True

class UserSettings:
    def __init__(self):
        #We Set Default Values, and Then Look for a config.toml
        self.settings_path = Path("settings/config.toml")
        self.info = False
        self.debug = False
        self.picture_format = "PNG"
        self.websites = ["Libby", "Hoopla"]
        self.max_images = int(50)
        self.max_memory_mb = int(50)
        self.saved_capture_boxes = {}
        self.__check_logger()
        self.__populate_settings()

    def __check_logger(self):
        if logs.LOGGER is None:
            log_level = []
            if self.info:
                log_level.append(logging.INFO)
            if self.debug:
                log_level.append(logging.DEBUG)
            logs.LOGGER = logs.AppLogger(ignore_levels=log_level).get_logger()

    def __safe_get(self, config, *keys, default=None):
        for key in keys:
            try:
                config = config[key]
            except (KeyError, TypeError):
                return default
        return config
        
    def __read_user_settings(self):
        output_path = self.settings_path.resolve()

        if not output_path.exists():
            logs.LOGGER.info("Config.toml not found")
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.touch()

            # Initialize with defualt content
            self.save_user_settings()
            logs.LOGGER.info("new config.toml created")
        
        with open(output_path, "rb") as f:
            return tomllib.load(f)
    
    def __populate_settings(self):
        config = self.__read_user_settings()
        self.info = self.__safe_get(config, "logging", "info", default=False)
        self.debug = self.__safe_get(config, "logging", "debug", default=False)
        self.picture_format = self.__safe_get(config,"settings", "picture_format", default = "PNG")
        self.websites = self.__safe_get(config,"settings", "websites", default = ["Libby", "Hoopla", "Fread"])
        self.max_images = self.__safe_get(config,"settings", "max_images", default = 50)
        self.max_memory_mb = self.__safe_get(config,"settings", "max_memory_mb", default = 200)
        for site in self.websites:
            site_config = self.__safe_get(config, site, default={})
            if not site_config: #Skip if site doesnt exist in config
                continue
            self.saved_capture_boxes[site] = {}

            # Loop through monitors
            for monitor in site_config:
                monitor_config = site_config[monitor]
                self.saved_capture_boxes[site][monitor] = {}

                # Looop through page types
                for page_type in monitor_config:
                    self.saved_capture_boxes[site][monitor][page_type] ={
                        "x1": self.__safe_get(monitor_config, page_type, "x1", default=100),
                        'y1': self.__safe_get(monitor_config, page_type, 'y1', default=100),
                        'x2': self.__safe_get(monitor_config, page_type, 'x2', default=100),
                        'y2': self.__safe_get(monitor_config, page_type, 'y2', default=100),
                    }


    def save_user_settings(self):
        config ={
            "settings": {
            "picture_format": self.picture_format,
            "websites": self.websites,
            "max_images": self.max_images,
            "max_memory_mb": self.max_memory_mb },
            "logging": { 
             "info": self.info,
              "debug": self.debug },
            **self.saved_capture_boxes }   
        
        output_path = self.settings_path.resolve()
            
        with open(output_path, "wb") as f:
            f.write(b"# Main application settings\n")
            tomli_w.dump(config, f)
            logs.LOGGER.debug(f"Saving user settings to: {self.settings_path.resolve()}")

    def update_saved_capture_box(self, site, page, my_dict):
        # Update Bounding Box For Current Site Based On Monitor, And Page View. 
        box = my_dict.copy()
        box.pop('monitor', None)
        monitor = str(my_dict["monitor"])
        self.saved_capture_boxes.setdefault(site, {}).setdefault(monitor, {}).setdefault(page, {}).update(box)
        self.save_user_settings()
