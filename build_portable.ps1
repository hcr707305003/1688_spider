param(
    [string]$Python = ".\.venv\Scripts\python.exe",
    [ValidateSet("Stable", "Beta", "Dev", "Canary")]
    [string]$Channel = "Stable"
)

$ErrorActionPreference = "Stop"
$projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$pythonPath = [System.IO.Path]::GetFullPath((Join-Path $projectRoot $Python))
$cacheRoot = Join-Path $projectRoot ".build-cache\chrome-for-testing"
$ariaVersion = "1.37.0"
$ariaCache = Join-Path $projectRoot ".build-cache\aria2\$ariaVersion"
$ariaExe = Join-Path $ariaCache "aria2c.exe"
$workRoot = Join-Path $projectRoot "build\portable"
$stageDist = Join-Path $workRoot "dist"
$packageName = "1688商品采集工具便携版"
$packageDir = Join-Path $stageDist $packageName
$finalDist = Join-Path $projectRoot "dist"
$finalPackage = Join-Path $finalDist $packageName
$versionInfo = Get-Content -Raw -LiteralPath (Join-Path $projectRoot "version.json") | ConvertFrom-Json
$applicationVersion = $versionInfo.version
$finalZip = Join-Path $finalDist "1688_spider-v$applicationVersion-windows-x64.zip"

function Invoke-ReliableDownload {
    param(
        [Parameter(Mandatory = $true)][string]$Uri,
        [Parameter(Mandatory = $true)][string]$Destination
    )

    $curl = Get-Command curl.exe -ErrorAction SilentlyContinue
    if ($curl) {
        & $curl.Source --location --fail --retry 5 --retry-delay 2 --continue-at - --output $Destination $Uri
        if ($LASTEXITCODE -eq 0 -and (Test-Path -LiteralPath $Destination -PathType Leaf)) {
            return
        }
    }

    for ($attempt = 1; $attempt -le 3; $attempt++) {
        try {
            Invoke-WebRequest -Uri $Uri -OutFile $Destination
            return
        } catch {
            if ($attempt -eq 3) {
                throw
            }
            Start-Sleep -Seconds (2 * $attempt)
        }
    }
}

if (-not (Test-Path -LiteralPath $pythonPath -PathType Leaf)) {
    throw "未找到构建Python：$pythonPath"
}

Set-Location -LiteralPath $projectRoot

Write-Host "[1/7] 获取官方浏览器版本..."
$metadataUrl = "https://googlechromelabs.github.io/chrome-for-testing/last-known-good-versions-with-downloads.json"
$metadata = Invoke-RestMethod -Uri $metadataUrl
$release = $metadata.channels.$Channel
$version = $release.version
$chromeUrl = ($release.downloads.chrome | Where-Object platform -eq "win64").url
$driverUrl = ($release.downloads.chromedriver | Where-Object platform -eq "win64").url
if (-not $version -or -not $chromeUrl -or -not $driverUrl) {
    throw "官方清单中没有找到 $Channel win64 浏览器或驱动"
}

$versionCache = Join-Path $cacheRoot $version
$chromeDir = Join-Path $versionCache "chrome-win64"
$driverDir = Join-Path $versionCache "chromedriver-win64"
$chromeExe = Join-Path $chromeDir "chrome.exe"
$driverExe = Join-Path $driverDir "chromedriver.exe"

if (-not (Test-Path -LiteralPath $chromeExe -PathType Leaf)) {
    Write-Host "[2/7] 下载浏览器 $version..."
    New-Item -ItemType Directory -Force -Path $versionCache | Out-Null
    $chromeZip = Join-Path $versionCache "chrome-win64.zip"
    Invoke-ReliableDownload -Uri $chromeUrl -Destination $chromeZip
    Expand-Archive -LiteralPath $chromeZip -DestinationPath $versionCache -Force
    Remove-Item -LiteralPath $chromeZip -Force -ErrorAction SilentlyContinue
} else {
    Write-Host "[2/7] 使用浏览器缓存 $version"
}

if (-not (Test-Path -LiteralPath $driverExe -PathType Leaf)) {
    Write-Host "[3/7] 下载匹配驱动 $version..."
    New-Item -ItemType Directory -Force -Path $versionCache | Out-Null
    $driverZip = Join-Path $versionCache "chromedriver-win64.zip"
    Invoke-ReliableDownload -Uri $driverUrl -Destination $driverZip
    Expand-Archive -LiteralPath $driverZip -DestinationPath $versionCache -Force
    Remove-Item -LiteralPath $driverZip -Force -ErrorAction SilentlyContinue
} else {
    Write-Host "[3/7] 使用驱动缓存 $version"
}

$browserVersion = (Get-Item -LiteralPath $chromeExe).VersionInfo.ProductVersion
$driverVersionText = & $driverExe --version
$driverVersion = [regex]::Match($driverVersionText, '\d+(\.\d+){3}').Value
if ($browserVersion -ne $version -or $driverVersion -ne $version) {
    throw "浏览器和驱动版本不匹配：清单=$version 浏览器=$browserVersion 驱动=$driverVersion"
}

if (-not (Test-Path -LiteralPath $ariaExe -PathType Leaf)) {
    Write-Host "[4/7] 下载 aria2 $ariaVersion..."
    New-Item -ItemType Directory -Force -Path $ariaCache | Out-Null
    $ariaZip = Join-Path $ariaCache "aria2.zip"
    $ariaUrl = "https://github.com/aria2/aria2/releases/download/release-$ariaVersion/aria2-$ariaVersion-win-64bit-build1.zip"
    Invoke-ReliableDownload -Uri $ariaUrl -Destination $ariaZip
    $ariaExtract = Join-Path $ariaCache "extract"
    Expand-Archive -LiteralPath $ariaZip -DestinationPath $ariaExtract -Force
    $downloadedAria = Get-ChildItem -LiteralPath $ariaExtract -Recurse -Filter "aria2c.exe" -File | Select-Object -First 1
    if (-not $downloadedAria) {
        throw "aria2压缩包中没有找到aria2c.exe"
    }
    Copy-Item -LiteralPath $downloadedAria.FullName -Destination $ariaExe -Force
    Remove-Item -LiteralPath $ariaZip -Force -ErrorAction SilentlyContinue
} else {
    Write-Host "[4/7] 使用 aria2 缓存 $ariaVersion"
}

Write-Host "[5/7] 构建Windows可执行文件..."
if (Test-Path -LiteralPath $workRoot) {
    Remove-Item -LiteralPath $workRoot -Recurse -Force
}
New-Item -ItemType Directory -Force -Path $workRoot | Out-Null
& $pythonPath -m PyInstaller --noconfirm --clean --distpath $stageDist --workpath (Join-Path $workRoot "work") portable_collector.spec
if ($LASTEXITCODE -ne 0) {
    throw "PyInstaller构建失败，退出码：$LASTEXITCODE"
}

Write-Host "[6/7] 组装便携目录..."
$browserTarget = Join-Path $packageDir "browser\chrome"
New-Item -ItemType Directory -Force -Path $browserTarget | Out-Null
Copy-Item -Path (Join-Path $chromeDir "*") -Destination $browserTarget -Recurse -Force
New-Item -ItemType Directory -Force -Path (Join-Path $packageDir "browser") | Out-Null
Copy-Item -LiteralPath $driverExe -Destination (Join-Path $packageDir "browser\chromedriver.exe") -Force
New-Item -ItemType Directory -Force -Path (Join-Path $packageDir "tools") | Out-Null
Copy-Item -LiteralPath $ariaExe -Destination (Join-Path $packageDir "tools\aria2c.exe") -Force
New-Item -ItemType Directory -Force -Path (Join-Path $packageDir "data\browser_data") | Out-Null
New-Item -ItemType Directory -Force -Path (Join-Path $packageDir "data\products") | Out-Null
Copy-Item -LiteralPath (Join-Path $projectRoot "packaging\使用说明.txt") -Destination (Join-Path $packageDir "使用说明.txt") -Force

$buildInfo = [ordered]@{
    application = "1688商品采集工具"
    application_version = $applicationVersion
    browser_version = $version
    channel = $Channel
    architecture = "win64"
    built_at = (Get-Date).ToString("yyyy-MM-ddTHH:mm:ssK")
}
$buildInfo | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $packageDir "build-info.json") -Encoding UTF8

Write-Host "[7/7] 生成发布目录和ZIP..."
New-Item -ItemType Directory -Force -Path $finalDist | Out-Null
if (Test-Path -LiteralPath $finalPackage) {
    Remove-Item -LiteralPath $finalPackage -Recurse -Force
}
if (Test-Path -LiteralPath $finalZip) {
    Remove-Item -LiteralPath $finalZip -Force
}
Copy-Item -LiteralPath $packageDir -Destination $finalPackage -Recurse -Force
Compress-Archive -LiteralPath $finalPackage -DestinationPath $finalZip -CompressionLevel Optimal

Write-Host "构建完成："
Write-Host "  目录：$finalPackage"
Write-Host "  ZIP： $finalZip"
