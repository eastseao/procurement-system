; NSIS 自定义脚本：修复桌面快捷方式和开始菜单图标
;
; 问题根因：
;   1. customInstall 在快捷方式创建之后执行，清除缓存太晚
;   2. 清除缓存后没有调用 SHChangeNotify 通知 Shell 刷新
;   3. 覆盖安装时 keepShortcuts 机制可能保留旧快捷方式不重建
;
; 解决方案：
;   1. customInit: 安装前（.onInit 阶段）清除图标缓存
;      → 快捷方式创建时 Windows 从新 EXE 提取图标，而非用旧缓存
;   2. customInstall: 安装后重新创建快捷方式 + 清除缓存 + 刷新 Shell
;      → 确保快捷方式图标来自新 EXE，且 Windows 立即刷新显示

; ============================================================
; 安装前：清除图标缓存（在快捷方式创建之前）
; ============================================================
!macro customInit
  ; 删除 IconCache.db（主图标缓存）
  Delete "$LOCALAPPDATA\IconCache.db"
  ; 删除 Explorer 图标缓存数据库
  Delete "$LOCALAPPDATA\Microsoft\Windows\Explorer\iconcache_16.db"
  Delete "$LOCALAPPDATA\Microsoft\Windows\Explorer\iconcache_32.db"
  Delete "$LOCALAPPDATA\Microsoft\Windows\Explorer\iconcache_48.db"
  Delete "$LOCALAPPDATA\Microsoft\Windows\Explorer\iconcache_96.db"
  Delete "$LOCALAPPDATA\Microsoft\Windows\Explorer\iconcache_256.db"
  Delete "$LOCALAPPDATA\Microsoft\Windows\Explorer\iconcache_768.db"
  Delete "$LOCALAPPDATA\Microsoft\Windows\Explorer\iconcache_1280.db"
  Delete "$LOCALAPPDATA\Microsoft\Windows\Explorer\iconcache_1920.db"
  Delete "$LOCALAPPDATA\Microsoft\Windows\Explorer\iconcache_2560.db"
  Delete "$LOCALAPPDATA\Microsoft\Windows\Explorer\iconcache_idx.db"
  Delete "$LOCALAPPDATA\Microsoft\Windows\Explorer\iconcache_sr.db"
  Delete "$LOCALAPPDATA\Microsoft\Windows\Explorer\iconcache_wide.db"
  Delete "$LOCALAPPDATA\Microsoft\Windows\Explorer\iconcache_wide_alternate.db"
  Delete "$LOCALAPPDATA\Microsoft\Windows\Explorer\iconcache_custom_stream.db"
  Delete "$LOCALAPPDATA\Microsoft\Windows\Explorer\iconcache_exif.db"
!macroend

; ============================================================
; 安装后：重新创建快捷方式 + 清除缓存 + 刷新 Shell
; ============================================================
!macro customInstall
  ; --- 重新创建桌面快捷方式（确保图标从新 EXE 提取）---
  ; 仅在用户未禁用桌面快捷方式时执行
  ${ifNot} ${isNoDesktopShortcut}
    ${if} ${FileExists} "$newDesktopLink"
      Delete "$newDesktopLink"
    ${endif}
    CreateShortCut "$newDesktopLink" "$appExe" "" "$appExe" 0 "" "" "${APP_DESCRIPTION}"
    ClearErrors
  ${endIf}

  ; --- 重新创建开始菜单快捷方式 ---
  ${if} ${FileExists} "$newStartMenuLink"
    Delete "$newStartMenuLink"
  ${endif}
  CreateShortCut "$newStartMenuLink" "$appExe" "" "$appExe" 0 "" "" "${APP_DESCRIPTION}"
  ClearErrors

  ; --- 再次清除图标缓存（快捷方式创建后可能产生新缓存）---
  Delete "$LOCALAPPDATA\IconCache.db"
  Delete "$LOCALAPPDATA\Microsoft\Windows\Explorer\iconcache_16.db"
  Delete "$LOCALAPPDATA\Microsoft\Windows\Explorer\iconcache_32.db"
  Delete "$LOCALAPPDATA\Microsoft\Windows\Explorer\iconcache_48.db"
  Delete "$LOCALAPPDATA\Microsoft\Windows\Explorer\iconcache_96.db"
  Delete "$LOCALAPPDATA\Microsoft\Windows\Explorer\iconcache_256.db"
  Delete "$LOCALAPPDATA\Microsoft\Windows\Explorer\iconcache_768.db"
  Delete "$LOCALAPPDATA\Microsoft\Windows\Explorer\iconcache_1280.db"
  Delete "$LOCALAPPDATA\Microsoft\Windows\Explorer\iconcache_1920.db"
  Delete "$LOCALAPPDATA\Microsoft\Windows\Explorer\iconcache_2560.db"
  Delete "$LOCALAPPDATA\Microsoft\Windows\Explorer\iconcache_idx.db"
  Delete "$LOCALAPPDATA\Microsoft\Windows\Explorer\iconcache_sr.db"
  Delete "$LOCALAPPDATA\Microsoft\Windows\Explorer\iconcache_wide.db"
  Delete "$LOCALAPPDATA\Microsoft\Windows\Explorer\iconcache_wide_alternate.db"
  Delete "$LOCALAPPDATA\Microsoft\Windows\Explorer\iconcache_custom_stream.db"
  Delete "$LOCALAPPDATA\Microsoft\Windows\Explorer\iconcache_exif.db"

  ; --- 通知 Shell 刷新图标（关键！没有这步 Windows 不会重新读取图标）---
  System::Call 'shell32::SHChangeNotify(i 0x8000000, i 0, i 0, i 0)'
!macroend
