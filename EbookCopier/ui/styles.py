
def pyside_themes(font=None, font_size=None, font_weight=None, theme=None):
    f_size = str(font_size or "14")
    f_family = font or "sans-serif"
    weight_mapping = {
        'thin': 100,
        'extra light': 200,
        'light': 300,
        'normal': 400,
        'medium': 500,
        'semi bold': 600,
        'bold': 700,
        'extra bold': 800,
        'black': 900,
        'heavy': 950  # Some fonts support this
    }
    weight = None
    # Determine font weight
    if isinstance(font_weight, int):
        weight = max(1, min(font_weight, 1000))  # clamp to valid ranges
    elif isinstance(font_weight, str):
        weight = 400  # Fallback
        font_weight = font_weight.lower().strip()

        if font_weight in weight_mapping:
            weight = weight_mapping[font_weight]
        else:
            for key, value in weight_mapping.items():
                if key in font_weight:
                    weight = value
                    break
    if weight is None:
        weight = 400
    font_spec = f"{weight} {f_size}pt '{f_family}'"

    def dict_to_stylesheet(theme_dict: dict) -> str:
        """convert nested theme dicts into a Qt stylesheet string"""
        stylesheet = []
        for selector, properties in theme_dict.items():
            stylesheet.append(f"{selector} {{")
            for prop, value, in properties.items():
                stylesheet.append(f"    {prop}: {value};")
            stylesheet.append("}")
        return "\n".join(stylesheet)

    themes = {
        "dark_theme": {
            "QDialog, QWidget": {
                "font": f"{font_spec}",
                "background-color": "#2e2e2e",
                "color": "#f0f0f0"
            },
            "QFrame#StyledFrame": {
                "background-color": "#3a3a3a",
                "border": "1px solid #5c5c5c",
                "border-radius": "4px"
            },
            "QLabel": {
                "font": f"{font_spec}",
                "color": "#e0e0e0",
            },
            "QLabel#Title": {
                "font-weight": "700",
                "color": "#ffffff",
            },
            "QPushButton": {
                "font": f"{font_spec}",
                "background-color": "#4a7cab",
                "color": "#ffffff",
                "border": "1px solid #1a3a5a",
                "border-radius": "4px",
            },
            "QPushButton:disabled": {
                "text-decoration": "line-through",
            },
            "QPushButton:hover": {
                "background-color": "#5b8ec2",
                "border": "2px solid #245a82",
            },
            "QPushButton:pressed": {
                "background-color": "#1a3a5a",
                "border": "2px inset #0f2a40",
            },
            "QPushButton:default": {
                "font": f"{font_spec}",
                "font-weight": "700",
                "background-color": "#4a7cab",
                "color": "#ffffff",
                "border": "1px solid #1a3a5a",
                "border-radius": "4px",
            },
            "QPushButton:default:hover": {
                "background-color": "#5b8ec2",
                "border": "2px solid #245a82",
            },
            "QPushButton:default:pressed": {
                "background-color": "#1a3a5a",
                "border": "2px inset #0f2a40",
            },
            "QComboBox": {
                "font": f"{font_spec}",
                "background-color": "#2e2e2e",
                "color": "#f0f0f0",
                "border": "1px solid #5c5c5c",
                "border-radius": "4px",
                "padding": "2px 6px"
            },
            "QComboBox QAbstractItemView": {
                "background-color": "#3a3a3a",
                "selection-background-color": "#4a7cab",
                "selection-color": "#ffffff",
                "color": "#f0f0f0",
                "border": "1px solid #5c5c5c",
            },
            "QComboBox::drop-down": {
                "subcontrol-origin": "padding",
                "subcontrol-position": "top right",
                "width": "20px",
                "background-color": "#4a7cab",
                "border-left": "1px solid #1a3a5a",
                "border-top-right-radius": "4px",
                "border-bottom-right-radius": "4px"
            },
            "QComboBox::down-arrow": {
                "width": "10px",
                "height": "10px",
                "image": "none"
            },
            "QLineEdit": {
                "font": f"{font_spec}",
                "background-color": "#1e1e1e",
                "color": "#f0f0f0",
                "border": "1px solid #5c5c5c",
                "border-radius": "4px",
                "padding": "2px 6px"
            },
            "QLineEdit:hover": {
                "border": "1px solid #4a7cab"
            },
            "QLineEdit:focus": {
                "border": "1px solid #4a7cab",
                "background-color": "#2a2a2a"
            },
            "QToolTip": {
                "background-color": "#3a3a3a",
                "color": "#ffffff",
                "border": "1px solid #5c5c5c"
            }
        },
        "warm_sand": {
            "QDialog, QWidget": {
                "font": f'{font_spec}',
                "background-color": "#fdf6ec",
                "color": "#3a2e2e"
            },
            "QFrame#StyledFrame": {
                "background-color": "#f7e9d0",  # Slightly darker than main bg
                "border": "1px solid #d5b99e",
                "border-radius": "4px"
            },
            "QLabel": {
                "font": f'{font_spec}',
                "color": "#343a40",
            },
            "QLabel#Title": {
                "font-weight": '700',
                "color": "#343a40",
            },
            "QPushButton": {
                "font": f'{font_spec}',
                "background-color": "#d9b382",
                "color": "#3a2e2e",
                "border": "1px solid #a57d52",
                "border-radius": "4px",
            },
            "QPushButton:disabled": {
                "text-decoration": "line-through",
            },
            "QPushButton:hover": {
                "background-color": "#e6c79c",
                "border": "2px solid #a57d52",
            },
            "QPushButton:pressed": {
                "background-color": "#c69c6d",
                "border": "2px inset #8a6540",
            },
            "QPushButton:default": {
                "font": f'{font_spec}',

                "background-color": "#d9b382",
                "color": "#3a2e2e",
                "border": "1px solid #a57d52",
                "border-radius": "4px",
                "font-weight": "700",

            },
            "QPushButton:default:hover": {
                "background-color": "#e6c79c",
                "border": "2px solid #a57d52",  # Thicker border on hover
            },
            "QPushButton:default:pressed": {
                "background-color": "#c69c6d",
                "border": "2px inset #8a6540",
            },
            "QComboBox": {
                "font": f"{font_spec}",
                "background-color": "#fdf6ec",
                "color": "#3a2e2e",
                "border": "1px solid #d5b99e",
                "border-radius": "4px",
                "padding": "2px 6px"
            },
            "QComboBox QAbstractItemView": {
                "background-color": "#ffffff",
                "selection-background-color": "#e6c79c",
                "selection-color": "#3a2e2e",
                "color": "#3a2e2e",
                "border": "1px solid #d5b99e",
            },

            "QComboBox::drop-down": {
                "subcontrol-origin": "padding",
                "subcontrol-position": "top right",
                "width": "20px",
                "background-color": "#e6c79c",
                "border-left": "1px solid #a57d52",
                "border-top-right-radius": "4px",
                "border-bottom-right-radius": "4px"
            },
            "QComboBox::down-arrow": {
                "width": "10px",
                "height": "10px",
                "image": "none"
            },
            "QLineEdit": {
                "font": f"{font_spec}",
                "background-color": "#ffffff",
                "color": "#3a2e2e",
                "border": "1px solid #d5b99e",
                "border-radius": "4px",
                "padding": "2px 6px"
            },
            "QLineEdit:hover": {
                "border": "1px solid #a57d52"
            },
            "QLineEdit:focus": {
                "border": "1px solid #a57d52",
                "background-color": "#fff8ed"
            },
            "QToolTip": {
                "background-color": "#fcefd9",
                "color": "#3a2e2e",
                "border": "1px solid #d5b99e"
            },

        },
        "midnight_theme": {
            "QDialog, QWidget": {
                "font": f"{font_spec}",
                "background-color": "#1b1b2f",
                "color": "#e0e0f0"
            },
            "QFrame#StyledFrame": {
                "background-color": "#292945",
                "border": "1px solid #3e3e66",
                "border-radius": "4px"
            },
            "QLabel": {
                "font": f"{font_spec}",
                "color": "#dcdcf5"
            },
            "QLabel#Title": {
                "font-weight": "700",
                "color": "#ffffff"
            },
            "QPushButton": {
                "font": f"{font_spec}",
                "background-color": "#5a4b81",
                "color": "#ffffff",
                "border": "1px solid #3b2f5a",
                "border-radius": "4px"
            },
            "QPushButton:disabled": {
                "text-decoration": "line-through"
            },
            "QPushButton:hover": {
                "background-color": "#6b5c92",
                "border": "2px solid #4c3b6a"
            },
            "QPushButton:pressed": {
                "background-color": "#3b2f5a",
                "border": "2px inset #2a1f3a"
            },
            "QPushButton:default": {
                "font": f"{font_spec}",
                "font-weight": "700",
                "background-color": "#5a4b81",
                "color": "#ffffff",
                "border": "1px solid #3b2f5a",
                "border-radius": "4px"
            },
            "QPushButton:default:hover": {
                "background-color": "#6b5c92",
                "border": "2px solid #4c3b6a"
            },
            "QPushButton:default:pressed": {
                "background-color": "#3b2f5a",
                "border": "2px inset #2a1f3a"
            },
            "QComboBox": {
                "font": f"{font_spec}",
                "background-color": "#1b1b2f",
                "color": "#e0e0f0",
                "border": "1px solid #3e3e66",
                "border-radius": "4px",
                "padding": "2px 6px"
            },
            "QComboBox QAbstractItemView": {
                "background-color": "#292945",
                "selection-background-color": "#5a4b81",
                "selection-color": "#ffffff",
                "color": "#e0e0f0",
                "border": "1px solid #3e3e66"
            },
            "QComboBox::drop-down": {
                "subcontrol-origin": "padding",
                "subcontrol-position": "top right",
                "width": "20px",
                "background-color": "#5a4b81",
                "border-left": "1px solid #3b2f5a",
                "border-top-right-radius": "4px",
                "border-bottom-right-radius": "4px"
            },
            "QComboBox::down-arrow": {
                "width": "10px",
                "height": "10px",
                "image": "none"
            },
            "QLineEdit": {
                "font": f"{font_spec}",
                "background-color": "#141428",
                "color": "#e0e0f0",
                "border": "1px solid #3e3e66",
                "border-radius": "4px",
                "padding": "2px 6px"
            },
            "QLineEdit:hover": {
                "border": "1px solid #5a4b81"
            },
            "QLineEdit:focus": {
                "border": "1px solid #5a4b81",
                "background-color": "#1e1e3a"
            },
            "QToolTip": {
                "background-color": "#292945",
                "color": "#ffffff",
                "border": "1px solid #3e3e66"
            }
        },
        "solar_cream": {
            "QDialog, QWidget": {
                "font": f"{font_spec}",
                "background-color": "#fdfaf3",
                "color": "#4a3c2f"
            },
            "QFrame#StyledFrame": {
                "background-color": "#f5ecd8",
                "border": "1px solid #d2c2a4",
                "border-radius": "4px"
            },
            "QLabel": {
                "font": f"{font_spec}",
                "color": "#4a3c2f"
            },
            "QLabel#Title": {
                "font-weight": "700",
                "color": "#3a2e23"
            },
            "QPushButton": {
                "font": f"{font_spec}",
                "background-color": "#e6cfa1",
                "color": "#3a2e23",
                "border": "1px solid #cbb07e",
                "border-radius": "4px"
            },
            "QPushButton:disabled": {
                "text-decoration": "line-through"
            },
            "QPushButton:hover": {
                "background-color": "#f0d8ad",
                "border": "2px solid #cbb07e"
            },
            "QPushButton:pressed": {
                "background-color": "#cbb07e",
                "border": "2px inset #9c865f"
            },
            "QPushButton:default": {
                "font-weight": "700",
                "background-color": "#e6cfa1",
                "color": "#3a2e23",
                "border": "1px solid #cbb07e",
                "border-radius": "4px"
            },
            "QPushButton:default:hover": {
                "background-color": "#f0d8ad",
                "border": "2px solid #cbb07e"
            },
            "QPushButton:default:pressed": {
                "background-color": "#cbb07e",
                "border": "2px inset #9c865f"
            },
            "QComboBox": {
                "font": f"{font_spec}",
                "background-color": "#fffdf7",
                "color": "#4a3c2f",
                "border": "1px solid #d2c2a4",
                "border-radius": "4px",
                "padding": "2px 6px"
            },
            "QComboBox QAbstractItemView": {
                "background-color": "#f5ecd8",
                "selection-background-color": "#e6cfa1",
                "selection-color": "#3a2e23",
                "color": "#4a3c2f",
                "border": "1px solid #d2c2a4"
            },
            "QComboBox::drop-down": {
                "subcontrol-origin": "padding",
                "subcontrol-position": "top right",
                "width": "20px",
                "background-color": "#e6cfa1",
                "border-left": "1px solid #cbb07e",
                "border-top-right-radius": "4px",
                "border-bottom-right-radius": "4px"
            },
            "QComboBox::down-arrow": {
                "width": "10px",
                "height": "10px",
                "image": "none"
            },
            "QLineEdit": {
                "font": f"{font_spec}",
                "background-color": "#fffdf7",
                "color": "#4a3c2f",
                "border": "1px solid #d2c2a4",
                "border-radius": "4px",
                "padding": "2px 6px"
            },
            "QLineEdit:hover": {
                "border": "1px solid #e6cfa1"
            },
            "QLineEdit:focus": {
                "border": "1px solid #e6cfa1",
                "background-color": "#f5ecd8"
            },
            "QToolTip": {
                "background-color": "#e6cfa1",
                "color": "#3a2e23",
                "border": "1px solid #cbb07e"
            }
        },
        "moon_parchment": {
            "QDialog, QWidget": {
                "font": f"{font_spec}",
                "background-color": "#2a2825",
                "color": "#e6e0d5"
            },
            "QFrame#StyledFrame": {
                "background-color": "#35322f",
                "border": "1px solid #7b7367",
                "border-radius": "4px"
            },
            "QLabel": {
                "font": f"{font_spec}",
                "color": "#e6e0d5"
            },
            "QLabel#Title": {
                "font-weight": "700",
                "color": "#f5ecd8"
            },
            "QPushButton": {
                "font": f"{font_spec}",
                "background-color": "#6f6452",
                "color": "#fdfaf3",
                "border": "1px solid #a4927a",
                "border-radius": "4px"
            },
            "QPushButton:disabled": {
                "text-decoration": "line-through"
            },
            "QPushButton:hover": {
                "background-color": "#8c7b63",
                "border": "2px solid #a4927a"
            },
            "QPushButton:pressed": {
                "background-color": "#564c3f",
                "border": "2px inset #3f382e"
            },
            "QPushButton:default": {
                "font-weight": "700",
                "background-color": "#6f6452",
                "color": "#fdfaf3",
                "border": "1px solid #a4927a",
                "border-radius": "4px"
            },
            "QPushButton:default:hover": {
                "background-color": "#8c7b63",
                "border": "2px solid #a4927a"
            },
            "QPushButton:default:pressed": {
                "background-color": "#564c3f",
                "border": "2px inset #3f382e"
            },
            "QComboBox": {
                "font": f"{font_spec}",
                "background-color": "#2a2825",
                "color": "#e6e0d5",
                "border": "1px solid #7b7367",
                "border-radius": "4px",
                "padding": "2px 6px"
            },
            "QComboBox QAbstractItemView": {
                "background-color": "#35322f",
                "selection-background-color": "#6f6452",
                "selection-color": "#fdfaf3",
                "color": "#e6e0d5",
                "border": "1px solid #7b7367"
            },
            "QComboBox::drop-down": {
                "subcontrol-origin": "padding",
                "subcontrol-position": "top right",
                "width": "20px",
                "background-color": "#6f6452",
                "border-left": "1px solid #a4927a",
                "border-top-right-radius": "4px",
                "border-bottom-right-radius": "4px"
            },
            "QComboBox::down-arrow": {
                "width": "10px",
                "height": "10px",
                "image": "none"
            },
            "QLineEdit": {
                "font": f"{font_spec}",
                "background-color": "#1e1c1a",
                "color": "#e6e0d5",
                "border": "1px solid #7b7367",
                "border-radius": "4px",
                "padding": "2px 6px"
            },
            "QLineEdit:hover": {
                "border": "1px solid #a4927a"
            },
            "QLineEdit:focus": {
                "border": "1px solid #a4927a",
                "background-color": "#2f2c29"
            },
            "QToolTip": {
                "background-color": "#3f3a35",
                "color": "#fdfaf3",
                "border": "1px solid #7b7367"
            }
        },
        "autumn_ember": {
            "QDialog, QWidget": {
                "font": f"{font_spec}",
                "background-color": "#2e1f1a",  # deep ember brown
                "color": "#f3e9d2"
            },
            "QFrame#StyledFrame": {
                "background-color": "#3b2a22",
                "border": "1px solid #a35f3f",
                "border-radius": "4px"
            },
            "QLabel": {
                "font": f"{font_spec}",
                "color": "#f3e9d2"
            },
            "QLabel#Title": {
                "font-weight": "700",
                "color": "#ffbc7a"
            },
            "QPushButton": {
                "font": f"{font_spec}",
                "background-color": "#b25029",
                "color": "#fff9f0",
                "border": "1px solid #8c3e20",
                "border-radius": "4px"
            },
            "QPushButton:disabled": {
                "text-decoration": "line-through"
            },
            "QPushButton:hover": {
                "background-color": "#c75d33",
                "border": "2px solid #9e4724"
            },
            "QPushButton:pressed": {
                "background-color": "#8c3e20",
                "border": "2px inset #5d2715"
            },
            "QPushButton:default": {
                "font-weight": "700",
                "background-color": "#b25029",
                "color": "#fff9f0",
                "border": "1px solid #8c3e20",
                "border-radius": "4px"
            },
            "QPushButton:default:hover": {
                "background-color": "#c75d33",
                "border": "2px solid #9e4724"
            },
            "QPushButton:default:pressed": {
                "background-color": "#8c3e20",
                "border": "2px inset #5d2715"
            },
            "QComboBox": {
                "font": f"{font_spec}",
                "background-color": "#2e1f1a",
                "color": "#f3e9d2",
                "border": "1px solid #a35f3f",
                "border-radius": "4px",
                "padding": "2px 6px"
            },
            "QComboBox QAbstractItemView": {
                "background-color": "#3b2a22",
                "selection-background-color": "#b25029",
                "selection-color": "#fff9f0",
                "color": "#f3e9d2",
                "border": "1px solid #a35f3f"
            },
            "QComboBox::drop-down": {
                "subcontrol-origin": "padding",
                "subcontrol-position": "top right",
                "width": "20px",
                "background-color": "#b25029",
                "border-left": "1px solid #8c3e20",
                "border-top-right-radius": "4px",
                "border-bottom-right-radius": "4px"
            },
            "QComboBox::down-arrow": {
                "width": "10px",
                "height": "10px",
                "image": "none"
            },
            "QLineEdit": {
                "font": f"{font_spec}",
                "background-color": "#201510",
                "color": "#f3e9d2",
                "border": "1px solid #a35f3f",
                "border-radius": "4px",
                "padding": "2px 6px"
            },
            "QLineEdit:hover": {
                "border": "1px solid #c75d33"
            },
            "QLineEdit:focus": {
                "border": "1px solid #c75d33",
                "background-color": "#2e1f1a"
            },
            "QToolTip": {
                "background-color": "#3b2a22",
                "color": "#fff9f0",
                "border": "1px solid #a35f3f"
            }
        },
        "winter_ash": {
            "QDialog, QWidget": {
                "font": f"{font_spec}",
                "background-color": "#f4f4f7",  # pale snow white
                "color": "#2c2c2c"
            },
            "QFrame#StyledFrame": {
                "background-color": "#e0e0e5",
                "border": "1px solid #b4b4b4",
                "border-radius": "4px"
            },
            "QLabel": {
                "font": f"{font_spec}",
                "color": "#2c2c2c"
            },
            "QLabel#Title": {
                "font-weight": "700",
                "color": "#1a1a1a"
            },
            "QPushButton": {
                "font": f"{font_spec}",
                "background-color": "#cfd8dc",
                "color": "#1a1a1a",
                "border": "1px solid #a0a0a0",
                "border-radius": "4px"
            },
            "QPushButton:disabled": {
                "text-decoration": "line-through"
            },
            "QPushButton:hover": {
                "background-color": "#b0bec5",
                "border": "2px solid #909aa0"
            },
            "QPushButton:pressed": {
                "background-color": "#90a4ae",
                "border": "2px inset #6e7c85"
            },
            "QPushButton:default": {
                "font-weight": "700",
                "background-color": "#cfd8dc",
                "color": "#1a1a1a",
                "border": "1px solid #a0a0a0",
                "border-radius": "4px"
            },
            "QPushButton:default:hover": {
                "background-color": "#b0bec5",
                "border": "2px solid #909aa0"
            },
            "QPushButton:default:pressed": {
                "background-color": "#90a4ae",
                "border": "2px inset #6e7c85"
            },
            "QComboBox": {
                "font": f"{font_spec}",
                "background-color": "#f4f4f7",
                "color": "#2c2c2c",
                "border": "1px solid #b4b4b4",
                "border-radius": "4px",
                "padding": "2px 6px"
            },
            "QComboBox QAbstractItemView": {
                "background-color": "#e0e0e5",
                "selection-background-color": "#cfd8dc",
                "selection-color": "#1a1a1a",
                "color": "#2c2c2c",
                "border": "1px solid #b4b4b4"
            },
            "QComboBox::drop-down": {
                "subcontrol-origin": "padding",
                "subcontrol-position": "top right",
                "width": "20px",
                "background-color": "#cfd8dc",
                "border-left": "1px solid #a0a0a0",
                "border-top-right-radius": "4px",
                "border-bottom-right-radius": "4px"
            },
            "QComboBox::down-arrow": {
                "width": "10px",
                "height": "10px",
                "image": "none"
            },
            "QLineEdit": {
                "font": f"{font_spec}",
                "background-color": "#ffffff",
                "color": "#2c2c2c",
                "border": "1px solid #b4b4b4",
                "border-radius": "4px",
                "padding": "2px 6px"
            },
            "QLineEdit:hover": {
                "border": "1px solid #90a4ae"
            },
            "QLineEdit:focus": {
                "border": "1px solid #90a4ae",
                "background-color": "#f0f2f5"
            },
            "QToolTip": {
                "background-color": "#e0e0e5",
                "color": "#1a1a1a",
                "border": "1px solid #b4b4b4"
            }
        },
        "neon_rain": {
            "QDialog, QWidget": {
                "font": f"{font_spec}",
                "background-color": "#12131a",  # dark slate
                "color": "#d0d0ff"
            },
            "QFrame#StyledFrame": {
                "background-color": "#1c1e2a",
                "border": "1px solid #3a3f55",
                "border-radius": "4px"
            },
            "QLabel": {
                "font": f"{font_spec}",
                "color": "#d0d0ff"
            },
            "QLabel#Title": {
                "font-weight": "700",
                "color": "#a678f4"  # violet glow
            },
            "QPushButton": {
                "font": f"{font_spec}",
                "background-color": "#2980b9",
                "color": "#ffffff",
                "border": "1px solid #145374",
                "border-radius": "4px"
            },
            "QPushButton:hover": {
                "background-color": "#3498db"
            },
            "QPushButton:pressed": {
                "background-color": "#1d5a83"
            },
            "QComboBox": {
                "background-color": "#1c1e2a",
                "color": "#d0d0ff",
                "border": "1px solid #3a3f55",
                "border-radius": "4px",
                "padding": "2px 6px"
            },
            "QComboBox QAbstractItemView": {
                "background-color": "#26293d",
                "selection-background-color": "#2980b9",
                "selection-color": "#ffffff",
                "border": "1px solid #3a3f55"
            },
            "QLineEdit": {
                "background-color": "#10121a",
                "color": "#d0d0ff",
                "border": "1px solid #3a3f55",
                "border-radius": "4px",
                "padding": "2px 6px"
            },
            "QLineEdit:focus": {
                "border": "1px solid #2980b9"
            },
            "QToolTip": {
                "background-color": "#26293d",
                "color": "#ffffff",
                "border": "1px solid #3a3f55"
            }
        },
        "plain_light": {
            "QDialog, QWidget": {
                "font": f"{font_spec}",
                "background-color": "#ffffff",
                "color": "#1a1a1a"
            },
            "QFrame#StyledFrame": {
                "background-color": "#f0f0f0",
                "border": "1px solid #d0d0d0",
                "border-radius": "4px"
            },
            "QLabel": {
                "font": f"{font_spec}",
                "color": "#1a1a1a"
            },
            "QLabel#Title": {
                "font-weight": "700",
                "color": "#000000"
            },
            "QPushButton": {
                "font": f"{font_spec}",
                "background-color": "#e0e0e0",
                "color": "#000000",
                "border": "1px solid #b0b0b0",
                "border-radius": "4px"
            },
            "QPushButton:hover": {
                "background-color": "#d6d6d6"
            },
            "QPushButton:pressed": {
                "background-color": "#bfbfbf"
            },
            "QComboBox": {
                "font": f"{font_spec}",
                "background-color": "#ffffff",
                "color": "#1a1a1a",
                "border": "1px solid #d0d0d0",
                "border-radius": "4px",
                "padding": "2px 6px"
            },
            "QComboBox QAbstractItemView": {
                "background-color": "#f7f7f7",
                "selection-background-color": "#e0e0e0",
                "selection-color": "#000000",
                "border": "1px solid #d0d0d0"
            },
            "QLineEdit": {
                "font": f"{font_spec}",
                "background-color": "#ffffff",
                "color": "#1a1a1a",
                "border": "1px solid #d0d0d0",
                "border-radius": "4px",
                "padding": "2px 6px"
            },
            "QLineEdit:focus": {
                "border": "1px solid #a0a0a0"
            },
            "QToolTip": {
                "background-color": "#f0f0f0",
                "color": "#000000",
                "border": "1px solid #d0d0d0"
            }
        },
        "plain_dark": {
            "QDialog, QWidget": {
                "font": f"{font_spec}",
                "background-color": "#1e1e1e",
                "color": "#f0f0f0"
            },
            "QFrame#StyledFrame": {
                "background-color": "#2a2a2a",
                "border": "1px solid #3c3c3c",
                "border-radius": "4px"
            },
            "QLabel": {
                "font": f"{font_spec}",
                "color": "#f0f0f0"
            },
            "QLabel#Title": {
                "font-weight": "700",
                "color": "#ffffff"
            },
            "QPushButton": {
                "font": f"{font_spec}",
                "background-color": "#3a3a3a",
                "color": "#ffffff",
                "border": "1px solid #5a5a5a",
                "border-radius": "4px"
            },
            "QPushButton:hover": {
                "background-color": "#505050"
            },
            "QPushButton:pressed": {
                "background-color": "#2f2f2f"
            },
            "QComboBox": {
                "font": f"{font_spec}",
                "background-color": "#1e1e1e",
                "color": "#f0f0f0",
                "border": "1px solid #3c3c3c",
                "border-radius": "4px",
                "padding": "2px 6px"
            },
            "QComboBox QAbstractItemView": {
                "background-color": "#2a2a2a",
                "selection-background-color": "#3a3a3a",
                "selection-color": "#ffffff",
                "border": "1px solid #3c3c3c"
            },
            "QLineEdit": {
                "font": f"{font_spec}",
                "background-color": "#1a1a1a",
                "color": "#f0f0f0",
                "border": "1px solid #3c3c3c",
                "border-radius": "4px",
                "padding": "2px 6px"
            },
            "QLineEdit:focus": {
                "border": "1px solid #707070"
            },
            "QToolTip": {
                "background-color": "#2a2a2a",
                "color": "#ffffff",
                "border": "1px solid #3c3c3c"
            }
        },
        "forest_theme": {
            "QDialog, QWidget": {
                "font": f"{font_spec}",
                "background-color": "#e9f5e1",  # Soft pale green
                "color": "#2e3d2f"              # Forest green text
            },
            "QFrame#StyledFrame": {
                "background-color": "#d6e8c6",
                "border": "1px solid #8c9e82",
                "border-radius": "4px"
            },
            "QLabel": {
                "font": f"{font_spec}",
                "color": "#2e3d2f"
            },
            "QLabel#Title": {
                "font-weight": "700",
                "color": "#1f2e20"
            },
            "QPushButton": {
                "font": f"{font_spec}",
                "background-color": "#739e5e",
                "color": "#ffffff",
                "border": "1px solid #5b7f4c",
                "border-radius": "4px"
            },
            "QPushButton:hover": {
                "background-color": "#85b06c",
                "border": "2px solid #4f6e3f"
            },
            "QPushButton:pressed": {
                "background-color": "#5b7f4c",
                "border": "2px inset #3e5834"
            },
            "QComboBox": {
                "font": f"{font_spec}",
                "background-color": "#e9f5e1",
                "color": "#2e3d2f",
                "border": "1px solid #8c9e82",
                "border-radius": "4px",
                "padding": "2px 6px"
            },
            "QComboBox QAbstractItemView": {
                "background-color": "#d6e8c6",
                "selection-background-color": "#739e5e",
                "selection-color": "#ffffff",
                "color": "#2e3d2f",
                "border": "1px solid #8c9e82"
            },
            "QComboBox::drop-down": {
                "subcontrol-origin": "padding",
                "subcontrol-position": "top right",
                "width": "20px",
                "background-color": "#739e5e",
                "border-left": "1px solid #5b7f4c",
                "border-top-right-radius": "4px",
                "border-bottom-right-radius": "4px"
            },
            "QComboBox::down-arrow": {
                "width": "10px",
                "height": "10px",
                "image": "none"
            },
            "QLineEdit": {
                "font": f"{font_spec}",
                "background-color": "#ffffff",
                "color": "#2e3d2f",
                "border": "1px solid #8c9e82",
                "border-radius": "4px",
                "padding": "2px 6px"
            },
            "QLineEdit:hover": {
                "border": "1px solid #739e5e"
            },
            "QLineEdit:focus": {
                "border": "1px solid #5b7f4c",
                "background-color": "#f3fbec"
            },
            "QToolTip": {
                "background-color": "#d6e8c6",
                "color": "#2e3d2f",
                "border": "1px solid #8c9e82"
            }
        },
        "forest_bark": {
            "QDialog, QWidget": {
                "font": f"{font_spec}",
                "background-color": "#2b2a27",  # Deep bark brown
                "color": "#e0e0d8"              # Warm light beige text
            },
            "QFrame#StyledFrame": {
                "background-color": "#3a382f",  # Tree bark midtone
                "border": "1px solid #555248",
                "border-radius": "4px"
            },
            "QLabel": {
                "font": f"{font_spec}",
                "color": "#dcdccf"
            },
            "QLabel#Title": {
                "font-weight": "700",
                "color": "#ffffff"
            },
            "QPushButton": {
                "font": f"{font_spec}",
                "background-color": "#5c6e58",  # Moss green
                "color": "#ffffff",
                "border": "1px solid #3e4f3c",
                "border-radius": "4px"
            },
            "QPushButton:hover": {
                "background-color": "#6e826a",
                "border": "2px solid #4c5e47"
            },
            "QPushButton:pressed": {
                "background-color": "#3e4f3c",
                "border": "2px inset #2e3a2c"
            },
            "QComboBox": {
                "font": f"{font_spec}",
                "background-color": "#2b2a27",
                "color": "#e0e0d8",
                "border": "1px solid #555248",
                "border-radius": "4px",
                "padding": "2px 6px"
            },
            "QComboBox QAbstractItemView": {
                "background-color": "#3a382f",
                "selection-background-color": "#5c6e58",
                "selection-color": "#ffffff",
                "color": "#e0e0d8",
                "border": "1px solid #555248"
            },
            "QComboBox::drop-down": {
                "subcontrol-origin": "padding",
                "subcontrol-position": "top right",
                "width": "20px",
                "background-color": "#5c6e58",
                "border-left": "1px solid #3e4f3c",
                "border-top-right-radius": "4px",
                "border-bottom-right-radius": "4px"
            },
            "QComboBox::down-arrow": {
                "width": "10px",
                "height": "10px",
                "image": "none"
            },
            "QLineEdit": {
                "font": f"{font_spec}",
                "background-color": "#1f1e1b",
                "color": "#e0e0d8",
                "border": "1px solid #555248",
                "border-radius": "4px",
                "padding": "2px 6px"
            },
            "QLineEdit:hover": {
                "border": "1px solid #6e826a"
            },
            "QLineEdit:focus": {
                "border": "1px solid #5c6e58",
                "background-color": "#2d2c29"
            },
            "QToolTip": {
                "background-color": "#3a382f",
                "color": "#ffffff",
                "border": "1px solid #555248"
            }
        }

    }
    stylesheet = dict_to_stylesheet(themes[theme])
    return stylesheet
