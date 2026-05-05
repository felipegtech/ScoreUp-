import sys
import json
import os
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                               QHBoxLayout, QLineEdit, QPushButton, QLabel,
                               QScrollArea, QMessageBox, QFrame, QTabWidget,
                               QInputDialog, QColorDialog)
from PySide6.QtCore import Qt
from PySide6.QtGui import QDoubleValidator, QColor, QIcon, QPixmap

DATA_FILE = "my_grades.json"


def create_color_icon(color_hex):
    """Creates a small square icon of the specified color for the tab."""
    pixmap = QPixmap(16, 16)
    pixmap.fill(QColor(color_hex))
    return QIcon(pixmap)


class GradeRow(QWidget):
    def __init__(self, delete_callback, activity="", grade="", weight=""):
        super().__init__()
        self.layout = QHBoxLayout()
        self.layout.setContentsMargins(0, 0, 0, 0)

        validator = QDoubleValidator(0.0, 100.0, 2)
        validator.setNotation(QDoubleValidator.StandardNotation)

        self.input_activity = QLineEdit(activity)
        self.input_activity.setPlaceholderText("e.g., Lab 1, Midterm")

        self.input_grade = QLineEdit(str(grade) if grade else "")
        self.input_grade.setPlaceholderText("Grade")
        self.input_grade.setFixedWidth(60)
        self.input_grade.setValidator(validator)

        self.input_weight = QLineEdit(str(weight) if weight else "")
        self.input_weight.setPlaceholderText("%")
        self.input_weight.setFixedWidth(60)
        self.input_weight.setValidator(validator)

        btn_delete = QPushButton("❌")
        btn_delete.setFixedWidth(30)
        btn_delete.setStyleSheet("color: #ff4c4c; border: none; font-weight: bold; font-size: 14px;")
        btn_delete.clicked.connect(lambda: delete_callback(self))

        self.layout.addWidget(QLabel("Assignment:"))
        self.layout.addWidget(self.input_activity, stretch=1)
        self.layout.addWidget(QLabel("Grade:"))
        self.layout.addWidget(self.input_grade)
        self.layout.addWidget(QLabel("Weight (%):"))
        self.layout.addWidget(self.input_weight)
        self.layout.addWidget(btn_delete)

        self.setLayout(self.layout)

    def get_data(self):
        try:
            grade = float(self.input_grade.text().replace(',', '.')) if self.input_grade.text() else 0.0
            weight = float(self.input_weight.text().replace(',', '.')) if self.input_weight.text() else 0.0
            activity = self.input_activity.text()
            return activity, grade, weight
        except ValueError:
            return self.input_activity.text(), 0.0, 0.0


class SubjectTab(QWidget):
    """Represents the content of a single subject/course."""

    def __init__(self, name, color_hex, target="3.0", row_data=None, save_callback=None):
        super().__init__()
        self.name = name
        self.color_hex = color_hex
        self.save_callback = save_callback
        self.rows = []

        main_layout = QVBoxLayout(self)

        # Top color banner
        banner = QFrame()
        banner.setFixedHeight(5)
        banner.setStyleSheet(f"background-color: {color_hex}; border-radius: 2px;")
        main_layout.addWidget(banner)

        # Target Grade Header
        header_layout = QHBoxLayout()
        header_layout.addWidget(QLabel("Passing Grade:"))
        self.input_target = QLineEdit(str(target))
        self.input_target.setFixedWidth(50)
        header_layout.addWidget(self.input_target)
        header_layout.addStretch()

        btn_delete_subject = QPushButton("🗑️ Delete Course")
        btn_delete_subject.setStyleSheet("color: #ff4c4c; border: 1px solid #ff4c4c; padding: 4px; border-radius: 4px;")
        header_layout.addWidget(btn_delete_subject)
        main_layout.addLayout(header_layout)

        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        main_layout.addWidget(line)

        # Scroll Area for grades
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.grades_widget = QWidget()
        self.grades_layout = QVBoxLayout(self.grades_widget)
        self.grades_layout.setAlignment(Qt.AlignTop)
        self.scroll_area.setWidget(self.grades_widget)
        main_layout.addWidget(self.scroll_area)

        # Bottom buttons
        buttons_layout = QHBoxLayout()
        btn_add = QPushButton("+ Add Assignment")
        btn_add.clicked.connect(self.add_row)

        btn_calculate = QPushButton("Calculate & Save")
        btn_calculate.setStyleSheet(
            f"background-color: {color_hex}; color: white; font-weight: bold; padding: 8px; border-radius: 4px;")
        btn_calculate.clicked.connect(self.calculate_result)

        buttons_layout.addWidget(btn_add)
        buttons_layout.addWidget(btn_calculate)
        main_layout.addLayout(buttons_layout)

        # Result Label
        self.label_result = QLabel("Enter your grades and press Calculate.")
        self.label_result.setAlignment(Qt.AlignCenter)
        self.label_result.setWordWrap(True)
        self.label_result.setStyleSheet("font-size: 14px; font-weight: bold; margin-top: 10px; min-height: 40px;")
        main_layout.addWidget(self.label_result)

        # Load initial rows
        if row_data:
            for data in row_data:
                self.add_row(data.get("activity", ""), data.get("grade", ""), data.get("weight", ""))
        else:
            for _ in range(3):
                self.add_row()

    def add_row(self, activity="", grade="", weight=""):
        row = GradeRow(self.delete_row, activity, grade, weight)
        self.rows.append(row)
        self.grades_layout.addWidget(row)

    def delete_row(self, row):
        self.rows.remove(row)
        self.grades_layout.removeWidget(row)
        row.deleteLater()
        self.calculate_result()

    def calculate_result(self):
        try:
            target = float(self.input_target.text().replace(',', '.'))
        except ValueError:
            QMessageBox.critical(self, "Error", "The passing grade must be a number.")
            return

        accumulated_grade = 0.0
        total_weight = 0.0

        for row in self.rows:
            _, grade, weight = row.get_data()
            accumulated_grade += grade * (weight / 100.0)
            total_weight += weight

        if total_weight > 100.0:
            self.label_result.setText(f"Error! The total weight is {total_weight}%. It exceeds 100%.")
            self.label_result.setStyleSheet("color: #ff4c4c; font-size: 14px; font-weight: bold;")
        else:
            remaining_weight = 100.0 - total_weight

            if remaining_weight <= 0.0:
                if accumulated_grade >= target:
                    self.label_result.setText(
                        f"Congratulations! You passed {self.name} with a {accumulated_grade:.2f}.")
                    self.label_result.setStyleSheet("color: #4caf50; font-size: 14px; font-weight: bold;")
                else:
                    self.label_result.setText(
                        f"Your final grade in {self.name} is {accumulated_grade:.2f}. Not enough to pass.")
                    self.label_result.setStyleSheet("color: #ff4c4c; font-size: 14px; font-weight: bold;")
            else:
                needed_grade = (target - accumulated_grade) / (remaining_weight / 100.0)

                if needed_grade <= 0:
                    self.label_result.setText(
                        f"You already passed {self.name}! You currently have {accumulated_grade:.2f}.")
                    self.label_result.setStyleSheet("color: #4caf50; font-size: 14px; font-weight: bold;")
                elif needed_grade > 5.0:  # Assuming 5.0 is the maximum grade
                    self.label_result.setText(
                        f"You need a {needed_grade:.2f} in the remaining {remaining_weight:.1f}%.\nMathematically impossible!")
                    self.label_result.setStyleSheet("color: #ff4c4c; font-size: 14px; font-weight: bold;")
                else:
                    self.label_result.setText(
                        f"To pass {self.name}, you need a {needed_grade:.2f} in the remaining {remaining_weight:.1f}%.")
                    self.label_result.setStyleSheet(f"color: {self.color_hex}; font-size: 14px; font-weight: bold;")

        # Auto-save after calculating
        if self.save_callback:
            self.save_callback()

    def collect_data(self):
        row_data = []
        for row in self.rows:
            activity, grade, weight = row.get_data()
            row_data.append({"activity": activity, "grade": grade, "weight": weight})

        return {
            "color": self.color_hex,
            "target": self.input_target.text(),
            "grades": row_data
        }


class GradeCalculatorApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Grade Calculator - Semester Tracker")
        self.setMinimumSize(650, 550)

        # Basic Dark Mode Configuration
        self.setStyleSheet("""
            QMainWindow, QWidget { background-color: #1e1e1e; color: #ffffff; }
            QLineEdit { background-color: #2d2d2d; border: 1px solid #444; padding: 4px; border-radius: 4px; color: white;}
            QPushButton { background-color: #333; border: 1px solid #555; padding: 6px; border-radius: 4px; color: white;}
            QPushButton:hover { background-color: #444; }
            QTabWidget::pane { border: 1px solid #444; background: #1e1e1e; }
            QTabBar::tab { background: #2d2d2d; color: white; padding: 8px 15px; border: 1px solid #444; border-bottom: none; border-top-left-radius: 4px; border-top-right-radius: 4px; }
            QTabBar::tab:selected { background: #1e1e1e; font-weight: bold; }
        """)

        central_widget = QWidget()
        self.main_layout = QVBoxLayout(central_widget)

        # Header with Add Course button
        top_header = QHBoxLayout()
        top_header.addWidget(QLabel("📚 <b>Your Courses</b>"))
        top_header.addStretch()
        btn_new_subject = QPushButton("+ New Course")
        btn_new_subject.setStyleSheet("background-color: #0078d7; font-weight: bold;")
        btn_new_subject.clicked.connect(self.create_new_subject)
        top_header.addWidget(btn_new_subject)
        self.main_layout.addLayout(top_header)

        # Tab System
        self.tabs = QTabWidget()
        self.main_layout.addWidget(self.tabs)

        self.setCentralWidget(central_widget)
        self.load_data()

    def load_data(self):
        if os.path.exists(DATA_FILE):
            try:
                with open(DATA_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    for subject_name, info in data.items():
                        self.add_tab(subject_name, info.get("color", "#008CBA"), info.get("target", "3.0"),
                                     info.get("grades", []))
            except Exception as e:
                print(f"Error loading data: {e}")

        # If no data (or file didn't exist), create a default tab
        if self.tabs.count() == 0:
            self.add_tab("Physics II", "#3498db")  # A default blue color to start

    def save_data(self):
        complete_data = {}
        for i in range(self.tabs.count()):
            subject_widget = self.tabs.widget(i)
            subject_name = subject_widget.name
            complete_data[subject_name] = subject_widget.collect_data()

        try:
            with open(DATA_FILE, "w", encoding="utf-8") as f:
                json.dump(complete_data, f, indent=4, ensure_ascii=False)
        except Exception as e:
            print(f"Error saving data: {e}")

    def create_new_subject(self):
        name, ok = QInputDialog.getText(self, "New Course", "Course name:")
        if ok and name:
            # Validate that it doesn't already exist
            for i in range(self.tabs.count()):
                if self.tabs.widget(i).name == name:
                    QMessageBox.warning(self, "Error", "This course already exists.")
                    return

            color = QColorDialog.getColor()
            if color.isValid():
                color_hex = color.name()
                self.add_tab(name, color_hex)
                self.tabs.setCurrentIndex(self.tabs.count() - 1)
                self.save_data()

    def add_tab(self, name, color_hex, target="3.0", row_data=None):
        tab = SubjectTab(name, color_hex, target, row_data, save_callback=self.save_data)

        # Connect the delete button of the tab
        btn_delete = tab.findChild(QPushButton)
        if btn_delete:
            btn_delete.clicked.connect(lambda: self.delete_subject(tab))

        icon = create_color_icon(color_hex)
        index = self.tabs.addTab(tab, icon, name)

        # Try to calculate upon adding to load saved results
        tab.calculate_result()

    def delete_subject(self, subject_widget):
        reply = QMessageBox.question(self, "Confirm",
                                     f"Are you sure you want to delete '{subject_widget.name}' and all its grades?",
                                     QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            index = self.tabs.indexOf(subject_widget)
            self.tabs.removeTab(index)
            subject_widget.deleteLater()
            self.save_data()

    def closeEvent(self, event):
        """This method runs automatically when the window is closed."""
        self.save_data()
        event.accept()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = GradeCalculatorApp()
    window.show()
    sys.exit(app.exec())