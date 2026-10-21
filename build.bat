@echo off
rem 1) exe yig'ish  2) installer yig'ish (Inno Setup kerak)
python -m PyInstaller --noconfirm --clean --windowed --name PyIDLE --add-data "themes;themes" main.py || exit /b 1
set ISCC=%LOCALAPPDATA%\Programs\Inno Setup 6\ISCC.exe
if not exist "%ISCC%" set ISCC=%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe
"%ISCC%" installer\PyIDLE.iss
