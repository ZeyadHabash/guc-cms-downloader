import os
import sys
import shutil
import requests
import tempfile
import subprocess

# Try to import py7zr, install if missing
try:
    import py7zr
except ImportError:
    print("py7zr not found. Installing py7zr...")
    subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'py7zr'])
    import py7zr

# URLs
YTDLP_URL = "https://github.com/yt-dlp/yt-dlp/releases/download/2025.06.09/yt-dlp.exe"
FFMPEG_URL = "https://www.gyan.dev/ffmpeg/builds/packages/ffmpeg-7.0.2-essentials_build.7z"

# Destination folder
DEST_FOLDER = r"C:\tools\yt-dlp"
YTDLP_DEST = os.path.join(DEST_FOLDER, "yt-dlp.exe")
FFMPEG_DEST = os.path.join(DEST_FOLDER, "ffmpeg.exe")

os.makedirs(DEST_FOLDER, exist_ok=True)

def download_file(url, dest):
    print(f"Downloading {url} ...")
    with requests.get(url, stream=True) as r:
        r.raise_for_status()
        with open(dest, 'wb') as f:
            for chunk in r.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
    print(f"Saved to {dest}")

def extract_ffmpeg_7z(archive_path, dest_folder):
    print(f"Extracting {archive_path} ...")
    with py7zr.SevenZipFile(archive_path, mode='r') as z:
        z.extractall(path=dest_folder)
    print(f"Extracted to {dest_folder}")

def find_ffmpeg_exe(extract_root):
    # Look for ffmpeg.exe in any bin/ subfolder
    for root, dirs, files in os.walk(extract_root):
        if 'ffmpeg.exe' in files:
            return os.path.join(root, 'ffmpeg.exe')
    return None

def set_env_var_win(name, value):
    # Set persistent user env var
    subprocess.run(['setx', name, value], check=True)
    print(f"Set {name} to {value} (persistent for user)")

def main():
    # 1. Download yt-dlp.exe
    if not os.path.exists(YTDLP_DEST):
        download_file(YTDLP_URL, YTDLP_DEST)
    else:
        print(f"yt-dlp.exe already exists at {YTDLP_DEST}")

    # 2. Download and extract ffmpeg
    with tempfile.TemporaryDirectory() as tmpdir:
        archive_path = os.path.join(tmpdir, 'ffmpeg.7z')
        download_file(FFMPEG_URL, archive_path)
        extract_ffmpeg_7z(archive_path, tmpdir)
        ffmpeg_exe = find_ffmpeg_exe(tmpdir)
        if not ffmpeg_exe:
            print("Could not find ffmpeg.exe in the extracted archive!")
            sys.exit(1)
        shutil.copy2(ffmpeg_exe, FFMPEG_DEST)
        print(f"Copied ffmpeg.exe to {FFMPEG_DEST}")

    # 3. Set environment variables
    set_env_var_win('YTDLP_PATH', YTDLP_DEST)
    set_env_var_win('FFMPEG_PATH', FFMPEG_DEST)

    print("\nSetup complete!")
    print(f"yt-dlp.exe: {YTDLP_DEST}")
    print(f"ffmpeg.exe: {FFMPEG_DEST}")
    print("\nYou may need to restart your terminal or log out/in for the environment variables to take effect.")

if __name__ == "__main__":
    main()