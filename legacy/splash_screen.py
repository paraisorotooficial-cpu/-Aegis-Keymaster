"""
Splash Screen Module
Displays the KeyMaster Pro banner on startup
"""
import customtkinter as ctk
from PIL import Image
import os


class SplashScreen(ctk.CTkToplevel):
    """Splash screen with banner image"""
    
    def __init__(self, parent, duration=2500):
        super().__init__(parent)
        
        self.duration = duration
        
        # Window configuration
        self.title("")
        self.overrideredirect(True)  # Remove window decorations
        
        # Get screen dimensions
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        
        # Banner dimensions
        banner_width = 1024
        banner_height = 512
        
        # Calculate position (center of screen)
        x = (screen_width - banner_width) // 2
        y = (screen_height - banner_height) // 2
        
        self.geometry(f"{banner_width}x{banner_height}+{x}+{y}")
        self.configure(fg_color="black")
        
        # Load and display banner
        self._load_banner()
        
        # Auto-close after duration
        self.after(duration, self.close_splash)
        
        # Make sure splash is on top
        self.lift()
        self.attributes('-topmost', True)
        
        # Center the parent window after splash
        self.after(duration + 100, lambda: self._center_main_window(parent))
    
    def _load_banner(self):
        """Load and display the banner image"""
        banner_path = os.path.join("assets", "banner.png")
        
        # Fallback if assets folder doesn't exist
        if not os.path.exists(banner_path):
            banner_path = "banner.png"
        
        try:
            # Load image
            banner_image = Image.open(banner_path)
            
            # Create CTkImage
            ctk_banner = ctk.CTkImage(
                light_image=banner_image,
                dark_image=banner_image,
                size=(1024, 512)
            )
            
            # Display in label
            banner_label = ctk.CTkLabel(
                self,
                image=ctk_banner,
                text=""
            )
            banner_label.pack(fill="both", expand=True)
            
            # Add subtle loading animation text
            loading_label = ctk.CTkLabel(
                self,
                text="Cargando...",
                font=("Roboto", 14),
                text_color="#3B8ED0"
            )
            loading_label.place(relx=0.5, rely=0.92, anchor="center")
            
            # Animate loading dots
            self._animate_loading(loading_label)
            
        except Exception as e:
            # Fallback: Show text if image can't be loaded
            error_label = ctk.CTkLabel(
                self,
                text="KeyMaster PRO\nMASTER THE DIGITAL REALM",
                font=("Roboto Black", 32),
                text_color="#FF4444"
            )
            error_label.pack(expand=True)
            
            subtitle = ctk.CTkLabel(
                self,
                text="LUBUNTU EDITION",
                font=("Roboto", 16),
                text_color="#9B59B6"
            )
            subtitle.pack(pady=(0, 50))
            
            print(f"Could not load banner image: {e}")
    
    def _animate_loading(self, label, dots=0):
        """Animate loading text"""
        if not self.winfo_exists():
            return
        
        dots = (dots + 1) % 4
        text = "Cargando" + "." * dots
        label.configure(text=text)
        
        self.after(400, lambda: self._animate_loading(label, dots))
    
    def _center_main_window(self, parent):
        """Center the main window after splash closes"""
        if parent.winfo_exists():
            parent.update_idletasks()
            
            # Get screen dimensions
            screen_width = parent.winfo_screenwidth()
            screen_height = parent.winfo_screenheight()
            
            # Get window dimensions
            window_width = parent.winfo_width()
            window_height = parent.winfo_height()
            
            # Calculate position
            x = (screen_width - window_width) // 2
            y = (screen_height - window_height) // 2
            
            parent.geometry(f"+{x}+{y}")
    
    def close_splash(self):
        """Close the splash screen"""
        self.destroy()


def show_splash(parent, duration=2500):
    """Show splash screen and return it"""
    splash = SplashScreen(parent, duration)
    return splash