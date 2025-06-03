# EasyNovelAssistant リポジトリ構造化計画

## 🎯 現在の問題点

### 散らばったファイル構造
- ルートディレクトリに多数のPythonファイルが混在
- ビルドファイルとソースコードが混在
- 設定ファイルが複数箇所に分散
- ドキュメントファイルが整理されていない

### 混在している要素
1. **コアソースコード**: `*.py` ファイル（メインロジック）
2. **ビルドスクリプト**: `build_*.py`, `*.spec` ファイル
3. **設定ファイル**: `*.json` ファイル
4. **ドキュメント**: `*.md` ファイル
5. **開発ツール**: 各種スクリプト
6. **リソース**: サンプル、テンプレート等

## 🏗️ 新しい構造設計

### 提案する理想的な構造
```
EasyNovelAssistant/
├── 📁 app/                        # アプリケーションコア
│   ├── core/                      # コアロジック
│   │   ├── __init__.py
│   │   ├── context.py
│   │   ├── const.py
│   │   └── path.py
│   ├── ui/                        # ユーザーインターフェース
│   │   ├── __init__.py
│   │   ├── form.py
│   │   ├── input_area.py
│   │   ├── output_area.py
│   │   └── gen_area.py
│   ├── integrations/              # 外部システム連携
│   │   ├── __init__.py
│   │   ├── kobold_cpp.py
│   │   ├── style_bert_vits2.py
│   │   └── movie_maker.py
│   ├── utils/                     # ユーティリティ
│   │   ├── __init__.py
│   │   ├── generator.py
│   │   ├── gguf_manager.py
│   │   └── job_queue.py
│   └── dialogs/                   # ダイアログ
│       ├── __init__.py
│       ├── model_add_dialog.py
│       └── integration_control_panel.py
├── 📁 build/                      # ビルド関連
│   ├── scripts/                   # ビルドスクリプト
│   │   ├── build_exe.py
│   │   ├── build_core.py
│   │   ├── package_release.py
│   │   └── create_distribution_package.py
│   ├── specs/                     # PyInstaller設定
│   │   └── easy_novel_assistant.spec
│   └── tools/                     # ビルドツール
│       ├── copy_modules.py
│       └── quick_build.py
├── 📁 config/                     # 設定ファイル
│   ├── app/                       # アプリケーション設定
│   │   ├── config.json
│   │   ├── llm.json
│   │   └── llm_sequence.json
│   ├── templates/                 # 設定テンプレート
│   └── defaults/                  # デフォルト設定
├── 📁 docs/                       # ドキュメント
│   ├── user/                      # ユーザー向け
│   │   ├── README.md
│   │   ├── INSTALLATION.md
│   │   └── USER_GUIDE.md
│   ├── dev/                       # 開発者向け
│   │   ├── BUILD_GUIDE.md
│   │   ├── ARCHITECTURE.md
│   │   └── API_REFERENCE.md
│   └── changelog/                 # 変更履歴
│       ├── CHANGELOG.md
│       └── RELEASE_NOTES.md
├── 📁 resources/                  # リソースファイル
│   ├── assets/                    # アセット
│   ├── samples/                   # サンプル
│   ├── templates/                 # テンプレート
│   └── icons/                     # アイコン
├── 📁 scripts/                    # 運用スクリプト
│   ├── install/                   # インストール
│   ├── update/                    # アップデート
│   └── maintenance/               # メンテナンス
├── 📁 tests/                      # テストファイル
│   ├── unit/                      # ユニットテスト
│   ├── integration/               # 統合テスト
│   └── fixtures/                  # テストデータ
├── 📁 external/                   # 外部システム
│   ├── KoboldCpp/                 # KoboldCpp
│   └── Style-Bert-VITS2/          # Style-Bert-VITS2
├── 📁 release/                    # リリースファイル
├── easy_novel_assistant.py        # メインエントリーポイント
├── requirements.txt               # Python依存関係
├── setup.py                       # セットアップスクリプト
├── .gitignore                     # Git除外設定
└── LICENSE.txt                    # ライセンス
```

## 🚀 実行計画

### Phase 1: コアアプリケーション構造化
1. `app/` ディレクトリ作成とモジュール分類
2. UI関連ファイルの整理
3. 統合システム（v3）の適切な配置

### Phase 2: ビルドシステム整理
1. `build/` ディレクトリ作成
2. ビルドスクリプトの統合
3. .specファイルの最適化

### Phase 3: 設定・ドキュメント整理
1. `config/` ディレクトリで設定統一
2. `docs/` でドキュメント体系化
3. README.mdの更新

### Phase 4: リソース・スクリプト整理
1. `resources/` でアセット統合
2. `scripts/` で運用スクリプト整理
3. 外部システムの分離

### Phase 5: 最終調整・テスト
1. インポートパスの修正
2. 設定ファイルパスの更新
3. 動作テスト・ビルドテスト

## 📊 期待される効果

### 開発効率の向上
- **モジュラー構造**: 機能別ディレクトリで開発効率アップ
- **明確な責任分離**: 各ディレクトリの役割が明確
- **スケーラビリティ**: 新機能追加が容易

### メンテナンス性の向上
- **問題の局所化**: バグやエラーの原因特定が容易
- **テスト容易性**: ユニットテスト・統合テストの実装が簡単
- **ドキュメント体系化**: 情報の検索・更新が効率的

### ユーザビリティの向上
- **明確な導入手順**: 整理されたドキュメントとスクリプト
- **トラブルシューティング**: 構造化された問題解決手順
- **カスタマイズ性**: 設定ファイルの一元管理

## ⚠️ 注意事項

### 破壊的変更
- インポートパスの大幅な変更
- 設定ファイルパスの変更
- ビルドプロセスの変更

### 後方互換性の維持
- 既存の設定ファイルの移行スクリプト作成
- 古いパスに対する警告・リダイレクト機能
- 段階的移行プロセスの実装 