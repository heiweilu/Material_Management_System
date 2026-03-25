<#
.SYNOPSIS
    物料管理系统 · 一键打包脚本
.DESCRIPTION
    使用 PyArmor 加密源码后，通过 PyInstaller 打包为 Windows 可执行文件。
    打包产物位于 dist/ 目录，可选生成 ZIP 压缩包便于分发。
.EXAMPLE
    .\build.ps1                  # 普通打包（含 PyArmor 加密）
    .\build.ps1 -NoEncrypt       # 跳过 PyArmor 加密
    .\build.ps1 -Clean           # 清理后重新打包
    .\build.ps1 -Debug           # 保留控制台窗口（调试用）
    .\build.ps1 -NoZip           # 不生成 ZIP
#>

param(
    [string] $Version    = "",
    [switch] $Clean      = $false,
    [switch] $NoZip      = $false,
    [switch] $NoEncrypt  = $false,
    [switch] $Debug      = $false
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$ProjectRoot = $PSScriptRoot
$VenvPython  = Join-Path $ProjectRoot ".venv\Scripts\python.exe"
$VenvPip     = Join-Path $ProjectRoot ".venv\Scripts\pip.exe"
$SpecFile    = Join-Path $ProjectRoot "MMS.spec"
$DistDir     = Join-Path $ProjectRoot "dist"
$BuildDir    = Join-Path $ProjectRoot "build"
$AppName     = "物料管理系统"

# ── 颜色辅助 ─────────────────────────────────────────────────────────
function Write-Step  { param($msg) Write-Host "`n▶ $msg" -ForegroundColor Cyan  }
function Write-OK    { param($msg) Write-Host "  ✓ $msg" -ForegroundColor Green }
function Write-Warn  { param($msg) Write-Host "  ⚠ $msg" -ForegroundColor Yellow }
function Write-Fail  { param($msg) Write-Host "  ✗ $msg" -ForegroundColor Red; exit 1 }

# ── 0. 确认虚拟环境 ─────────────────────────────────────────────────
Write-Step "检查 Python 虚拟环境"
if (-not (Test-Path $VenvPython)) {
    Write-Fail "找不到虚拟环境 Python：$VenvPython`n请先运行 python -m venv .venv && .\.venv\Scripts\Activate.ps1 && pip install -r requirements.txt"
}
$pyVersion = & $VenvPython --version 2>&1
Write-OK "Python: $pyVersion"

# ── 1. 确保 PyInstaller 已安装 ───────────────────────────────────────
Write-Step "检查 PyInstaller"
$piVersion = & $VenvPython -m PyInstaller --version 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Warn "PyInstaller 未安装，正在安装…"
    & $VenvPip install pyinstaller --quiet
    if ($LASTEXITCODE -ne 0) { Write-Fail "PyInstaller 安装失败" }
    $piVersion = & $VenvPython -m PyInstaller --version 2>&1
}
Write-OK "PyInstaller: $piVersion"

# ── 2. 确保 PyArmor 已安装（可选） ──────────────────────────────────
if (-not $NoEncrypt) {
    Write-Step "检查 PyArmor"
    $PyArmorExe = Join-Path $ProjectRoot ".venv\Scripts\pyarmor.exe"
    if (-not (Test-Path $PyArmorExe)) {
        Write-Warn "PyArmor 未安装，正在安装…"
        & $VenvPip install pyarmor --quiet
        if ($LASTEXITCODE -ne 0) { Write-Fail "PyArmor 安装失败" }
    }
    $paVersion = & $PyArmorExe --version 2>&1 | Select-String "Pyarmor" | Select-Object -First 1
    Write-OK "PyArmor: $paVersion"
}

# ── 3. 读取版本号 ────────────────────────────────────────────────────
Write-Step "读取版本号"
if (-not $Version) {
    $appPy = Join-Path $ProjectRoot "src\app.py"
    if (Test-Path $appPy) {
        $match = Select-String -Path $appPy -Pattern 'setApplicationVersion\("([^"]+)"\)' | Select-Object -First 1
        if ($match) {
            $Version = $match.Matches[0].Groups[1].Value
        }
    }
}
if (-not $Version) { $Version = (Get-Date -Format "yyyy.MM.dd") }
Write-OK "版本号: $Version"

# ── 4. 清理 ──────────────────────────────────────────────────────────
if ($Clean) {
    Write-Step "清理旧产物"
    foreach ($dir in @($BuildDir, (Join-Path $DistDir $AppName))) {
        if (Test-Path $dir) {
            Remove-Item $dir -Recurse -Force
            Write-OK "已删除 $dir"
        }
    }
}

# ── 5. PyArmor 加密（可选） ────────────────────────────────────────────
$actualSpec = $SpecFile
if (-not $NoEncrypt) {
    Write-Step "PyArmor 源码加密"
    $encryptDir = Join-Path $ProjectRoot ".pyarmor_dist"
    if (Test-Path $encryptDir) { Remove-Item $encryptDir -Recurse -Force }

    Set-Location $ProjectRoot
    & $PyArmorExe gen `
        --output $encryptDir `
        --recursive `
        --exclude ".venv" `
        --exclude "tests" `
        --exclude "build" `
        --exclude "dist" `
        --exclude "data" `
        "src"
    if ($LASTEXITCODE -ne 0) { Write-Fail "PyArmor 加密失败" }

    # 将加密后的 src/ 覆盖到临时打包目录
    $tempBuildSrc = Join-Path $ProjectRoot ".build_staging"
    if (Test-Path $tempBuildSrc) { Remove-Item $tempBuildSrc -Recurse -Force }
    New-Item -ItemType Directory -Path $tempBuildSrc -Force | Out-Null

    # 复制项目结构
    Copy-Item (Join-Path $ProjectRoot "main.py") $tempBuildSrc
    Copy-Item (Join-Path $ProjectRoot "config.example.yaml") $tempBuildSrc
    Copy-Item (Join-Path $encryptDir "src") (Join-Path $tempBuildSrc "src") -Recurse
    # 确保 theme 文件存在
    $themeDst = Join-Path $tempBuildSrc "src\ui\theme"
    if (-not (Test-Path $themeDst)) { New-Item -ItemType Directory -Path $themeDst -Force | Out-Null }
    Copy-Item (Join-Path $ProjectRoot "src\ui\theme\*.qss") $themeDst -Force

    # 创建临时 spec 指向加密目录
    $specContent = Get-Content $SpecFile -Raw
    $specContent = $specContent -replace [regex]::Escape("Path(SPECPATH)"), "Path(r'$tempBuildSrc')"
    $tempSpec = Join-Path $ProjectRoot "MMS_encrypted.spec"
    $specContent | Set-Content $tempSpec -Encoding UTF8
    $actualSpec = $tempSpec

    Write-OK "源码加密完成"
}

# ── 6. 调试模式 ──────────────────────────────────────────────────────
$specContent = Get-Content $actualSpec -Raw
if ($Debug -and $specContent -match "console=False") {
    $tempSpec2 = Join-Path $ProjectRoot "MMS_debug.spec"
    $specContent -replace "console=False", "console=True" | Set-Content $tempSpec2 -Encoding UTF8
    $actualSpec = $tempSpec2
    Write-Warn "已启用调试控制台"
}

# ── 7. 执行 PyInstaller ─────────────────────────────────────────────
Write-Step "开始打包 (PyInstaller)"
Set-Location $ProjectRoot
& $VenvPython -m PyInstaller $actualSpec --noconfirm
if ($LASTEXITCODE -ne 0) { Write-Fail "PyInstaller 打包失败，退出码 $LASTEXITCODE" }
Write-OK "PyInstaller 打包完成"

# ── 8. 清理临时文件 ──────────────────────────────────────────────────
foreach ($tmp in @(
    (Join-Path $ProjectRoot "MMS_encrypted.spec"),
    (Join-Path $ProjectRoot "MMS_debug.spec"),
    (Join-Path $ProjectRoot ".build_staging"),
    (Join-Path $ProjectRoot ".pyarmor_dist")
)) {
    if (Test-Path $tmp) { Remove-Item $tmp -Recurse -Force }
}

# ── 9. 写入版本文件 ──────────────────────────────────────────────────
$appDistDir = Join-Path $DistDir $AppName
$versionFile = Join-Path $appDistDir "VERSION"
$Version | Set-Content $versionFile -Encoding UTF8
Write-OK "版本文件已写入：$versionFile"

# ── 10. 生成 ZIP ──────────────────────────────────────────────────────
if (-not $NoZip) {
    Write-Step "压缩打包目录"
    $safeVersion = $Version -replace "[:/\\]", "-"
    $zipName     = "${AppName}_v${safeVersion}.zip"
    $zipPath     = Join-Path $DistDir $zipName

    if (Test-Path $zipPath) { Remove-Item $zipPath -Force }

    Compress-Archive -Path $appDistDir -DestinationPath $zipPath -CompressionLevel Optimal
    $zipSize = [math]::Round((Get-Item $zipPath).Length / 1MB, 1)
    Write-OK "已生成 ZIP：$zipPath  (${zipSize} MB)"
}

# ── 11. 完成 ──────────────────────────────────────────────────────────
Write-Host ""
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Green
Write-Host "  打包完成！发布目录：$appDistDir"  -ForegroundColor Green
if (-not $NoZip) {
    Write-Host "  分发包：$zipPath"  -ForegroundColor Green
}
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Green
