# MarkIT Annotator

## Overview

The MarkIT Annotator is a desktop application designed for annotating and identifying specific locations in scanned exam PDFs. It enables users to load a PDF document, create bounding boxes around areas of interest, and label those areas for easy identification. This tool is particularly useful for educators and students who need to highlight answers or important sections in exam papers.

## Features

- **Load PDF Files**: Open scanned PDF documents for annotation.
- **Create Annotations**: Draw bounding boxes around specific areas and assign labels to them.
- **Load Existing Annotations**: Import previously saved annotations from JSON files.
- **Save Annotations**: Export annotations to a JSON file for future reference.
- **Navigation**: Easily navigate between pages of the PDF document.
- **Zoom Functionality**: Zoom in and out of the PDF for detailed viewing.

## Installation

To run the application, ensure you have Python installed along with the required libraries. You can install the necessary packages using pip:

```commandline
pip install PyQt5 PyMuPDF
```


## Usage Instructions

### Launching the Application

Run the script using Python. The application window will open.

### Loading a PDF

Click on the "Load PDF" button to select and open a scanned exam PDF file.

### Annotating the PDF

1. Navigate to the desired page using the "Next Page" and "Previous Page" buttons.
2. Click and drag to create a bounding box around the area you want to annotate.
3. After drawing the box, you will be prompted to enter a label for that annotation.

### Saving Annotations

To save your annotations, click on the "Save Annotations" button and choose a location to save your JSON file.

### Loading Annotations

If you have previously saved annotations, you can load them by clicking on "Load Annotations" and selecting your JSON file.

### Deleting Annotations

Right-click on any existing bounding box to delete it along with its associated label.

### Zooming In/Out

Use Ctrl + mouse wheel to zoom in or out of the document for better visibility.
