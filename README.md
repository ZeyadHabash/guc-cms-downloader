# 📚 GUC CMS Downloader

A user-friendly tool to download content from the GUC CMS, featuring a graphical user interface (GUI) for ease of use.

## Features

- Download course materials directly from the GUC CMS
- Simple and intuitive GUI

## Prerequisites

- **Python 3.8+** (recommended: Python 3.11)
- **pip** (Python package manager)
- **tkinter** (Python GUI library, required for the application window)

> **Note:** `tkinter` is required for the GUI to work. See below for installation instructions if it's not already included with your Python installation.

## Installation

1. **Clone the repository:**

   ```bash
   git clone https://github.com/yourusername/guc-cms-downloader.git
   cd guc-cms-downloader
   ```

2. **Activate the existing virtual environment:**

   - **On macOS/Linux:**
     ```bash
     source venv/bin/activate
     ```
   - **On Windows (CMD):**
     ```cmd
     venv/bin/activate
     ```
   - **On Windows (PowerShell):**
     ```powershell
     venv/bin/activate
     ```

3. **Install the required Python packages:**

   > **You must install all required dependencies before running the application.**

   ```bash
   pip install -r requirements.txt
   ```

## Downloading VoDs (Video on Demand)

## Windows Users: Initial Setup (If you want to download VoDs)

Before running the GUI (`cms-downloader-gui.py`), you **must** run the provided setup script, which will **automatically download and configure `yt-dlp` and `ffmpeg` for you**. You do **not** need to manually download these tools.

1. **Run the setup script as an administrator in PowerShell**:
   - Right-click on PowerShell and select **Run as administrator**.
   - Navigate to the project directory, then run:
   ```
   python setup_ytdlp_ffmpeg.py
   ```
   - The script will handle downloading and setting up both `yt-dlp` and `ffmpeg` automatically. Once it finishes, you can proceed to use the GUI as normal.

## macOS and Linux Users: Initial Setup (If you want to download VoDs)

Before running the GUI (`cms-downloader-gui.py`), you need to install `yt-dlp` and `ffmpeg` and ensure they are available in your system `PATH`.

### 1. Install `yt-dlp` and `ffmpeg`

#### **macOS (using Homebrew):**

```bash
brew install yt-dlp ffmpeg
```

#### **Linux (Debian/Ubuntu):**

```bash
sudo apt update
sudo apt install yt-dlp ffmpeg
```

#### **Linux (Fedora):**

```bash
sudo dnf install yt-dlp ffmpeg
```

### 2. Ensure they are in your PATH

You should be able to run these commands in your terminal:

```bash
yt-dlp --version
ffmpeg -version
```

If not, add their install locations to your `PATH`.

After setup is complete, you can run the GUI as normal:

## Running the GUI

To start the graphical user interface, run:

```bash
python cms-downloader-gui.py
```

This will launch the application window. Follow the on-screen instructions to log in and download your course materials.

## Troubleshooting

- If you encounter issues with missing packages, ensure you have installed all dependencies with `pip install -r requirements.txt`.
- For problems related to Python versions, check your Python installation with `python --version`.
- If you see errors related to `customtkinter`, make sure your environment is activated and dependencies are installed.
- **Blank window or content not rendering (macOS, sometimes other platforms):**
  - There is a known bug in the underlying GUI toolkit (tkinter/customtkinter) where sometimes the application window opens blank or does not render its content, especially on macOS. If this happens, simply move or drag the window with your mouse, or click the window's title bar. This will force the content to render and the window to become responsive. This is a platform-level issue and not a bug in this application.

---

## Installing tkinter

### Windows

- The official Python installer for Windows usually includes `tkinter` by default. If you encounter errors about missing `tkinter`, re-run the Python installer and ensure the "tcl/tk and IDLE" option is selected.

### macOS

- `tkinter` is typically included with Python on macOS. If you installed Python via Homebrew and `tkinter` is missing, install it with:
  ```bash
  brew install python-tk
  ```

### Linux (Debian/Ubuntu)

- Install `tkinter` using:
  ```bash
  sudo apt update
  sudo apt install python3-tk
  ```

### Linux (Fedora)

- Install `tkinter` using:
  ```bash
  sudo dnf install python3-tkinter
  ```

After installing `tkinter`, you should be able to run the GUI as described above.
