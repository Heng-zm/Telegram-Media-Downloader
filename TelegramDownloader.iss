; Telegram Media Downloader - Inno Setup script
; Requires: build your app with PyInstaller (one-folder) into dist\app_pyqt6\

#define MyAppName "Telegram Media Downloader"
#define MyAppVersion "2.5.3"
#define MyAppPublisher "Ozo.Designer"
#define MyAppURL "https://link.payway.com.kh/ABAPAYm0348597m"
; Prefer new PyInstaller output name if present; otherwise fall back to legacy app_pyqt6
#ifexist "dist\\Telegram Media Downloader\\Telegram Media Downloader.exe"
  #define MyAppExeName "Telegram Media Downloader.exe"
  #define MyAppDistDir "dist\\Telegram Media Downloader"
#else
  #define MyAppExeName "app_pyqt6.exe"
  #define MyAppDistDir "dist\\app_pyqt6"
#endif

[Setup]
AppId={{9AEBE4F5-7F64-4C66-B9F1-1A6E9E3B1A2D}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
OutputDir=E:\output
OutputBaseFilename=TelegramMediaDownloader-Setup
Compression=lzma
SolidCompression=yes
DisableDirPage=no
PrivilegesRequired=lowest
ArchitecturesInstallIn64BitMode=x64
; File version metadata
VersionInfoVersion=2.5.3.0
VersionInfoProductVersion=2.5.3
VersionInfoProductName={#MyAppName}
VersionInfoCompany={#MyAppPublisher}
VersionInfoDescription={#MyAppName} Setup
VersionInfoCopyright=Copyright © 2025 OZO. DESIGNER. All rights reserved.
AppCopyright=Copyright © 2025 OZO. DESIGNER. All rights reserved.
; If you provide an icon file next to this script, it will be used for the installer icon
#ifexist "app.ico"
  #define SetupIco "app.ico"
#else
  #ifexist "icon.ico"
    #define SetupIco "icon.ico"
  #else
    #ifexist "telegram.ico"
      #define SetupIco "telegram.ico"
    #endif
  #endif
#endif
#ifdef SetupIco
SetupIconFile={#SetupIco}
#endif
UninstallDisplayIcon={app}\{#MyAppExeName}

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "Create a &desktop icon"; GroupDescription: "Additional icons:"; Flags: unchecked

[Files]
; Main executable and all dependency files from PyInstaller one-folder build
Source: "{#MyAppDistDir}\{#MyAppExeName}"; DestDir: "{app}"; Flags: ignoreversion
Source: "{#MyAppDistDir}\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
; Optional icon file if not embedded in the exe (installed with the app)
#ifexist "app.ico"
Source: "app.ico"; DestDir: "{app}"; Flags: ignoreversion
#else
  #ifexist "icon.ico"
  Source: "icon.ico"; DestDir: "{app}"; Flags: ignoreversion
  #else
    #ifexist "telegram.ico"
    Source: "telegram.ico"; DestDir: "{app}"; Flags: ignoreversion
    #endif
  #endif
#endif

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{group}\Uninstall {#MyAppName}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "Launch {#MyAppName}"; Flags: nowait postinstall skipifsilent
