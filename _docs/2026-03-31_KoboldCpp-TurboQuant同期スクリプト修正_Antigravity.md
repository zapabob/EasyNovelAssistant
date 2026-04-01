# 2026-03-31 KoboldCpp-TurboQuant 同期スクリプト修正

## 方針

- PowerShell の `param()` ブロックがスクリプトの先頭（コメント・改行を除く最初のステートメント）にないための ParserError を解決。
- 開発ガイドラインに基づき、`Write-Host` を廃止し、タイムスタンプおよびレベル付きの `Write-Log` 関数によるロギングを実装。

## 反映内容

### 1) Sync-KoboldCpp-TurboQuant.ps1 の修正

#### [MODIFY] [Sync-KoboldCpp-TurboQuant.ps1](file:///c:/Users/downl/Desktop/EasyNovelAssistant/EasyNovelAssistant/Sync-KoboldCpp-TurboQuant.ps1)

- `param()` ブロックをファイルの先頭に移動。
- `Write-Log` 関数を追加し、標準出力へフォーマット済みログを出力するように変更。
- 既存の `Write-Host` 呼び出しを `Write-Log` へ置換。

## 検証結果

- PowerShell による構文チェックおよび実行確認を実施。
- 実行時に ParserError が発生しないことを確認済み。
- ログ出力が `[yyyy-MM-dd HH:mm:ss] [INFO] ...` の形式で出力されることを確認。

## 通常手順

1. `Run-EasyNovelAssistant-KoboldCpp-TurboQuant.bat` から呼び出される際、正しく引数が処理され、同期が開始される。
