[Setup]
AppName=PyIDLE
AppVersion=0.1.0
DefaultDirName={autopf}\PyIDLE
DefaultGroupName=PyIDLE
OutputDir=..\dist
OutputBaseFilename=PyIDLE-Setup
Compression=lzma2
SolidCompression=yes
PrivilegesRequired=lowest
ArchitecturesInstallIn64BitMode=x64compatible
UninstallDisplayIcon={app}\PyIDLE.exe

[Files]
Source: "..\dist\PyIDLE\*"; DestDir: "{app}"; Flags: recursesubdirs ignoreversion

[Icons]
Name: "{group}\PyIDLE"; Filename: "{app}\PyIDLE.exe"
Name: "{autodesktop}\PyIDLE"; Filename: "{app}\PyIDLE.exe"; Tasks: desktopicon

[Tasks]
Name: "desktopicon"; Description: "Desktop yorlig'i yaratish"; Flags: unchecked

[Run]
Filename: "{app}\PyIDLE.exe"; Description: "PyIDLE'ni ishga tushirish"; Flags: nowait postinstall skipifsilent
