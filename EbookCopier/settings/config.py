import tomllib
import tomli_w
from pathlib import Path
from utils import logs

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

class UserSettings:
    def __init__(self):
        #We Set Default Values, and Then Look for a config.toml
        self.settings_path = Path("settings/config.toml")
        self.info = None
        self.debug = None
        self.picture_format = ""
        self.websites = []
        self.max_images = int()
        self.max_memory_mb = int()
        self.saved_capture_boxes = {}
        self.__populate_settings()
        #self.x = Path(self.settings_path)
        

    def __safe_get(self, config, *keys, default=None):
        for key in keys:
            try:
                config = config[key]
            except (KeyError, TypeError):
                return default
        return config
        
    def __read_user_settings(self):
        try:
            with open(self.settings_path.resolve(), "rb") as f:
                return tomllib.load(f)
        except FileNotFoundError:
            # config.toml not found revert to default
            self.save_user_settings()
            logs.LOGGER.info("Config.toml not found, creating new config.toml")
            return {}
    
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
