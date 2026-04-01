param(
    [string]$SourceRoot = "C:\Users\downl\Desktop\koboldcpp-turboquant-integration\koboldcpp",
    [string]$TargetRoot = "C:\Users\downl\Desktop\EasyNovelAssistant\EasyNovelAssistant\KoboldCpp"
)

$ErrorActionPreference = "Stop"

function Write-Log {
    param(
        [Parameter(Mandatory=$true)]
        [string]$Message,
        [string]$Level = "INFO"
    )
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    Write-Output "[$timestamp] [$Level] $Message"
}

if (-not (Test-Path $SourceRoot)) {
    throw "SourceRoot not found: $SourceRoot"
}

if (-not (Test-Path $TargetRoot)) {
    New-Item -ItemType Directory -Path $TargetRoot | Out-Null
}

$copyList = @(
    "koboldcpp.py",
    "koboldcpp_cublas.dll",
    "ggml.dll",
    "ggml-base.dll",
    "ggml-cpu.dll"
)

foreach ($name in $copyList) {
    $src = Join-Path $SourceRoot $name
    if (Test-Path $src) {
        Copy-Item -Path $src -Destination (Join-Path $TargetRoot $name) -Force
        Write-Log "[sync] copied $name"
    } else {
        Write-Log "[sync] skipped $name (not found in source)" "WARN"
    }
}

Write-Log "TurboQuant KoboldCpp sync complete."
Write-Log "Target: $TargetRoot"
Write-Log "Run launcher: Run-EasyNovelAssistant-KoboldCpp-TurboQuant.bat"

