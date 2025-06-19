import requests
from requests.adapters import HTTPAdapter
from requests_ntlm import HttpNtlmAuth
from selectolax.parser import HTMLParser
import os
from dataclasses import dataclass, asdict
from scraper import parse_courses_html_from_url
import re
from vod_downloader import download_single_video

DOMAIN = "https://cms.guc.edu.eg"
course_url = "/apps/student/CourseViewStn.aspx?id=175&sid=59"
current_session_name = ""  # Global variable to store current session name

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


def update_course_url(username, password, selected_course):
    global course_url, current_session_name

    # Get all courses from all sessions
    all_courses_by_season = parse_courses_html_from_url(username, password)
    
    # Find the selected course across all sessions
    for season_title, courses in all_courses_by_season.items():
        for course in courses:
            if course['name'] == selected_course:
                course_url = "/apps/student/CourseViewStn.aspx?id=" + course['id'] + "&sid=" + course['sid']
                current_session_name = season_title  # Store the session name
                return
    
    # Fallback to old method if not found
    url = "https://cms.guc.edu.eg/apps/student/HomePageStn.aspx"
    resp = requests.get(url, auth=HttpNtlmAuth(username.strip()+"@student.guc.edu.eg", password))

    if resp.status_code != 200:
            print("An Error Occurred. Check Credentials And Try Again.")
            return
    
    html = HTMLParser(resp.text)
    all_courses = html.css("table#ContentPlaceHolderright_ContentPlaceHoldercontent_GridViewcourses tr")[1:]

    for course in all_courses:
        course_name = course.css("td")[1].text()
        # Use the same parsing logic as the scraper to remove pipes and brackets
        # Use regex to extract code and name, ignore all bracketed content at the end
        match = re.match(r"\(\|([A-Za-z0-9 ]+)\|\)\s*([^(]+?)(?:\s*\([^)]*\))*$", course_name)
        if match:
            code = match.group(1).strip()
            name = match.group(2).strip()
            # Format as "Course Name (CODE)" for consistency
            clean_name = f"{name} ({code})" if code else name
        else:
            # fallback: remove last bracketed number if present
            clean_name = re.sub(r"\s*\([^)]*\)\s*$", "", course_name).strip()
        # Normalize whitespace to a single space
        clean_name = re.sub(r"\s+", " ", clean_name)
        if selected_course == clean_name:
            course_url = "/apps/student/CourseViewStn.aspx?id=" + course.css("td")[4].text() + "&sid=" + course.css("td")[5].text()
            current_session_name = "Unknown Session"  # Fallback session name
            break
    
    
      

def get_courses(username, password):
    """Get all courses from all sessions using the scraper"""
    all_courses_by_season = parse_courses_html_from_url(username, password)
    
    if not all_courses_by_season:
        # Fallback to old method if scraper fails
        url = "https://cms.guc.edu.eg/apps/student/HomePageStn.aspx"
        resp = requests.get(url, auth=HttpNtlmAuth(username.strip()+"@student.guc.edu.eg", password))
        if resp.status_code != 200:
                print("An Error Occurred. Check Credentials And Try Again.")
                return []
        
        html = HTMLParser(resp.text)
        final_courses=[]
        all_courses = html.css("table#ContentPlaceHolderright_ContentPlaceHoldercontent_GridViewcourses tr")[1:]

        for course in all_courses:
            course_name = course.css("td")[1].text()
            # Use the same parsing logic as the scraper to remove pipes and brackets
            # Use regex to extract code and name, ignore all bracketed content at the end
            match = re.match(r"\(\|([A-Za-z0-9 ]+)\|\)\s*([^(]+?)(?:\s*\([^)]*\))*$", course_name)
            if match:
                code = match.group(1).strip()
                name = match.group(2).strip()
                # Format as "Course Name (CODE)" for consistency
                clean_name = f"{name} ({code})" if code else name
            else:
                # fallback: remove last bracketed number if present
                clean_name = re.sub(r"\s*\([^)]*\)\s*$", "", course_name).strip()
            # Normalize whitespace to a single space
            clean_name = re.sub(r"\s+", " ", clean_name)
            final_courses.append(clean_name)

        return final_courses
    
    # Format courses for dropdown with session categorization
    formatted_courses = []
    for season_title, courses in all_courses_by_season.items():
        # Add session header
        formatted_courses.append(f"--- {season_title} ---")
        # Add courses under this session
        for course in courses:
            # Format as "Course Name (CODE)" for dropdown display
            formatted_courses.append(f"  {course['name']}")
    
    return formatted_courses


def get_course_info_from_formatted_name(formatted_course_name, username, password):
    """Extract actual course name from formatted dropdown option"""
    if formatted_course_name.startswith("---") and formatted_course_name.endswith("---"):
        return None  # This is a session header
    
    # Remove the leading spaces and get the actual course name
    actual_course_name = formatted_course_name.strip()
    
    # Get all courses to find the matching one
    all_courses_by_season = parse_courses_html_from_url(username, password)
    
    for season_title, courses in all_courses_by_season.items():
        for course in courses:
            if course['name'] == actual_course_name:
                return {
                    'name': course['name'],
                    'id': course['id'],
                    'sid': course['sid']
                }
    
    return None

def get_types(username, password):
    global DOMAIN, course_url
    resp = requests.get(DOMAIN + course_url, auth=HttpNtlmAuth(username+"@student.guc.edu.eg", password))
    
    if resp.status_code != 200:
            print("An Error Occurred. Check Credentials And Try Again.")
            return {'exam_sched': [], 'success' : False}
    
    html = HTMLParser(resp.text)
    all_cards = html.css(".card-body")
    course_name = html.css_first("#ContentPlaceHolderright_ContentPlaceHoldercontent_LabelCourseName").text()
    # Use the same parsing logic as the scraper to remove pipes and brackets
    # Use regex to extract code and name, ignore all bracketed content at the end
    match = re.match(r"\(\|([A-Za-z0-9 ]+)\|\)\s*([^(]+?)(?:\s*\([^)]*\))*$", course_name)
    if match:
        code = match.group(1).strip()
        name = match.group(2).strip()
        # Format as "Course Name (CODE)" for consistency
        course_name = f"{name} ({code})" if code else name
    else:
        # fallback: remove last bracketed number if present
        course_name = re.sub(r"\s*\([^)]*\)\s*$", "", course_name).strip()
    # Normalize whitespace to a single space
    course_name = re.sub(r"\s+", " ", course_name)
    all_types = []

    for card in all_cards:
            title = card.css_first("div").text().strip().split("\n")[0]
            # Extract content type from the last set of parentheses
            last_open = title.rfind("(")
            last_close = title.rfind(")")
            if last_open != -1 and last_close != -1 and last_close > last_open:
                title = title[last_open + 1 : last_close]
            
            if title not in all_types:
                all_types.append(title)

    return {'types' : all_types, 'course_name' : course_name}
        

def download_content(username, password, types, progress_callback=None, cancellation_check=None, output_folder=None, org_mode='type', include_week=True, include_type=False):
    global DOMAIN, course_url, current_session_name
    if not types:
        print("No content types selected. Aborting download.")
        return {'exam_sched': [], 'success': False, 'error': 'No content types selected.'}
    resp = requests.get(DOMAIN + course_url, auth=HttpNtlmAuth(username+"@student.guc.edu.eg", password))

    if resp.status_code != 200:
            print("An Error Occurred. Check Credentials And Try Again.")
            return {'exam_sched': [], 'success' : False}

    html = HTMLParser(resp.text)

    # 1. Parse weeks, reverse them to be in chronological order, and map content to a week number
    content_to_week_map = {}
    all_weeks = html.css(".card.mb-5.weeksdata")
    all_weeks.reverse() # Weeks in HTML are newest to oldest, reverse for chronological order (Week 1, 2, 3...)

    for week_number, week_div in enumerate(all_weeks, 1):
        content_items = week_div.css("div[id^=content]")
        for item in content_items:
            content_id = item.id
            content_to_week_map[content_id] = week_number

    all_cards = html.css(".card-body")
    all_types = []

    # Count total files to download for progress tracking
    total_files = 0
    files_to_download = []

    for card in all_cards:
            title = card.css_first("div").text().strip().split("\n")[0]
            # Extract content type from the last set of parentheses
            last_open = title.rfind("(")
            last_close = title.rfind(")")
            if last_open != -1 and last_close != -1 and last_close > last_open:
                title = title[last_open + 1 : last_close]

            if title not in all_types:
                all_types.append(title)

            if (title in types):
                total_files += 1
                files_to_download.append(card)

    # Create a mapping from file content types to selected filter names
    # This handles cases where the file's internal type doesn't exactly match the filter name
    content_type_mapping = {}
    for card in all_cards:
        file_content_type = card.css_first("div").text().strip().split("\n")[0]
        # Extract content type from the last set of parentheses
        last_open = file_content_type.rfind("(")
        last_close = file_content_type.rfind(")")
        if last_open != -1 and last_close != -1 and last_close > last_open:
            file_content_type = file_content_type[last_open + 1 : last_close]

        # Find which selected filter this file belongs to
        for selected_type in types:
            # Check if the file content type is contained in the selected filter name
            # or if the selected filter name is contained in the file content type
            if (file_content_type.lower() in selected_type.lower() or
                selected_type.lower() in file_content_type.lower() or
                file_content_type == selected_type):
                content_type_mapping[file_content_type] = selected_type
                break

    # Download files with progress tracking
    downloaded_files = 0
    for card in files_to_download:
        # Check for cancellation before each download
        if cancellation_check and cancellation_check():
            print("Download cancelled by user")
            return all_types

        file_content_type = card.css_first("div").text().strip().split("\n")[0]
        # Extract content type from the last set of parentheses
        last_open = file_content_type.rfind("(")
        last_close = file_content_type.rfind(")")
        if last_open != -1 and last_close != -1 and last_close > last_open:
            file_content_type = file_content_type[last_open + 1 : last_close]

        if (file_content_type in types):
            course_name = html.css_first("#ContentPlaceHolderright_ContentPlaceHoldercontent_LabelCourseName").text()
            # Use the same parsing logic as the scraper to remove pipes and brackets
            # Use regex to extract code and name, ignore all bracketed content at the end
            match = re.match(r"\(\|([A-Za-z0-9 ]+)\|\)\s*([^(]+?)(?:\s*\([^)]*\))*$", course_name)
            if match:
                code = match.group(1).strip()
                name = match.group(2).strip()
                # Format as "Course Name (CODE)" for folder naming
                course_name = f"{name} ({code})" if code else name
            else:
                # fallback: remove last bracketed number if present
                course_name = re.sub(r"\s*\([^)]*\)\s*$", "", course_name).strip()
            # Normalize whitespace to a single space
            course_name = re.sub(r"\s+", " ", course_name)

            # 2. Get week number and create the new prefixed title
            content_id_div = card.css_first("div[id^=content]")
            content_id = content_id_div.id if content_id_div else None
            week_num = content_to_week_map.get(content_id) if content_id else None

            lecture_title_raw = card.css_first("div strong").text()
            # Remove the numeric prefix like "1 - " to get the base title
            lecture_title = re.sub(r'^\d+\s*-\s*', '', lecture_title_raw).strip()

            # Use output_folder as root if provided
            root_folder = output_folder if output_folder else os.getcwd()

            # Create session folder first
            session_folder = os.path.join(root_folder, current_session_name.rstrip())
            try:
                os.makedirs(session_folder, exist_ok=True)
            except OSError as error:
                print(error)

            # Create course folder inside session folder
            course_folder_path = os.path.join(session_folder, course_name.rstrip())
            try:
                os.makedirs(course_folder_path, exist_ok=True)
            except OSError as error:
                print(error)

            # Determine file path base depending on org_mode and toggles
            if org_mode == 'type':
                # Use the mapped filter name for the subfolder (or fallback to file content type)
                filter_name = content_type_mapping.get(file_content_type, file_content_type).rstrip()
                filter_folder = os.path.join(course_folder_path, filter_name)
                try:
                    os.makedirs(filter_folder, exist_ok=True)
                except OSError as error:
                    print(error)
                # Filename prefix logic
                name_parts = []
                if include_week and week_num:
                    name_parts.append(f"Week {str(week_num).rstrip()}")
                if include_type:
                    name_parts.append(f"({file_content_type.rstrip()})")
                name_parts.append(lecture_title.rstrip())
                file_name = " - ".join(name_parts).rstrip()
                file_path_base = os.path.join(filter_folder, file_name)
            elif org_mode == 'week':
                # Organize by week number
                week_folder = f"Week {str(week_num).rstrip()}" if week_num else "No Week"
                week_folder_path = os.path.join(course_folder_path, week_folder.rstrip())
                try:
                    os.makedirs(week_folder_path, exist_ok=True)
                except OSError as error:
                    print(error)
                # Filename prefix logic
                name_parts = []
                if include_week and week_num:
                    name_parts.append(f"Week {str(week_num).rstrip()}")
                if include_type:
                    name_parts.append(f"({file_content_type.rstrip()})")
                name_parts.append(lecture_title.rstrip())
                file_name = " - ".join(name_parts).rstrip()
                file_path_base = os.path.join(week_folder_path, file_name)
            else:
                # Flat structure
                name_parts = []
                if include_week and week_num:
                    name_parts.append(f"Week {str(week_num).rstrip()}")
                if include_type:
                    name_parts.append(f"({file_content_type.rstrip()})")
                name_parts.append(lecture_title.rstrip())
                file_name = " - ".join(name_parts).rstrip()
                file_path_base = os.path.join(course_folder_path, file_name)

            if file_content_type.lower().rstrip() == "vod":
                file_path = file_path_base + ".mkv"
                # Check if file already exists, skip if so
                if os.path.exists(file_path):
                    print(f"File already exists, skipping: {file_path}")
                    downloaded_files += 1
                    if progress_callback:
                        progress_callback(downloaded_files, total_files, lecture_title, "VoD")
                    continue

                # Find the input with class 'vodbutton' and get its id as contentId
                vod_input = card.css_first("input.vodbutton")
                if vod_input is not None:
                    vod_content_id = vod_input.attributes.get('id')
                    if vod_content_id:
                        # Call the VoD downloader
                        download_single_video(vod_content_id, file_path, username, password)
                        downloaded_files += 1
                        if progress_callback:
                            progress_callback(downloaded_files, total_files, lecture_title, "VoD")
                        continue
                    else:
                        print(f"Could not find contentId for VoD file: {lecture_title}")
                        continue
                else:
                    print(f"Could not find vodbutton input for VoD file: {lecture_title}")
                    continue
            else:
                # Regular file download
                link_tag = card.css_first("a")
                if not link_tag or not link_tag.attributes.get('href'):
                    print(f"Could not find download link for: {lecture_title}")
                    continue
                
                link = link_tag.attributes.get('href')
                original_filename = link.split('/')[-1]
                file_format = original_filename.split('.')[-1] if '.' in original_filename else 'unknown'
                
                file_path = file_path_base + "." + file_format
                
                # Check if file already exists, skip if so
                if os.path.exists(file_path):
                    print(f"File already exists, skipping: {file_path}")
                    downloaded_files += 1
                    if progress_callback:
                        progress_callback(downloaded_files, total_files, lecture_title, file_progress_str)
                    continue
                print(DOMAIN + link)
                # Stream the file in chunks and report progress
                with requests.get(DOMAIN + link, auth=HttpNtlmAuth(username+"@student.guc.edu.eg", password), stream=True) as download_resp:
                    print("\nDOWNLOAD STATUS: " + str(download_resp.status_code) + "\n")
                    total_size = int(download_resp.headers.get('content-length', 0))
                    bytes_downloaded = 0
                    chunk_size = 8192
                    file_progress_str = ""
                    with open(file_path, "wb") as file:
                        for chunk in download_resp.iter_content(chunk_size=chunk_size):
                            if chunk:
                                file.write(chunk)
                                bytes_downloaded += len(chunk)
                                if total_size > 0:
                                    percent = (bytes_downloaded / total_size) * 100
                                    file_progress_str = f"{bytes_downloaded/1024/1024:.2f} MB / {total_size/1024/1024:.2f} MB ({percent:.1f}%)"
                                else:
                                    file_progress_str = f"{bytes_downloaded/1024/1024:.2f} MB / ? MB"
                                if progress_callback:
                                    progress_callback(downloaded_files, total_files, lecture_title, file_progress_str)
                    # Final callback to ensure 100% is shown
                    if progress_callback:
                        progress_callback(downloaded_files, total_files, lecture_title, file_progress_str)
                downloaded_files += 1
                if progress_callback:
                    progress_callback(downloaded_files, total_files, lecture_title)
    return all_types


def get_total_files(username, password, types):
    global DOMAIN, course_url
    resp = requests.get(DOMAIN + course_url, auth=HttpNtlmAuth(username+"@student.guc.edu.eg", password))
    if resp.status_code != 200:
        return 0
    html = HTMLParser(resp.text)
    all_cards = html.css(".card-body")
    total_files = 0
    for card in all_cards:
        title = card.css_first("div").text().strip().split("\n")[0]
        last_open = title.rfind("(")
        last_close = title.rfind(")")
        if last_open != -1 and last_close != -1 and last_close > last_open:
            title = title[last_open + 1 : last_close]
        if title in types:
            total_files += 1
    return total_files

# login("seif.alsaid", "2002frolicGamer")
# download_content("seif.alsaid", "2002frolicGamer", ["Lecture slides"])
# get_courses("seif.alsaid", "2002frolicGamer")
# update_course_url("seif.alsaid", "2002frolicGamer", "Computer System Architecture")
# print(DOMAIN + course_url)