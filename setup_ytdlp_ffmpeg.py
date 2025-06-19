import os
import sys
import shutil
import subprocess
import tempfile
import ctypes
import zipfile

# Ensure gdown is installed
try:
    import gdown
except ImportError:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "gdown"])
    import gdown

# URLs and IDs
YTDLP_URL = "https://github.com/yt-dlp/yt-dlp/releases/download/2025.06.09/yt-dlp.exe"
FFMPEG_FILE_ID = "1-ACF2V2zmEIP1gi4PeXbDGaVOcG6yoC0"

# Destination folder
DEST_FOLDER = r"C:\tools\yt-dlp"
YTDLP_DEST = os.path.join(DEST_FOLDER, "yt-dlp.exe")
FFMPEG_DEST = os.path.join(DEST_FOLDER, "ffmpeg.exe")

os.makedirs(DEST_FOLDER, exist_ok=True)

def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def download_file(url, dest):
    print(f"Downloading {url} ...")
    import requests
    with requests.get(url, stream=True) as r:
        r.raise_for_status()
        with open(dest, 'wb') as f:
            for chunk in r.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
    print(f"Saved to {dest}")

def download_ffmpeg_zip(file_id, output_path):
    print(f"Downloading ffmpeg.zip from Google Drive (ID: {file_id}) ...")
    gdown.download(id=file_id, output=output_path, quiet=False)
    print(f"Saved to {output_path}")

def extract_ffmpeg_zip(archive_path, dest_folder):
    print(f"Extracting {archive_path} ...")
    with zipfile.ZipFile(archive_path, 'r') as z:
        z.extractall(dest_folder)
    print(f"Extracted to {dest_folder}")

def find_ffmpeg_exe(extract_root):
    for root, dirs, files in os.walk(extract_root):
        if 'ffmpeg.exe' in files:
            return os.path.join(root, 'ffmpeg.exe')
    return None

def set_env_var_win(name, value):
    subprocess.run(['setx', name, value, '/M'], check=True)
    print(f"Set {name} to {value} (system-wide, all users)")

def main():
    print("This script requires administrator privileges to set system-wide environment variables.")
    if not is_admin():
        print("\nERROR: This script must be run as administrator to set system-wide environment variables.")
        print("Please re-run this script as administrator.")
        sys.exit(1)

    # 1. Download and extract ffmpeg.zip via gdown
    with tempfile.TemporaryDirectory() as tmpdir:
        zip_path = os.path.join(tmpdir, 'ffmpeg.zip')
        download_ffmpeg_zip(FFMPEG_FILE_ID, zip_path)
        extract_ffmpeg_zip(zip_path, tmpdir)
        ffmpeg_exe = find_ffmpeg_exe(tmpdir)
        if not ffmpeg_exe:
            print("Could not find ffmpeg.exe in the extracted archive!")
            sys.exit(1)
        shutil.copy2(ffmpeg_exe, FFMPEG_DEST)
        print(f"Copied ffmpeg.exe to {FFMPEG_DEST}")
    
    # 2. Download yt-dlp.exe
    if not os.path.exists(YTDLP_DEST):
        download_file(YTDLP_URL, YTDLP_DEST)
    else:
        print(f"yt-dlp.exe already exists at {YTDLP_DEST}")


    # 3. Set environment variables (system-wide)
    set_env_var_win('YTDLP_PATH', YTDLP_DEST)
    set_env_var_win('FFMPEG_PATH', FFMPEG_DEST)

    print("\n✅ Setup complete!")
    print(f"yt-dlp.exe: {YTDLP_DEST}")
    print(f"ffmpeg.exe: {FFMPEG_DEST}")
    print("\nYou may need to restart your computer or log out/in for the environment variables to take effect for all users.")

if __name__ == "__main__":
    main()
