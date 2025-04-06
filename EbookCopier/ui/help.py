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
                "1: The Book You Wish To Copy Is Open And Is The Active Tab In Microsoft Edge\n\n"
                "2: Microsoft Edge Is In Fullscreen\n\n"
                "3: You Are On The First Page Of The Book\n\n"
                "4: You Know How Big To Set The Capture Area\n\n"
                "5: Article Button Is Set To Never\n\n"
                "You Can Pause By Pressing The Esc Key\n\n"
                "Press Help for More Information..\n"
        )
        help =[
            {'label': 
                "You May Need To Press \"Arrow Up\" Or \"Arrow Down\" On The Keyboard To Open And Close The Menu Bar"
                "Set Your Page View By Pressing The Circled Button "
                "This Will Change Wether You See Two Pages At Once Or One Page", 
                'image_path': "images/libby_page_view_button.png"
            },
            {'label': 
                "Next You Can Select The Appearance Button To Adjust Font, Theme, And Remove Article Button", 
                'image_path': "images/libby_apperance_button.png"
            },
            {"label": 
                "Ensure The Article Button Is Set To Never Under Apperance"
                "You Can Change Font Size, Color, Etc. Just Remember How Wide To Draw Your Capture Area", 
                "image_path": "images/libby_article_button.png"
            },
            {"label": 
                "Ensure All Menus Are Closed Before You Continue"
                "You May Need To Click The Carrot Button \"^\" To Close The Appearance Menu"
                "And/Or Press The \"Up Arrow\" Or \"Down Arrow\" To Close The Top Menu On Libby"},
            {"label":
                "Keep In Mind How Big You Need To Make The Capture Area After Making Any Changes"}]
        
    elif selected_site.lower() == "hoopla":
        message = (
                "Please Ensure The Following:\n"
                "1: The Book You Wish To Copy Is Open And Is The Active Tab In Microsoft Edge\n"
                "2: Microsoft Edge Is In Fullscreen\n"
                "3: Ensure You Have The Correct Page Count When The Book Is Open In FullScreen (FN+F11)\n"
                "4: You Are On The First Page Of The Book\n"
                "5: Calculating Pages Has Dissapeared From The Bottom Of The Page\n"
                "Hoopla Screen May Unload During The Next Step, It Should Load By The Time The Book Copy Starts\n"
                "You Can Pause By Pressing The ESC key\n"
                "Press Help for More Informatiion")
        
        help = [
            {"label":
                "If You Wish To Change Color Scheme, Or Text Size Of The Book Do So Now"
                "By Pressing The Menu Button",
                "image_path": "images/hoopla_menu_button.png"},
             {"label": 
                "Click The Settiings Button",
                "image_path": "images/hoopla_settings_button.png"},
              {"label": 
                "Here You Can Change Theme, Text Size, Line Spacing Etc To Your Preference"},
               {"label": 
                    "Close Settings When Done And Wait For Calculating Pages To Dissapear At The Bottom",
                    "image_path": "images/hoopla_calculating_pages.png"},
                {"label":
                    "Keep In Mind How Big You Need To Make The Capture Area After Making Any Changes"}]
    return message, help

 