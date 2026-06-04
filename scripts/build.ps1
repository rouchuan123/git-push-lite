$ErrorActionPreference = "Stop"
$env:PYTHONPATH = "src"
python -m PyInstaller --noconfirm --onedir --windowed --name "GitHub HQ" --paths src src\github_hq_app.py
Write-Host "Build output: dist\GitHub HQ\GitHub HQ.exe"
