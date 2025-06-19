import requests
from requests_ntlm import HttpNtlmAuth
from bs4 import BeautifulSoup
import os
import re
import subprocess
import sys

def download_single_video(content_id, output_filename=None, username=None, password=None):
    """
    Downloads a single video from GUC CMS using its contentId.
    
    Args:
        content_id (str): The content ID of the video to download.
        output_filename (str, optional): Custom filename for the video. If None, uses "Video_{content_id}.mkv".
        username (str, optional): GUC username. If None, uses the global GUC_USERNAME.
        password (str, optional): GUC password. If None, uses the global GUC_PASSWORD.
    """
    # Use global credentials if not provided
    if username is None:
        username = GUC_USERNAME
    if password is None:
        password = GUC_PASSWORD
    
    # Set default filename if not provided
    if output_filename is None:
        output_filename = f"Video_{content_id}.mkv"
    
    print(f"Attempting to download video with contentId: {content_id}")
    print(f"Output filename: {output_filename}")
    
    # First, try to get the actual content ID if the provided one is short
    actual_content_id = content_id
    
    # Check if this looks like a short content ID (contains underscore and is relatively short)
    if '_' in content_id and len(content_id) < 50:
        print("Detected short content ID. Attempting to resolve to actual content ID...")
        
        # Try to get the actual content ID from the info API
        info_url = f"https://playback.dacast.com/content/info?contentId={content_id}&provider=dacast"
        
        try:
            info_resp = requests.get(info_url)
            if info_resp.status_code == 200:
                info_data = info_resp.json()
                actual_content_id = info_data.get('contentInfo', {}).get('contentId')
                
                if actual_content_id:
                    print(f"✅ Successfully resolved content ID: {content_id} -> {actual_content_id}")
                else:
                    print("❌ Could not find actual content ID in the response")
                    return
            else:
                print(f"❌ Failed to resolve content ID. Info API returned status: {info_resp.status_code}")
                return
        except requests.RequestException as e:
            print(f"❌ An error occurred while resolving content ID: {e}")
            return
        except Exception as e:
            print(f"❌ An unexpected error occurred while resolving content ID: {e}")
            return
    
    # This is the Dacast API endpoint that provides the HLS link
    access_url = f"https://playback.dacast.com/content/access?contentId={actual_content_id}&provider=universe"
    
    try:
        # This request does NOT require GUC authentication
        print("Fetching HLS stream URL...")
        hls_resp = requests.get(access_url)
        
        if hls_resp.status_code == 200:
            hls_data = hls_resp.json()
            hls_url = hls_data.get('hls')
            
            if hls_url:
                print("✅ Successfully obtained HLS URL!")
                print("Starting download with enhanced quality...")
                
                # Use yt-dlp with ffmpeg for better quality
                # Allow overriding yt-dlp and ffmpeg paths via environment variables
                yt_dlp_path = os.environ.get('YTDLP_PATH', 'yt-dlp')
                ffmpeg_path = os.environ.get('FFMPEG_PATH', 'ffmpeg')
                cmd = [
                    yt_dlp_path,
                    '--downloader', 'ffmpeg',
                    '--ffmpeg-location', ffmpeg_path,
                    '--hls-use-mpegts',
                    '-o', output_filename,
                    hls_url
                ]
                
                print(f"Running command: {' '.join(cmd)}")
                
                # Execute the download command
                result = subprocess.run(cmd, capture_output=True, text=True)
                
                if result.returncode == 0:
                    print(f"✅ Download completed successfully!")
                    print(f"Video saved as: {output_filename}")
                    
                    # Check if file exists and show its size
                    if os.path.exists(output_filename):
                        file_size = os.path.getsize(output_filename)
                        print(f"File size: {file_size:,} bytes ({file_size/1024:.1f} KB)")
                else:
                    print(f"❌ Download failed!")
                    print(f"Error output: {result.stderr}")
                    
            else:
                print("❌ API call successful, but no HLS URL was found in the response.")
                print(f"Response content: {hls_data}")
        else:
            print(f"❌ Failed to get HLS link. Dacast API returned status: {hls_resp.status_code}")
            print(f"Response content: {hls_resp.text}")

    except requests.RequestException as e:
        print(f"❌ An error occurred while calling the Dacast API: {e}")
    except subprocess.CalledProcessError as e:
        print(f"❌ An error occurred during download: {e}")
    except Exception as e:
        print(f"❌ An unexpected error occurred: {e}")


def get_video_download_commands(username, password, course_id, session_id):
    """
    Scrapes a GUC course page for VOD content, fetches the HLS stream links,
    and prints the corresponding yt-dlp download commands.

    Args:
        username (str): Your GUC username (e.g., 'jane.doe').
        password (str): Your GUC password.
        course_id (str): The course ID from the URL (e.g., '2672').
        session_id (str): The session ID from the URL (e.g., '65').
    """
    # Construct the course page URL
    course_url = f"https://cms.guc.edu.eg/apps/student/CourseViewStn.aspx?id={course_id}&sid={session_id}"
    
    print(f"Attempting to log in and access course page: {course_url}\n")
    
    try:
        # Use a session to maintain login state
        with requests.Session() as s:
            s.auth = HttpNtlmAuth(username.strip() + "@student.guc.edu.eg", password)
            
            # First, make an authenticated request to the page
            resp = s.get(course_url)
            
            if resp.status_code != 200:
                print(f"Error: Failed to access course page. Status code: {resp.status_code}")
                print("Please check your credentials, course ID, and session ID.")
                return

            print("Successfully accessed course page. Searching for videos...")
            soup = BeautifulSoup(resp.text, 'html.parser')

            # Find all buttons that trigger a video modal
            video_buttons = soup.find_all('input', class_='vodbutton')

            if not video_buttons:
                print("No video buttons found on this page.")
                return
            
            print(f"Found {len(video_buttons)} video(s). Fetching download links...\n")

            for i, button in enumerate(video_buttons):
                content_id = button.get('id')
                
                # Try to find a descriptive name for the video
                # Often, the button is in a table row (tr) with the title in a previous cell (td)
                video_title = f"Video_{i+1}" # Default title
                parent_row = button.find_parent('tr')
                if parent_row:
                    first_cell = parent_row.find('td')
                    if first_cell:
                        video_title = first_cell.get_text(strip=True)

                # Sanitize the title to create a valid filename
                # Remove special characters and limit length
                sanitized_title = re.sub(r'[^\w\s-]', '', video_title).strip()
                sanitized_title = re.sub(r'[-\s]+', '_', sanitized_title)
                output_filename = f"{sanitized_title}.mkv"

                if not content_id:
                    print(f"--- Video {i+1} ({video_title}) ---")
                    print("Could not find contentId for this video. Skipping.")
                    print("-" * 20 + "\n")
                    continue

                # This is the Dacast API endpoint that provides the HLS link
                access_url = f"https://playback.dacast.com/content/access?contentId={content_id}&provider=universe"
                
                try:
                    # This request does NOT require GUC authentication
                    hls_resp = requests.get(access_url)
                    if hls_resp.status_code == 200:
                        hls_data = hls_resp.json()
                        hls_url = hls_data.get('hls')
                        
                        if hls_url:
                            print(f"--- Video {i+1}: {video_title} ---")
                            print("Success! Use the following command in your terminal to download:")
                            # Print the enhanced command for yt-dlp with ffmpeg for better quality
                            print("\n" + f'yt-dlp --downloader ffmpeg --hls-use-mpegts -o "{output_filename}" "{hls_url}"' + "\n")
                        else:
                            print(f"--- Video {i+1}: {video_title} ---")
                            print("API call successful, but no HLS URL was found in the response.")
                    else:
                        print(f"--- Video {i+1}: {video_title} ---")
                        print(f"Failed to get HLS link. Dacast API returned status: {hls_resp.status_code}")

                except requests.RequestException as e:
                    print(f"--- Video {i+1}: {video_title} ---")
                    print(f"An error occurred while calling the Dacast API: {e}")

                print("-" * 20 + "\n")

    except requests.RequestException as e:
        print(f"An error occurred during the request: {e}")


# --- HOW TO USE ---

# 1. Fill in your credentials below
GUC_USERNAME = "seif.alsaid"  # e.g., 'seif.alsaid'
GUC_PASSWORD = "GUCentral@1243"

# 2. Go to the course page on the GUC CMS in your browser.
#    Look at the URL. It will look like:
#    https://cms.guc.edu.eg/apps/student/CourseViewStn.aspx?id=2672&sid=65
# 3. Copy the 'id' and 'sid' from the URL into the variables below.
COURSE_ID = "1705"  # The 'id' from the URL
SESSION_ID = "65"   # The 'sid' from the URL

# 4. Run the script: python vod-downloader.py
if __name__ == "__main__":
    if GUC_USERNAME == "YOUR_USERNAME" or GUC_PASSWORD == "YOUR_PASSWORD":
        print("Please open the script and fill in your GUC_USERNAME and GUC_PASSWORD.")
    else:
        # === HOW TO USE THE SINGLE VIDEO DOWNLOADER ===
        # 
        # Method 1: Edit the content_id below and run the script
        # content_id = "YOUR_CONTENT_ID_HERE"
        # download_single_video(content_id, "My_Video.mkv")
        
        # Method 2: Call the function from Python console
        # from vod_downloader import download_single_video
        # download_single_video("your_content_id", "output_filename.mkv")
        
        # Method 3: Use command line arguments (if you want to add this feature)
        
        print("=== GUC Video Downloader ===")
        print("To download a single video:")
        print("1. Get the contentId from the video button on GUC CMS")
        print("2. Edit this script and set the content_id variable")
        print("3. Run: python vod-downloader.py")
        print("\nExample:")
        print("content_id = 'your-content-id-here'")
        print("download_single_video(content_id, 'My_Video.mkv')")
        
        # Uncomment and modify the lines below to download a specific video:
        content_id = "150675_f_1006741"
        download_single_video(content_id, "My_Video_Cloud.mkv")
        
        # Or uncomment the line below to scrape all videos from a course
        # get_video_download_commands(GUC_USERNAME, GUC_PASSWORD, COURSE_ID, SESSION_ID)