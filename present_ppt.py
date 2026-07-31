import os
import sys

try:
    import win32com.client
except ImportError:
    print("Error: The 'pywin32' library is required to automate PowerPoint presentations.")
    print("Please install it by running: pip install pywin32")
    sys.exit(1)

def present_ppt(file_path):
    # Ensure the path is absolute
    abs_path = os.path.abspath(file_path)
    
    if not os.path.exists(abs_path):
        print(f"Error: Presentation file not found at {abs_path}")
        return

    print(f"Opening and presenting: {abs_path}")
    
    # Initialize the PowerPoint application
    powerpoint = win32com.client.Dispatch("PowerPoint.Application")
    powerpoint.Visible = True
    
    # Open the presentation
    presentation = powerpoint.Presentations.Open(abs_path)
    
    # Start the slide show
    presentation.SlideShowSettings.Run()
    
    print("Slideshow started successfully! Press ESC to exit the presentation when done.")

if __name__ == "__main__":
    ppt_file = "PeopleRiskAI_Introduction.pptx"
    present_ppt(ppt_file)
