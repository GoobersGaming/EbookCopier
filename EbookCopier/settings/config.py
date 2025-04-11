import tomllib
import tomli_w
from pathlib import Path
import logging
logger = logging.getLogger(__name__)

"""Book/User Settings"""
# TODO:
# After popuplate settings, add a check to see if any settings were missing, and save if so.


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
            raise ValueError("invalid_file_path")
        if not str(self.timer).isdigit():
            raise ValueError("invalid_timer")
        if not str(self.book_length).isdigit():
            raise ValueError("invalid_book_length")
        if not self.selected_site:
            raise ValueError("empty_site_selected")
        if not self.page_view:
            raise ValueError("invalid_page_view")
        return True


class UserSettings:
    def __init__(self, path=None):
        """Read settings from config.toml if exists, if not create it with defualt settings"""

        self.settings_path = Path(path if path is not None else "settings/config.toml")
        self.info = True
        self.debug = True
        self.console_logging = False
        self.console_level = "INFO"
        self.picture_format = "PNG"
        self.websites = ["Libby", "Hoopla"]
        self.max_images = int(50)
        self.max_memory_mb = int(200)
        self.saved_capture_boxes = {}
        self.thresholds = {"Libby": 0.006, "Hoopla": 0.000}
        self.extra_delay = {"Libby": 1.0, "Hoopla": 20.0}
        self.__populate_settings()
        self.save_user_settings()

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
            logging.info("No config.toml")
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.touch()

            # Initialize with defualt content
            self.save_user_settings()
            logging.info("config.toml created with default settings")

        with open(output_path, "rb") as f:
            return tomllib.load(f)

    def __populate_settings(self):
        config = self.__read_user_settings()
        self.info = self.__safe_get(config, "logging", "info", default=True)
        self.debug = self.__safe_get(config, "logging", "debug", default=True)
        self.picture_format = self.__safe_get(config, "settings", "picture_format", default="PNG")
        self.websites = self.__safe_get(config, "settings", "websites", default=["Libby", "Hoopla"])
        self.max_images = self.__safe_get(config, "settings", "max_images", default=50)
        self.max_memory_mb = self.__safe_get(config, "settings", "max_memory_mb", default=200)
        self.thresholds = self.__safe_get(config, "settings", "threshold", default={"Libby": 0.006, "Hoopla": 0.000})
        self.extra_delay = self.__safe_get(config, "settings", "extra_delay", default={"Libby": 1.0, "Hoopla": 20})
        self.console_logging = self.__safe_get(config, "logging", "console_logging", default=False)
        self.console_level = self.__safe_get(config, "logging", "console_level", default="INFO")
        for site in self.websites:
            site_config = self.__safe_get(config, site, default={})
            if not site_config:  # Skip if site doesnt exist in config
                continue
            self.saved_capture_boxes[site] = {}

            # Loop through monitors
            for monitor in site_config:
                monitor_config = site_config[monitor]
                self.saved_capture_boxes[site][monitor] = {}

                # Looop through page types
                for page_type in monitor_config:
                    self.saved_capture_boxes[site][monitor][page_type] = {
                        "x1": self.__safe_get(monitor_config, page_type, "x1", default=100),
                        "y1": self.__safe_get(monitor_config, page_type, "y1", default=100),
                        "x2": self.__safe_get(monitor_config, page_type, "x2", default=100),
                        "y2": self.__safe_get(monitor_config, page_type, "y2", default=100),
                    }

    def save_user_settings(self):
        config = {
            "settings": {
                "picture_format": self.picture_format,
                "websites": self.websites,
                "max_images": self.max_images,
                "max_memory_mb": self.max_memory_mb,
                "threshold": self.thresholds,
                "extra_delay": self.extra_delay},
            "logging": {
                "info": self.info,
                "debug": self.debug,
                "console_logging": self.console_logging,
                "console_level": self.console_level},
            **self.saved_capture_boxes}

        output_path = self.settings_path.resolve()

        with open(output_path, "wb") as f:
            f.write(b"# Main application settings\n")
            tomli_w.dump(config, f)
            logging.info("Saving to config.toml")

    def update_saved_capture_box(self, site, page, my_dict):
        # Update Bounding Box For Current Site Based On Monitor, And Page View.
        box = my_dict.copy()
        box.pop("monitor", None)
        monitor = str(my_dict["monitor"])
        self.saved_capture_boxes.setdefault(site, {}).setdefault(monitor, {}).setdefault(page, {}).update(box)
        self.save_user_settings()
