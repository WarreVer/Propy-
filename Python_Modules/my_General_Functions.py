"""
    Module Name: my_GeneralFunctions.py
    
    THIS MODULE CONTAINS ALL GENERAL PROCEDURES
"""    

import time

##
nameDummyStart = "START"
keyDummyStart = "DS"
nameDummyEnd = "END"
keyDummyEnd = "DE"

## Global visualization style settings
    #In Matplotlib, the default font size depends on the version and the style settings, but typically:
    #Axis labels (set_xlabel / set_ylabel): fontsize = 12
    #Title (set_title): fontsize = 12
    #Tick labels (set_xticklabels / set_yticklabels): fontsize = 10

# Variables for the Gantt Charts and Project Network
# Default sizes
Value_xlabel_size = 20  # X-axis label font size (default 14)
Value_ylabel_size = 20  # Y-axis label font size (default 14)
Value_xtick_size = 15   # X-axis tick labels (values, e.g. time) font size (default 14)
Value_ytick_size = 15   # Y-axis tick labels (values, e.g. activity names) font size (default 14)
Value_title_size = 20   # Plot title font size (default 14)
Value_node_size = 2000  # Size of the node in the project network (default 2000)
Value_legend_size = 11  # Font size of legend for graphs (Put to 0 for not displaying the legend) (default 12)

# Variables for Project Network: No local parameter
#showEdgeLabels=False


def print_progress_bar(title, count, total_count, steps = 1, bar_length = 40):
    
    if count == 0:
        print("\n" + title)

    
    # Note that count has to start at 0 and ends at total_count - 1
    step = 1  # Percentage steps (e.g., every 5%)
    bar_length = 40  # Length of the progress bar (e.g., 40 characters wide)

    progress = ((count + 1) / total_count) * 100

    # Calculate the number of # characters to display in the progress bar
    bar = 'x' * int((progress / 100) * bar_length)
    spaces = ' ' * (bar_length - len(bar))

    # Only print when the progress is a multiple of the step size
    if progress % step == 0:
        print(f"\r[{bar}{spaces}] {int(progress)}%", end="", flush=True)

#    if count == total_count - 1:
#        print(" processing generated data...")
    return

#!pip install pymupdf
import os
import fitz
from PIL import Image
from IPython.display import display

def print_book_cover(Infofolder, scale=1.0):
    pdf_path = Infofolder + "ProPy_Book_Cover.pdf"
#    print("File exists:", os.path.exists(pdf_path))
#    print("Absolute path:", os.path.abspath(pdf_path))

    doc = fitz.open(pdf_path)

    for page in doc:
        pix = page.get_pixmap()
        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        
        # Scale the image
        if scale != 1.0:
            new_width = int(img.width * scale)
            new_height = int(img.height * scale)
            img = img.resize((new_width, new_height), Image.LANCZOS)
        
        display(img)

    
def print_summary_file(Infofolder, ExperimentID):


    pdf_path = Infofolder + "Summary_Experiment_" + str(ExperimentID) + ".pdf"
    print("File exists:", os.path.exists(pdf_path))
    print("Absolute path:", os.path.abspath(pdf_path))

    doc = fitz.open(pdf_path)

    for page in doc:
        pix = page.get_pixmap()
        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        display(img)