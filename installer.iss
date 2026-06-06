#define MyAppVersion "1.1"

[Setup]
AppId=PLauncher
AppName=PLauncher
AppVersion={#MyAppVersion}
DisableDirPage=yes
PrivilegesRequired=lowest
DefaultDirName={userappdata}\PLauncher
DefaultGroupName=PLauncher
OutputDir=output
OutputBaseFilename=PLauncher-{#MyAppVersion}-setup
Compression=lzma2
SolidCompression=yes
ArchitecturesInstallIn64BitMode=x64compatible

[Languages]
#expr EmitLanguagesSection

[Files]
Source: "dist\main.dist\*"; DestDir: "{app}"; Flags: recursesubdirs createallsubdirs

[Tasks]
Name: "desktopicon"; Description: "Create desktop icon"

[Icons]
Name: "{autoprograms}\PLauncher"; Filename: "{app}\main.exe"
Name: "{autodesktop}\PLauncher"; Filename: "{app}\main.exe"; Tasks: desktopicon

[Run]
Filename: "{app}\main.exe"; Description: "Launch PLauncher"; Flags: nowait postinstall skipifsilent shellexec