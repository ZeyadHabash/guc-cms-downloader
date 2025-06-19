from bs4 import BeautifulSoup
import json
import re
import requests
from requests_ntlm import HttpNtlmAuth

def parse_courses_html_from_url(username, password):
    """
    Fetches and parses the HTML content from the GUC CMS URL to extract course information.

    Args:
        username (str): The username for authentication.
        password (str): The password for authentication.

    Returns:
        dict: A dictionary where keys are season titles and values are lists of course dictionaries.
              Each course dictionary contains 'name', 'id', and 'sid'.
              Returns an empty dictionary if the request fails or parsing fails.
    """
    url = "https://cms.guc.edu.eg/apps/student/ViewAllCourseStn"
    
    try:
        resp = requests.get(url, auth=HttpNtlmAuth(username.strip()+"@student.guc.edu.eg", password))
        
        if resp.status_code != 200:
            print(f"Error: Request failed with status code {resp.status_code}. Check credentials and try again.")
            return {}
            
        html_content = resp.text
    except Exception as e:
        print(f"Error fetching content from URL: {e}")
        return {}

    soup = BeautifulSoup(html_content, 'html.parser')
    all_courses_by_season = {}

    # Find all card-hover-shadow profile-responsive card-border mb-3 card divs, which represent seasons
    season_cards = soup.find_all('div', class_='card-hover-shadow profile-responsive card-border mb-3 card')

    for card in season_cards:
        # Extract season title
        season_title_div = card.find('div', class_='menu-header-title')
        season_title = ""
        if season_title_div:
            season_title = season_title_div.get_text(strip=True).replace('Season :', '').replace('Title:', '').strip()
            # Replace comma with dash for better folder naming
            season_title = season_title.replace(',', ' -')
            # Normalize whitespace in season/session name
            season_title = re.sub(r"\s+", " ", season_title)
        else:
            # Fallback if the specific div is not found, though it should be present
            season_title = "Unknown Season"

        # Find the table within the current season card
        table = card.find('table', class_='table')

        if table:
            courses = []
            # Find all table rows (tr) - handle both tbody and direct tr elements
            tbody = table.find('tbody')
            if tbody:
                rows = tbody.find_all('tr')
            else:
                # If no tbody, get all tr elements directly from table
                rows = table.find_all('tr')

            if not rows:
                continue  # No rows found, skip this season

            # Get the header row to find the index of Name, ID, and SeasonId
            # Check if there's a <thead>; if not, assume first <tr> is the header
            header_row_container = table.find('thead')
            if not header_row_container:
                # If no thead, use the first row as header and then process the rest
                if rows:
                    header_row_elements = rows[0].find_all(['th', 'td']) # Headers can sometimes be td in tbody
                    headers = [element.get_text(strip=True) for element in header_row_elements]
                    data_rows = rows[1:] # Actual data rows start from the second row
                else:
                    continue # No rows in table
            else:
                header_row_elements = header_row_container.find('tr').find_all(['th', 'td'])
                headers = [element.get_text(strip=True) for element in header_row_elements]
                data_rows = rows

            name_index = -1
            id_index = -1
            season_id_index = -1

            for i, header in enumerate(headers):
                if 'Name' in header: # Use 'in' for more robustness
                    name_index = i
                elif 'ID' in header and not 'SeasonId' in header: # Ensure it's the course ID
                    id_index = i
                elif 'SeasonId' in header:
                    season_id_index = i

            # Iterate over each course data row
            for row in data_rows:
                cols = row.find_all('td')
                # Ensure there are enough columns to extract data
                if len(cols) > max(name_index, id_index, season_id_index):
                    # Extract text, remove parentheses and numbers for cleaner name if desired, or keep as is
                    course_full_name = cols[name_index].get_text(" ", strip=True) if name_index != -1 else 'N/A'
                    # Use regex to extract code and name, ignore all bracketed content at the end
                    match = re.match(r"\(\|([A-Za-z0-9 ]+)\|\)\s*([^(]+?)(?:\s*\([^)]*\))*$", course_full_name)
                    if match:
                        code = match.group(1).strip()
                        name = match.group(2).strip()
                        # Format as "Course Name (CODE)" for consistency
                        clean_name = f"{name} ({code})" if code else name
                    else:
                        # fallback: remove last bracketed number if present
                        clean_name = re.sub(r"\s*\([^)]*\)\s*$", "", course_full_name).strip()
                    # Normalize whitespace to a single space
                    clean_name = re.sub(r"\s+", " ", clean_name)
                    
                    course_id = cols[id_index].get_text(strip=True) if id_index != -1 else 'N/A'
                    session_id = cols[season_id_index].get_text(strip=True) if season_id_index != -1 else 'N/A'

                    courses.append({
                        'name': clean_name,
                        'id': course_id,
                        'sid': session_id
                    })
            if season_title: # Only add if a valid season title was found
                all_courses_by_season[season_title] = courses

    return all_courses_by_season

# Example usage:
# parsed_data = parse_courses_html_from_url('your_username', 'your_password')
# print(json.dumps(parsed_data, indent=4))

# For testing, you can uncomment the line below and provide your credentials:
# parsed_data = parse_courses_html_from_url('seif.alsaid', '2002frolicGamer')
# print(json.dumps(parsed_data, indent=4))
