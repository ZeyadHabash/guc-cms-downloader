import customtkinter as ctk
import requests
from requests_ntlm import HttpNtlmAuth
from bs4 import BeautifulSoup
from main import download_content, get_types, login, get_courses, update_course_url, get_course_info_from_formatted_name
from main import get_total_files
import threading
import time
from datetime import datetime
import math
import os
from tkinter import filedialog
from dotenv import load_dotenv, set_key

# Configure appearance
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

class LoadingSpinner(ctk.CTkFrame):
    """Custom animated loading spinner widget"""
    def __init__(self, master, size=60, color="#4CAF50", **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        
        self.size = size
        self.color = color
        self.angle = 0
        self.is_animating = False
        
        # Create canvas for the spinner
        self.canvas = ctk.CTkCanvas(
            self, 
            width=size, 
            height=size, 
            bg="#2b2b2b",  # Dark background that matches dark theme
            highlightthickness=0
        )
        self.canvas.pack(expand=True)
        
        # Draw the spinner
        self.draw_spinner()
    
    def draw_spinner(self):
        """Draw the spinner on the canvas"""
        self.canvas.delete("all")
        
        center_x = self.size // 2
        center_y = self.size // 2
        radius = (self.size // 2) - 5
        
        # Draw 8 dots around a circle
        for i in range(8):
            angle = self.angle + (i * 45)
            x = center_x + radius * math.cos(math.radians(angle))
            y = center_y + radius * math.sin(math.radians(angle))
            
            # Calculate opacity based on position (fade effect)
            opacity = 1.0 - (i * 0.1)
            opacity = max(0.2, opacity)  # Minimum opacity
            
            # Create color with opacity
            color_hex = self.color.lstrip('#')
            r = int(color_hex[0:2], 16)
            g = int(color_hex[2:4], 16)
            b = int(color_hex[4:6], 16)
            
            # Apply opacity
            r = int(r * opacity)
            g = int(g * opacity)
            b = int(b * opacity)
            
            dot_color = f'#{r:02x}{g:02x}{b:02x}'
            
            # Draw dot
            dot_size = 4 if i == 0 else 3  # First dot is slightly larger
            self.canvas.create_oval(
                x - dot_size, y - dot_size,
                x + dot_size, y + dot_size,
                fill=dot_color, outline=""
            )
    
    def start_animation(self):
        """Start the spinning animation"""
        self.is_animating = True
        self.animate()
    
    def stop_animation(self):
        """Stop the spinning animation"""
        self.is_animating = False
    
    def animate(self):
        """Animate the spinner"""
        if self.is_animating:
            self.angle = (self.angle + 10) % 360
            self.draw_spinner()
            self.after(50, self.animate)  # Update every 50ms for smooth animation

class ModernCMSDownloader:
    def __init__(self):
        self.root = ctk.CTk()
        self.root.geometry("900x1000")
        self.root.title("GUC CMS Downloader")
        self.root.resizable(True, True)
        self.root.minsize(800, 600)  # Set minimum window size
        
        # Center the window
        self.center_window()
        
        # Ensure .env exists and load it
        self.ensure_env_file()
        load_dotenv()
        
        # Variables
        self.input_username = ""
        self.input_password = ""
        self.all_types = ["--"]
        self.page_index = 0
        self.all_checkboxes = []
        self.checkboxes = {}
        self.pages = []
        self.current_download_thread = None
        self.is_downloading = False
        self.output_folder = None
        self.load_last_output_folder()
        
        # Create pages
        self.create_login_page()
        self.create_courses_page()
        self.create_download_page()
        self.create_loading_page()
        
        # Initialize pages list
        self.pages = [self.login_frame, self.courses_frame, self.download_frame, self.loading_frame]
        
        # Check for saved credentials
        self.check_saved_credentials()
        
        # Start the app
        self.root.mainloop()
    
    def center_window(self):
        """Center the window on screen"""
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f'{width}x{height}+{x}+{y}')
    
    def create_login_page(self):
        """Create the login page with modern design"""
        self.login_frame = ctk.CTkFrame(master=self.root, fg_color="transparent")
        
        # Main container (now scrollable)
        main_container = ctk.CTkScrollableFrame(master=self.login_frame, corner_radius=20)
        main_container.pack(pady=40, padx=40, fill="both", expand=True)
        
        # Configure grid weights for responsiveness
        main_container.grid_columnconfigure(0, weight=1)
        main_container.grid_rowconfigure(1, weight=1)  # Form container should expand
        
        # Header
        header_frame = ctk.CTkFrame(master=main_container, fg_color="transparent")
        header_frame.pack(pady=(40, 20), padx=40, fill="x")
        
        # Logo/Icon placeholder
        logo_label = ctk.CTkLabel(
            master=header_frame, 
            text="📚", 
            font=ctk.CTkFont(size=48)
        )
        logo_label.pack(pady=(0, 10))
        
        title_label = ctk.CTkLabel(
            master=header_frame, 
            text="GUC CMS Downloader",
            font=ctk.CTkFont(size=28, weight="bold")
        )
        title_label.pack()
        
        subtitle_label = ctk.CTkLabel(
            master=header_frame, 
            text="Download your course materials easily",
            font=ctk.CTkFont(size=14),
            text_color="gray"
        )
        subtitle_label.pack(pady=(5, 0))
        
        # Form container
        form_container = ctk.CTkFrame(master=main_container, fg_color="transparent")
        form_container.pack(pady=20, padx=40, fill="both", expand=True)
        
        # Configure grid weights for form responsiveness
        form_container.grid_columnconfigure(0, weight=1)
        
        # Username field
        username_label = ctk.CTkLabel(
            master=form_container,
            text="Username",
            font=ctk.CTkFont(size=14, weight="bold"),
            anchor="w"
        )
        username_label.pack(pady=(0, 5), padx=5, anchor="w")
        
        self.username_entry = ctk.CTkEntry(
            master=form_container,
            placeholder_text="Enter your GUC username",
            height=45,
            font=ctk.CTkFont(size=14)
        )
        self.username_entry.pack(pady=(0, 20), padx=5, fill="x")
        
        # Password field
        password_label = ctk.CTkLabel(
            master=form_container,
            text="Password",
            font=ctk.CTkFont(size=14, weight="bold"),
            anchor="w"
        )
        password_label.pack(pady=(0, 5), padx=5, anchor="w")
        
        self.password_entry = ctk.CTkEntry(
            master=form_container,
            placeholder_text="Enter your password",
            show="•",
            height=45,
            font=ctk.CTkFont(size=14)
        )
        self.password_entry.pack(pady=(0, 30), padx=5, fill="x")
        
        # Error label
        self.error_label = ctk.CTkLabel(
            master=form_container,
            text="Invalid credentials. Please try again.",
            font=ctk.CTkFont(size=12),
            text_color="#ff6b6b"
        )
        
        # Login button
        self.login_button = ctk.CTkButton(
            master=form_container,
            text="Sign In",
            command=self.login_gui,
            height=50,
            font=ctk.CTkFont(size=16, weight="bold"),
            fg_color="#4CAF50",
            hover_color="#45a049"
        )
        self.login_button.pack(pady=(0, 20), padx=5, fill="x")
        
        # Footer
        footer_label = ctk.CTkLabel(
            master=main_container,
            text="© 2025 GUC CMS Downloader",
            font=ctk.CTkFont(size=10),
            text_color="gray"
        )
        footer_label.pack(side="bottom", pady=20)
    
    def create_courses_page(self):
        """Create the course selection page"""
        self.courses_frame = ctk.CTkFrame(master=self.root, fg_color="transparent")
        
        # Main container (now scrollable)
        main_container = ctk.CTkScrollableFrame(master=self.courses_frame, corner_radius=20, height=600)
        main_container.pack(pady=40, padx=40, fill="both", expand=True)
        
        # Configure grid weights for responsiveness
        main_container.grid_columnconfigure(0, weight=1)
        main_container.grid_rowconfigure(1, weight=1)  # Selection container should expand
        
        # Header
        header_frame = ctk.CTkFrame(master=main_container, fg_color="transparent")
        header_frame.pack(pady=(40, 20), padx=40, fill="x")
        
        title_label = ctk.CTkLabel(
            master=header_frame,
            text="Select Course",
            font=ctk.CTkFont(size=28, weight="bold")
        )
        title_label.pack()
        
        subtitle_label = ctk.CTkLabel(
            master=header_frame,
            text="Choose the course you want to download materials from",
            font=ctk.CTkFont(size=14),
            text_color="gray"
        )
        subtitle_label.pack(pady=(5, 0))
        
        # Course selection container
        selection_container = ctk.CTkFrame(master=main_container, fg_color="transparent")
        selection_container.pack(pady=40, padx=40, fill="x")
        
        course_label = ctk.CTkLabel(
            master=selection_container,
            text="Course",
            font=ctk.CTkFont(size=14, weight="bold"),
            anchor="w"
        )
        course_label.pack(pady=(0, 10), padx=5, anchor="w")
        
        self.course_select = ctk.CTkOptionMenu(
            selection_container,
            values=self.all_types,
            height=45,
            font=ctk.CTkFont(size=14),
            command=self.on_course_selection
        )
        self.course_select.pack(pady=(0, 30), padx=5, fill="x")
        
        # Buttons container
        buttons_container = ctk.CTkFrame(master=main_container, fg_color="transparent")
        buttons_container.pack(pady=20, padx=40, fill="x")
        
        # Configure grid weights for button layout  
        buttons_container.grid_columnconfigure(0, weight=1)
        buttons_container.grid_columnconfigure(1, weight=1)
        
        self.next_button = ctk.CTkButton(
            master=buttons_container,
            text="Continue",
            command=lambda: self.next_page(self.course_select.get()),
            height=50,
            font=ctk.CTkFont(size=16, weight="bold"),
            fg_color="#2196F3",
            hover_color="#1976D2"
        )
        self.next_button.grid(row=0, column=0, padx=(5, 2.5), pady=(0, 15), sticky="ew")
        
        self.download_all_button = ctk.CTkButton(
            master=buttons_container,
            text="Download All",
            command=self.download_all_courses,
            height=50,
            font=ctk.CTkFont(size=16, weight="bold"),
            fg_color="#4CAF50",
            hover_color="#45a049"
        )
        self.download_all_button.grid(row=0, column=1, padx=(2.5, 5), pady=(0, 15), sticky="ew")
        
        self.logout_button = ctk.CTkButton(
            master=buttons_container,
            text="Log Out",
            command=self.prev_page,
            height=45,
            font=ctk.CTkFont(size=14),
            fg_color="transparent",
            border_width=2,
            text_color="#ff6b6b",
            border_color="#ff6b6b",
            hover_color="#ff9999"
        )
        self.logout_button.grid(row=1, column=0, columnspan=2, padx=5, pady=(0, 0), sticky="ew")
    
    def create_download_page(self):
        """Create the download page with checkboxes and organization dropdown/toggles"""
        self.download_frame = ctk.CTkFrame(master=self.root, fg_color="transparent")
        
        # Main container (now scrollable)
        main_container = ctk.CTkScrollableFrame(master=self.download_frame, corner_radius=20, height=600)
        main_container.pack(pady=40, padx=40, fill="both", expand=True)
        
        # Header
        header_frame = ctk.CTkFrame(master=main_container, fg_color="transparent")
        header_frame.pack(pady=(40, 20), padx=40, fill="x")
        
        self.course_title_label = ctk.CTkLabel(
            master=header_frame,
            text="Course Name",
            font=ctk.CTkFont(size=24, weight="bold")
        )
        self.course_title_label.pack()
        
        subtitle_label = ctk.CTkLabel(
            master=header_frame,
            text="Select the content types you want to download",
            font=ctk.CTkFont(size=14),
            text_color="gray"
        )
        subtitle_label.pack(pady=(5, 0))
        
        # Organization dropdown and toggles
        org_label = ctk.CTkLabel(
            master=header_frame,
            text="Folder Organization:",
            font=ctk.CTkFont(size=14, weight="bold"),
            anchor="w"
        )
        org_label.pack(pady=(18, 2), anchor="w")
        self.org_modes = ["By type", "By week", "Flat"]
        self.org_mode_map = {"By type": "type", "By week": "week", "Flat": "none"}
        self.org_mode = "type"  # Default
        self.include_week = True
        self.include_type = False
        # Add week description toggle (default False)
        self.week_description_toggle_var = ctk.BooleanVar(value=False)
        def set_toggle_defaults(mode):
            if mode == "type":
                self.include_week = True
                self.include_type = False
            elif mode == "week":
                self.include_week = False
                self.include_type = True
            else:
                self.include_week = True
                self.include_type = True
            self.week_toggle_var.set(self.include_week)
            self.type_toggle_var.set(self.include_type)
            self.week_description_toggle_var.set(False)  # Always reset to default (unchecked)
        def on_org_mode_select(choice):
            self.org_mode = self.org_mode_map[choice]
            set_toggle_defaults(self.org_mode)
            # Re-pack toggles to ensure spacing is applied after dropdown changes
            self.week_toggle.pack_forget()
            self.type_toggle.pack_forget()
            self.week_description_toggle.pack_forget()
            self.week_toggle.pack(pady=(10, 0), anchor="w")
            self.type_toggle.pack(pady=(8, 0), anchor="w")
            self.week_description_toggle.pack(pady=(8, 0), anchor="w")
        self.org_dropdown = ctk.CTkOptionMenu(
            master=header_frame,
            values=self.org_modes,
            command=on_org_mode_select
        )
        self.org_dropdown.set("By type")
        self.org_dropdown.pack(pady=(0, 10), anchor="w")
        # Toggles for week/type in filename
        self.week_toggle_var = ctk.BooleanVar(value=True)
        self.type_toggle_var = ctk.BooleanVar(value=False)
        self.week_toggle = ctk.CTkCheckBox(
            master=header_frame,
            text="Include week number in file name",
            variable=self.week_toggle_var
        )
        self.type_toggle = ctk.CTkCheckBox(
            master=header_frame,
            text="Include type in file name",
            variable=self.type_toggle_var
        )
        # New: Week description toggle
        self.week_description_toggle = ctk.CTkCheckBox(
            master=header_frame,
            text="Include week description in file/folder names",
            variable=self.week_description_toggle_var
        )
        # Show toggles by default with improved spacing
        self.week_toggle.pack(pady=(10, 0), anchor="w")
        self.type_toggle.pack(pady=(8, 0), anchor="w")
        self.week_description_toggle.pack(pady=(8, 0), anchor="w")
        
        # Scrollable content container
        types_label = ctk.CTkLabel(
            master=main_container,
            text="Types:",
            font=ctk.CTkFont(size=14, weight="bold"),
            anchor="w"
        )
        types_label.pack(pady=(10, 0), padx=40, anchor="w")
        content_container = ctk.CTkScrollableFrame(
            master=main_container,
            fg_color="transparent"
        )
        content_container.pack(pady=20, padx=40, fill="both", expand=True)
        
        self.checkboxes_container = content_container
        
        # Select All button container
        select_all_container = ctk.CTkFrame(master=main_container, fg_color="transparent")
        select_all_container.pack(pady=(0, 20), padx=40, fill="x")
        
        # Configure grid weights for button layout
        select_all_container.grid_columnconfigure(0, weight=1)
        select_all_container.grid_columnconfigure(1, weight=1)
        
        self.select_all_button = ctk.CTkButton(
            master=select_all_container,
            text="Select All",
            command=self.select_all_checkboxes,
            height=40,
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color="#FF9800",
            hover_color="#F57C00"
        )
        self.select_all_button.grid(row=0, column=0, padx=(5, 2.5), pady=5, sticky="ew")
        
        self.deselect_all_button = ctk.CTkButton(
            master=select_all_container,
            text="Deselect All",
            command=self.deselect_all_checkboxes,
            height=40,
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color="#9E9E9E",
            hover_color="#757575"
        )
        self.deselect_all_button.grid(row=0, column=1, padx=(2.5, 5), pady=5, sticky="ew")
        
        # Output folder selection
        output_folder_container = ctk.CTkFrame(master=main_container, fg_color="transparent")
        output_folder_container.pack(pady=(0, 20), padx=40, fill="x")
        output_label = ctk.CTkLabel(
            master=output_folder_container,
            text="Output Folder:",
            font=ctk.CTkFont(size=14, weight="bold"),
            anchor="w"
        )
        output_label.pack(side="left", padx=(0, 10))
        self.output_folder_var = ctk.StringVar(value=self.output_folder or "No folder selected")
        self.output_folder_display = ctk.CTkLabel(
            master=output_folder_container,
            textvariable=self.output_folder_var,
            font=ctk.CTkFont(size=14),
            text_color="gray",
            anchor="w"
        )
        self.output_folder_display.pack(side="left", fill="x", expand=True)
        browse_button = ctk.CTkButton(
            master=output_folder_container,
            text="Browse",
            command=self.browse_output_folder,
            height=32,
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color="#2196F3",
            hover_color="#1976D2"
        )
        browse_button.pack(side="right", padx=(10, 0))
        
        # Buttons container
        buttons_container = ctk.CTkFrame(master=main_container, fg_color="transparent")
        buttons_container.pack(pady=20, padx=40, fill="x")
        
        self.download_button = ctk.CTkButton(
            master=buttons_container,
            text="Download Selected",
            command=self.start_download,
            height=50,
            font=ctk.CTkFont(size=16, weight="bold"),
            fg_color="#4CAF50",
            hover_color="#45a049"
        )
        self.download_button.pack(pady=(0, 15), padx=5, fill="x")
        
        self.back_button = ctk.CTkButton(
            master=buttons_container,
            text="Back",
            command=self.prev_page,
            height=45,
            font=ctk.CTkFont(size=14),
            fg_color="transparent",
            border_width=2,
            text_color="#2196F3",
            border_color="#2196F3",
            hover_color="#2196F3"
        )
        self.back_button.pack(padx=5, fill="x")
    
    def create_loading_page(self):
        """Create the loading page with progress bar and animated spinner"""
        self.loading_frame = ctk.CTkFrame(master=self.root, fg_color="transparent")
        
        # Main container (now scrollable)
        main_container = ctk.CTkScrollableFrame(master=self.loading_frame, corner_radius=20, height=600)
        main_container.pack(pady=40, padx=40, fill="both", expand=True)
        
        # Header
        header_frame = ctk.CTkFrame(master=main_container, fg_color="transparent")
        header_frame.pack(pady=(40, 20), padx=40, fill="x")
        
        self.loading_title = ctk.CTkLabel(
            master=header_frame,
            text="Downloading Files",
            font=ctk.CTkFont(size=28, weight="bold")
        )
        self.loading_title.pack()
        
        self.loading_subtitle = ctk.CTkLabel(
            master=header_frame,
            text="Please wait while we download your selected content",
            font=ctk.CTkFont(size=14),
            text_color="gray"
        )
        self.loading_subtitle.pack(pady=(5, 0))
        
        # Spinner container (above progress)
        spinner_container = ctk.CTkFrame(master=main_container, fg_color="transparent")
        spinner_container.pack(pady=(40, 20), padx=40, fill="x")
        
        # Animated loading spinner
        self.loading_spinner = LoadingSpinner(
            master=spinner_container,
            size=50,  # Made smaller
            color="#4CAF50"
        )
        self.loading_spinner.pack()
        
        # Progress container
        progress_container = ctk.CTkFrame(master=main_container, fg_color="transparent")
        progress_container.pack(pady=20, padx=40, fill="x")
        
        # Progress bar
        self.progress_bar = ctk.CTkProgressBar(
            master=progress_container,
            height=20,
            progress_color="#4CAF50"
        )
        self.progress_bar.pack(pady=(0, 20), padx=5, fill="x")
        self.progress_bar.set(0)
        
        # Progress text
        self.progress_text = ctk.CTkLabel(
            master=progress_container,
            text="0% Complete",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        self.progress_text.pack(pady=(0, 10))
        
        # File counter
        self.file_counter = ctk.CTkLabel(
            master=progress_container,
            text="0 of 0 files downloaded",
            font=ctk.CTkFont(size=14),
            text_color="gray"
        )
        self.file_counter.pack(pady=(0, 20))
        
        # Current file label
        self.current_file_label = ctk.CTkLabel(
            master=progress_container,
            text="Preparing download...",
            font=ctk.CTkFont(size=12),
            text_color="gray"
        )
        self.current_file_label.pack()
        
        # Cancel button
        self.cancel_button = ctk.CTkButton(
            master=progress_container,
            text="Cancel Download",
            command=self.cancel_download,
            height=45,
            font=ctk.CTkFont(size=14),
            fg_color="transparent",
            border_width=2,
            text_color="#ff6b6b",
            border_color="#ff6b6b",
            hover_color="#ff9999"
        )
        self.cancel_button.pack(pady=(30, 0), padx=5, fill="x")
    
    def ensure_env_file(self):
        if not os.path.exists(".env"):
            with open(".env", "w") as f:
                f.write("USERNAME=\nPASSWORD=\nOUTPUT_FOLDER=\n")
    
    def check_saved_credentials(self):
        """Check for saved credentials and auto-login if available"""
        username = os.getenv("USERNAME", "")
        password = os.getenv("PASSWORD", "")
        if username and password:
            self.update_courses(username, password)
            self.page_index = 1
            self.show_page(1)
        else:
            self.show_page(0)
    
    def show_page(self, page_index):
        """Show the specified page"""
        self.page_index = page_index
        for page in self.pages:
            page.pack_forget()
        self.pages[page_index].pack(pady=20, padx=40, fill="both", expand=True)
        # Force GUI update to ensure proper redrawing
        self.root.update_idletasks()
        
        # Special focus handling for courses page
        if page_index == 1:  # Courses page
            # Use after() to schedule focus change after the current event is processed
            self.root.after(10, self._clear_focus)
        
        # Reset loading page state when entering download page
        if page_index == 2:  # Download page
            if hasattr(self, 'progress_bar'):
                self.progress_bar.set(0)
            if hasattr(self, 'progress_text'):
                self.progress_text.configure(text="0% Complete")
            if hasattr(self, 'file_counter'):
                self.file_counter.configure(text="0 of 0 files downloaded")
            if hasattr(self, 'current_file_label'):
                self.current_file_label.configure(text="Preparing download...")
            if hasattr(self, 'download_button'):
                self.download_button.configure(text="Download Selected", state="normal")
    
    def next_page(self, selected_course):
        """Navigate to next page"""
        if self.page_index < len(self.pages) - 2:  # Exclude loading page
            if self.page_index == 1:  # From courses to download page
                # Check if selected item is a session header
                if selected_course.startswith("---") and selected_course.endswith("---"):
                    # Show error popup for session header selection
                    self.show_session_header_error()
                    return
                
                # Handle "All Courses" selection
                if selected_course == "All Courses":
                    # Start download all process directly
                    self.download_all_courses()
                    return
                
                username, password = self.get_credentials()
                # Extract actual course name from formatted selection
                actual_course_name = selected_course.strip()
                update_course_url(username, password, actual_course_name)
                self.render_checkboxes()
            self.show_page(self.page_index + 1)
    
    def prev_page(self):
        """Navigate to previous page"""
        if self.page_index > 0:
            if self.page_index == 0:  # Clear credentials when going back to login
                set_key(".env", "USERNAME", "")
                set_key(".env", "PASSWORD", "")
                load_dotenv(override=True)
            self.show_page(self.page_index - 1)
    
    def download_all_courses(self):
        """Download from all available courses"""
        if not self.output_folder:
            self.show_no_output_folder_popup()
            return
        
        username, password = self.get_credentials()
        all_courses = get_courses(username, password)
        
        # Filter out session headers and get only actual courses
        actual_courses = []
        for course in all_courses:
            if not course.startswith("---") and not course.endswith("---") and course.strip() != "--":
                actual_courses.append(course.strip())
        
        if not actual_courses:
            self.show_no_courses_popup()
            return
        
        # Show confirmation dialog and get content type choice
        content_type_choice = self.show_download_all_confirmation(actual_courses)
        if not content_type_choice:  # User cancelled
            return
        
        # Switch to loading page
        self.show_page(3)  # Loading page
        self.loading_spinner.start_animation()
        
        # Start download in separate thread
        self.is_downloading = True
        self.current_download_thread = threading.Thread(
            target=self.download_all_thread,
            args=(actual_courses, content_type_choice)
        )
        self.current_download_thread.start()
    
    def download_all_thread(self, courses, content_type_choice):
        """Download thread for all courses"""
        username, password = self.get_credentials()
        total_courses = len(courses)
        completed_courses = 0
        
        # Update loading title based on content type choice
        if content_type_choice == "vods":
            title_text = "Downloading VODs from All Courses"
            subtitle_text = f"Processing VODs from {total_courses} courses..."
        else:
            title_text = "Downloading All Content from All Courses"
            subtitle_text = f"Processing all content from {total_courses} courses..."
        
        self.root.after(0, lambda: self.loading_title.configure(text=title_text))
        self.root.after(0, lambda: self.loading_subtitle.configure(text=subtitle_text))
        
        try:
            for course in courses:
                if not self.is_downloading:
                    break
                
                # Update current course
                self.root.after(0, lambda c=course: self.current_file_label.configure(text=f"Processing course: {c}"))
                
                # Update course URL for this course
                update_course_url(username, password, course)
                
                # Get available types for this course
                get_types_output = get_types(username, password)
                all_types = get_types_output.get('types', [])
                
                if all_types:
                    # Filter types based on user choice
                    if content_type_choice == "vods":
                        # Filter to only include VOD-related types
                        vod_keywords = ["VOD", "Video", "Lecture", "Recording", "Stream"]
                        selected_types = []
                        for content_type in all_types:
                            if any(keyword.lower() in content_type.lower() for keyword in vod_keywords):
                                selected_types.append(content_type)
                        # If no VOD types found, skip this course
                        if not selected_types:
                            completed_courses += 1
                            continue
                    else:
                        # Use all available types
                        selected_types = all_types
                    
                    # Download selected content types for this course
                    def progress_callback(downloaded, total, current_file, file_progress_str=None):
                        if not self.is_downloading:
                            return
                        # Update progress with course context
                        course_progress = f"Course {completed_courses + 1}/{total_courses}: {course}"
                        self.root.after(0, lambda: self.file_counter.configure(text=f"{course_progress} - {downloaded} of {total} files"))
                        if file_progress_str == "VoD":
                            self.root.after(0, lambda cf=current_file: self.current_file_label.configure(text=f"Downloading (VoD): {cf}"))
                        elif file_progress_str:
                            self.root.after(0, lambda cf=current_file, fps=file_progress_str: self.current_file_label.configure(text=f"Downloading: {cf} ({fps})"))
                        else:
                            self.root.after(0, lambda cf=current_file: self.current_file_label.configure(text=f"Downloading: {cf}"))
                    
                    def cancellation_check():
                        return not self.is_downloading
                    
                    download_content(
                        username, password, selected_types, progress_callback, cancellation_check,
                        self.output_folder, "type", True, False, False  # Default organization settings
                    )
                
                completed_courses += 1
                
                # Update overall progress
                overall_progress = completed_courses / total_courses
                self.root.after(0, lambda p=overall_progress: self.progress_bar.set(p))
                self.root.after(0, lambda p=overall_progress: self.progress_text.configure(text=f"{int(p * 100)}% of courses complete"))
            
            # Download completed
            if self.is_downloading:
                self.root.after(0, self.download_all_completed)
        except Exception as e:
            if self.is_downloading:
                self.root.after(0, lambda e=e: self.download_error(str(e)))
    
    def download_all_completed(self):
        """Handle completion of downloading all courses"""
        # Stop the spinner animation
        self.loading_spinner.stop_animation()
        
        self.progress_bar.set(1.0)
        self.progress_text.configure(text="100% Complete")
        self.current_file_label.configure(text="All courses downloaded successfully!")
        
        # Show completion message and return to courses page
        self.root.after(3000, lambda: self.show_page(1))
    
    def show_download_all_confirmation(self, courses):
        """Show confirmation dialog for downloading all courses"""
        # Create popup window
        popup = ctk.CTkToplevel(self.root)
        popup.title("Download All Courses")
        popup.geometry("520x500")
        popup.resizable(False, False)
        
        # Center the popup on the main window
        popup.transient(self.root)
        popup.grab_set()  # Make popup modal
        
        # Center the popup
        popup.update_idletasks()
        x = (popup.winfo_screenwidth() // 2) - (520 // 2)
        y = (popup.winfo_screenheight() // 2) - (500 // 2)
        popup.geometry(f'520x500+{x}+{y}')
        
        # Main scrollable container
        main_container = ctk.CTkScrollableFrame(master=popup, corner_radius=15)
        main_container.pack(pady=20, padx=20, fill="both", expand=True)
        
        # Icon and title
        icon_label = ctk.CTkLabel(
            master=main_container,
            text="📚",
            font=ctk.CTkFont(size=32)
        )
        icon_label.pack(pady=(20, 10))
        
        title_label = ctk.CTkLabel(
            master=main_container,
            text="Download All Courses",
            font=ctk.CTkFont(size=18, weight="bold")
        )
        title_label.pack(pady=(0, 10))
        
        message_label = ctk.CTkLabel(
            master=main_container,
            text=f"You are about to download content from {len(courses)} courses.\nThis may take a long time. Continue?",
            font=ctk.CTkFont(size=14),
            text_color="gray"
        )
        message_label.pack(pady=(0, 15))
        
        # Content type selection
        content_type_label = ctk.CTkLabel(
            master=main_container,
            text="What content would you like to download?",
            font=ctk.CTkFont(size=12, weight="bold"),
            anchor="w"
        )
        content_type_label.pack(pady=(0, 10), anchor="w")
        
        # Radio button variable
        content_type_var = ctk.StringVar(value="all")
        
        # All content radio button
        all_content_radio = ctk.CTkRadioButton(
            master=main_container,
            text="All content types (lectures, assignments, quizzes, etc.)",
            variable=content_type_var,
            value="all",
            font=ctk.CTkFont(size=12)
        )
        all_content_radio.pack(pady=(0, 8), anchor="w")
        
        # VODs only radio button
        vods_only_radio = ctk.CTkRadioButton(
            master=main_container,
            text="VODs (Video on Demand) only",
            variable=content_type_var,
            value="vods",
            font=ctk.CTkFont(size=12)
        )
        vods_only_radio.pack(pady=(0, 15), anchor="w")
        
        # Scrollable list of courses
        courses_label = ctk.CTkLabel(
            master=main_container,
            text="Courses to download:",
            font=ctk.CTkFont(size=12, weight="bold"),
            anchor="w"
        )
        courses_label.pack(pady=(0, 5), anchor="w")
        
        courses_frame = ctk.CTkScrollableFrame(master=main_container, height=150)
        courses_frame.pack(pady=(0, 20), padx=10, fill="x")
        
        for course in courses:
            course_label = ctk.CTkLabel(
                master=courses_frame,
                text=f"• {course}",
                font=ctk.CTkFont(size=11),
                anchor="w"
            )
            course_label.pack(pady=2, anchor="w")
        
        # Button container
        button_container = ctk.CTkFrame(master=main_container, fg_color="transparent")
        button_container.pack(pady=(0, 20), fill="x")
        
        # Configure grid weights for button layout
        button_container.grid_columnconfigure(0, weight=1)
        button_container.grid_columnconfigure(1, weight=1)
        
        result = [None]  # Use list to store result from closure
        
        def on_confirm():
            result[0] = content_type_var.get()
            popup.destroy()
        
        def on_cancel():
            result[0] = None
            popup.destroy()
        
        confirm_button = ctk.CTkButton(
            master=button_container,
            text="Download All",
            command=on_confirm,
            height=40,
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color="#4CAF50",
            hover_color="#45a049"
        )
        confirm_button.grid(row=0, column=0, padx=(5, 2.5), pady=5, sticky="ew")
        
        cancel_button = ctk.CTkButton(
            master=button_container,
            text="Cancel",
            command=on_cancel,
            height=40,
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color="#9E9E9E",
            hover_color="#757575"
        )
        cancel_button.grid(row=0, column=1, padx=(2.5, 5), pady=5, sticky="ew")
        
        # Focus on the popup and make it modal
        popup.focus_set()
        popup.wait_window()
        
        return result[0]
    
    def show_no_courses_popup(self):
        """Show popup when no courses are available"""
        # Create popup window
        popup = ctk.CTkToplevel(self.root)
        popup.title("No Courses Available")
        popup.geometry("400x200")
        popup.resizable(False, False)
        
        # Center the popup on the main window
        popup.transient(self.root)
        popup.grab_set()  # Make popup modal
        
        # Center the popup
        popup.update_idletasks()
        x = (popup.winfo_screenwidth() // 2) - (400 // 2)
        y = (popup.winfo_screenheight() // 2) - (200 // 2)
        popup.geometry(f'400x200+{x}+{y}')
        
        # Main container
        main_container = ctk.CTkFrame(master=popup, corner_radius=15)
        main_container.pack(pady=20, padx=20, fill="both", expand=True)
        
        # Icon and title
        icon_label = ctk.CTkLabel(
            master=main_container,
            text="ℹ️",
            font=ctk.CTkFont(size=32)
        )
        icon_label.pack(pady=(20, 10))
        
        title_label = ctk.CTkLabel(
            master=main_container,
            text="No Courses Available",
            font=ctk.CTkFont(size=18, weight="bold")
        )
        title_label.pack(pady=(0, 10))
        
        message_label = ctk.CTkLabel(
            master=main_container,
            text="No courses are available for download.",
            font=ctk.CTkFont(size=14),
            text_color="gray"
        )
        message_label.pack(pady=(0, 20))
        
        # OK button
        ok_button = ctk.CTkButton(
            master=main_container,
            text="OK",
            command=popup.destroy,
            height=40,
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color="#2196F3",
            hover_color="#1976D2"
        )
        ok_button.pack(pady=(0, 20), padx=20, fill="x")
        
        # Focus on the popup and make it modal
        popup.focus_set()
        popup.wait_window()

    def get_credentials(self):
        """Get saved credentials"""
        return [os.getenv("USERNAME", ""), os.getenv("PASSWORD", "")]
    
    def update_courses(self, username, password):
        """Update course list"""
        all_courses = get_courses(username, password)
        
        # Add "All Courses" option at the beginning
        course_options = ["All Courses"] + all_courses
        self.course_select.configure(values=course_options)
        
        # Set initial selection to first actual course (not session header)
        initial_selection = "--"
        for course in all_courses:
            if not course.startswith("---") and not course.endswith("---"):
                initial_selection = course
                break
        
        self.course_select.set(initial_selection)
        
        # Set initial button state
        if initial_selection == "--":
            self.next_button.configure(state="disabled")
        else:
            self.next_button.configure(state="normal")
        
        # Use after() to schedule focus change after the current event is processed
        self.root.after(10, self._clear_focus)
    
    def render_checkboxes(self):
        """Render checkboxes for content types"""
        username, password = self.get_credentials()
        get_types_output = get_types(username, password)
        all_types = get_types_output.get('types', [])
        course_name = get_types_output.get('course_name', 'Unknown Course')
        
        # Update course title
        self.course_title_label.configure(text=course_name)
        
        # Clear existing checkboxes
        for widget in self.checkboxes_container.winfo_children():
            widget.destroy()
        
        # Create new checkboxes
        self.checkboxes = {}
        for content_type in all_types:
            checkbox = ctk.CTkCheckBox(
                master=self.checkboxes_container,
                text=content_type,
                font=ctk.CTkFont(size=14),
                checkbox_width=20,
                checkbox_height=20
            )
            checkbox.pack(pady=8, padx=10, anchor="w", fill="x")
            self.checkboxes[content_type] = checkbox
    
    def get_selected_types(self):
        """Get selected content types"""
        username, password = self.get_credentials()
        selected = []
        get_types_output = get_types(username, password)
        all_types = get_types_output.get('types', [])
        
        for content_type in all_types:
            if self.checkboxes.get(content_type) and self.checkboxes[content_type].get() == 1:
                selected.append(content_type)
        return selected
    
    def login_gui(self):
        """Handle login"""
        username = self.username_entry.get()
        password = self.password_entry.get()
        
        if not username or not password:
            self.show_error("Please enter both username and password")
            return
        
        # Show loading state
        self.login_button.configure(text="Signing In...", state="disabled")
        self.root.update()
        
        # Try login
        login_state = login(username=username, password=password)
        
        if login_state:
            # Save credentials to .env
            set_key(".env", "USERNAME", username)
            set_key(".env", "PASSWORD", password)
            load_dotenv(override=True)
            self.update_courses(username, password)
            self.next_page(self.course_select.get())
        else:
            self.show_error("Invalid credentials. Please try again.")
        
        # Reset button
        self.login_button.configure(text="Sign In", state="normal")
    
    def show_error(self, message):
        """Show error message"""
        self.error_label.configure(text=message)
        self.error_label.pack(pady=(0, 20), padx=5)
        self.root.after(3000, lambda: self.error_label.pack_forget())
    
    def start_download(self):
        """Start the download process"""
        selected_types = self.get_selected_types()
        
        if not selected_types:
            # Show popup asking user to select at least one filter
            self.show_no_filters_popup()
            return
        
        if not self.output_folder:
            self.show_no_output_folder_popup()
            return
        
        # Change button text to Processing... and disable it
        if hasattr(self, 'download_button'):
            self.download_button.configure(text="Processing...", state="disabled")
        self.root.update_idletasks()
        
        # Switch to loading page
        self.show_page(3)  # Loading page
        
        # Start the loading spinner animation
        self.loading_spinner.start_animation()
        
        # Start download in separate thread
        self.is_downloading = True
        self.current_download_thread = threading.Thread(
            target=self.download_thread,
            args=(
                selected_types,
                self.org_mode,
                self.week_toggle_var.get(),
                self.type_toggle_var.get(),
                self.week_description_toggle_var.get()  # Pass new toggle value
            )
        )
        self.current_download_thread.start()
    
    def show_no_filters_popup(self):
        """Show popup dialog when no filters are selected"""
        # Create popup window
        popup = ctk.CTkToplevel(self.root)
        popup.title("No Filters Selected")
        popup.geometry("400x200")
        popup.resizable(False, False)
        
        # Center the popup on the main window
        popup.transient(self.root)
        popup.grab_set()  # Make popup modal
        
        # Center the popup
        popup.update_idletasks()
        x = (popup.winfo_screenwidth() // 2) - (400 // 2)
        y = (popup.winfo_screenheight() // 2) - (200 // 2)
        popup.geometry(f'400x200+{x}+{y}')
        
        # Main container
        main_container = ctk.CTkFrame(master=popup, corner_radius=15)
        main_container.pack(pady=20, padx=20, fill="both", expand=True)
        
        # Icon and title
        icon_label = ctk.CTkLabel(
            master=main_container,
            text="⚠️",
            font=ctk.CTkFont(size=32)
        )
        icon_label.pack(pady=(20, 10))
        
        title_label = ctk.CTkLabel(
            master=main_container,
            text="No Filters Selected",
            font=ctk.CTkFont(size=18, weight="bold")
        )
        title_label.pack(pady=(0, 10))
        
        message_label = ctk.CTkLabel(
            master=main_container,
            text="Please select at least one content type\nto download before proceeding.",
            font=ctk.CTkFont(size=14),
            text_color="gray"
        )
        message_label.pack(pady=(0, 20))
        
        # OK button
        ok_button = ctk.CTkButton(
            master=main_container,
            text="OK",
            command=popup.destroy,
            height=40,
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color="#2196F3",
            hover_color="#1976D2"
        )
        ok_button.pack(pady=(0, 20), padx=20, fill="x")
        
        # Focus on the popup and make it modal
        popup.focus_set()
        popup.wait_window()
    
    def download_thread(self, selected_types, org_mode, include_week, include_type, include_week_description=False):
        """Download thread to prevent GUI freezing"""
        username, password = self.get_credentials()
        
        # Get total files before starting download
        total_files = get_total_files(username, password, selected_types)
        self.root.after(0, lambda: self.file_counter.configure(text=f"0 of {total_files} files downloaded"))
        
        def progress_callback(downloaded, total, current_file, file_progress_str=None):
            if not self.is_downloading:
                return
            # Update progress on main thread
            self.root.after(0, lambda: self.update_progress(downloaded, total, current_file, file_progress_str))
        
        def cancellation_check():
            return not self.is_downloading
        
        try:
            download_content(
                username, password, selected_types, progress_callback, cancellation_check,
                self.output_folder, org_mode, include_week, include_type, include_week_description
            )
            
            # Download completed
            if self.is_downloading:
                self.root.after(0, self.download_completed)
        except Exception as e:
            if self.is_downloading:
                self.root.after(0, lambda e=e: self.download_error(str(e)))
    
    def update_progress(self, downloaded, total, current_file, file_progress_str=None):
        """Update progress bar and labels, including per-file progress if available"""
        if total > 0:
            progress = downloaded / total
            self.progress_bar.set(progress)
            self.progress_text.configure(text=f"{int(progress * 100)}% Complete")
            self.file_counter.configure(text=f"{downloaded} of {total} files downloaded")
            if file_progress_str == "VoD":
                self.current_file_label.configure(text=f"Downloading (VoD): {current_file}")
            elif file_progress_str:
                self.current_file_label.configure(text=f"Downloading: {current_file} ({file_progress_str})")
            else:
                self.current_file_label.configure(text=f"Downloading: {current_file}")
    
    def download_completed(self):
        """Handle download completion"""
        # Stop the spinner animation
        self.loading_spinner.stop_animation()
        
        self.progress_bar.set(1.0)
        self.progress_text.configure(text="100% Complete")
        self.current_file_label.configure(text="Download completed successfully!")
        
        # Show completion message and return to download page
        self.root.after(2000, lambda: self.show_page(2))
    
    def download_error(self, error_message):
        """Handle download error"""
        # Stop the spinner animation
        self.loading_spinner.stop_animation()
        
        self.current_file_label.configure(text=f"Error: {error_message}")
        self.root.after(3000, lambda: self.show_page(2))
    
    def cancel_download(self):
        """Cancel the current download"""
        # Stop the spinner animation
        self.loading_spinner.stop_animation()
        
        self.is_downloading = False
        self.current_file_label.configure(text="Download cancelled")
        # Immediately return to download page since cancellation is now properly handled
        self.show_page(2)
        # Force GUI update to prevent blank page
        self.root.update()
        self.root.update_idletasks()

    def select_all_checkboxes(self):
        """Select all checkboxes"""
        for checkbox in self.checkboxes.values():
            checkbox.select()

    def deselect_all_checkboxes(self):
        """Deselect all checkboxes"""
        for checkbox in self.checkboxes.values():
            checkbox.deselect()

    def on_course_selection(self, selection):
        """Handle course selection from dropdown"""
        # Check if the selection is a session header
        if selection.startswith("---") and selection.endswith("---"):
            # Disable the continue button for session headers
            self.next_button.configure(state="disabled")
        elif selection == "All Courses":
            # Enable the continue button for "All Courses" option
            self.next_button.configure(state="normal")
        else:
            # Enable the continue button for actual courses
            self.next_button.configure(state="normal")
        
        # Use after() to schedule focus change after the current event is processed
        self.root.after(10, self._clear_focus)
    
    def _clear_focus(self):
        """Clear focus from dropdown and set it to the root window"""
        # Clear focus from the dropdown
        self.course_select.focus_set()
        self.course_select.focus_force()
        
        # Then immediately clear focus to root window
        self.root.focus_set()
        self.root.focus_force()
        
        # Force GUI update to ensure focus change takes effect
        self.root.update_idletasks()

    def show_session_header_error(self):
        """Show popup dialog when user tries to select a session header"""
        # Create popup window
        popup = ctk.CTkToplevel(self.root)
        popup.title("Invalid Selection")
        popup.geometry("400x200")
        popup.resizable(False, False)
        
        # Center the popup on the main window
        popup.transient(self.root)
        popup.grab_set()  # Make popup modal
        
        # Center the popup
        popup.update_idletasks()
        x = (popup.winfo_screenwidth() // 2) - (400 // 2)
        y = (popup.winfo_screenheight() // 2) - (200 // 2)
        popup.geometry(f'400x200+{x}+{y}')
        
        # Main container
        main_container = ctk.CTkFrame(master=popup, corner_radius=15)
        main_container.pack(pady=20, padx=20, fill="both", expand=True)
        
        # Icon and title
        icon_label = ctk.CTkLabel(
            master=main_container,
            text="⚠️",
            font=ctk.CTkFont(size=32)
        )
        icon_label.pack(pady=(20, 10))
        
        title_label = ctk.CTkLabel(
            master=main_container,
            text="Invalid Selection",
            font=ctk.CTkFont(size=18, weight="bold")
        )
        title_label.pack(pady=(0, 10))
        
        message_label = ctk.CTkLabel(
            master=main_container,
            text="Please select a specific course,\nnot a session header.",
            font=ctk.CTkFont(size=14),
            text_color="gray"
        )
        message_label.pack(pady=(0, 20))
        
        # OK button
        ok_button = ctk.CTkButton(
            master=main_container,
            text="OK",
            command=popup.destroy,
            height=40,
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color="#2196F3",
            hover_color="#1976D2"
        )
        ok_button.pack(pady=(0, 20), padx=20, fill="x")
        
        # Focus on the popup and make it modal
        popup.focus_set()
        popup.wait_window()

    def load_last_output_folder(self):
        folder = os.getenv("OUTPUT_FOLDER", None)
        if folder:
            self.output_folder = folder

    def save_last_output_folder(self):
        set_key(".env", "OUTPUT_FOLDER", self.output_folder or "")
        load_dotenv(override=True)

    def browse_output_folder(self):
        folder_selected = filedialog.askdirectory()
        if folder_selected:
            self.output_folder = folder_selected
            self.output_folder_var.set(folder_selected)
            self.save_last_output_folder()

    def show_no_output_folder_popup(self):
        popup = ctk.CTkToplevel(self.root)
        popup.title("No Output Folder Selected")
        popup.geometry("400x200")
        popup.resizable(False, False)
        popup.transient(self.root)
        popup.grab_set()
        popup.update_idletasks()
        x = (popup.winfo_screenwidth() // 2) - (400 // 2)
        y = (popup.winfo_screenheight() // 2) - (200 // 2)
        popup.geometry(f'400x200+{x}+{y}')
        main_container = ctk.CTkFrame(master=popup, corner_radius=15)
        main_container.pack(pady=20, padx=20, fill="both", expand=True)
        icon_label = ctk.CTkLabel(
            master=main_container,
            text="⚠️",
            font=ctk.CTkFont(size=32)
        )
        icon_label.pack(pady=(20, 10))
        title_label = ctk.CTkLabel(
            master=main_container,
            text="No Output Folder Selected",
            font=ctk.CTkFont(size=18, weight="bold")
        )
        title_label.pack(pady=(0, 10))
        message_label = ctk.CTkLabel(
            master=main_container,
            text="Please select an output folder before downloading.",
            font=ctk.CTkFont(size=14),
            text_color="gray"
        )
        message_label.pack(pady=(0, 20))
        def on_ok():
            popup.destroy()
            # Only retry if output_folder is now set
            if self.output_folder:
                self.start_download()
        ok_button = ctk.CTkButton(
            master=main_container,
            text="OK",
            command=on_ok,
            height=40,
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color="#2196F3",
            hover_color="#1976D2"
        )
        ok_button.pack(pady=(0, 20), padx=20, fill="x")
        popup.focus_set()
        popup.wait_window()

if __name__ == "__main__":
    app = ModernCMSDownloader()
