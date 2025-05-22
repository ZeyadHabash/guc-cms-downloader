# GUC CMS Downloader

A desktop application that helps GUC students download course materials from the Content Management System (CMS).

## Features

- **Login with GUC Credentials**: Securely log in to the CMS system using your GUC credentials.
- **Navigate Semesters**: Browse through all available semesters, not just the current one.
- **Course Selection**: Choose specific courses to download materials from.
- **Content Filtering**: Select specific types of content to download (lectures, assignments, etc.).
- **Bulk Download**: Download materials from multiple courses across multiple semesters at once.
- **Specific Course Selection**: Select specific courses from each semester for bulk downloading.
- **Enhanced Content Detection**: Improved detection of all content types including lab manuals, exam solutions, and other materials.
- **Dynamic Content Type Handling**: The "All file types" option automatically creates folders for any new content type detected.
- **Organized Structure**: Downloaded content is automatically organized by semester, course, and content type.
- **Improved UI**: Better visibility of buttons and scrollable content areas for easier navigation.

## How to Use

1. **Login**: Enter your GUC username and password to access the system.

2. **Individual Course Download**:
   - Select a semester from the dropdown menu
   - Choose a specific course
   - Select the types of content you want to download
   - Click "Download" to start the process

3. **Bulk Download (All Courses)**:
   - After logging in, select "Download All Courses" from the semester dropdown
   - Check the semesters you want to download content from
   - Click the expand arrows (▼) next to semesters to select specific courses
   - Select content types to download (like lectures, assignments, lab manuals, etc.)
   - For dynamic content type handling, select the "All file types" option
   - Click "Download Selected Content" to begin the download process

## Requirements

- Python 3.x
- Required packages (install using `pip install -r requirements.txt`):
  - customtkinter
  - requests
  - requests_ntlm
  - selectolax

## Installation

1. Clone the repository or download the zip file
2. Install the required packages:
   ```
   pip install -r requirements.txt
   ```
3. Run the application:
   ```
   python cms-downloader-gui.py
   ```

## Notes

- Downloaded files are stored in a "Downloads" folder, organized by semester and course.
- Your credentials are temporarily stored in the configuration file to keep you logged in.
- You can log out by clicking the "Log Out" button to clear stored credentials.
- When using the "All file types" option, the system will create folders for any content type detected, ensuring nothing is missed.

## License

This project is for educational purposes only. Use responsibly.
