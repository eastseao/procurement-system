; 采购管理系统 - 安装脚本
; Inno Setup 6

#define MyAppName "采购助手"
#define MyAppNameEn "ProcurementAssistant"
#define MyAppExeName "采购助手.exe"
#define MyAppVersion "2.3.4"
#define MyAppPublisher "同仁堂健康药业"
#define SourcePath "I:\采购管理系统\采购管理系统V2.3.2\dist"
#define AssetsPath "I:\采购管理系统\采购管理系统V2.3.2\assets"

[Setup]
AppId={{A1B2C3D4-E5F6-7890-ABCD-EF1234567890}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppVerName={#MyAppName} V{#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirname={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
AllowNoIcons=yes
; 英文名安装包
OutputBaseFilename={#MyAppNameEn}_V{#MyAppVersion}_Setup
SetupIconFile=I:\采购管理系统\采购管理系统V2.3.2\assets\同仁堂logo\同仁堂企业LOGO_×256.ico
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=lowest
OutputDir=I:\采购管理系统\安装包

[Languages]
Name: "default"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "创建桌面快捷方式"; GroupDescription: "附加快捷方式:"; Flags: checkedonce

[Files]
Source: "{#SourcePath}\{#MyAppExeName}"; DestDir: "{app}"; Flags: ignoreversion

; ── 模板文件 ──
Source: "{#AssetsPath}\contract_template.docx"; DestDir: "{app}\templates"; Flags: ignoreversion
Source: "{#AssetsPath}\产品包装报价单_模板.xlsx"; DestDir: "{app}\templates"; Flags: ignoreversion
Source: "{#AssetsPath}\比价表模板.xlsx"; DestDir: "{app}\templates"; Flags: ignoreversion
Source: "{#AssetsPath}\物料查询导入模板.csv"; DestDir: "{app}\templates"; Flags: ignoreversion

; ── Logo 图标 ──
Source: "{#AssetsPath}\同仁堂logo\同仁堂企业LOGO_×256.ico"; DestDir: "{app}\assets\同仁堂logo"; Flags: ignoreversion

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{group}\卸载 {#MyAppName}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "启动 {#MyAppName}"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
Type: filesandordirs; Name: "{app}"

[Code]
function InitializeSetup(): Boolean;
begin
  Result := True;
end;

procedure CurStepChanged(CurStep: TSetupStep);
begin
  if CurStep = ssPostInstall then begin
    // 安装完成后可执行额外操作
  end;
end;
