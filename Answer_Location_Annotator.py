import json
import sys
import os
import fitz  # PyMuPDF
from PyQt5.QtCore import Qt, QPointF, QRectF, QSize
from PyQt5.QtGui import QPixmap, QImage, QPolygonF, QPen, QBrush, QIcon, QFont, QColor
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QPushButton, QFileDialog, QVBoxLayout, QWidget, QGraphicsView, QGraphicsScene, QGraphicsRectItem,
    QInputDialog, QGraphicsPolygonItem, QGraphicsTextItem, QHBoxLayout, QLabel, QSizePolicy
)
import qdarktheme


class AnnotationApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("MarkIT Annotation Tool")
        self.setGeometry(100, 100, 1200, 900)
        self.current_page = 0
        self.pdf_document = None
        self.annotations = {}
        self.points = []
        self.temp_lines = []
        self.temp_rect = None
        self.selected_point_idx = None
        self.zoom_factor = 1.0
        self.bounding_boxes = []
        self.point_items = []
        self.text_items = {}

        # Set up the layout and scene
        self.layout = QHBoxLayout()  # Horizontal layout for main window

        # Main widget for the PDF viewer
        self.main_widget = QWidget()
        self.main_layout = QVBoxLayout()

        self.title_label = QLabel("MarkIT Annotation Tool")
        self.title_label.setAlignment(Qt.AlignCenter)  # Center the title
        self.title_label.setStyleSheet("font-size: 24px; font-weight: bold; color: #AAAAAA; margin-bottom: 20px;")
        self.main_layout.addWidget(self.title_label)

        self.graphics_view = QGraphicsView()
        self.scene = QGraphicsScene()
        self.graphics_view.setScene(self.scene)

        self.main_layout.addWidget(self.graphics_view)
        self.main_widget.setLayout(self.main_layout)
        # Right side vertical button layout
        self.right_layout = QVBoxLayout()
        self.right_layout.setSpacing(15)  # Increased spacing between buttons for more room
        self.right_layout.setContentsMargins(10, 10, 10, 10)  # Add margins around the layout

        # Add company logo to the top right corner
        self.logo_label = QLabel()
        logo_path = os.path.join('resources', 'images', 'company_logo.png')  # Path to your logo
        pixmap = QPixmap(logo_path)
        self.logo_label.setPixmap(pixmap.scaled(150, 100, 1))  # Resize the logo to fit
        self.logo_label.setAlignment(Qt.AlignTop)  # Align to the top-right
        self.right_layout.addWidget(self.logo_label)  # Top-aligned logo


        # Existing buttons with fixed size
        self.load_pdf_button = QPushButton("Load PDF")
        self.load_pdf_button.clicked.connect(self.load_pdf)
        self.load_pdf_button.setFixedWidth(150)  # Fix the width for consistency
        self.load_pdf_button.setFixedHeight(40)  # Set fixed height for consistency

        self.load_annotations_button = QPushButton("Load Annotations")
        self.load_annotations_button.clicked.connect(self.load_annotations)
        self.load_annotations_button.setFixedWidth(150)
        self.load_annotations_button.setFixedHeight(40)

        self.save_annotations_button = QPushButton("Save Annotations")
        self.save_annotations_button.clicked.connect(self.save_annotations)
        self.save_annotations_button.setFixedWidth(150)
        self.save_annotations_button.setFixedHeight(40)

        # Arrow buttons for page navigation (placed side by side) with fixed size
        self.arrow_layout = QHBoxLayout()  # Horizontal layout for arrow buttons

        self.previous_page_button = QPushButton()
        prev_arrow_path = os.path.join('resources', 'images', 'left_arrow_icon.png')  # Path to left arrow icon
        self.previous_page_button.setIcon(QIcon(prev_arrow_path))
        self.previous_page_button.setIconSize(QSize(20, 20))  # Adjust icon size for better fit
        self.previous_page_button.setFixedSize(40, 40)  # Set fixed button size
        self.previous_page_button.clicked.connect(self.previous_page)

        self.next_page_button = QPushButton()
        next_arrow_path = os.path.join('resources', 'images', 'right_arrow_icon.png')  # Path to right arrow icon
        self.next_page_button.setIcon(QIcon(next_arrow_path))
        self.next_page_button.setIconSize(QSize(20, 20))  # Adjust icon size for better fit
        self.next_page_button.setFixedSize(40, 40)  # Set fixed button size
        self.next_page_button.clicked.connect(self.next_page)

        # Add the arrow buttons to the horizontal layout
        self.arrow_layout.addWidget(self.previous_page_button)
        self.arrow_layout.addWidget(self.next_page_button)

        # Add the other buttons to the right layout with spacing
        self.right_layout.addWidget(self.load_pdf_button)
        self.right_layout.addWidget(self.load_annotations_button)
        self.right_layout.addLayout(self.arrow_layout)  # Add arrow buttons layout
        self.right_layout.addWidget(self.save_annotations_button)

        # Add stretch to push the powered by label down
        self.right_layout.addStretch(1)

        # Add the "Powered by NCAI" text at the bottom right with fixed size
        self.powered_by_label = QLabel("Powered by NCAI")
        self.powered_by_label.setAlignment(Qt.AlignBottom)
        self.right_layout.addWidget(self.powered_by_label)


        # Create a container widget for the button layout
        self.right_widget = QWidget()
        self.right_widget.setLayout(self.right_layout)

        # Add the graphics view and right sidebar to the main horizontal layout
        self.layout.addWidget(self.main_widget)
        self.layout.addWidget(self.right_widget)

        container = QWidget()
        container.setLayout(self.layout)
        self.setCentralWidget(container)

        # Apply some styling to the buttons for better appearance
        self.setStyleSheet("""
            QPushButton {
                font-size: 14px;
                padding: 10px;
                border-radius: 5px;
                background-color: #007BFF; 
                color: black;
                border: none;
            }
            QPushButton:hover {
                background-color: #0056b3;  
            }
            QPushButton:pressed {
                background-color: #004085;
            }
            QLabel {
                font-size: 12px;
                color: #888888;
            }
        """)

    def load_annotations(self):
        file_name, _ = QFileDialog.getOpenFileName(self, "Open Annotations File", "", "JSON Files (*.json)")

        if file_name:
            with open(file_name, "r") as json_file:
                loaded_annotations = json.load(json_file)

            # Merge loaded annotations with current annotations
            for page_number, data in loaded_annotations.items():
                if page_number not in self.annotations:
                    self.annotations[page_number] = {"labels": []}
                self.annotations[page_number]["labels"].extend(data["labels"])  # Add existing labels

            # Draw existing annotations on the current page
            self.draw_existing_annotations()

    def draw_existing_annotations(self):
        page_number = str(self.current_page + 1)
        if page_number in self.annotations:
            for label in self.annotations[page_number]["labels"]:
                x = label["position"]["x"]
                y = label["position"]["y"]
                width = label["position"]["width"]
                height = label["position"]["height"]
                text = label["text"]

                # Create bounding box
                rect_points = QPolygonF([
                    QPointF(x, y),
                    QPointF(x + width, y),
                    QPointF(x + width, y + height),
                    QPointF(x, y + height)
                ])

                bounding_box = QGraphicsPolygonItem(rect_points)
                bounding_box.setBrush(QColor(255, 0, 0, 50))  # Semi-transparent red fill for better visibility
                bounding_box.setPen(QPen(QColor(255, 0, 0), 3))  # Thicker red border

                # Add the bounding box to the scene
                self.scene.addItem(bounding_box)
                self.bounding_boxes.append(bounding_box)

                # Create text annotation
                label_item = QGraphicsTextItem(text)
                label_item.setFont(QFont("Arial", 13, QFont.Bold))  # Set a larger, bold font
                label_item.setPos(x + width / 2 - label_item.boundingRect().width() / 2,
                                  y + height / 2 - label_item.boundingRect().height() / 2)
                label_item.setDefaultTextColor(Qt.blue)
                # Store the mapping of bounding box to text item
                self.text_items[bounding_box] = label_item
                self.scene.addItem(label_item)

    def enterEvent(self, event):
        self.graphics_view.setCursor(Qt.CrossCursor)
        super().enterEvent(event)

    def keyPressEvent(self, e):
        if e.key() == Qt.Key_A:  # "A" key for previous page
            self.previous_page()
        elif e.key() == Qt.Key_D:  # "D" key for next page
            self.next_page()

    def load_pdf(self):
        file_name, _ = QFileDialog.getOpenFileName(self, "Open PDF File", "", "PDF Files (*.pdf)")
        if file_name:
            self.pdf_document = fitz.open(file_name)
            self.current_page = 0
            self.annotations = {}
            self.load_page()

    def load_page(self):
        if self.pdf_document:
            page = self.pdf_document.load_page(self.current_page)
            zoom_x = 2.0  # Increase for higher horizontal resolution
            zoom_y = 2.0  # Increase for higher vertical resolution
            matrix = fitz.Matrix(zoom_x, zoom_y) * fitz.Matrix(self.zoom_factor, self.zoom_factor)
            pix = page.get_pixmap(matrix=matrix)
            qt_image = QImage(pix.samples, pix.width, pix.height, pix.stride, QImage.Format_RGB888)

            pixmap = QPixmap.fromImage(qt_image)

            # Resize the pixmap to a fixed size (2160, 1440) without changing the actual image
            pixmap = pixmap.scaled(1440, 2160, Qt.KeepAspectRatio, Qt.SmoothTransformation)

            self.scene.clear()  # Clear previous items
            self.scene.addPixmap(pixmap)  # Add the new page image
            self.graphics_view.setScene(self.scene)  # Set the scene in the graphics view

            self.points = []  # Clear points for new bounding box
            self.temp_lines = []  # Clear temporary lines
            self.temp_rect = None  # Clear temporary rectangle

            # Draw existing annotations for the current page
            self.draw_existing_annotations()

    def commit_bounding_box(self):
        if len(self.points) == 2:
            top_left = QPointF(self.points[0])
            bottom_right = QPointF(self.points[1])

            # Create a rectangle using the top-left and bottom-right points
            rect = QRectF(top_left, bottom_right)
            rect_points = QPolygonF([rect.topLeft(), rect.topRight(), rect.bottomRight(), rect.bottomLeft()])

            # Create a QGraphicsPolygonItem for the bounding box
            bounding_box = QGraphicsPolygonItem(rect_points)
            bounding_box.setBrush(QColor(255, 0, 0, 50))  # Semi-transparent red fill for better visibility
            bounding_box.setPen(QPen(QColor(255, 0, 0), 3))  # Thicker red border

            self.scene.addItem(bounding_box)

            # Store bounding box in the list
            self.bounding_boxes.append(bounding_box)

            # Calculate coordinates and dimensions
            x1, y1 = int(rect.topLeft().x()), int(rect.topLeft().y())
            width, height = int(rect.width()), int(rect.height())

            # Automatically prompt user for annotation label
            label, ok = QInputDialog.getText(self, "Set Annotation Label", "Enter label:")
            if ok and label:
                page_number = str(self.current_page + 1)
                if page_number not in self.annotations:
                    self.annotations[page_number] = {"labels": []}

                self.annotations[page_number]["labels"].append({
                    "position": {"x": x1, "y": y1, "width": width, "height": height},
                    "text": label
                })

                # Create the text annotation inside the bounding box
                label_item = QGraphicsTextItem(label)
                label_item.setFont(QFont("Arial", 13, QFont.Bold))  # Set a larger, bold font
                label_item.setPos(x1 + width / 2 - label_item.boundingRect().width() / 2,
                                  y1 + height / 2 - label_item.boundingRect().height() / 2)
                label_item.setDefaultTextColor(Qt.blue)  # Set text color to white for better contrast

                self.scene.addItem(label_item)

                # Store the text item
                self.text_items[bounding_box] = label_item
            else:
                # If the user cancels the prompt, remove the bounding box
                self.scene.removeItem(bounding_box)
                self.bounding_boxes.remove(bounding_box)

            # Clear temporary items after committing the bounding box
            self.points = []
            self.clear_temporary_items()

    def next_page(self):
        if self.pdf_document and self.current_page < len(self.pdf_document) - 1:
            self.current_page += 1
            self.load_page()

    def previous_page(self):
        if self.pdf_document and self.current_page > 0:  # Ensure current_page is greater than 0
            self.current_page -= 1
            self.load_page()  # Load the previous page

    def save_annotations(self):
        file_name, _ = QFileDialog.getSaveFileName(self, "Save Annotations", "", "JSON Files (*.json)")
        if file_name:
            with open(file_name, "w") as json_file:
                json.dump(self.annotations, json_file, indent=4)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton and self.graphics_view.underMouse():
            # Map the view coordinates to the scene coordinates
            scene_pos = self.graphics_view.mapToScene(event.pos())

            # Define adjustable offsets
            x_offset = getattr(self, "x_offset", -20)  # Default to 0 if not set
            y_offset = getattr(self, "y_offset", -78)  # Default to 0 if not set

            # Adjust for zoom factor
            scale_factor = self.graphics_view.transform().m11()  # Assumes uniform scaling
            adjusted_pos = QPointF(scene_pos.x() + x_offset / scale_factor,
                                   scene_pos.y() + y_offset / scale_factor)

            if len(self.points) < 2:
                self.points.append(adjusted_pos)  # Add the adjusted position

                # Draw point as a red circle
                point_item = self.scene.addEllipse(
                    adjusted_pos.x() - 3 / scale_factor,  # Adjust size for zoom
                    adjusted_pos.y() - 3 / scale_factor,
                    6 / scale_factor,
                    6 / scale_factor,
                    QPen(Qt.red),
                    QBrush(Qt.red)
                )
                self.point_items.append(point_item)  # Store the point item

                if len(self.points) == 2:
                    self.update_bounding_box()  # Draw bounding box once 2 points are added
                    self.commit_bounding_box()

                self.graphics_view.viewport().update()

        elif event.button() == Qt.RightButton:
            self.delete_bounding_box(event.pos())

    def delete_bounding_box(self, position):
        # Map the view position to the scene position
        pos = self.graphics_view.mapToScene(position)

        # Adjust for zoom factor and offset
        scale_factor = self.graphics_view.transform().m11()  # Assumes uniform scaling
        x_offset = getattr(self, "x_offset", -20)  # Default to 0 if not set
        y_offset = getattr(self, "y_offset", -78)  # Default to 0 if not set
        adjusted_pos = QPointF(pos.x() + x_offset / scale_factor,
                               pos.y() + y_offset / scale_factor)

        # Loop through the bounding boxes to check if the click position is inside any of them
        for box in self.bounding_boxes:
            if box.contains(adjusted_pos):
                # Remove the bounding box from the scene and the list
                self.scene.removeItem(box)
                self.bounding_boxes.remove(box)

                # Remove the corresponding annotation from self.annotations
                page_number = str(self.current_page + 1)
                if page_number in self.annotations:
                    labels = self.annotations[page_number]["labels"]
                    for label in labels:
                        if self.is_bbox_match(label["position"], box):
                            labels.remove(label)
                            break

                # Remove the associated text item
                if box in self.text_items:
                    text_item = self.text_items[box]
                    self.scene.removeItem(text_item)  # Remove from scene
                    del self.text_items[box]  # Remove from dictionary
                break

    def is_bbox_match(self, annotation_position, box):
        # Helper method to check if the bounding box matches the annotation position
        box_points = [box.polygon().at(i) for i in range(4)]
        x1, y1 = annotation_position["x"], annotation_position["y"]
        x2, y2 = annotation_position["x"] + annotation_position["width"], annotation_position["y"] + \
                 annotation_position["height"]
        return (min(box_points[0].x(), box_points[2].x()) <= x1 <= max(box_points[0].x(), box_points[2].x()) and
                min(box_points[0].y(), box_points[2].y()) <= y1 <= max(box_points[0].y(), box_points[2].y()) and
                min(box_points[0].x(), box_points[2].x()) <= x2 <= max(box_points[0].x(), box_points[2].x()) and
                min(box_points[0].y(), box_points[2].y()) <= y2 <= max(box_points[0].y(), box_points[2].y()))

    def select_point(self, event):
        # Select the nearest point within a threshold distance
        threshold = 10  # Threshold to select a point for dragging
        for idx, point in enumerate(self.points):
            if abs(event.x() - point.x()) < threshold and abs(event.y() - point.y()) < threshold:
                self.selected_point_idx = idx
                break

    def update_bounding_box(self):
        if self.temp_rect:
            self.scene.removeItem(self.temp_rect)

        if len(self.points) == 2:
            top_left = QPointF(self.points[0])
            bottom_right = QPointF(self.points[1])

            # Create a rectangle using the top-left and bottom-right points
            rect = QRectF(top_left, bottom_right)

            # Create a QGraphicsPolygonItem for the rectangle
            self.temp_rect = QGraphicsPolygonItem(QPolygonF(rect))
            self.temp_rect.setPen(QPen(Qt.blue, 2))
            self.temp_rect.setBrush(QBrush(Qt.blue, Qt.Dense4Pattern))
            self.scene.addItem(self.temp_rect)

    def clear_temporary_items(self):
        for line in self.temp_lines:
            self.scene.removeItem(line)
        self.temp_lines = []

        if self.temp_rect:
            self.scene.removeItem(self.temp_rect)
            self.temp_rect = None

        # Remove point items from the scene
        for point_item in self.point_items:
            self.scene.removeItem(point_item)
        self.point_items = []

    def wheelEvent(self, event):
        # Zoom in or zoom out using Ctrl + mouse wheel
        if event.modifiers() == Qt.ControlModifier:
            zoom_in = event.angleDelta().y() > 0
            if zoom_in:
                self.zoom_factor *= 1.1
            else:
                self.zoom_factor /= 1.1

            # Apply the zoom transformation to the view, not the image itself
            self.graphics_view.setTransform(
                self.graphics_view.transform().scale(1.1 if zoom_in else 0.9, 1.1 if zoom_in else 0.9))


if __name__ == "__main__":
    qdarktheme.enable_hi_dpi()
    app = QApplication(sys.argv + ['-platform', 'windows:darkmode=1'])
    qdarktheme.setup_theme()

    window = AnnotationApp()
    window.show()
    sys.exit(app.exec_())
