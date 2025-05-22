import requests
from requests.adapters import HTTPAdapter
from requests_ntlm import HttpNtlmAuth
from selectolax.parser import HTMLParser
import os
from dataclasses import dataclass, asdict
import re

DOMAIN = "https://cms.guc.edu.eg"
course_url = "/apps/student/CourseViewStn.aspx?id=175&sid=59"
current_semester_id = None

# Define video file extensions at the start of the file
VIDEO_EXTENSIONS = {
    'mp4', 'mov', 'avi', 'wmv', 'flv', 'mkv', 'webm',  # Common video formats
    'm4v', '3gp', 'mpg', 'mpeg', 'ogg', 'ogv', 'qt',   # Additional formats
    'vob', 'rm', 'rmvb', 'asf', 'divx', 'f4v'          # Less common formats
}

def login(username, password):
    url = "https://apps.guc.edu.eg/student_ext/Console.aspx"
    try:
        print("MY URL: " + url)
        resp = requests.get(url, auth=HttpNtlmAuth(username.strip()+"@student.guc.edu.eg", password))
        print("STATUS: " + str(resp.status_code))
        if (resp.status_code == 200):
              return True
        else:
              return False
    except:
        return False

def get_semesters(username, password):
    """Fetch all available semesters from the CMS."""
    url = "https://cms.guc.edu.eg/apps/student/HomePageStn.aspx"
    resp = requests.get(url, auth=HttpNtlmAuth(username.strip()+"@student.guc.edu.eg", password))
    
    if resp.status_code != 200:
        print("An Error Occurred. Check Credentials And Try Again.")
        return []
    
    html = HTMLParser(resp.text)
    semester_dropdown = html.css_first("#ContentPlaceHolderright_ContentPlaceHoldercontent_ddlSemester")
    
    if not semester_dropdown:
        return []
        
    semesters = []
    for option in semester_dropdown.css("option"):
        semester_id = option.attributes.get("value")
        semester_name = option.text()
        semesters.append({"id": semester_id, "name": semester_name})
    
    return semesters

def set_semester(username, password, semester_id):
    """Set the active semester."""
    global current_semester_id
    
    if not semester_id:
        return False
    
    url = "https://cms.guc.edu.eg/apps/student/HomePageStn.aspx"
    
    # First get the page to extract the viewstate and other form fields
    resp = requests.get(url, auth=HttpNtlmAuth(username.strip()+"@student.guc.edu.eg", password))
    
    if resp.status_code != 200:
        print("An Error Occurred. Check Credentials And Try Again.")
        return False
    
    html = HTMLParser(resp.text)
    
    # Extract form fields
    viewstate = html.css_first("#__VIEWSTATE").attributes.get("value", "")
    viewstategenerator = html.css_first("#__VIEWSTATEGENERATOR").attributes.get("value", "")
    eventvalidation = html.css_first("#__EVENTVALIDATION").attributes.get("value", "")
    
    # Prepare form data for POST request
    form_data = {
        "__EVENTTARGET": "ctl00$ContentPlaceHolderright$ContentPlaceHoldercontent$ddlSemester",
        "__EVENTARGUMENT": "",
        "__VIEWSTATE": viewstate,
        "__VIEWSTATEGENERATOR": viewstategenerator,
        "__EVENTVALIDATION": eventvalidation,
        "ctl00$ContentPlaceHolderright$ContentPlaceHoldercontent$ddlSemester": semester_id
    }
    
    # Make POST request to change semester
    resp = requests.post(url, data=form_data, auth=HttpNtlmAuth(username.strip()+"@student.guc.edu.eg", password))
    
    if resp.status_code == 200:
        current_semester_id = semester_id
        return True
    else:
        print(f"Failed to set semester. Status code: {resp.status_code}")
        return False

def update_course_url(username, password, selected_course):
    global course_url

    url = "https://cms.guc.edu.eg/apps/student/HomePageStn.aspx"
    resp = requests.get(url, auth=HttpNtlmAuth(username.strip()+"@student.guc.edu.eg", password))

    if resp.status_code != 200:
            print("An Error Occurred. Check Credentials And Try Again.")
            return
    
    html = HTMLParser(resp.text)
    all_courses = html.css("table#ContentPlaceHolderright_ContentPlaceHoldercontent_GridViewcourses tr")[1:]

    for course in all_courses:
        course_name = course.css("td")[1].text()
        course_name = course_name[course_name.find("|)") + 3: course_name.find(" (")]
        if selected_course == course_name:
            course_url = "/apps/student/CourseViewStn.aspx?id=" + course.css("td")[4].text() + "&sid=" + course.css("td")[5].text()
            break
    
    
      

def get_courses(username, password, semester_id=None):
    url = "https://cms.guc.edu.eg/apps/student/HomePageStn.aspx"
    
    # If a semester ID is provided, set it as the active semester
    if semester_id:
        if not set_semester(username, password, semester_id):
            print("Failed to set semester.")
            return []
    
    resp = requests.get(url, auth=HttpNtlmAuth(username.strip()+"@student.guc.edu.eg", password))
    if resp.status_code != 200:
            print("An Error Occurred. Check Credentials And Try Again.")
            return []
    
    html = HTMLParser(resp.text)
    final_courses=[]
    all_courses = html.css("table#ContentPlaceHolderright_ContentPlaceHoldercontent_GridViewcourses tr")[1:]

    for course in all_courses:
        course_name = course.css("td")[1].text()
        course_name = course_name[course_name.find("|)") + 3: course_name.find(" (")]
        final_courses.append(course_name)

    return final_courses


def get_types(username, password):
    global DOMAIN, course_url
    resp = requests.get(DOMAIN + course_url, auth=HttpNtlmAuth(username+"@student.guc.edu.eg", password))
    
    if resp.status_code != 200:
            print("An Error Occurred. Check Credentials And Try Again.")
            return {'types': [], 'course_name': 'Unknown', 'success': False}
    
    html = HTMLParser(resp.text)
    all_cards = html.css(".card-body")
    
    # Extract course name from page title
    course_name_elem = html.css_first("#ContentPlaceHolderright_ContentPlaceHoldercontent_LabelCourseName")
    if course_name_elem:
        course_full_name = course_name_elem.text()
        # Try to extract the clean course name
        if "|)" in course_full_name and " (" in course_full_name:
            course_name = course_full_name[course_full_name.find("|)") + 3: course_full_name.find(" (")]
        else:
            course_name = course_full_name.strip()
    else:
        course_name = "Unknown Course"
    
    all_types = []

    # Use improved content type detection
    for card in all_cards:
        try:
            card_title_div = card.css_first("div")
            if not card_title_div:
                continue
                
            title_text = card_title_div.text().strip().split("\n")[0]
              # Extract content type with the same enhanced detection logic
            if "(" in title_text and ")" in title_text:
                # Standard format with parentheses
                title = title_text[title_text.find("(")+1 : title_text.find(")")]
            elif "vod" in title_text.lower() or "video on demand" in title_text.lower():
                # Special handling for video content
                title = "VoD"
            elif "exam" in title_text.lower():
                # Special handling for exam-related content
                if "solution" in title_text.lower():
                    title = "Exam Solutions"
                else:
                    title = "Exam"
            elif "lab" in title_text.lower():
                # Special handling for lab materials
                if "manual" in title_text.lower():
                    title = "Lab Manuals"
                else:
                    title = "Lab"
            elif "-" in title_text:
                # Try extracting from text with hyphens
                title_parts = title_text.split('-')
                title = title_parts[0].strip()
            else:
                # Default categorization based on common keywords
                lower_text = title_text.lower()
                if "lecture" in lower_text or "lect" in lower_text:
                    title = "Lecture slides"
                elif "assignment" in lower_text or "hw" in lower_text:
                    title = "Assignments"
                elif "tutorial" in lower_text or "tut" in lower_text:
                    title = "Tutorial"
                elif "project" in lower_text:
                    title = "Project"
                elif "note" in lower_text:
                    title = "Notes"
                elif "solution" in lower_text:
                    title = "Solutions"
                else:
                    title = "Others"
            
            if title and title not in all_types:
                all_types.append(title)
        except:
            continue

    return {'types': all_types, 'course_name': course_name}
        

def download_content(username, password, types, semester_name=None):
    global DOMAIN, course_url
    resp = requests.get(DOMAIN + course_url, auth=HttpNtlmAuth(username+"@student.guc.edu.eg", password))
    
    if resp.status_code != 200:
            print("An Error Occurred. Check Credentials And Try Again.")
            return {'exam_sched': [], 'success' : False}
    
    html = HTMLParser(resp.text)
    all_cards = html.css(".card-body")
    all_types = []
    
    # Get course name for folder structure
    course_full_name = html.css_first("#ContentPlaceHolderright_ContentPlaceHoldercontent_LabelCourseName").text()
    course_name = course_full_name[course_full_name.find("|)") + 3: course_full_name.find(" (")]
    
    # Create base directory structure
    base_dir = "Downloads"
    if not os.path.exists(base_dir):
        os.mkdir(base_dir)
    
    # Create semester directory if provided
    if semester_name:
        semester_dir = os.path.join(base_dir, semester_name)
        if not os.path.exists(semester_dir):
            os.mkdir(semester_dir)
        course_dir = os.path.join(semester_dir, course_name)
    else:
        course_dir = os.path.join(base_dir, course_name)
    
    # Create course directory
    if not os.path.exists(course_dir):
        os.mkdir(course_dir)
    
    # Process content to download
    for card in all_cards:
            title = card.css_first("div").text().strip().split("\n")[0]
            title = title[title.find("(")+1 : title.find(")")]
            
            if title not in all_types:
                all_types.append(title)
            
            if (title in types):
                # Create type directory (e.g., "Lecture slides", "Assignments")
                type_dir = os.path.join(course_dir, title)
                if not os.path.exists(type_dir):
                    os.mkdir(type_dir)
                
                lecture_title = card.css_first("div strong").text().split(" - ")[1]
                link = card.css_first("a").attributes.get('href')
                file_format = link.split(".")[1]
                
                print(f"Downloading: {DOMAIN + link}")
                download_resp = requests.get(DOMAIN + link, auth=HttpNtlmAuth(username+"@student.guc.edu.eg", password))
                print(f"DOWNLOAD STATUS: {download_resp.status_code}")
                
                file_name = f"{course_name} - {lecture_title}.{file_format}"
                file_path = os.path.join(type_dir, file_name)
                
                with open(file_path, "wb") as file:
                    file.write(download_resp.content)
                    print(f"Saved: {file_path}")
    
    return all_types

def get_all_semesters_with_courses(username, password):
    """Fetches all semesters with their courses from the View All Courses page."""
    url = "https://cms.guc.edu.eg/apps/student/ViewAllCourseStn"
    resp = requests.get(url, auth=HttpNtlmAuth(username.strip()+"@student.guc.edu.eg", password))
    
    if resp.status_code != 200:
        print("An Error Occurred. Check Credentials And Try Again.")
        return []
    
    html = HTMLParser(resp.text)
    semester_sections = []
    
    # Each semester section has a card with season info and a table with courses
    card_sections = html.css(".card-hover-shadow")
    
    for section in card_sections:
        # Extract semester info
        try:
            header = section.css_first(".menu-header-title")
            if not header:
                continue
                
            semester_text = header.text().strip()
            # Extract semester ID and name using regex
            match = re.search(r'Season : (\d+)\s*,\s*Title: (.*)', semester_text)
            if not match:
                continue
                
            semester_id = match.group(1).strip()
            semester_name = match.group(2).strip()
            
            # Extract courses from the table
            courses = []
            table = section.css_first("table")
            if not table:
                continue
                
            rows = table.css("tr")[1:]  # Skip header row
            
            for row in rows:
                cells = row.css("td")
                if len(cells) < 5:
                    continue
                    
                # Extract course info
                course_name = cells[1].text().strip()
                course_status = cells[2].text().strip()
                course_id = cells[3].text().strip()
                course_semester_id = cells[4].text().strip()
                
                if course_status == "Active":
                    courses.append({
                        "id": course_id,
                        "name": course_name,
                        "semesterId": course_semester_id
                    })
            
            semester_sections.append({
                "id": semester_id,
                "name": semester_name,
                "courses": courses,
                "isCurrent": "Current Season" in section.text()
            })
            
        except Exception as e:
            print(f"Error processing semester section: {str(e)}")
            continue
    
    return semester_sections

def download_course_content(username, password, course, semester_name=None, selected_types=None, download_all_types=False):
    """Download content from a specific course.
    
    Args:
        username: User's CMS username
        password: User's CMS password
        course: Dictionary containing course information
        semester_name: Name of the semester for folder structure
        selected_types: List of content types to download or None for all types
        download_all_types: If True, dynamically create folders for all detected content types
    """
    global DOMAIN
    
    # Extract course ID and semester ID from the course object
    course_id = course.get("id")
    semester_id = course.get("semesterId")
    course_name = course.get("name")
    
    # Clean up course name for folder structure
    if "(" in course_name:
        course_name = course_name[course_name.find("|)") + 3: course_name.find(" (")]
    
    # Construct course URL
    course_url = f"/apps/student/CourseViewStn.aspx?id={course_id}&sid={semester_id}"
    resp = requests.get(DOMAIN + course_url, auth=HttpNtlmAuth(username+"@student.guc.edu.eg", password))
    
    if resp.status_code != 200:
        print(f"An Error Occurred accessing course {course_name}. Status: {resp.status_code}")
        return []
    
    html = HTMLParser(resp.text)
    all_cards = html.css(".card-body")
    
    # Create base directory structure
    base_dir = "Downloads"
    if not os.path.exists(base_dir):
        os.makedirs(base_dir, exist_ok=True)
    
    # Create semester directory
    if semester_name:
        semester_dir = os.path.join(base_dir, semester_name)
        if not os.path.exists(semester_dir):
            os.makedirs(semester_dir, exist_ok=True)
        course_dir = os.path.join(semester_dir, course_name)
    else:
        course_dir = os.path.join(base_dir, course_name)
    
    # Create course directory
    if not os.path.exists(course_dir):
        os.makedirs(course_dir, exist_ok=True)
      
    # Get all available content types - using improved parsing for more reliable extraction
    content_types = []
    content_type_map = {}  # Maps raw content types to standardized names
    
    # First pass: identify all content types
    for card in all_cards:
        try:
            # Get the card title div
            card_title_div = card.css_first("div")
            if not card_title_div:
                continue
                
            title_text = card_title_div.text().strip().split("\n")[0]
            raw_title = title_text  # Keep the raw title for reference
            
            # Enhanced content type detection with better categorization
            # First try the standard format with parentheses
            if "(" in title_text and ")" in title_text:
                # Standard format with parentheses
                title = title_text[title_text.find("(")+1 : title_text.find(")")]
            elif "vod" in title_text.lower() or "video on demand" in title_text.lower():
                # Special handling for video content
                title = "VoD"
            elif "exam" in title_text.lower():
                # Special handling for exam-related content
                if "solution" in title_text.lower():
                    title = "Exam Solutions"
                else:
                    title = "Exam"
            elif "lab" in title_text.lower():
                # Special handling for lab materials
                if "manual" in title_text.lower():
                    title = "Lab Manuals"
                else:
                    title = "Lab"
            elif "-" in title_text:
                # Try extracting from text with hyphens
                title_parts = title_text.split('-')
                title = title_parts[0].strip()
            else:
                # Default categorization based on common keywords
                lower_text = title_text.lower()
                if "lecture" in lower_text or "lect" in lower_text:
                    title = "Lecture slides"
                elif "assignment" in lower_text or "hw" in lower_text:
                    title = "Assignments"
                elif "tutorial" in lower_text or "tut" in lower_text:
                    title = "Tutorial"
                elif "project" in lower_text:
                    title = "Project"
                elif "note" in lower_text:
                    title = "Notes"
                elif "solution" in lower_text:
                    title = "Solutions"
                else:
                    title = "Others"
            
            # Clean up the title to avoid spaces at the beginning or end
            title = title.strip()
            
            if title and title not in content_types:
                content_types.append(title)
                
            # Store mapping of raw title to standardized title
            content_type_map[raw_title] = title
                
        except Exception as e:
            print(f"Error detecting content type: {str(e)}")
            continue
    
    # If download_all_types is enabled, use all detected types
    # Otherwise, filter by the selected types
    types_to_download = []
    if download_all_types:
        types_to_download = content_types
    else:
        # If no specific types requested, download all available types
        if not selected_types:
            types_to_download = content_types
        else:
            types_to_download = [t for t in content_types if t in selected_types]
    
    # Process and download content
    downloaded_files = []
    for card in all_cards:
        try:
            card_title_div = card.css_first("div")
            if not card_title_div:
                continue
                
            title_text = card_title_div.text().strip().split("\n")[0]
            raw_title = title_text  # Keep the raw title for matching
            
            # Skip any VoD content early to avoid unnecessary processing
            if any(term in title_text.lower() for term in ["vod", "video on demand", "video", "recorded lecture"]):
                print(f"Skipping VoD content: {title_text}")
                continue
            
            # Use our stored mapping to get the standardized content type
            if raw_title in content_type_map:
                title = content_type_map[raw_title]
            else:
                # Use the enhanced detection logic as fallback
                if "(" in title_text and ")" in title_text:
                    title = title_text[title_text.find("(")+1 : title_text.find(")")]
                elif "exam" in title_text.lower():
                    title = "Exam Solutions" if "solution" in title_text.lower() else "Exam"
                elif "lab" in title_text.lower():
                    title = "Lab Manuals" if "manual" in title_text.lower() else "Lab"
                elif "-" in title_text:
                    title_parts = title_text.split('-')
                    title = title_parts[0].strip()
                else:
                    lower_text = title_text.lower()
                    if "lecture" in lower_text or "lect" in lower_text:
                        title = "Lecture slides"
                    elif "assignment" in lower_text or "hw" in lower_text:
                        title = "Assignments"
                    elif "tutorial" in lower_text or "tut" in lower_text:
                        title = "Tutorial"
                    elif "project" in lower_text:
                        title = "Project"
                    elif "note" in lower_text:
                        title = "Notes"
                    elif "solution" in lower_text:
                        title = "Solutions"
                    else:
                        title = "Others"
                
                # Clean up the title to avoid spaces at the beginning or end
                title = title.strip()
            
            # Check if this content type should be downloaded
            if title in types_to_download or download_all_types:
                # Skip any content labeled as VoD (Video on Demand)
                if "vod" in title_text.lower() or "video on demand" in title_text.lower():
                    print(f"Skipping VoD content: {title_text}")
                    continue
                
                # Create type directory - ensure the title is properly cleaned up to avoid trailing spaces
                type_dir = os.path.join(course_dir, title.strip())
                try:
                    if not os.path.exists(type_dir):
                        os.makedirs(type_dir, exist_ok=True)
                except Exception as e:
                    print(f"Error creating directory {type_dir}: {str(e)}")
                    # Try an alternative directory name if there was an error
                    sanitized_title = re.sub(r'[\\/*?:"<>|]', "", title).strip()
                    type_dir = os.path.join(course_dir, sanitized_title)
                    os.makedirs(type_dir, exist_ok=True)
                
                # Extract lecture title with more robust handling
                title_elem = card.css_first("div strong")
                
                # Safer parsing of lecture title
                if title_elem:
                    title_text = title_elem.text()
                    if " - " in title_text:
                        try:
                            lecture_title = title_text.split(" - ")[1].strip()
                        except IndexError:
                            lecture_title = title_text.strip()
                    else:
                        lecture_title = title_text.strip()
                        
                    # Skip if the lecture title contains VoD indicators
                    if "vod" in lecture_title.lower() or "video" in lecture_title.lower():
                        print(f"Skipping VoD content: {lecture_title}")
                        continue
                else:
                    # If no strong element, use a fallback name
                    lecture_title = f"File_{len(downloaded_files)+1}"
                
                # Find download link with better error handling
                link_elem = card.css_first("a")
                if not link_elem or not link_elem.attributes.get('href'):
                    print(f"No download link found for {lecture_title}")
                    continue
                    
                link = link_elem.attributes.get('href')
                
                # Handle file extension more carefully
                if "." in link:
                    file_format = link.split(".")[-1]  # Use -1 to handle cases where there are multiple dots
                    
                    # Skip known video file formats
                    if file_format.lower() in VIDEO_EXTENSIONS:
                        print(f"Skipping video file: {lecture_title}.{file_format}")
                        continue
                else:
                    file_format = "pdf"  # Default to PDF if no extension
                
                # Clean the lecture title to avoid invalid file names
                lecture_title = re.sub(r'[\\/*?:"<>|]', "", lecture_title)  # Remove invalid file characters
                
                print(f"Downloading: {course_name} - {lecture_title}.{file_format}")
                
                # Add retries for more reliable downloads
                max_retries = 3
                retry_count = 0
                
                while retry_count < max_retries:
                    try:
                        download_resp = requests.get(DOMAIN + link, auth=HttpNtlmAuth(username+"@student.guc.edu.eg", password))
                        
                        if download_resp.status_code == 200:
                            file_name = f"{course_name} - {lecture_title}.{file_format}"
                            file_path = os.path.join(type_dir, file_name)
                            
                            with open(file_path, "wb") as file:
                                file.write(download_resp.content)
                            
                            print(f"Saved: {file_path}")
                            downloaded_files.append(file_path)
                            break  # Success, exit retry loop
                        else:
                            print(f"Failed download attempt {retry_count+1}: {lecture_title}. Status: {download_resp.status_code}")
                            retry_count += 1
                    except Exception as e:
                        print(f"Error downloading {lecture_title} (attempt {retry_count+1}): {str(e)}")
                        retry_count += 1
                        
                if retry_count == max_retries:
                    print(f"Failed to download {lecture_title} after {max_retries} attempts.")        
        except Exception as e:
            print(f"Error processing card: {str(e)}")
            # Track the failure but continue with other files
            continue
    
    return {
        "course_name": course_name,
        "content_types": content_types,
        "downloaded_files": downloaded_files
    }

def download_all_content(username, password, semester_selections=None, type_filter=None, download_all_types=False):
    """Download content from specific courses in selected semesters.
    
    Args:
        username: User's CMS username
        password: User's CMS password
        semester_selections: Dictionary with semester IDs as keys and either "all" or a list of course IDs as values
        type_filter: List of content types to download or None for all types
        download_all_types: If True, dynamically create folders for new content types
        
    Returns:
        Dictionary with download statistics
    """
    print("Fetching all semesters and courses...")
    all_semesters = get_all_semesters_with_courses(username, password)
    
    if not all_semesters:
        print("No semesters found or error occurred.")
        return {"success": False, "error": "No semesters found"}
    
    # Determine which semesters and courses to process
    if not semester_selections:
        # Default to current semester if no selections provided
        for semester in all_semesters:
            if semester.get("isCurrent", False):
                semester_selections = {semester["id"]: "all"}
                break
    
    if not semester_selections:
        print("No semesters selected and no current semester found.")
        return {"success": False, "error": "No semesters selected"}
    
    # Statistics tracking
    stats = {
        "total_downloads": 0,
        "total_failures": 0,
        "semesters_processed": 0,
        "courses_processed": 0,
        "files_by_semester": {},
        "files_by_type": {}
    }
    
    # Process each selected semester
    for semester in all_semesters:
        semester_id = semester["id"]
        semester_name = semester["name"]
        
        # Skip if this semester wasn't selected
        if semester_id not in semester_selections:
            continue
            
        print(f"\n{'='*50}\nProcessing semester: {semester_name}\n{'='*50}")
        stats["semesters_processed"] += 1
        stats["files_by_semester"][semester_name] = 0
        
        courses = semester.get("courses", [])
        if not courses:
            print(f"No courses found for semester {semester_name}")
            continue
        
        # Get the course selection for this semester
        course_selection = semester_selections[semester_id]
        selected_courses = []
        
        if course_selection == "all":
            # Download all courses for this semester
            selected_courses = courses
        else:
            # Filter by selected course IDs
            for course in courses:
                if course["id"] in course_selection:
                    selected_courses.append(course)
        
        if not selected_courses:
            print(f"No courses selected for semester {semester_name}")
            continue
            
        print(f"Found {len(selected_courses)} courses to download")
        
        # Process each selected course
        for i, course in enumerate(selected_courses):
            course_name = course.get("name", "Unknown Course")
            print(f"\n[{i+1}/{len(selected_courses)}] Processing course: {course_name}")
            
            try:
                # Pass the download_all_types flag to download_course_content
                result = download_course_content(username, password, course, semester_name, type_filter, download_all_types)
                stats["courses_processed"] += 1
                
                if result and "downloaded_files" in result:
                    downloaded_count = len(result["downloaded_files"])
                    stats["total_downloads"] += downloaded_count
                    stats["files_by_semester"][semester_name] += downloaded_count
                    
                    # Track downloads by content type
                    for file_path in result["downloaded_files"]:
                        # Extract content type from path - typically the parent directory of the file
                        path_parts = os.path.normpath(file_path).split(os.sep)
                        if len(path_parts) > 2:  # Should be at least Downloads/Type/file.ext
                            content_type = path_parts[-2]  # Second to last element is the content type directory
                            if content_type not in stats["files_by_type"]:
                                stats["files_by_type"][content_type] = 0
                            stats["files_by_type"][content_type] += 1
                        
                    print(f"Downloaded {downloaded_count} files from {course_name}")
                else:
                    print(f"No files downloaded from {course_name}")
            except Exception as e:
                print(f"Error processing course {course_name}: {str(e)}")
                stats["total_failures"] += 1
    
    # Print download summary
    print(f"\n{'='*50}")
    print(f"DOWNLOAD SUMMARY")
    print(f"{'='*50}")
    print(f"Total files downloaded: {stats['total_downloads']}")
    print(f"Semesters processed: {stats['semesters_processed']}")
    print(f"Courses processed: {stats['courses_processed']}")
    print(f"Failed downloads: {stats['total_failures']}")
    
    print("\nFiles by semester:")
    for sem_name, count in stats["files_by_semester"].items():
        print(f"  - {sem_name}: {count} files")
    
    print("\nFiles by content type:")
    for content_type, count in stats["files_by_type"].items():
        print(f"  - {content_type}: {count} files")
    
    print(f"{'='*50}")
    
    return {
        "success": True,
        "stats": stats
    }