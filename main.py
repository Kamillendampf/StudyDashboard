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
    """
    Die Klasse StudyConfig verwaltet die Konfigurationsdaten für das Studium,
    einschließlich der Zielstudienzeit und der Zielnote.

    Die Konfiguration wird in einer JSON-Datei gespeichert und geladen.
    Falls keine Konfigurationsdatei existiert, wird der Benutzer aufgefordert,
    die Daten einzugeben.
    """
    CONFIG_FILE = "save/config.json"

    def __init__(self):
        """
        Initialisiert die StudyConfig-Klasse mit Standardwerten und lädt die Konfiguration.
        """
        self.target_time = 0
        self.target_grade = 0.0
        self.load_config()

    def load_config(self):
        """
        Lädt die Konfiguration aus der JSON-Datei.
        Falls die Datei nicht existiert oder fehlerhaft ist, wird eine Benutzerabfrage gestartet.

        Falls die Datei vorhanden ist, werden die Werte für Ziel-Studienzeit und Zielnote ausgelesen.
        """
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
        """
        Fordert den Benutzer auf, neue Konfigurationswerte einzugeben.
        Verwendet ein Dialogfenster (ConfigDialog), um die Werte zu erfassen.
        Die neuen Werte werden anschließend gespeichert.
        """
        dialog = ConfigDialog()
        if dialog.exec():
            self.target_time = dialog.target_time_input.value()
            self.target_grade = dialog.target_grade_input.value()
            self.save_config()

    def save_config(self):
        """
        Speichert die aktuellen Konfigurationswerte (Zielzeit und Zielnote) in die JSON-Datei.
        Falls die Datei nicht existiert, wird sie erstellt.

        Ein Log-Eintrag wird geschrieben, um den erfolgreichen Speichervorgang zu dokumentieren.
        """
        with open(self.CONFIG_FILE, "w") as file:
            json.dump({
                "target_time": self.target_time,
                "target_grade": self.target_grade
            }, file)
            log.info("Konfiguration gespeichert: %d Jahre, Zielnote %.2f", self.target_time,
                     self.target_grade)


class ConfigDialog(QDialog):
    """
    Ein Dialogfenster zur Erstkonfiguration der Studienziele.

    Der Benutzer kann hier die gewünschte Studienzeit (in Semestern)
    und die angestrebte Abschlussnote eingeben. Die Werte werden nach
    Bestätigung des Dialogs gespeichert.
    """

    def __init__(self):
        """
        Initialisiert das Konfigurationsdialogfenster mit Eingabefeldern
        für die Zielzeit (in Semestern) und die Zielnote.
        """
        super().__init__()
        self.setWindowTitle("Erstkonfiguration")
        layout = QVBoxLayout()
        # Eingabefeld für die Zielzeit (Anzahl der Semester)
        self.target_time_input = QSpinBox(self)
        self.target_time_input.setRange(1, 10)  # Semesterbereich von 1 bis 10
        layout.addWidget(QLabel("Zielzeit in Semestern:"))
        layout.addWidget(self.target_time_input)

        # Eingabefeld für die Zielnote
        self.target_grade_input = QDoubleSpinBox(self)
        self.target_grade_input.setRange(1.0, 5.0)  # Notenskala von 1.0 (beste) bis 5.0 (schlechteste)
        self.target_grade_input.setSingleStep(0.1)  # Schrittweite 0.1 für präzise Eingabe
        layout.addWidget(QLabel("Zielnote:"))
        layout.addWidget(self.target_grade_input)

        # Speichern-Button, der den Dialog schließt und die Eingaben bestätigt
        self.save_button = QPushButton("Speichern", self)
        self.save_button.clicked.connect(self.accept)  # Verbindet den Button mit der accept()-Method
        layout.addWidget(self.save_button)

        self.setLayout(layout)


class Course:
    """
    Repräsentiert einen Kurs innerhalb eines Studienprogramms.

    Ein Kurs enthält Informationen wie den Namen, die Anzahl der ECTS-Punkte,
    die erreichte Note, die angestrebte Note und das Semester, in dem er fällig ist.
    """

    def __init__(self, name, ects, grade, target_grade, semester):
        """
        Initialisiert ein neues Kursobjekt.

        Args:
            name (str): Der Name des Kurses.
            ects (int): Die Anzahl der ECTS-Punkte des Kurses.
            grade (float or None): Die erreichte Note (falls bereits bewertet).
            target_grade (float): Die angestrebte Zielnote.
            semester (int): Das Semester, in dem der Kurs absolviert.
        """
        self.name = name
        if ects != 0:  # ECTS sollte nicht null sein, daher eine Sicherheitsprüfung
            self.ects = ects
        self.grade = grade  # Die tatsächlich erreichte Note (None, falls noch nicht bewertet)
        self.target_grade = target_grade  # Die angestrebte Zielnote für den Kurs
        self.semester = semester  # Das Semester, in dem der Kurs absolviert wird

    def is_completed(self):
        """
        Überprüft, ob der Kurs bestanden wurde. Erst ab der Note 4 aufwärts wird der Kurs als bestanden bewertet.

        Returns:
            bool: True, wenn der Kurs eine gültige Note (1-4) hat, andernfalls False.
        """
        return self.grade is not None and 1 <= self.grade <= 4

    def to_dict(self):
        """
        Wandelt das Kursobjekt in ein Dictionary um, das zur Speicherung oder Serialisierung verwendet werden kann.

        Returns:
            dict: Ein Wörterbuch mit den Kursinformationen.
        """
        return {"name": self.name, "ects": self.ects, "grade": self.grade, "target_grade": self.target_grade,
                "semester": self.semester}

    @staticmethod
    def from_dict(data):
        """
        Erstellt ein `Course`-Objekt aus einem Dictionary.

        Args:
            data (dict): Ein Dictionary mit den Schlüsselwerten für einen Kurs.

        Returns:
            Course: Ein neues Kursobjekt mit den Werten aus dem Dictionary.
        """
        return Course(data["name"], data["ects"], data["grade"], data["target_grade"], data["semester"])


class CourseManager:
    """
    Die Klasse `CourseManager` verwaltet eine Sammlung von Kursen.

    Sie ermöglicht das Speichern von Kurzen in einer JSON-Datei, Laden von Kurzen aus
    einer JSON-Datei und Sortieren von Kursen.
    """
    FILE_PATH = "save/courses.json"

    @staticmethod
    def save_courses(courses, parent=None):
        """
        Speichert die übergebenen Kurse in einer JSON-Datei.

        Doppelte Kurse werden entfernt, basierend auf ihrem Namen. Falls doppelte Kurse
        erkannt werden, wird eine Warnung angezeigt.

        Args:
            courses (list of Course): Eine Liste von `Course`-Objekten.
            parent (QWidget, optional): Ein optionales Eltern-Widget für Meldungsfenster.

        Returns:
            bool: True, wenn die Kurse erfolgreich gespeichert wurden, andernfalls False.
        """

        # Erstelle ein Dictionary, um doppelte Kurse anhand des Namens zu eliminieren
        existing_courses = {course.name: course for course in courses}

        # Überprüfung, ob doppelte Kurse entfernt wurden
        if len(existing_courses) < len(courses):
            log.info("Doppelte Kurse wurden entfernt.")
            QMessageBox.warning(parent, "Der Kurs existiert bereits", "Einige doppelte Kurse wurden entfernt.")
            return False  # Speichern wird nicht durchgeführt, weil doppelte Einträge existierten

        # Speichern der Kursdaten in die JSON-Datei
        with open(CourseManager.FILE_PATH, "w") as file:
            json.dump([course.to_dict() for course in existing_courses.values()], file)
            return True
            log.info(" Neuer Kurs wurde angelegt")

    @staticmethod
    def load_courses():
        """
        Lädt gespeicherte Kurse aus der JSON-Datei.

        Falls die Datei nicht existiert oder fehlerhaft ist, wird eine leere Datei erstellt.

        Returns:
            list of Course: Eine Liste der geladenen `Course`-Objekte.
        """
        try:
            # Aufruf und auslesen aus der Kursdatei
            with open(CourseManager.FILE_PATH, "r") as file:
                courses = [Course.from_dict(data) for data in json.load(file)]
                log.info("%d Kurse erfolgreich geladen.", len(courses))
                return courses

        except (FileNotFoundError, json.JSONDecodeError):
            log.info("Kursdatei nicht gefunden - wird erstellt.")

            # Erstelle eine neue leere Datei
            with open(CourseManager.FILE_PATH, "w") as file:
                json.dump("", file)
                log.info("Kursdatei wurde erstellt.")
            return []

    @staticmethod
    def sort_courses_by_semester(courses):
        """
        Sortiert eine Liste von Kursen basierend auf dem Semester.

        Args:
            courses (list of Course): Eine Liste von `Course`-Objekten.

        Returns:
            list of Course: Eine nach Semestern sortierte Liste von Kursen.
        """
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
    """
    Ein Dialogfenster zum Hinzufügen eines neuen Kurses.

    Der Benutzer kann den Namen, die ECTS-Punkte, die Zielnote und das Semester angeben.
    Der Dialog übernimmt außerdem die maximale Semesteranzahl aus der `StudyConfig`.
    """

    def __init__(self, course):
        """
        Initialisiert den Dialog zur Eingabe eines neuen Kurses.
        Erstellt die notwendigen Eingabefelder und einen "Hinzufügen"-Button.
        """
        super().__init__()

        # Lade die Studienkonfiguration (z. B. maximale Studienzeit)
        self.config = StudyConfig()

        self.setWindowTitle("Modul bearbeiten")
        self.layout = QVBoxLayout()
        # Eingabefeld für den Kursnamen
        self.name_input = QLineEdit()

        # Eingabefeld für die ECTS-Punkte
        self.ects_input = QSpinBox()
        self.ects_input.setRange(1, 5)  # ECTS-Punkte müssen zwischen 1 und 5 liegen

        # Eingabefeld für die Endnote
        self.grade_input = QDoubleSpinBox()
        self.grade_input.setRange(0.0, 5.0)  # Notenskala von 1.0 (beste) bis 5.0 (schlechteste)

        # Eingabefeld für die Zielnote
        self.target_grade_input = QDoubleSpinBox()
        self.target_grade_input.setRange(1.0, 5.0)  # Notenskala von 1.0 (beste) bis 5.0 (schlechteste)

        # Eingabefeld für das Semester, in dem der Kurs belegt wird
        self.semester_input = QSpinBox()
        self.semester_input.setRange(1,
                                     self.config.target_time * 2)  # Die maximale Semesterzahl ist doppelt so hoch wie die Studienzeit in Jahren

        if course:
            self.name_input.setText(course.name)
            self.ects_input.setValue(course.ects)
            if course.grade:
                self.grade_input.setValue(course.grade)
            self.target_grade_input.setValue(course.target_grade)
            self.semester_input.setValue(course.semester)

        # Zu weisen der einzelnen input felder zu dem widget
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

        # "Hinzufügen"-Button, der den Dialog bestätigt
        self.save_button = QPushButton("Speichern")
        self.save_button.clicked.connect(self.accept) # Akzeptiert den Dialog
        self.layout.addWidget(self.save_button)

        self.setLayout(self.layout)

    def get_course(self):
        """
        Erstellt ein `Course`-Objekt aus den eingegebenen Daten.

        Returns:
            Course: Ein `Course`-Objekt mit den eingegebenen Werten.
        """
        return Course(
            self.name_input.text(),
            self.ects_input.value(),
            self.grade_input.value(),
            self.target_grade_input.value(),
            self.semester_input.value()
        )


class Dashboard(QWidget):
    """
    Das `Dashboard`-Widget dient als Hauptansicht zur Verwaltung der Studienmodule.

    Es zeigt Informationen zur Zielstudienzeit, Zielsemesteranzahl und Zielnote an.
    Zudem werden Kurse in einer Tabelle dargestellt und verschiedene Statistiken
    in Diagrammen visualisiert.
    """
    def __init__(self):
        """
        Initialisiert das Dashboard.

        Lädt die gespeicherten Kurse und die Konfiguration und rendert die Benutzeroberfläche.
        """
        super().__init__()
        self.config = StudyConfig() # Lade die Studienkonfiguration
        self.courses = CourseManager.load_courses() # Lade die gespeicherten Kurse
        self.render() # Erstelle die Benutzeroberfläche


    def render(self):
        """
        Erstellt und setzt das Layout des Dashboards.

        Hier werden das Fenster, die Tabellenansicht, Buttons und Diagramme initialisiert.
        """

        # Setzt das Fenster auf die Bildschirmgröße
        self.setGeometry(0, 0, GetSystemMetrics(0), GetSystemMetrics(1))

        self.setWindowTitle("ECTS & Abschlussnote Dashboard")

        main_layout = QVBoxLayout()
        info_layout = QVBoxLayout()
        content_layout = QHBoxLayout()

        # Anzeige der Konfigurationswerte
        info_layout.addWidget(QLabel(f"Zielzeit: {self.config.target_time} Jahre"))
        info_layout.addWidget(QLabel(f"Zielsemester: {self.config.target_time * 2} Semeseter"))
        info_layout.addWidget(QLabel(f"Zielnote: {self.config.target_grade}"))

        # Buttons für Kursverwaltung
        self.add_course_button = QPushButton("Modul hinzufügen")
        self.add_course_button.clicked.connect(self.add_course)
        info_layout.addWidget(self.add_course_button)

        self.edit_course_button = QPushButton("Modul bearbeiten")
        self.edit_course_button.clicked.connect(self.edit_course)
        info_layout.addWidget(self.edit_course_button)

        # Tabelle zur Anzeige der Kurse
        self.course_table = QTableWidget()
        self.course_table.setColumnCount(5)
        self.course_table.setHorizontalHeaderLabels(["Name", "ECTS", "Note", "Zielnote", "Semester"])
        content_layout.addWidget(self.course_table)

        # Diagramm für Notenübersicht
        self.canvas = FigureCanvas(plt.figure())
        content_layout.addWidget(self.canvas)

        # Burndown-Diagramm für ECTS-Fortschritt
        self.burndown_canvas = FigureCanvas(plt.figure())
        content_layout.addWidget(self.burndown_canvas)

        main_layout.addLayout(info_layout)
        main_layout.addLayout(content_layout)
        self.setLayout(main_layout)

        # Initialisiere Diagramme und Tabelle
        self.update_chart()
        self.update_burndown_chart()
        self.update_table()

    def edit_course(self):
        """
          Öffnet einen Dialog zum Bearbeiten eines ausgewählten Kurses.

          Falls kein Kurs ausgewählt wurde, erscheint eine Warnmeldung.
          """
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
        """
        Aktualisiert die Tabelle mit den gespeicherten Kursen.

        Berechnet außerdem die Durchschnittsnote (GPA) der abgeschlossenen Kurse.
        """
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
        """
        Erstellt ein Balkendiagramm, das die aktuelle Durchschnittsnote mit der Zielnote vergleicht.
        """
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
        """
        Erstellt ein Burndown-Chart, das den verbleibenden ECTS-Fortschritt darstellt.
        """
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
        """
        Öffnet den `AddCourseDialog`, um einen neuen Kurs hinzuzufügen.
        """
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
    """
    Startet die Dashboard-Anwendung.

    - Erstellt das erforderliche Log-Verzeichnis, falls es nicht existiert.
    - Initialisiert das Logging-System zur Fehler- und Ereignisprotokollierung.
    - Startet die PyQt6-Anwendung und zeigt das Dashboard-Fenster an.
    """
    # Prüfe, ob das Log-Verzeichnis existiert, und erstelle es falls notwendig
    if not os.path.exists("save/log"):
        os.makedirs("save/log")

    # Initialisiere das Logging-System
    log.basicConfig(filename='save/log/dashboard.log', level=log.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')

    # Erstelle die PyQt6-Anwendung
    app = QApplication(sys.argv)
    # Initialisiere und zeige das Dashboard
    dashboard = Dashboard()
    dashboard.show()
    # Starte die Ereignisschleife der Anwendung
    sys.exit(app.exec())

# Überprüft, ob das Skript direkt ausgeführt wird
if __name__ == "__main__":
    main()