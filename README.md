# guc-cms-downloader

A user-friendly tool to download content from the GUC CMS, featuring a graphical user interface (GUI) for ease of use.

## Features

- Download course materials directly from the GUC CMS
- Simple and intuitive GUI

## Prerequisites

- **Python 3.8+** (recommended: Python 3.11)
- **pip** (Python package manager)

## Installation

1. **Clone the repository:**

   ```bash
   git clone https://github.com/yourusername/guc-cms-downloader.git
   cd guc-cms-downloader
   ```

2. **(Optional but recommended) Create a virtual environment:**

   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

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
