[Setup]
AppName=FriskoOCR
AppVersion=1.0
DefaultDirName={pf}\FriskoOCR
DefaultGroupName=FriskoOCR
OutputDir=Output
OutputBaseFilename=FriskoOCR_Setup
UninstallDisplayIcon={app}\launcher.exe
PrivilegesRequired=admin
AllowNoIcons=yes

[Files]
; Protected application files from dist folder
Source: "dist\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
; PyArmor runtime files
Source: "dist\pytransform\*"; DestDir: "{app}\pytransform"; Flags: ignoreversion recursesubdirs createallsubdirs
; Create logs directory
Source: "*"; DestDir: "{app}\logs"; Flags: ignoreversion recursesubdirs createallsubdirs; Permissions: users-modify

[Dirs]
; Ensure these directories are writable by users
Name: "{app}\logs"; Permissions: users-modify
Name: "{app}\friskocr"; Permissions: users-modify
Name: "{app}\pytransform"; Permissions: users-modify

[Icons]
Name: "{group}\FriskoOCR"; Filename: "{app}\launcher.exe"
Name: "{commondesktop}\FriskoOCR"; Filename: "{app}\launcher.exe"
Name: "{group}\Uninstall FriskoOCR"; Filename: "{uninstallexe}"

[Registry]
Root: HKLM; Subkey: "SYSTEM\CurrentControlSet\Control\Session Manager\Environment"; ValueType: expandsz; ValueName: "Path"; ValueData: "{olddata};{app}\friskocr\Scripts"; Check: NeedsAddPath('{app}\friskocr\Scripts')

[Run]
Filename: "{app}\launcher.exe"; Description: "Launch FriskoOCR"; Flags: postinstall nowait

[Code]
function InitializeSetup(): Boolean;
begin
  Result := True;
  
  if not RegKeyExists(HKEY_LOCAL_MACHINE, 'SOFTWARE\Python\PythonCore') and
     not RegKeyExists(HKEY_CURRENT_USER, 'SOFTWARE\Python\PythonCore') then
  begin
    MsgBox('Python is required but not found. Please install Python before continuing.', mbError, MB_OK);
    Result := False;
  end;
end;

function NeedsAddPath(Path: string): Boolean;
var
  OrigPath: string;
begin
  if not RegQueryStringValue(HKEY_LOCAL_MACHINE,
    'SYSTEM\CurrentControlSet\Control\Session Manager\Environment',
    'Path', OrigPath)
  then begin
    Result := True;
    exit;
  end;
  Result := Pos(';' + Uppercase(Path) + ';', ';' + Uppercase(OrigPath) + ';') = 0;
end;

[UninstallDelete]
Type: filesandordirs; Name: "{app}\logs"
Type: filesandordirs; Name: "{app}\friskocr"
Type: filesandordirs; Name: "{app}\pytransform" 