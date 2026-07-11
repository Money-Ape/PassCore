#define MyAppName "PassCore"
#define MyAppVersion "0.4.4"
#define MyAppPublisher "Lovepreet Singh (Money-Ape)"
#define MyAppURL "https://github.com/Money-Ape/PassCore.git"
#define MyAppExeName "PassCore.exe"

[Setup]
AppId={{4826B2E9-F36C-486B-8C37-04285270C507}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
;AppVerName={#MyAppName} {#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}
DefaultDirName={autopf}\{#MyAppName}
UninstallDisplayIcon={app}\{#MyAppExeName}
; "ArchitecturesAllowed=x64compatible" specifies that Setup cannot run
; on anything but x64 and Windows 11 on Arm.
ArchitecturesAllowed=x64compatible
; "ArchitecturesInstallIn64BitMode=x64compatible" requests that the
; install be done in "64-bit mode" on x64 or Windows 11 on Arm,
; meaning it should use the native 64-bit Program Files directory and
; the 64-bit view of the registry.
ArchitecturesInstallIn64BitMode=x64compatible
DefaultGroupName={#MyAppName}
LicenseFile=D:\DEV\PassCore\packaging\windows\release\LICENSE.txt
InfoBeforeFile=D:\DEV\PassCore\packaging\windows\release\README.txt
InfoAfterFile=D:\DEV\PassCore\packaging\windows\release\INIT.txt
;PrivilegesRequired=lowest
OutputDir=D:\DEV\PassCore\packaging\windows\release
OutputBaseFilename=PassCore-Setup_{#MyAppVersion}
SetupIconFile=D:\DEV\PassCore\assets\PassCore.ico
SolidCompression=yes
WizardStyle=modern dynamic polar

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
Source: "D:\DEV\PassCore\packaging\windows\release\{#MyAppExeName}"; DestDir: "{app}"; Flags: ignoreversion
Source: "D:\DEV\PassCore\packaging\windows\release\LICENSE.txt"; DestDir: "{app}"; Flags: ignoreversion
Source: "D:\DEV\PassCore\packaging\windows\release\README.txt"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{group}\{cm:UninstallProgram,{#MyAppName}}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent
