import customtkinter
import requests
import threading
import tkinter as tk
from requests_ntlm import HttpNtlmAuth
from selectolax.parser import HTMLParser
from main import download_content, get_types, login, get_courses, update_course_url, get_semesters, set_semester, get_all_semesters_with_courses, download_all_content

customtkinter.set_appearance_mode("System")
customtkinter.set_default_color_theme("dark-blue")

input_username = ""
input_password = ""
all_types = ["--"]
page_index = 0
all_checkboxes = []
all_semesters = []
current_semester = None
all_semester_courses = []
all_semester_checkboxes = []
semester_course_checkboxes = {}  # Dictionary to store courses checkboxes for each semester
expanded_semesters = set()  # Track which semesters are expanded to show courses
download_in_progress = False

root = customtkinter.CTk()
root.geometry("800x700")
root.title("GUC CMS Downloader")


def start_download():
    selected_types = get_selected()
    [username, password] = getCredentials()
    current_semester_name = semester_select.get() if current_semester else None
    download_content(username, password, selected_types, current_semester_name)


def start_all_download():
    global download_in_progress
    
    if download_in_progress:
        show_message("Download in progress", "Please wait for the current download to finish.")
        return
    
    [username, password] = getCredentials()
    
    # Structure to hold selected semesters and courses
    selected_items = {}
    
    # Check which semesters/courses are selected
    for i, semester in enumerate(all_semester_courses):
        semester_id = semester["id"]
        semester_selected = (i < len(all_semester_checkboxes) and all_semester_checkboxes[i].get() == 1)
        
        if semester_selected:
            # Check if specific courses are selected for this semester
            if semester_id in semester_course_checkboxes:
                course_selections = []
                any_course_selected = False
                
                # Check each course checkbox
                for course_data in semester_course_checkboxes[semester_id]["courses"]:
                    if course_data["var"].get() == 1:
                        course_selections.append(course_data["course_data"]["id"])
                        any_course_selected = True
                
                # If no specific courses are selected, include all courses
                if not any_course_selected:
                    selected_items[semester_id] = "all"
                else:
                    # Store specific course IDs
                    selected_items[semester_id] = course_selections
    
    if not selected_items:
        show_message("No Selection", "Please select at least one semester or course to download.")
        return
    
    # Get selected content types
    selected_types = []
    download_all_types = False  # Flag to indicate if "All file types" is selected
    
    for type_name, var in bulk_type_checkboxes.items():
        if var.get() == 1:
            if type_name == "All file types":
                download_all_types = True
            else:
                selected_types.append(type_name)
    
    # If no content types selected and "All file types" not checked
    if not selected_types and not download_all_types:
        response = show_confirmation("No Content Types", "No content types selected. Download ALL available content?")
        if not response:
            return
        download_all_types = True  # If user confirms, download all types
    
    # Start download in background thread
    download_in_progress = True
    download_status_label.configure(text="Download in progress... This may take a while.")
    download_status_label.pack(pady=10)
    
    download_thread = threading.Thread(
        target=run_download, 
        args=(username, password, selected_items, selected_types, download_all_types)
    )
    download_thread.daemon = True
    download_thread.start()


def run_download(username, password, semester_selections, types, download_all_types=False):
    global download_in_progress
    try:
        # Update the status label to show progress
        root.after(0, lambda: download_status_label.configure(text="Starting download process...\nThis may take a while depending on the number of files."))
        
        # Call the updated download function that handles specific course selection
        result = download_all_content(username, password, semester_selections, types, download_all_types)
        
        if result and result.get("success"):
            stats = result.get("stats", {})
            total_files = stats.get("total_downloads", 0)
            courses_processed = stats.get("courses_processed", 0)
            
            success_message = f"Download completed!\n{total_files} files downloaded from {courses_processed} courses."
            root.after(0, lambda: download_status_label.configure(text=success_message))
            
            # Show a completion message
            if total_files > 0:
                show_message("Download Complete", 
                             f"Successfully downloaded {total_files} files!\n\n"
                             f"Files are saved in the Downloads folder.")
        else:
            error_msg = result.get("error", "Unknown error") if result else "Download failed"
            root.after(0, lambda: download_status_label.configure(text=f"Error: {error_msg}"))
    except Exception as e:
        error_message = f"Error: {str(e)}"
        root.after(0, lambda: download_status_label.configure(text=error_message))
        
        # Show error popup
        show_message("Download Error", f"An error occurred during download:\n{str(e)}")
    finally:
        download_in_progress = False


def show_message(title, message):
    popup = customtkinter.CTkToplevel(root)
    popup.title(title)
    popup.geometry("300x150")
    popup.transient(root)
    popup.grab_set()
    
    label = customtkinter.CTkLabel(popup, text=message)
    label.pack(pady=20)
    
    button = customtkinter.CTkButton(popup, text="OK", command=popup.destroy)
    button.pack(pady=10)


def show_confirmation(title, message):
    result = [False]  # Use list to store result because nonlocal is not available in Python 2
    
    popup = customtkinter.CTkToplevel(root)
    popup.title(title)
    popup.geometry("300x200")
    popup.transient(root)
    popup.grab_set()
    
    label = customtkinter.CTkLabel(popup, text=message)
    label.pack(pady=20)
    
    def on_yes():
        result[0] = True
        popup.destroy()
    
    def on_no():
        result[0] = False
        popup.destroy()
    
    button_frame = customtkinter.CTkFrame(popup)
    button_frame.pack(pady=10)
    
    yes_button = customtkinter.CTkButton(button_frame, text="Yes", command=on_yes)
    yes_button.pack(side="left", padx=10)
    
    no_button = customtkinter.CTkButton(button_frame, text="No", command=on_no)
    no_button.pack(side="right", padx=10)
    
    popup.wait_window()
    return result[0]


def getCredentials():
    with open("cms_downloader.config", "r") as file:
            return [file.readline().split("=")[1].strip(), file.readline().split("=")[1].strip()]


def next_page(selected_item=None):
    [username, password] = getCredentials()
    global page_index, current_semester
    
    # Store current page to handle special transitions
    old_page_index = page_index
    
    # Regular navigation logic
    if page_index < len(pages) - 1:
        # Hide all pages
        for page in pages:
            page.pack_forget()
        
        # Default increment
        page_index += 1
        
        # Handle different page transitions
        if page_index == 1:  # After login, load semesters
            load_semesters(username, password)
        elif page_index == 2:  # After semester selection
            if selected_item == "Download All Courses":
                # Special case: Go to bulk download page
                page_index = 4  # Index of all_semesters_frame
                load_all_semesters(username, password)
            else:
                # Regular case: Go to course selection for a specific semester
                current_semester = selected_item
                semester_id = next((s["id"] for s in all_semesters if s["name"] == selected_item), None)
                if semester_id:
                    set_semester(username, password, semester_id)
                    update_courses(username, password)
        elif page_index == 3:  # After course selection
            update_course_url(username, password, selected_item)
            render_checkboxes()
        
        # Show the new page
        pages[page_index].pack(pady=20, padx=60, fill="both", expand=True)


def load_semesters(username, password):
    global all_semesters
    all_semesters = get_semesters(username, password)
    
    # Add special option for downloading all courses
    semester_names = [semester["name"] for semester in all_semesters]
    
    # Make sure "Download All Courses" is always in the list
    if "Download All Courses" not in semester_names:
        semester_names.append("Download All Courses")
    
    if semester_names:
        semester_select.configure(values=semester_names)
        semester_select.set(semester_names[0])  # Default to first regular semester
        
        # Make sure buttons are packed (visible)
        semester_next_button.pack(pady=12, padx=10)
        semester_logout_button.pack(pady=12, padx=10)
    else:
        # If no semesters could be found, show an error
        error_label = customtkinter.CTkLabel(master=semester_frame, text="No semesters found", fg_color='#f00')
        error_label.pack(pady=12, padx=10)


def load_all_semesters(username, password):
    global all_semester_courses, all_semester_checkboxes, bulk_type_checkboxes, semester_course_checkboxes
    
    # Clear previous checkboxes
    for checkbox in all_semester_checkboxes:
        if hasattr(checkbox, 'pack_forget'):  # Check if it's a widget
            checkbox.pack_forget()
    all_semester_checkboxes = []
    
    # Clear course checkboxes dictionary
    for semester_id, checkboxes_list in semester_course_checkboxes.items():
        for widget in checkboxes_list:
            if hasattr(widget, 'pack_forget'):
                widget.pack_forget()
    semester_course_checkboxes = {}
    
    # Remove existing bulk type checkboxes if any
    for checkbox in bulk_type_checkboxes.values():
        if hasattr(checkbox, 'pack_forget'):  # Check if it's a widget
            checkbox.pack_forget()
    bulk_type_checkboxes = {}
    
    # Fetch all semesters with courses
    all_semester_data = get_all_semesters_with_courses(username, password)
    all_semester_courses = all_semester_data
    
    # Create frames for each semester with expand/collapse functionality
    for semester in all_semester_data:
        semester_id = semester["id"]
        semester_name = semester["name"]
        course_count = len(semester["courses"])
        
        # Create a frame for this semester
        semester_frame = customtkinter.CTkFrame(semesters_scroll_frame)
        semester_frame.pack(pady=5, padx=5, fill="x", expand=True)
        
        # Create a header frame with checkbox and expand button
        header_frame = customtkinter.CTkFrame(semester_frame)
        header_frame.pack(pady=2, padx=2, fill="x", expand=True)
        
        # Create semester checkbox
        var = customtkinter.IntVar()
        checkbox = customtkinter.CTkCheckBox(header_frame, 
                                           text=f"{semester_name} ({course_count} courses)",
                                           variable=var,
                                           command=lambda s=semester_id, v=var: toggle_semester_courses(s, v.get()))
        checkbox.pack(side="left", pady=5, padx=10)
        all_semester_checkboxes.append(var)
        
        # Create expand/collapse button
        expand_btn = customtkinter.CTkButton(
            header_frame,
            text="▼",  # Down arrow for expand
            width=30,
            command=lambda s=semester_id, sf=semester_frame: toggle_semester_view(s, sf)
        )
        expand_btn.pack(side="right", padx=10)
        
        # Create a container for courses (hidden initially)
        courses_container = customtkinter.CTkFrame(semester_frame)
        courses_container.pack(pady=0, padx=20, fill="x", expand=False)
        courses_container.pack_forget()  # Initially hidden
        
        # Store reference to courses container to show/hide later
        semester_course_checkboxes[semester_id] = {
            "container": courses_container,
            "courses": [],
            "expand_btn": expand_btn
        }
        
        # Add course checkboxes (but don't display them yet)
        for course in semester["courses"]:
            course_var = customtkinter.IntVar()
            course_checkbox = customtkinter.CTkCheckBox(
                courses_container,
                text=course["name"],
                variable=course_var
            )
            course_checkbox.pack(pady=2, padx=10, anchor="w")
            semester_course_checkboxes[semester_id]["courses"].append({
                "checkbox": course_checkbox,
                "var": course_var, 
                "course_data": course
            })
    
    # Add buttons for semester selection management
    buttons_frame = customtkinter.CTkFrame(semesters_scroll_frame)
    buttons_frame.pack(pady=10, padx=10, fill="x", expand=True)
    
    # Add "Select All" button for semesters
    select_all_button = customtkinter.CTkButton(
        buttons_frame, 
        text="Select All Semesters", 
        command=lambda: toggle_all_checkboxes(all_semester_checkboxes, True)
    )
    select_all_button.pack(side="left", pady=10, padx=10)
    
    # Add "Deselect All" button for semesters
    deselect_all_button = customtkinter.CTkButton(
        buttons_frame, 
        text="Deselect All Semesters", 
        command=lambda: toggle_all_checkboxes(all_semester_checkboxes, False)
    )
    deselect_all_button.pack(side="left", pady=10, padx=10)
    
    # Add button to expand/collapse all semesters
    expand_all_button = customtkinter.CTkButton(
        buttons_frame,
        text="Expand All",
        command=expand_all_semesters
    )
    expand_all_button.pack(side="right", pady=10, padx=10)
      # Create content type checkboxes
    # Use the predefined common content types list defined at the bottom of the file
    # This includes all the category types we want to ensure are available
    
    for content_type in common_content_types:
        var = customtkinter.IntVar()
        checkbox = customtkinter.CTkCheckBox(content_types_frame, text=content_type, variable=var)
        checkbox.pack(pady=5, padx=10, anchor="w")
        bulk_type_checkboxes[content_type] = var
    
    # Add Select All button for content types
    select_all_types_button = customtkinter.CTkButton(
        content_types_frame, 
        text="Select All Types", 
        command=lambda: toggle_all_checkboxes([v for v in bulk_type_checkboxes.values()], True)
    )
    select_all_types_button.pack(pady=10, padx=10)
    
    # Add Deselect All button for content types
    deselect_all_types_button = customtkinter.CTkButton(
        content_types_frame, 
        text="Deselect All Types", 
        command=lambda: toggle_all_checkboxes([v for v in bulk_type_checkboxes.values()], False)
    )
    deselect_all_types_button.pack(pady=10, padx=10)
      # No need to pack buttons or status label here as they're already packed in UI definition
    # Just make sure they're visible
    download_status_label.configure(text="")  # Clear any previous messages


def toggle_all_checkboxes(checkboxes, value):
    for checkbox in checkboxes:
        if hasattr(checkbox, 'select') and hasattr(checkbox, 'deselect'):
            # It's a CTkCheckBox widget
            checkbox.select() if value else checkbox.deselect()
        elif hasattr(checkbox, 'set'):
            # It's an IntVar
            checkbox.set(1 if value else 0)


def prev_page():
    global page_index
    if page_index > 0:
        # Hide all pages
        for page in pages:
            page.pack_forget()
            
        # Special case: if we're in the bulk download page (index 4)
        # we should go back to the semester selection page (index 1)
        if page_index == 4:
            page_index = 1
        else:
            # Regular navigation - go back one step
            page_index -= 1
        
        # If going back to login page, clear credentials
        if page_index == 0:
            with open("cms_downloader.config", "w") as file:
                file.write("username=")
                file.write("\npassword=")
                file.close()
        
        # Show the page we navigated to
        pages[page_index].pack(pady=20, padx=60, fill="both", expand=True)
        
        # If we're going back to the semester selection page, reload semesters
        if page_index == 1:
            [username, password] = getCredentials()
            load_semesters(username, password)


def update_courses(username, password):
    all_courses = get_courses(username, password)
    if all_courses:
        type_select.configure(values=all_courses)
        type_select.set(all_courses[0])
        next_button.pack(pady=12, padx=10)
        logout_button.pack(pady=12, padx=10)
    else:
        # Handle error case
        error_label = customtkinter.CTkLabel(master=courses_frame, text="No courses found for this semester", fg_color='#f00')
        error_label.pack(pady=12, padx=10)

def render_checkboxes():
    [username, password] = getCredentials()
    get_types_output = get_types(username, password)
    all_types = get_types_output.get('types')
    course_name = get_types_output.get('course_name')

    course_label.configure(text=course_name, font=('Outfit', 25))

    # Clear previous checkboxes
    for box in all_checkboxes:
        box.pack_forget()
    all_checkboxes.clear()
    
    # Clear the checkboxes dictionary
    checkboxes.clear()

    # Add checkboxes to the scrollable frame
    for type in all_types:
        checkboxes[type] = customtkinter.CTkCheckBox(download_scroll_frame, text=type)
        checkboxes[type].pack(pady=5, padx=10, anchor="w")
        all_checkboxes.append(checkboxes[type])
    
    # Add Select All / Deselect All buttons
    select_all_btn = customtkinter.CTkButton(
        download_scroll_frame,
        text="Select All Types",
        command=lambda: toggle_all_checkboxes(all_checkboxes, True)
    )
    select_all_btn.pack(pady=10, padx=10)
    
    deselect_all_btn = customtkinter.CTkButton(
        download_scroll_frame,
        text="Deselect All Types",
        command=lambda: toggle_all_checkboxes(all_checkboxes, False)
    )
    deselect_all_btn.pack(pady=10, padx=10)
    
    # Pack buttons at the bottom of the main frame
    download_button.pack(pady=12, padx=10)
    back_button.pack(pady=12, padx=10)


def get_selected():
    [username, password] = getCredentials()
    selected = []
    all_types = get_types(username, password).get('types')
    for type in all_types:
        if checkboxes[type].get() == 1:
            selected.append(type)
    return selected


def loginGUI(username, password):
    global input_username, input_password

    loginState = login(username=username, password=password)

    if (loginState):
        with open("cms_downloader.config", "w") as file:
            file.write("username="+username)
            file.write("\npassword="+password)
            file.close()
        next_page()  # This will navigate to semester selection page
    else:
        print("Error - Login failed")
        error_label.pack(pady=12, padx=10)



# Login Page
login_frame = customtkinter.CTkFrame(master=root)
# login_frame.pack(pady=20, padx=60, fill="both", expand=True)

label = customtkinter.CTkLabel(master=login_frame, text="CMS Downloader")
label.pack(pady=12, padx=10)

error_label = customtkinter.CTkLabel(master=login_frame, text="Error. Please Check Credentials", fg_color='#f00')

username = customtkinter.CTkEntry(master=login_frame, placeholder_text="Username")
username.pack(pady=12, padx=10)

password = customtkinter.CTkEntry(master=login_frame, placeholder_text="Password", show="*")
password.pack(pady=12, padx=10)

login_button = customtkinter.CTkButton(master=login_frame, text="Login", command= lambda: loginGUI(username=username.get(), password=password.get()))
login_button.pack(pady=12, padx=10)


# Semester Select Page
semester_frame = customtkinter.CTkFrame(master=root)

semester_label = customtkinter.CTkLabel(master=semester_frame, text="Choose a semester")
semester_label.pack(pady=12, padx=10)

semester_select = customtkinter.CTkOptionMenu(semester_frame, values=["--"])
semester_select.pack(pady=12, padx=10)

semester_next_button = customtkinter.CTkButton(master=semester_frame, text="Next", command=lambda: next_page(semester_select.get()))
semester_logout_button = customtkinter.CTkButton(master=semester_frame, text="Log Out", command=prev_page)


# Course Select Page
courses_frame = customtkinter.CTkFrame(master=root)

courses_label = customtkinter.CTkLabel(master=courses_frame, text="Choose a course")
courses_label.pack(pady=12, padx=10)

type_select = customtkinter.CTkOptionMenu(courses_frame, values=all_types)
type_select.pack(pady=12, padx=10)

next_button = customtkinter.CTkButton(master=courses_frame, text="Next", command= lambda: next_page(type_select.get()))
logout_button = customtkinter.CTkButton(master=courses_frame, text="Log Out", command= prev_page)


# Download Page
download_frame = customtkinter.CTkFrame(master=root)

course_label = customtkinter.CTkLabel(master=download_frame, text="")
course_label.pack(pady=12, padx=10)

# Create scrollable frame for content type checkboxes
download_scroll_frame = customtkinter.CTkScrollableFrame(
    master=download_frame,
    width=700,
    height=400,  # Taller frame to accommodate all checkboxes
    label_text="Available Content"
)
download_scroll_frame.pack(pady=10, padx=10, fill="both", expand=True)

checkboxes = {}

# Create a container for buttons to ensure they're always visible
button_container = customtkinter.CTkFrame(master=download_frame)
button_container.pack(side="bottom", fill="x", pady=10, padx=10)

download_button = customtkinter.CTkButton(master=button_container, text="Download", command=start_download)
download_button.pack(side="left", pady=12, padx=10)

back_button = customtkinter.CTkButton(master=button_container, text="Back", command=prev_page)
back_button.pack(side="right", pady=12, padx=10)
# These buttons are now packed in the button_container


# All Semesters Download Page
all_semesters_frame = customtkinter.CTkScrollableFrame(master=root)

# Main title
all_semesters_title = customtkinter.CTkLabel(
    master=all_semesters_frame, 
    text="Download Content from Multiple Semesters", 
    font=("Outfit", 20)
)
all_semesters_title.pack(pady=20, padx=10)

# Create a scrollable frame for semesters and their courses
semesters_scroll_frame = customtkinter.CTkScrollableFrame(
    master=all_semesters_frame,
    width=700,
    height=300,  # Taller to fit expanded semester sections
    label_text="Available Semesters and Courses"
)
semesters_scroll_frame.pack(pady=10, padx=10, fill="both", expand=True)

# Create a scrollable frame for content types
content_types_scroll_frame = customtkinter.CTkScrollableFrame(
    master=all_semesters_frame,
    width=700,
    height=150,
    label_text="Content Types to Download"
)
content_types_scroll_frame.pack(pady=10, padx=10, fill="both", expand=True)

# We'll add content type checkboxes to this frame
content_types_frame = content_types_scroll_frame

# Create a button frame at the bottom to ensure buttons are visible
bottom_frame = customtkinter.CTkFrame(master=all_semesters_frame)
bottom_frame.pack(side="bottom", fill="x", pady=10, padx=10)

# Download status
download_status_label = customtkinter.CTkLabel(
    master=bottom_frame, 
    text="",
    font=("Outfit", 14),
    wraplength=500  # Allow text to wrap for longer messages
)
download_status_label.pack(pady=10, padx=10)

# Button to start download
all_download_button = customtkinter.CTkButton(
    master=bottom_frame, 
    text="Download Selected Content", 
    command=start_all_download,
    font=("Outfit", 14),
    height=40  # Make button taller for better visibility
)
all_download_button.pack(pady=10, padx=10, fill="x")

# Back button
bulk_back_button = customtkinter.CTkButton(
    master=bottom_frame, 
    text="Back to Semester Selection", 
    command=prev_page,
    height=35  # Make button taller for better visibility
)
bulk_back_button.pack(pady=5, padx=10, fill="x")

# Dictionary to store bulk download content type checkboxes
bulk_type_checkboxes = {}


def toggle_semester_view(semester_id, semester_frame):
    """Toggle the visibility of courses for a semester"""
    global expanded_semesters, semester_course_checkboxes
    
    container = semester_course_checkboxes[semester_id]["container"]
    expand_btn = semester_course_checkboxes[semester_id]["expand_btn"]
    
    if semester_id in expanded_semesters:
        # Collapse
        container.pack_forget()
        expand_btn.configure(text="▼")  # Down arrow
        expanded_semesters.remove(semester_id)
    else:
        # Expand
        container.pack(pady=0, padx=20, fill="x", expand=True)
        expand_btn.configure(text="▲")  # Up arrow
        expanded_semesters.add(semester_id)


def expand_all_semesters():
    """Expand all semesters to show their courses"""
    global expanded_semesters, semester_course_checkboxes
    
    for semester_id, data in semester_course_checkboxes.items():
        container = data["container"]
        expand_btn = data["expand_btn"]
        
        # Always expand
        container.pack(pady=0, padx=20, fill="x", expand=True)
        expand_btn.configure(text="▲")  # Up arrow
        expanded_semesters.add(semester_id)


def toggle_semester_courses(semester_id, checked):
    """Toggle all courses in a semester when the semester checkbox is clicked"""
    if semester_id not in semester_course_checkboxes:
        return
        
    # Set all course checkboxes to match the semester checkbox
    for course_data in semester_course_checkboxes[semester_id]["courses"]:
        course_data["var"].set(1 if checked else 0)


config_username = getCredentials()[0]
config_password = getCredentials()[1]
if config_username != "" and config_password != "":
    # When credentials are already available, start with the semester selection
    page_index = 1
    semester_frame.pack(pady=20, padx=60, fill="both", expand=True)
    load_semesters(config_username, config_password)
else:
    login_frame.pack(pady=20, padx=60, fill="both", expand=True)


# Initialize common content types for the bulk download interface
common_content_types = [
    "All file types",  # New option to dynamically handle all content types
    "Lecture slides", "Assignments", "Course material", "Tutorial", 
    "Exam", "Exam Solutions", "Lab", "Lab Manuals", "Project", 
    "Notes", "Solutions", "Others", "Course Info", "Syllabus"
]

# Set up pages array for navigation
pages = [login_frame, semester_frame, courses_frame, download_frame, all_semesters_frame]
root.mainloop()
