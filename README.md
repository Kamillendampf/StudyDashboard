# 📌 Anleitung zur Ausführung und Einrichtung des StudyDashboard

Zum Projekt: [GitHub](https://github.com/Kamillendampf/StudyDashboard.git) 

Diese Anleitung beschreibt zwei Methoden zur Nutzung des StudyDashboard:
- **Direkte Ausführung der .exe** (für Endnutzer)
- **Manuelles Setup in einer Entwicklungsumgebung** (für Entwickler)

---

## 🚀 1. Nutzung der ausführbaren Datei
Falls Sie das Dashboard direkt nutzen möchten, ohne eine Entwicklungsumgebung einzurichten, folgen Sie diesen Schritten:

### 🔹 **Schritt 1: Herunterladen**
Laden Sie die neueste Version der Anwendung als ausführbare Datei (`.exe`) von [GitHub](https://github.com/Kamillendampf/StudyDashboard/releases/tag/release) herunter.

### 🔹 **Schritt 2: Ausführen**
- Öffnen Sie den Download-Ordner.
- Führen Sie die Datei `StudyDashboard.exe` durch **Doppelklick** aus.
- Folgen Sie den Anweisungen auf dem Bildschirm.

✅ **Das Dashboard ist nun betriebsbereit!**

---

## 🛠 2. Einrichtung der Entwicklungsumgebung (IDE-Setup)
Falls Sie das Dashboard weiterentwickeln oder anpassen möchten, folgen Sie dieser Anleitung:

### 🔹 **Schritt 1: Git-Repository klonen**
Öffnen Sie eine Kommandozeile oder PowerShell und führen Sie folgenden Befehl aus:

```cmd
 git clone https://github.com/Kamillendampf/StudyDashboard.git
```
Nach dem Klonen wird ein neuer Ordner `StudyDashboard` mit dem Quellcode erstellt.

### 🔹 **Schritt 2: In das Projektverzeichnis wechseln**
```cmd
cd StudyDashboard
```

### 🔹 **Schritt 3: Virtuelle Umgebung einrichten und Abhängigkeiten installieren**
Führen Sie das bereitgestellte PowerShell-Skript aus:

```powershell
powershell -ExecutionPolicy Bypass -File setup.ps1
```

Falls PowerShell-Skripte blockiert sind, können Sie die Ausführung mit folgendem Befehl erlauben:

```powershell
Set-ExecutionPolicy Unrestricted -Scope Process
```

### 🔹 **Schritt 4: Start des Dashboards**
Sobald die Installation abgeschlossen ist, können Sie das Dashboard mit folgendem Befehl starten:

```cmd
python main.py
```

✅ **Das Dashboard läuft nun lokal in Ihrer Entwicklungsumgebung!** 🚀# StudyDashboard
