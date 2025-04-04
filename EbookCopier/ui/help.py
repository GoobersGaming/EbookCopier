import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
from utils import logs
from ui.styles import configure_styles

class NavigationPopup:
    def __init__(self, root, items):
        self.root = root
        self.items = items
        self.current_index = 0
        
        # Create popup window
        self.popup = tk.Toplevel(root)
        self.popup.title("Help")
        self.popup.geometry("500x500")
        self.popup.resizable(False, False)
        configure_styles(self.popup)
        
        # Create main container
        self.container = ttk.Frame(self.popup)
        self.container.pack(expand=True, fill=tk.BOTH, padx=20, pady=20)
        
        # Label
        #self.label = ttk.Label(self.container, text="", font=('Arial', 12))
        self.label = ttk.Label(self.container, text="", font=("", 12))
        self.label.pack(pady=10)
        
        # Image display (will be empty if no image)
        self.image_label = ttk.Label(self.container)
        self.image_label.pack(pady=10)
        
        # Button frame
        self.button_frame = ttk.Frame(self.container)
        self.button_frame.pack(pady=20)
        
        # Buttons
        self.prev_button = ttk.Button(self.button_frame, text="Previous", command=self.show_previous)
        self.prev_button.pack(side=tk.LEFT, padx=5)
        
        self.next_button = ttk.Button(self.button_frame, text="Next", command=self.show_next)
        self.next_button.pack(side=tk.LEFT, padx=5)
        
        self.cancel_button = ttk.Button(self.button_frame, text="Cancel", command=self.close_popup)
        self.cancel_button.pack(side=tk.LEFT, padx=5)
        
        # Load first item
        self.show_item()
    
    def show_item(self):
        item = self.items[self.current_index]
        
        # Update label
        self.label.config(text=item['label'])
        
        # Display image if provided, otherwise clear the image area
        if 'image_path' in item and item['image_path'] is not None:
            try:
                image = Image.open(item['image_path'])
                image = image.resize((300, 200), Image.Resampling.LANCZOS)
                photo = ImageTk.PhotoImage(image)
                self.image_label.config(image=photo)
                self.image_label.image = photo  # Keep reference
            except Exception as e:
                logs.LOGGER.error(f"Error loading image: {e}")
                self.image_label.config(image='')
        else:
            self.image_label.config(image='')
        
        # Update button states
        self.prev_button['state'] = tk.NORMAL if self.current_index > 0 else tk.DISABLED
        
        # Check if last item
        if self.current_index == len(self.items) - 1:
            self.next_button.config(text="Done", command=self.close_popup)
            self.cancel_button.pack_forget()
        else:
            self.next_button.config(text="Next", command=self.show_next)
            self.cancel_button.pack(side=tk.LEFT, padx=5)
    
    def show_next(self):
        if self.current_index < len(self.items) - 1:
            self.current_index += 1
            self.show_item()
    
    def show_previous(self):
        if self.current_index > 0:
            self.current_index -= 1
            self.show_item()
    
    def close_popup(self):
        self.popup.destroy()


def cont_message(selected_site, page_view):
    message = None
    help = None
    if selected_site.lower() == "libby":
        message = (
                "Please Ensure The Following:\n\n"
                "1: The Book You Wish To Copy Is Open And Is The Active Tab In Microsoft Edge\n"
                f"2: The Book is set to view {page_view} at once\n"
                "3: You Are On The First Page Of The Book\n"
                "4: Article Button Is Set To Never\n"
                "5: Microsoft Edge Is In Fullscreen\n"
                "6: Microsoft Edge Is Open On The Correct Display, If Not Please Move It Before You Continue\n\n"
                "You Can Pause By Pressing The Esc Key"
                "Press Help for More Informatiion"
        )
        help =[
            {'label': 
                "You May Need To Press \"Arrow Up\" Or \"Arrow Down\" To Open And Close The Top Menu Bar\n "
                "Set Your Page View By Pressing The Circled Button\n "
                "This Will Change Wether You See Two Pages At Once Or One Page", 
                'image_path': "images/libby_page_view_button.png"
            },
            {'label': 
                "Next Select The Appearance Button A Menu Should Appear At The Bottom Of The Screen", 
                'image_path': "images/libby_apperance_button.png"
            },
            {"label": 
                "Scroll Down To The Bottom Of The Apperance Menu And Set Article Button To Never\n"
                "You May Change The Background Color If You Wish, But It Shouldnt Matter", 
                "image_path": "images/libby_article_button.png"
            },
            {"label": 
                "Please Ensure All Menus In Libby Are Closed Before Proceeding.\n"
                "You May Need To Click The Carrot Button \"^\" To Close The Appearance Menu\n"
                "And/Or Press The \"Up Arrow\" Or \"Down Arrow\" To Close The Top Menu On Libby"}]
        
    elif selected_site.lower() == "hoopla":
        message = (
                "Please Ensure The Following:\n\n"
                "1: The Book You Wish To Copy Is Open And Is The Active Tab In Microsoft Edge\n\n"
                "2: Ensure The Page Count Is Correct, Page Count Is Differfent In Full Screen, Cancel If Not\n\n"
                "3: You Are On The First Page Of The Book\n\n"
                "4: Calculating Pages Has Dissapeared From The Bottom Of The Page\n\n"
                "5: Microsoft Edge Is In Fullscreen\n\n"
                "6: Microsoft Edge Is Open On The Correct Display, If Not Please Move It Before You Continue\n\n"
                "Hoopla Screen May Unload During The Next Step, It Should Load By The Time The Book Copy Starts\n\n"
                "Once Copying Starts You Can Pause\\Cancel By Pressing The ESC Key.\n\n"
                "Press Help for More Informatiion")
        
        help = [
            {"label":
                "If You Wish To Change Color Scheme, Or Text Size Of The Book Do So Now\n"
                "By Pressing The Menu Button",
                "image_path": "images/hoopla_menu_button.png"},
             {"label": 
                "Click The Settiings Button",
                "image_path": "images/hoopla_settings_button.png"},
              {"label": 
                "Here You Can Change Theme, Text Size, Line Spacing Etc To Your Preference"},
               {"label": 
                    "Close Settings When Done And Wait For Calculating Pages To Dissapear At The Bottom",
                    "image_path": "images/hoopla_calculating_pages.png"}]
    return message, help

 