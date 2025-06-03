# EasyNovelAssistant 統合管理スクリプト (PowerShell)
# RTX 3080環境での最適化運用を含む包括的管理ツール

param(
    [Parameter(Mandatory=$false)]
    [ValidateSet("install", "update", "run", "optimize", "monitor", "menu")]
    [string]$Action = "menu",
    
    [Parameter(Mandatory=$false)]
    [string]$ModelName = "",
    
    [Parameter(Mandatory=$false)]
    [switch]$Force = $false,
    
    [Parameter(Mandatory=$false)]
    [switch]$Verbose = $false
)

# 設定とパス
$script:Config = @{
    ProjectRoot = $PSScriptRoot
    PythonPath = "$PSScriptRoot\EasyNovelAssistant\setup\lib\python\python.exe"
    VenvPath = "$PSScriptRoot\venv"
    KoboldCppPath = "$PSScriptRoot\KoboldCpp"
    StyleBertVitsPath = "$PSScriptRoot\Style-Bert-VITS2"
    ConfigFile = "$PSScriptRoot\config.json"
    LogDir = "$PSScriptRoot\log"
}

# ログ関数
function Write-LogMessage {
    param([string]$Message, [string]$Level = "INFO")
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $logEntry = "[$timestamp] [$Level] $Message"
    Write-Host $logEntry
    
    # ログファイルに記録
    $logFile = "$($script:Config.LogDir)\$(Get-Date -Format 'yyyyMMdd')\manager.log"
    $logDir = Split-Path $logFile -Parent
    if (!(Test-Path $logDir)) {
        New-Item -ItemType Directory -Path $logDir -Force | Out-Null
    }
    Add-Content -Path $logFile -Value $logEntry -Encoding UTF8
}

# GPU情報取得
function Get-GPUInfo {
    try {
        $gpuQuery = "nvidia-smi --query-gpu=name,memory.total,driver_version,temperature.gpu --format=csv,noheader,nounits"
        $result = Invoke-Expression $gpuQuery 2>$null
        
        if ($result) {
            $gpuData = $result.Split(',')
            return @{
                Name = $gpuData[0].Trim()
                MemoryMB = [int]$gpuData[1].Trim()
                DriverVersion = $gpuData[2].Trim()
                Temperature = [int]$gpuData[3].Trim()
                IsRTX3080 = $gpuData[0] -like "*RTX 3080*"
            }
        }
    }
    catch {
        Write-LogMessage "GPU情報の取得に失敗: $_" "ERROR"
    }
    
    return @{
        Name = "Unknown"
        MemoryMB = 8192
        DriverVersion = "Unknown"
        Temperature = 0
        IsRTX3080 = $false
    }
}

# 環境チェック
function Test-Environment {
    Write-LogMessage "環境チェックを実行中..."
    
    $issues = @()
    
    # Python確認
    if (!(Test-Path $script:Config.PythonPath)) {
        $issues += "Python実行ファイルが見つかりません: $($script:Config.PythonPath)"
    }
    
    # CUDA確認
    try {
        $null = Get-Command "nvidia-smi" -ErrorAction Stop
        $gpuInfo = Get-GPUInfo
        Write-LogMessage "GPU検出: $($gpuInfo.Name) (VRAM: $([math]::Round($gpuInfo.MemoryMB/1024, 1))GB)"
        
        if (!$gpuInfo.IsRTX3080) {
            Write-LogMessage "注意: RTX 3080以外のGPUが検出されました。最適化設定が適用されない可能性があります。" "WARN"
        }
    }
    catch {
        $issues += "NVIDIA GPU またはドライバが検出されません。CUDA機能が利用できません。"
    }
    
    # 設定ファイル確認
    if (!(Test-Path $script:Config.ConfigFile)) {
        $issues += "設定ファイルが見つかりません: $($script:Config.ConfigFile)"
    }
    
    if ($issues.Count -gt 0) {
        Write-LogMessage "環境チェックで問題が検出されました:" "ERROR"
        $issues | ForEach-Object { Write-LogMessage "  - $_" "ERROR" }
        return $false
    }
    
    Write-LogMessage "環境チェック完了：問題ありません" "SUCCESS"
    return $true
}

# インストール・セットアップ
function Install-EasyNovelAssistant {
    Write-LogMessage "EasyNovelAssistantのインストールを開始..."
    
    try {
        # 仮想環境作成
        if (!(Test-Path $script:Config.VenvPath)) {
            Write-LogMessage "Python仮想環境を作成中..."
            & python -m venv $script:Config.VenvPath
        }
        
        # pip更新
        Write-LogMessage "依存関係をインストール中..."
        & "$($script:Config.VenvPath)\Scripts\pip.exe" install --upgrade pip
        
        # 必要パッケージインストール
        $packages = @(
            "torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118",
            "numpy pandas tqdm requests",
            "tkinter jsonschema",
            "psutil GPUtil"
        )
        
        foreach ($package in $packages) {
            & "$($script:Config.VenvPath)\Scripts\pip.exe" install $package.Split(' ')
        }
        
        # KoboldCpp CUDA12版ダウンロード
        if (!(Test-Path "$($script:Config.KoboldCppPath)\koboldcpp.exe")) {
            Write-LogMessage "KoboldCpp CUDA12版をダウンロード中..."
            $koboldUrl = "https://github.com/LostRuins/koboldcpp/releases/latest/download/koboldcpp_cu12.exe"
            
            if (!(Test-Path $script:Config.KoboldCppPath)) {
                New-Item -ItemType Directory -Path $script:Config.KoboldCppPath -Force | Out-Null
            }
            
            Invoke-WebRequest -Uri $koboldUrl -OutFile "$($script:Config.KoboldCppPath)\koboldcpp.exe"
        }
        
        Write-LogMessage "インストール完了！" "SUCCESS"
        return $true
    }
    catch {
        Write-LogMessage "インストール中にエラーが発生: $_" "ERROR"
        return $false
    }
}

# アップデート
function Update-EasyNovelAssistant {
    Write-LogMessage "EasyNovelAssistantのアップデートを開始..."
    
    try {
        # KoboldCpp更新
        Write-LogMessage "KoboldCpp CUDA12版を更新中..."
        $koboldUrl = "https://github.com/LostRuins/koboldcpp/releases/latest/download/koboldcpp_cu12.exe"
        Invoke-WebRequest -Uri $koboldUrl -OutFile "$($script:Config.KoboldCppPath)\koboldcpp.exe"
        
        # Python依存関係更新
        Write-LogMessage "Python依存関係を更新中..."
        & "$($script:Config.VenvPath)\Scripts\pip.exe" install --upgrade pip
        & "$($script:Config.VenvPath)\Scripts\pip.exe" install --upgrade torch torchvision torchaudio
        
        Write-LogMessage "アップデート完了！" "SUCCESS"
        return $true
    }
    catch {
        Write-LogMessage "アップデート中にエラーが発生: $_" "ERROR"
        return $false
    }
}

# RTX 3080最適化
function Optimize-ForRTX3080 {
    param([string]$ModelName)
    
    Write-LogMessage "RTX 3080向け最適化を実行中..."
    
    try {
        # Python最適化スクリプト実行
        $optimizeScript = "$($script:Config.ProjectRoot)\optimize_config.py"
        if (Test-Path $optimizeScript) {
            if ($ModelName) {
                & "$($script:Config.VenvPath)\Scripts\python.exe" $optimizeScript $ModelName
            } else {
                & "$($script:Config.VenvPath)\Scripts\python.exe" $optimizeScript
            }
        } else {
            Write-LogMessage "最適化スクリプトが見つかりません: $optimizeScript" "ERROR"
            return $false
        }
        
        Write-LogMessage "最適化完了！" "SUCCESS"
        return $true
    }
    catch {
        Write-LogMessage "最適化中にエラーが発生: $_" "ERROR"
        return $false
    }
}

# パフォーマンス監視
function Monitor-Performance {
    Write-LogMessage "パフォーマンス監視を開始..."
    
    $monitorCount = 0
    while ($monitorCount -lt 60) { # 5分間監視
        try {
            $gpuInfo = Get-GPUInfo
            $cpuUsage = (Get-Counter '\Processor(_Total)\% Processor Time').CounterSamples.CookedValue
            $memInfo = Get-CimInstance Win32_OperatingSystem
            $memUsage = [math]::Round(($memInfo.TotalVisibleMemorySize - $memInfo.FreePhysicalMemory) / $memInfo.TotalVisibleMemorySize * 100, 1)
            
            $status = @{
                Timestamp = Get-Date -Format "HH:mm:ss"
                CPU = "$([math]::Round($cpuUsage, 1))%"
                Memory = "$memUsage%"
                GPU = $gpuInfo.Name
                GPUTemp = "$($gpuInfo.Temperature)°C"
            }
            
            Write-Host "[$($status.Timestamp)] CPU: $($status.CPU) | Memory: $($status.Memory) | GPU Temp: $($status.GPUTemp)"
            
            Start-Sleep -Seconds 5
            $monitorCount++
        }
        catch {
            Write-LogMessage "監視中にエラー: $_" "ERROR"
            break
        }
    }
}

# アプリケーション実行
function Start-EasyNovelAssistant {
    Write-LogMessage "EasyNovelAssistantを起動中..."
    
    if (!(Test-Environment)) {
        Write-LogMessage "環境チェックに失敗したため、起動を中止します。" "ERROR"
        return
    }
    
    try {
        # メインアプリケーション起動
        $mainScript = "$($script:Config.ProjectRoot)\easy_novel_assistant.py"
        
        if (Test-Path $mainScript) {
            # バックグラウンドで起動（オプション）
            if ($Force) {
                & "$($script:Config.VenvPath)\Scripts\python.exe" $mainScript
            } else {
                Start-Process -FilePath "$($script:Config.VenvPath)\Scripts\python.exe" -ArgumentList $mainScript -WorkingDirectory $script:Config.ProjectRoot
            }
            
            Write-LogMessage "EasyNovelAssistant起動完了！" "SUCCESS"
        } else {
            Write-LogMessage "メインスクリプトが見つかりません: $mainScript" "ERROR"
        }
    }
    catch {
        Write-LogMessage "起動中にエラーが発生: $_" "ERROR"
    }
}

# 対話メニュー
function Show-Menu {
    Clear-Host
    Write-Host "======================================="
    Write-Host "  EasyNovelAssistant 統合管理ツール"
    Write-Host "  RTX 3080最適化対応版"
    Write-Host "======================================="
    Write-Host ""
    
    # GPU情報表示
    $gpuInfo = Get-GPUInfo
    Write-Host "検出GPU: $($gpuInfo.Name)"
    Write-Host "VRAM: $([math]::Round($gpuInfo.MemoryMB/1024, 1))GB"
    Write-Host "温度: $($gpuInfo.Temperature)°C"
    Write-Host ""
    
    Write-Host "利用可能な操作:"
    Write-Host "1. インストール・セットアップ"
    Write-Host "2. アップデート"
    Write-Host "3. RTX 3080最適化実行"
    Write-Host "4. アプリケーション起動"
    Write-Host "5. パフォーマンス監視"
    Write-Host "6. 環境チェック"
    Write-Host "7. 終了"
    Write-Host ""
    
    do {
        $choice = Read-Host "選択してください (1-7)"
        
        switch ($choice) {
            "1" { 
                if (Install-EasyNovelAssistant) {
                    Read-Host "Enterキーで続行..."
                }
            }
            "2" { 
                if (Update-EasyNovelAssistant) {
                    Read-Host "Enterキーで続行..."
                }
            }
            "3" { 
                $model = Read-Host "モデル名を入力 (空白でconfig.jsonから自動取得)"
                if (Optimize-ForRTX3080 -ModelName $model) {
                    Read-Host "Enterキーで続行..."
                }
            }
            "4" { 
                Start-EasyNovelAssistant
                Read-Host "Enterキーで続行..."
            }
            "5" { 
                Monitor-Performance
                Read-Host "Enterキーで続行..."
            }
            "6" { 
                Test-Environment | Out-Null
                Read-Host "Enterキーで続行..."
            }
            "7" { 
                Write-LogMessage "管理ツールを終了します"
                return 
            }
            default { 
                Write-Host "無効な選択です。1-7の数字を入力してください。" -ForegroundColor Red 
            }
        }
        
        if ($choice -ne "7") {
            Show-Menu
        }
    } while ($choice -ne "7")
}

# メイン実行部分
Write-LogMessage "EasyNovelAssistant管理ツール開始 (引数: $Action)"

switch ($Action.ToLower()) {
    "install" { Install-EasyNovelAssistant }
    "update" { Update-EasyNovelAssistant }
    "run" { Start-EasyNovelAssistant }
    "optimize" { Optimize-ForRTX3080 -ModelName $ModelName }
    "monitor" { Monitor-Performance }
    "menu" { Show-Menu }
    default { Show-Menu }
} 