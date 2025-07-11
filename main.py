import requests
from requests.adapters import HTTPAdapter
from requests_ntlm import HttpNtlmAuth
from bs4 import BeautifulSoup
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
    
    soup = BeautifulSoup(resp.text, 'html.parser')
    all_courses = soup.select("table#ContentPlaceHolderright_ContentPlaceHoldercontent_GridViewcourses tr")[1:]

    for course in all_courses:
        tds = course.find_all("td")
        course_name = tds[1].get_text()
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
            course_url = "/apps/student/CourseViewStn.aspx?id=" + tds[4].get_text() + "&sid=" + tds[5].get_text()
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
        
        soup = BeautifulSoup(resp.text, 'html.parser')
        final_courses=[]
        all_courses = soup.select("table#ContentPlaceHolderright_ContentPlaceHoldercontent_GridViewcourses tr")[1:]

        for course in all_courses:
            tds = course.find_all("td")
            course_name = tds[1].get_text()
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
    
    soup = BeautifulSoup(resp.text, 'html.parser')
    all_cards = soup.select(".card-body")
    course_name = soup.select_one("#ContentPlaceHolderright_ContentPlaceHoldercontent_LabelCourseName").get_text()
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
            title = card.find("div").get_text().strip().split("\n")[0]
            # Extract content type from the last set of parentheses
            last_open = title.rfind("(")
            last_close = title.rfind(")")
            if last_open != -1 and last_close != -1 and last_close > last_open:
                title = title[last_open + 1 : last_close]
            
            if title not in all_types:
                all_types.append(title)

    return {'types' : all_types, 'course_name' : course_name}
        

def download_content(username, password, types, progress_callback=None, cancellation_check=None, output_folder=None, org_mode='type', include_week=True, include_type=False, include_week_description=False):
    global DOMAIN, course_url, current_session_name
    if not types:
        print("No content types selected. Aborting download.")
        return {'exam_sched': [], 'success': False, 'error': 'No content types selected.'}
    resp = requests.get(DOMAIN + course_url, auth=HttpNtlmAuth(username+"@student.guc.edu.eg", password))

    if resp.status_code != 200:
            print("An Error Occurred. Check Credentials And Try Again.")
            return {'exam_sched': [], 'success' : False}

    soup = BeautifulSoup(resp.text, 'html.parser')

    # 1. Parse weeks, reverse them, and map content to a week number and description
    content_to_week_map = {}
    week_to_description_map = {} # To store week descriptions
    all_weeks = soup.select(".card.mb-5.weeksdata")
    all_weeks = list(reversed(all_weeks)) # Weeks in HTML are newest to oldest, reverse for chronological order

    for week_number, week_div in enumerate(all_weeks, 1):
        # Extract week description
        description_text = "No Description"
        # The description <p> tag is the one not inside a div with style="display:none;"
        all_p_tags = week_div.find_all("p", class_="m-2 p2")
        for p_tag in all_p_tags:
            if not p_tag.find_parent("div", style="display:none;"):
                description_text = p_tag.text.strip()
                break
        week_to_description_map[week_number] = description_text

        # Map content IDs to this week number
        content_items = week_div.select("div[id^=content]")
        for item in content_items:
            content_id = item.get("id")
            content_to_week_map[content_id] = week_number

    all_cards = soup.select(".card-body")
    all_types = []

    # Count total files to download for progress tracking
    total_files = 0
    files_to_download = []

    for card in all_cards:
            title = card.find("div").get_text().strip().split("\n")[0]
            last_open = title.rfind("(")
            last_close = title.rfind(")")
            if last_open != -1 and last_close != -1 and last_close > last_open:
                title = title[last_open + 1 : last_close]

            if title not in all_types:
                all_types.append(title)

            if (title in types):
                total_files += 1
                files_to_download.append(card)

    content_type_mapping = {}
    for card in all_cards:
        file_content_type = card.find("div").get_text().strip().split("\n")[0]
        last_open = file_content_type.rfind("(")
        last_close = file_content_type.rfind(")")
        if last_open != -1 and last_close != -1 and last_close > last_open:
            file_content_type = file_content_type[last_open + 1 : last_close]
        for selected_type in types:
            if (file_content_type.lower() in selected_type.lower() or
                selected_type.lower() in file_content_type.lower() or
                file_content_type == selected_type):
                content_type_mapping[file_content_type] = selected_type
                break

    downloaded_files = 0
    for card in files_to_download:
        try:
            if cancellation_check and cancellation_check():
                print("Download cancelled by user")
                return all_types

            file_content_type = card.find("div").get_text().strip().split("\n")[0]
            last_open = file_content_type.rfind("(")
            last_close = file_content_type.rfind(")")
            if last_open != -1 and last_close != -1 and last_close > last_open:
                file_content_type = file_content_type[last_open + 1 : last_close]

            if (file_content_type in types):
                course_name = soup.select_one("#ContentPlaceHolderright_ContentPlaceHoldercontent_LabelCourseName").get_text()
                match = re.match(r"\(\|([A-Za-z0-9 ]+)\|\)\s*([^(]+?)(?:\s*\([^)]*\))*$", course_name)
                if match:
                    code = match.group(1).strip()
                    name = match.group(2).strip()
                    course_name = f"{name} ({code})" if code else name
                else:
                    course_name = re.sub(r"\s*\([^)]*\)\s*$", "", course_name).strip()
                course_name = re.sub(r"\s+", " ", course_name)

                content_id_div = card.select_one("div[id^=content]")
                content_id = content_id_div.get("id") if content_id_div else None
                week_num = content_to_week_map.get(content_id) if content_id else None

                # Create the week prefix with description
                week_prefix_for_filename = ""
                week_prefix_for_foldername = ""
                if week_num:
                    week_description = week_to_description_map.get(week_num, "").strip()
                    # Sanitize description for filesystem (removes invalid chars and control chars)
                    sanitized_description = re.sub(r'[\\/*?:"<>|\x00-\x1f]', '', week_description) if week_description else ""
                    
                    week_part = f"Week {str(week_num).rstrip()}"
                    week_prefix_for_filename = week_part # Filename inside week folder is simple
                    
                    if include_week_description and sanitized_description:
                        week_prefix_for_foldername = f"{week_part} [{sanitized_description}]"
                    else:
                        week_prefix_for_foldername = week_part

                lecture_title_raw = card.select_one("div strong").get_text()
                lecture_title = re.sub(r'^\d+\s*-\s*', '', lecture_title_raw).strip()

                root_folder = output_folder if output_folder else os.getcwd()

                session_folder = os.path.join(root_folder, current_session_name.rstrip())
                try:
                    os.makedirs(session_folder, exist_ok=True)
                except OSError as error:
                    print(error)

                course_folder_path = os.path.join(session_folder, course_name.rstrip())
                try:
                    os.makedirs(course_folder_path, exist_ok=True)
                except OSError as error:
                    print(error)

                if org_mode == 'type':
                    filter_name = content_type_mapping.get(file_content_type, file_content_type).rstrip()
                    filter_folder = os.path.join(course_folder_path, filter_name)
                    try:
                        os.makedirs(filter_folder, exist_ok=True)
                    except OSError as error:
                        print(error)
                    name_parts = []
                    if include_week and week_prefix_for_foldername:
                        name_parts.append(week_prefix_for_foldername)
                    if include_type:
                        name_parts.append(f"({file_content_type.rstrip()})")
                    name_parts.append(lecture_title.rstrip())
                    file_name = " - ".join(name_parts).rstrip()
                    file_path_base = os.path.join(filter_folder, file_name)
                elif org_mode == 'week':
                    week_folder = week_prefix_for_foldername if week_prefix_for_foldername else "No Week"
                    week_folder_path = os.path.join(course_folder_path, week_folder.rstrip())
                    try:
                        os.makedirs(week_folder_path, exist_ok=True)
                    except OSError as error:
                        print(error)
                    name_parts = []
                    if include_week and week_prefix_for_filename:
                        name_parts.append(week_prefix_for_filename)
                    if include_type:
                        name_parts.append(f"({file_content_type.rstrip()})")
                    name_parts.append(lecture_title.rstrip())
                    file_name = " - ".join(name_parts).rstrip()
                    file_path_base = os.path.join(week_folder_path, file_name)
                else: # Flat structure
                    name_parts = []
                    if include_week and week_prefix_for_foldername:
                        name_parts.append(week_prefix_for_foldername)
                    if include_type:
                        name_parts.append(f"({file_content_type.rstrip()})")
                    name_parts.append(lecture_title.rstrip())
                    file_name = " - ".join(name_parts).rstrip()
                    file_path_base = os.path.join(course_folder_path, file_name)

                if file_content_type.lower().rstrip() == "vod":
                    file_path = file_path_base + ".mkv"
                    if os.path.exists(file_path):
                        print(f"File already exists, skipping: {file_path}")
                        downloaded_files += 1
                        if progress_callback:
                            progress_callback(downloaded_files, total_files, lecture_title, "VoD")
                        continue

                    vod_input = card.select_one("input.vodbutton")
                    if vod_input is not None:
                        vod_content_id = vod_input.get('id')
                        if vod_content_id:
                            try:
                                download_single_video(vod_content_id, file_path, username, password)
                            except Exception as e:
                                print(f"Error downloading VoD file {lecture_title}: {e}")
                                continue
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
                    link_tag = card.find("a")
                    if not link_tag or not link_tag.get('href'):
                        print(f"Could not find download link for: {lecture_title}")
                        continue
                    
                    link = link_tag.get('href')
                    original_filename = link.split('/')[-1]
                    file_format = original_filename.split('.')[-1] if '.' in original_filename else 'unknown'
                    
                    file_path = file_path_base + "." + file_format
                    
                    if os.path.exists(file_path):
                        print(f"File already exists, skipping: {file_path}")
                        downloaded_files += 1
                        if progress_callback:
                            progress_callback(downloaded_files, total_files, lecture_title, "Already Exists")
                        continue
                    print(DOMAIN + link)
                    try:
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
                            if progress_callback:
                                progress_callback(downloaded_files, total_files, lecture_title, file_progress_str)
                        downloaded_files += 1
                        if progress_callback:
                            progress_callback(downloaded_files, total_files, lecture_title, "Downloaded")
                    except Exception as e:
                        print(f"Error downloading file {lecture_title}: {e}")
                        continue
        except Exception as e:
            print(f"Unexpected error processing file: {e}")
            continue
    return all_types

def get_total_files(username, password, types):
    global DOMAIN, course_url
    resp = requests.get(DOMAIN + course_url, auth=HttpNtlmAuth(username+"@student.guc.edu.eg", password))
    if resp.status_code != 200:
        return 0
    soup = BeautifulSoup(resp.text, 'html.parser')
    all_cards = soup.select(".card-body")
    total_files = 0
    for card in all_cards:
        title = card.find("div").get_text().strip().split("\n")[0]
        last_open = title.rfind("(")
        last_close = title.rfind(")")
        if last_open != -1 and last_close != -1 and last_close > last_open:
            title = title[last_open + 1 : last_close]
        if title in types:
            total_files += 1
    return total_files