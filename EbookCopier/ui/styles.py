import tkinter as tk
from tkinter import ttk



def configure_styles(root):
    """Configure all application styles"""
    style = ttk.Style(root)
        # Modern theme
    style.theme_use('clam')

    # Main windw background
    root.configure(bg="#f0f0f0")
    
    # Frame Styles
    style.configure("Container.TFrame",
                    background="#ffffff",
                    borderwidth=1,
                    relief="solid",
                    bordercolor="#e0e0e0",
                    padding=10)
    # Label styling
    style.configure('TLabel', 
                    font=('Segoe UI', 10),
                    padding=5)
    
    style.configure("Title.TLabel",
                    font=('Segoe UI', 12, 'bold'),
                    foreground='#333333')
    
    # Button styling
    style.configure('TButton',
                    font=('Segoe UI', 10, 'bold'),
                    padding=6,
                    background='#4a6baf',
                    foreground='white',
                    borderwidth=1)
    
    style.map('TButton',
            background=[('active', '#3a5a9f')],
            foreground=[("active", "white")])
    
    # Disabled controls
    style.map('Disabled.TButton',
             background=[('disabled', '#d9d9d9')],
             foreground=[('disabled', '#a0a0a0')])
    
    
    # Entry styles
    style.configure('TEntry',
                  font=('Segoe UI', 10),
                  padding=5,
                  bordercolor='#d9d9d9',
                  lightcolor='#d9d9d9',
                  darkcolor='#d9d9d9')
    
    style.configure('TCombobox',
                  font=('Segoe UI', 10),
                  arrowsize=22,
                  fieldbackground="#738cd6",
                  background="#3a5a9f",
                  foreground="white",
                  selectbackground="#738cd6",
                  padding=5)
    
    style.map('TCombobox',
        fieldbackground=[
            ('!disabled', '#738cd6'),  # Normal state
            ('disabled', '#3a5a9f'),    # Disabled state
            ('readonly', '#738cd6')     # Readonly state
        ],
        foreground=[
            ('!disabled', 'white'),
            ('disabled', 'white'),
            ('readonly', 'white')
        ],
        background=[
            ('!disabled', '#738cd6'),
            ('disabled', '#3a5a9f'),
            ('readonly', '#738cd6')
        ],
        selectbackground=[
            ('!disabled', '#738cd6'),
            ('disabled', '#3a5a9f'),
            ('readonly', '#738cd6')
        ]
    )
    
    # Special styles
    style.configure('Image.TLabel',
                  background='#ffffff',
                  borderwidth=1,
                  relief='solid',
                  bordercolor='#d9d9d9')