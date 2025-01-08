import sys
import json
import fitz  # PyMuPDF
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QLabel, QPushButton, QFileDialog, QVBoxLayout, QWidget, QGraphicsView, QGraphicsScene,
    QInputDialog, QGraphicsPolygonItem, QGraphicsTextItem
)
from PyQt5.QtGui import QPixmap, QImage, QPolygonF, QPen, QBrush, QFont
from PyQt5.QtCore import Qt, QPointF, QRectF


class AnnotationApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PDF Annotation Tool")
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

        self.layout = QVBoxLayout()
        self.graphics_view = QGraphicsView()
        self.scene = QGraphicsScene()

        self.graphics_view.setScene(self.scene)

        # Existing buttons
        self.load_pdf_button = QPushButton("Load PDF")
        self.load_pdf_button.clicked.connect(self.load_pdf)

        # New button for loading annotations
        self.load_annotations_button = QPushButton("Load Annotations")
        self.load_annotations_button.clicked.connect(self.load_annotations)

        # Other buttons (commit, next page, save)
        self.commit_button = QPushButton("Commit Bounding Box")
        self.commit_button.clicked.connect(self.commit_bounding_box)

        self.next_page_button = QPushButton("Next Page")
        self.next_page_button.clicked.connect(self.next_page)

        self.save_annotations_button = QPushButton("Save Annotations")
        self.save_annotations_button.clicked.connect(self.save_annotations)

        self.previous_page_button = QPushButton("Previous Page")
        self.previous_page_button.clicked.connect(self.previous_page)

        # Add buttons to layout
        self.layout.addWidget(self.graphics_view)
        self.layout.addWidget(self.load_pdf_button)
        self.layout.addWidget(self.load_annotations_button)  # Add new button here
        self.layout.addWidget(self.next_page_button)
        self.layout.addWidget(self.previous_page_button)  # Add this line to include the button in the layout
        self.layout.addWidget(self.save_annotations_button)

        container = QWidget()
        container.setLayout(self.layout)
        self.setCentralWidget(container)

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
                bounding_box.setBrush(Qt.transparent)
                bounding_box.setPen(Qt.red)
                self.scene.addItem(bounding_box)
                self.bounding_boxes.append(bounding_box)

                # Create text annotation
                label_item = QGraphicsTextItem(text)
                label_item.setPos(x + width / 2 - label_item.boundingRect().width() / 2,
                                  y + height / 2 - label_item.boundingRect().height() / 2)
                label_item.setDefaultTextColor(Qt.red)
                # Store the mapping of bounding box to text item
                self.text_items[bounding_box] = label_item
                self.scene.addItem(label_item)

    def enterEvent(self, event):
        self.graphics_view.setCursor(Qt.CrossCursor)
        super().enterEvent(event)

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
            bounding_box.setBrush(Qt.transparent)
            bounding_box.setPen(Qt.red)
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
                label_item.setPos(x1 + width / 2 - label_item.boundingRect().width() / 2,
                                  y1 + height / 2 - label_item.boundingRect().height() / 2)
                label_item.setDefaultTextColor(Qt.red)  # Set text color to red for visibility
                self.scene.addItem(label_item)
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
            # Get the scene position based on the mouse event
            pos = self.graphics_view.mapToScene(event.pos())

            # Get the current scale factor from the view's transformation
            scale_factor = self.graphics_view.transform().m11()  # Assumes uniform scaling

            # Adjust the cursor size based on the scale
            cursor_size = 20  # Base cursor size
            adjusted_cursor_size = cursor_size / scale_factor  # Scale cursor size with zoom level

            # Adjust click position based on scaled cursor size
            pos_adjusted = QPointF(pos.x() - adjusted_cursor_size / 2, pos.y() - adjusted_cursor_size / 2)

            if len(self.points) < 2:
                self.points.append(pos_adjusted)  # Add point to list

                # Draw point as a red circle
                point_item = self.scene.addEllipse(
                    pos_adjusted.x() - 3 / scale_factor,  # Adjust circle size for zoom
                    pos_adjusted.y() - 3 / scale_factor,
                    6 / scale_factor,
                    6 / scale_factor,
                    QPen(Qt.red),
                    QBrush(Qt.red)
                )
                self.point_items.append(point_item)  # Store the point item

                if len(self.points) == 2:
                    self.update_bounding_box()  # Draw bounding box once 4 points are added
                    self.commit_bounding_box()

                self.graphics_view.viewport().update()

            else:
                self.select_point(event)

        elif event.button() == Qt.RightButton:
            self.delete_bounding_box(event.pos())

    def delete_bounding_box(self, position):
        pos = self.graphics_view.mapToScene(position)
        for box in self.bounding_boxes:
            if box.contains(pos):
                #
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
    app = QApplication(sys.argv)
    window = AnnotationApp()
    window.show()
    sys.exit(app.exec_())
