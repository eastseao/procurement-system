/**
 * electron-builder afterPack hook
 * 用 ResourceHacker 命令行工具把多尺寸 ICO 写入主 EXE。
 * ResourceHacker 是成熟的 Windows 资源编辑工具，比 ctypes 调用 API 更稳定。
 */
const path = require('path');
const { execFileSync } = require('child_process');
const fs = require('fs');

module.exports = async function afterPack(context) {
  // 只在 Windows 平台执行
  if (context.electronPlatformName !== 'win32') return;

  const appOutDir = context.appOutDir;      // dist_release/win-unpacked
  const projectDir = context.packager.projectDir;

  // ResourceHacker.exe 路径
  const rhExe = path.join(projectDir, 'build-hooks', 'ResourceHacker', 'ResourceHacker.exe');
  if (!fs.existsSync(rhExe)) {
    console.warn('[afterPack] ResourceHacker.exe 不存在:', rhExe);
    return;
  }

  // 目标 EXE
  const exeName = context.packager.appInfo.productFilename + '.exe';
  const exePath = path.join(appOutDir, exeName);
  if (!fs.existsSync(exePath)) {
    console.warn('[afterPack] EXE 不存在:', exePath);
    return;
  }

  // 正确的多尺寸 ICO
  const icoPath = path.join(projectDir, 'assets', 'icon', 'app-icon-multi.ico');
  if (!fs.existsSync(icoPath)) {
    console.warn('[afterPack] ICO 不存在:', icoPath);
    return;
  }

  console.log('[afterPack] 注入图标:', exePath);
  console.log('[afterPack] ICO:', icoPath);
  console.log('[afterPack] ResourceHacker:', rhExe);

  // 写临时 .rc 文件（ResourceHacker 需要通过 .rc 来添加图标）
  // 使用资源 ID = 1（Windows 主图标标准 ID）
  const rcContent = `#define IDR_MAINICON 1\nIDR_MAINICON ICON "${icoPath.replace(/\\/g, '\\\\')}"\n`;
  const rcPath = path.join(appOutDir, '_icon_temp.rc');
  fs.writeFileSync(rcPath, rcContent, 'utf-8');

  try {
    // 用 ResourceHacker 编译 .rc 并注入到 EXE
    // -open: 输入 EXE
    // -save: 输出 EXE（可同输入）
    // -action compile: 编译 .rc 并合并资源
    // -res: .rc 文件路径
    const output = execFileSync(rhExe, [
      '-open', exePath,
      '-save', exePath,
      '-action', 'compile',
      '-res', rcPath,
    ], {
      stdio: 'pipe',
      encoding: 'utf-8',
      timeout: 30000,
    });
    console.log('[afterPack] ResourceHacker 输出:', output);
    console.log('[afterPack] 图标注入成功 ✓');
  } catch (e) {
    console.error('[afterPack] ResourceHacker 失败:');
    console.error('  stdout:', e.stdout);
    console.error('  stderr:', e.stderr);
    console.error('  message:', e.message);
  } finally {
    // 删除临时 .rc 文件
    try { fs.unlinkSync(rcPath); } catch (e) { /* ignore */ }
  }
};
