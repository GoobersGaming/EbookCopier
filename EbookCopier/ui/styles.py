from tkinter import ttk


def configure_styles(root):
    """Configure all application styles"""
    style = ttk.Style(root)
    # Modern theme
    style.theme_use("clam")

    # Main windw background
    root.configure(bg="#828fbb")

    # Frame Styles
    style.configure("Container.TFrame",
                    background="#828fbb",
                    borderwidth=1,
                    bordercolor="#e0e0e0",
                    padding=10)
    # Label styling
    style.configure("TLabel",
                    font=("Verdana", 10),
                    padding=5)

    style.configure("Title.TLabel",
                    font=("Verdana", 12, "bold"),
                    foreground="black",
                    background="#828fbb")

    # Button styling
    style.configure("TButton",
                    font=("Verdana", 10, "bold"),
                    padding=10,
                    background="#4a6baf",
                    foreground="white",
                    borderwidth=4,
                    bordercolor="#2a3a56",
                    relief="raised")

    style.map("TButton",
              background=[("active", "#3a5a9f")],
              foreground=[("active", "white")])

    # Disabled controls
    style.map("Disabled.TButton",
              background=[("disabled", "#d9d9d9")],
              foreground=[("disabled", "#a0a0a0")])

    # Entry styles
    style.configure("TEntry",
                    font=("Verdana", 10),
                    padding=5,
                    bordercolor="#d9d9d9",
                    lightcolor="#d9d9d9",
                    darkcolor="#d9d9d9")

    style.configure("TCombobox",
                    font=("Verdana", 10),
                    arrowsize=22,
                    fieldbackground="#738cd6",
                    background="#3a5a9f",
                    foreground="white",
                    selectbackground="#738cd6",
                    padding=5)

    style.map("TCombobox",
              fieldbackground=[("!disabled", "#738cd6"),  # Normal state
                               ("disabled", "#3a5a9f"),    # Disabled state
                               ("readonly", "#738cd6")],    # Readonly state

              foreground=[("!disabled", "white"),
                          ("disabled", "white"),
                          ("readonly", "white")],
              background=[("!disabled", "#738cd6"),
                          ("disabled", "#3a5a9f"),
                          ("readonly", "#738cd6")],
              selectbackground=[("!disabled", "#738cd6"),
                                ("disabled", "#3a5a9f"),
                                ("readonly", "#738cd6")])

    # Special styles
    style.configure("Dupe.TFrame", background="#828fbb")

    style.configure("Dupe.TLabelframe",
                    background="#828fbb",
                    bordercolor="#4a6baf",
                    foreground="#70facb",
                    relief="flat",
                    borderwidth=0)

    style.configure("Dupe.TLabelframe.Label",
                    font=("Verdana", 12, "bold", "underline"),
                    foreground="black",
                    background="#828fbb")

    style.configure("Hel.TLabel",
                    font=("Verdana", 12),
                    foreground="black",
                    background="#828fbb",
                    padding=5)
