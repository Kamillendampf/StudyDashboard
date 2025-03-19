import json
import logging as log
import os.path
import sys

from win32api import GetSystemMetrics

from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton, QLabel, QLineEdit, QTableWidget, \
    QTableWidgetItem, QSpinBox, QDoubleSpinBox, QDialog, QMessageBox, QHBoxLayout

from matplotlib import pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas




class StudyConfig:
    CONFIG_FILE = "save/config.json"

    def __init__(self):
        self.target_time = 0
        self.target_grade = 0.0
        self.load_config()

    def load_config(self):

        try:
            with open(self.CONFIG_FILE, "r") as file:
                data = json.load(file)
                self.target_time = data.get("target_time", 0)
                self.target_grade = data.get("target_grade", 0.0)
                log.info("Konfiguration wurde erfoglreich geladen")
        except (FileNotFoundError, json.JSONDecodeError):
            log.warning("Konfigurationsdatei nicht gefunden.")
            self.ask_user_for_config()

    def ask_user_for_config(self):

        dialog = ConfigDialog()
        if dialog.exec():
            self.target_time = dialog.target_time_input.value()
            self.target_grade = dialog.target_grade_input.value()
            self.save_config()

    def save_config(self):

        with open(self.CONFIG_FILE, "w") as file:
            json.dump({
                "target_time": self.target_time,
                "target_grade": self.target_grade
            }, file)
            log.info("Konfiguration gespeichert: %d Jahre, Zielnote %.2f",  self.target_time,
                     self.target_grade)


class ConfigDialog(QDialog):

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Erstkonfiguration")
        layout = QVBoxLayout()

        self.target_time_input = QSpinBox(self)
        self.target_time_input.setRange(1, 10)
        layout.addWidget(QLabel("Zielzeit in Semestern:"))
        layout.addWidget(self.target_time_input)

        self.target_grade_input = QDoubleSpinBox(self)
        self.target_grade_input.setRange(1.0, 5.0)
        self.target_grade_input.setSingleStep(0.1)
        layout.addWidget(QLabel("Zielnote:"))
        layout.addWidget(self.target_grade_input)

        self.save_button = QPushButton("Speichern", self)
        self.save_button.clicked.connect(self.accept)
        layout.addWidget(self.save_button)

        self.setLayout(layout)


class Course:

    def __init__(self, name, ects, grade, target_grade, semester):

        self.name = name
        if ects != 0:
            self.ects = ects
        self.grade = grade
        self.target_grade = target_grade
        self.semester = semester

    def is_completed(self):

        return self.grade is not None and 1 <= self.grade <= 4

    def to_dict(self):

        return {"name": self.name, "ects": self.ects, "grade": self.grade, "target_grade": self.target_grade,
                "semester": self.semester}

    @staticmethod
    def from_dict(data):

        return Course(data["name"], data["ects"], data["grade"], data["target_grade"], data["semester"])


class CourseManager:
    FILE_PATH = "save/courses.json"

    @staticmethod
    def save_courses(courses, parent=None):

        existing_courses = {course.name: course for course in courses}
        if len(existing_courses) < len(courses):
            log.info("Doppelte Kurse wurden entfernt.")
            QMessageBox.warning(parent, "Der Kurs existiert bereits", "Einige doppelte Kurse wurden entfernt.")
            return False

        with open(CourseManager.FILE_PATH, "w") as file:
            json.dump([course.to_dict() for course in existing_courses.values()], file)
            return True
            log.info(" Neuer Kurs wurde angelegt")

    @staticmethod
    def load_courses():

        try:
            with open(CourseManager.FILE_PATH, "r") as file:
                courses = [Course.from_dict(data) for data in json.load(file)]
                log.info("%d Kurse erfolgreich geladen.", len(courses))
                return courses

        except (FileNotFoundError, json.JSONDecodeError):
            log.info("Kursdatei nicht gefunden - wird erstellt.")
            with open(CourseManager.FILE_PATH, "w") as file:
                json.dump("", file)
                log.info("Kursdatei wurde erstellt.")
            return []

    @staticmethod
    def sort_courses_by_semester(courses):

        return sorted(courses, key=lambda course: course.semester)


class AddCourseDialog(QDialog):

    def __init__(self):
        super().__init__()

        self.config = StudyConfig()

        self.setWindowTitle("Neues Modul hinzufügen")
        layout = QVBoxLayout()

        self.name_input = QLineEdit(self)
        layout.addWidget(QLabel("Kursname:"))
        layout.addWidget(self.name_input)

        self.ects_input = QSpinBox(self)
        self.ects_input.setRange(1, 5)
        layout.addWidget(QLabel("ECTS:"))
        layout.addWidget(self.ects_input)

        self.target_grade_input = QDoubleSpinBox(self)
        self.target_grade_input.setRange(1.0, 5.0)
        self.target_grade_input.setSingleStep(0.1)
        layout.addWidget(QLabel("Zielnote:"))
        layout.addWidget(self.target_grade_input)

        self.semester_input = QSpinBox(self)
        self.semester_input.setRange(1, self.config.target_time * 2)
        layout.addWidget(QLabel("Semester:"))
        layout.addWidget(self.semester_input)

        self.add_button = QPushButton("Hinzufügen", self)
        self.add_button.clicked.connect(self.accept)
        layout.addWidget(self.add_button)

        self.setLayout(layout)

    def get_course(self):
        return Course(
            self.name_input.text(),
            self.ects_input.value(),
            0,
            self.target_grade_input.value(),
            self.semester_input.value()
        )


class EditCourseDialog(QDialog):

    def __init__(self, course):
        super().__init__()

        self.config = StudyConfig()

        self.setWindowTitle("Modul bearbeiten")
        self.layout = QVBoxLayout()
        self.name_input = QLineEdit()
        self.ects_input = QSpinBox()
        self.ects_input.setRange(1, 5)
        self.grade_input = QDoubleSpinBox()
        self.grade_input.setRange(0.0, 5.0)
        self.target_grade_input = QDoubleSpinBox()
        self.target_grade_input.setRange(1.0, 5.0)
        self.semester_input = QSpinBox()
        self.semester_input.setRange(1, self.config.target_time * 2)

        if course:
            self.name_input.setText(course.name)
            self.ects_input.setValue(course.ects)
            if course.grade:
                self.grade_input.setValue(course.grade)
            self.target_grade_input.setValue(course.target_grade)
            self.semester_input.setValue(course.semester)

        self.layout.addWidget(QLabel("Kursname:"))
        self.layout.addWidget(self.name_input)
        self.layout.addWidget(QLabel("ECTS:"))
        self.layout.addWidget(self.ects_input)
        self.layout.addWidget(QLabel("Note:"))
        self.layout.addWidget(self.grade_input)
        self.layout.addWidget(QLabel("Zielnote:"))
        self.layout.addWidget(self.target_grade_input)
        self.layout.addWidget(QLabel("Semester:"))
        self.layout.addWidget(self.semester_input)

        self.save_button = QPushButton("Speichern")
        self.save_button.clicked.connect(self.accept)
        self.layout.addWidget(self.save_button)

        self.setLayout(self.layout)

    def get_course(self):

        return Course(
            self.name_input.text(),
            self.ects_input.value(),
            self.grade_input.value(),
            self.target_grade_input.value(),
            self.semester_input.value()
        )


class Dashboard(QWidget):

    def __init__(self):
        super().__init__()
        self.config = StudyConfig()
        self.courses = CourseManager.load_courses()
        self.render()


    def render(self):

        self.setGeometry(0, 0, GetSystemMetrics(0), GetSystemMetrics(1))

        self.setWindowTitle("ECTS & Abschlussnote Dashboard")


        main_layout = QVBoxLayout()
        info_layout = QVBoxLayout()
        content_layout = QHBoxLayout()

        info_layout.addWidget(QLabel(f"Zielzeit: {self.config.target_time} Jahre"))
        info_layout.addWidget(QLabel(f"Zielsemester: {self.config.target_time * 2} Semeseter"))
        info_layout.addWidget(QLabel(f"Zielnote: {self.config.target_grade}"))

        self.add_course_button = QPushButton("Modul hinzufügen")
        self.add_course_button.clicked.connect(self.add_course)
        info_layout.addWidget(self.add_course_button)

        self.edit_course_button = QPushButton("Modul bearbeiten")
        self.edit_course_button.clicked.connect(self.edit_course)
        info_layout.addWidget(self.edit_course_button)

        self.course_table = QTableWidget()
        self.course_table.setColumnCount(5)
        self.course_table.setHorizontalHeaderLabels(["Name", "ECTS", "Note", "Zielnote", "Semester"])
        content_layout.addWidget(self.course_table)

        self.canvas = FigureCanvas(plt.figure())
        content_layout.addWidget(self.canvas)

        self.burndown_canvas = FigureCanvas(plt.figure())
        content_layout.addWidget(self.burndown_canvas)

        main_layout.addLayout(info_layout)
        main_layout.addLayout(content_layout)
        self.setLayout(main_layout)

        self.update_chart()
        self.update_burndown_chart()
        self.update_table()

    def edit_course(self):

        selected_row = self.course_table.currentRow()
        print(selected_row)
        if selected_row == -1:
            QMessageBox.warning(self, "Keine Auswahl", "Bitte wählen Sie einen Kurs zum Bearbeiten aus.")
            return

        course = self.courses[selected_row]
        dialog = EditCourseDialog(course)
        if dialog.exec():
            self.courses[selected_row] = dialog.get_course()
            CourseManager.save_courses(self.courses, self)
            self.update_table()
            self.update_burndown_chart()
            self.update_chart()
            log.info("Kurs bearbeitet: %s", course.name)

    def update_table(self):

        self.courses = CourseManager.sort_courses_by_semester(self.courses)
        self.course_table.setRowCount(len(self.courses))

        total_weighted = sum(course.ects * (course.grade or 0) for course in self.courses if course.grade is not None)
        total_ects = sum(course.ects for course in self.courses if course.grade != 0)
        gpa = round(total_weighted / total_ects, 2) if total_ects else "N/A"

        for row, course in enumerate(self.courses):
            self.course_table.setItem(row, 0, QTableWidgetItem(course.name))
            self.course_table.setItem(row, 1, QTableWidgetItem(str(course.ects)))
            self.course_table.setItem(row, 2,
                                      QTableWidgetItem(str(course.grade) if course.grade != 0 else "N/A"))
            self.course_table.setItem(row, 3, QTableWidgetItem(str(course.target_grade)))
            self.course_table.setItem(row, 4, QTableWidgetItem(str(course.semester)))

    def update_chart(self):

        grades = [course.grade for course in self.courses if course.grade]
        if grades:
            avg_grade = sum(grades) / len(grades)
        else:
            avg_grade = 0

        self.canvas.figure.clear()
        ax = self.canvas.figure.add_subplot(111)
        ax.bar(["Aktuelle Note"], [avg_grade], color='blue', label="Durchschnittsnote")
        ax.axhline(self.config.target_grade, color='red', linestyle='dashed', label="Zielnote")

        ax.set_ylabel("Note")
        ax.legend()
        self.canvas.draw()

    def update_burndown_chart(self):
        target_ects = sum(course.ects for course in self.courses)

        time_periods = list(range(1, self.config.target_time * 2 + 1))

        ects_progress = []
        optimal_progress = []
        average_burn_rate = []


        optimal_progress.append(target_ects)
        ects_progress.append(target_ects)
        average_burn_rate.append(target_ects)


        earned_ects = sum(course.ects for course in self.courses if course.is_completed())
        remaining_ects = target_ects - earned_ects


        total_time = len(time_periods)
        if total_time > 1:
            average_rate = (target_ects - remaining_ects) / (total_time - 1)


        for i in range(1, total_time + 1):

            if i <= len(time_periods):
                ects_progress.append(target_ects - i * (earned_ects / total_time))
                optimal_progress.append(target_ects - (target_ects / total_time) * i)
                average_burn_rate.append(target_ects - i * average_rate)


        self.burndown_canvas.figure.clear()
        ax = self.burndown_canvas.figure.add_subplot(111)

        ax.plot(time_periods, ects_progress[:len(time_periods)], marker='o', linestyle='-', color='blue',
                label="Verbleibende ECTS (tatsächlich)")

        ax.plot(time_periods, optimal_progress[:len(time_periods)], linestyle='dashed', color='red',
                label="Optimale Burndown-Linie")

        ax.plot(time_periods, average_burn_rate[:len(time_periods)], linestyle='-', color='green',
                label="Durchschnittliche Abbrennrate")

        ax.set_xlabel("Semester")
        ax.set_ylabel("Verbleibende ECTS")
        ax.set_title("ECTS Burndown Chart")
        ax.legend()
        self.burndown_canvas.draw()

    def add_course(self):

        dialog = AddCourseDialog()
        if dialog.exec():
            new_course = dialog.get_course()
            self.courses.append(new_course)
            is_saved_successful = CourseManager.save_courses(self.courses, self)
            if not is_saved_successful:
                del self.courses[-1]
            self.update_table()
            self.update_burndown_chart()
            self.update_chart()


def main():
    if not os.path.exists("save/log"):
        os.makedirs("save/log")

    log.basicConfig(filename='save/log/dashboard.log', level=log.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')

    app = QApplication(sys.argv)
    dashboard = Dashboard()
    dashboard.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
