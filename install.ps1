
$VENV_NAME = ".venv"
$REQUIREMENTS_FILE = "requirements.txt"

# Erstellen der virtuellen Umgebung
Write-Host "📦 Erstelle virtuelle Umgebung..."
python -m venv .venv

# Aktivieren der virtuellen Umgebung (Windows)
Write-Host "✅ Aktiviere virtuelle Umgebung..."
$venvActivate = ".venv\Scripts\Activate"

# PowerShell-Skript für die Aktivierung ausführen
& $venvActivate

# Installieren der Abhängigkeiten aus requirements.txt

Write-Host "📦 Installiere Abhängigkeiten aus requirements.txt..."
pip install -r $REQUIREMENTS_FILE

python main.py


