# EasyNovelAssistant

軽量で規制も検閲もない日本語ローカルLLM『LightChatAssistant-TypeB』による、簡単なノベル生成アシスタントです。ローカル特権の永続生成 Generate forever で、当たりガチャを積み上げます。読み上げにも対応。

## 🚀 最新機能

* **タブ機能**: プロンプト入力欄にタブを追加し、複数のプロンプトの比較や調整が容易になりました
* **イントロプロンプト**: 特定のタブをイントロプロンプトとして設定し、他のタブに自動的に追加する機能を実装。世界観やキャラ設定を一元管理できます
* **複数ファイル対応**: 複数ファイルやフォルダをドラッグ＆ドロップで簡単に読み込めます
* **最新軽量モデル対応**: Ninja-V3-7B などの最新軽量モデルに対応し、生成品質が向上

## 📁 リポジトリ構造

このリポジトリは効率的な開発とメンテナンスのために以下のように整理されています：

```
EasyNovelAssistant/
├── 📁 app/                        # アプリケーションコア
│   ├── core/                      # コアロジック
│   ├── ui/                        # ユーザーインターフェース
│   ├── integrations/              # 外部システム連携
│   ├── utils/                     # ユーティリティ
│   └── dialogs/                   # ダイアログ
├── 📁 config/                     # 設定ファイル
│   ├── app/                       # アプリケーション設定
│   ├── templates/                 # 設定テンプレート
│   └── defaults/                  # デフォルト設定
├── 📁 docs/                       # ドキュメント
│   ├── user/                      # ユーザー向け
│   ├── dev/                       # 開発者向け
│   └── changelog/                 # 変更履歴
├── 📁 resources/                  # リソースファイル
│   ├── assets/                    # アセット
│   ├── samples/                   # サンプル
│   ├── templates/                 # テンプレート
│   └── icons/                     # アイコン
├── 📁 scripts/                    # 運用スクリプト
│   ├── install/                   # インストール
│   ├── update/                    # アップデート
│   └── misc/                      # その他
├── 📁 external/                   # 外部システム
│   ├── KoboldCpp/                 # KoboldCpp
│   └── Style-Bert-VITS2/          # Style-Bert-VITS2
└── easy_novel_assistant.py        # メインエントリーポイント
```

## 🛠️ インストール

詳細なインストール手順は [docs/user/INSTALLATION.md](docs/user/INSTALLATION.md) をご覧ください。

## 📖 使用方法

1. `easy_novel_assistant.py` を実行してアプリケーションを起動
2. プロンプト入力欄にテキストを入力
3. 生成設定を調整して文章を生成
4. 必要に応じて読み上げ機能を利用

詳細なユーザーガイドは [docs/user/](docs/user/) をご覧ください。

## 🔧 開発者向け情報

- [ビルドガイド](docs/dev/BUILD_GUIDE.md)
- [アーキテクチャ説明](docs/dev/ARCHITECTURE.md)
- [API リファレンス](docs/dev/API_REFERENCE.md)

## 📜 ライセンス

このプロジェクトは MIT License の下で公開されています。詳細は [LICENSE.txt](LICENSE.txt) をご覧ください。

## 🤝 コントリビューション

プルリクエストやイシューの報告を歓迎します。

## 📞 サポート

問題や質問がある場合は、GitHub Issues でお知らせください。

---

**注意**: このプロジェクトはローカル環境でのAI活用を目的としており、外部サービスに依存しません。プライバシーとデータセキュリティが確保されています。 