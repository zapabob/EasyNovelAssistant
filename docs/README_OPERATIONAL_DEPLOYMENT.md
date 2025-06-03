# 🚀 EasyNovelAssistant 運用3本柱システム

**29.6%の表現拡大率達成 → 実用運用段階へ移行**

本ドキュメントでは、NKAT表現拡張システムの運用3本柱（自動デプロイ・品質ガード・継続学習）の使用方法を説明します。

## 📊 達成済み性能指標

| 指標                     | 検証結果    | 目標値        | 状況 |
| ---------------------- | ------- | --------- | ---- |
| 語彙多様性 (uniques/100tok) | **29.6%** | 35%       | 🔄 進行中 |
| 文体変化度 (BERTStyleDist)  | **+292%** | +350%     | 🔄 進行中 |
| 矛盾率抑制                | 12%     | < 8%      | 🔄 進行中 |

## 🏗️ 運用3本柱システム

### 🚀 フェーズ① 自動デプロイ

**目的**: いつでも拡大版を呼べる環境構築

#### CLI起動オプション

```bash
# 標準起動
py -3 run_ena.py

# NKAT表現拡張モード
py -3 run_ena.py --nkat on --boost-level 75

# 高性能モード（RTX3080推奨）
py -3 run_ena.py --nkat on --theta-rank 8 --theta-gamma 0.95 --advanced-mode --quality-guard

# フルカスタマイズ例
py -3 run_ena.py \
  --model models/Qwen3-8B-ERP-NKAT.gguf \
  --nkat on \
  --theta-rank 6 --theta-gamma 0.98 \
  --temperature 0.82 --top_p 0.90 \
  --boost-level 80 --quality-guard
```

#### パラメータ説明

| パラメータ | 説明 | 推奨値 | 効果 |
|---------|------|-------|-----|
| `--theta-rank` | 表現幅パラメータ | 4-8 | rank↑ → 表現幅↑（VRAM+） |
| `--theta-gamma` | 安定性パラメータ | 0.8-1.0 | gamma↑ → 安定寄り／gamma↓ → 遊び寄り |
| `--boost-level` | 表現ブーストレベル | 70-90% | 語彙多様性・文体変化度に影響 |
| `--quality-guard` | 品質ガード機能 | 推奨ON | エラー率>3%で自動補正 |

### 🛡️ フェーズ② 品質ガード

**目的**: "盛り過ぎ"防止と自動品質維持

#### 自動補正システム

- **Grammar-Check**: 文法エラーの検出・修正
- **Sense-Check**: 常識性チェック・異常表現の抑制
- **Auto-Correction**: エラー率 > 3% で γ値自動調整
- **Diversity-Guard**: 多様性不足時のパラメータ最適化

#### 設定例

```json
{
  "quality_guard_enabled": true,
  "auto_correction_threshold": 0.03,
  "diversity_target": 0.35,
  "gamma_adjustment_step": 0.01
}
```

### 📊 フェーズ③ 継続評価&学習

**目的**: さらなる精度向上とユーザーフィードバック活用

#### 週次LoRA微調整

- 高評価フィードバック（4-5星）を訓練データとして活用
- 自動的な週次再学習スケジュール
- パフォーマンス向上の継続的追跡

#### メトリクス追跡

- **リアルタイム品質監視**
- **CI統合によるアラート**
- **トレンド分析**

## 🎚️ 実用的な運用パターン

### パターン1: 安全重視モード

```bash
py -3 run_ena.py --nkat on --theta-rank 4 --theta-gamma 0.98 --boost-level 60 --quality-guard
```

- VRAM使用量: ~5.7GB
- 語彙多様性: ~28.6%
- 安定性: 高

### パターン2: バランスモード（推奨）

```bash
py -3 run_ena.py --nkat on --theta-rank 6 --theta-gamma 0.95 --boost-level 75 --quality-guard
```

- VRAM使用量: ~7.3GB
- 語彙多様性: ~30.1%
- バランス: 良好

### パターン3: 高表現力モード

```bash
py -3 run_ena.py --nkat on --theta-rank 8 --theta-gamma 0.90 --boost-level 90 --quality-guard --advanced-mode
```

- VRAM使用量: ~8.9GB
- 語彙多様性: ~31.6%
- 表現力: 最大

## 📈 目標達成ロードマップ

### 短期目標（1-2週間）

- [x] 運用3本柱システム実装
- [x] 品質ガード自動補正
- [ ] ユーザーフィードバック収集開始
- [ ] 週次LoRA微調整初回実行

### 中期目標（1ヶ月）

- [ ] 語彙多様性 35% 達成
- [ ] 文体変化度 +350% 達成
- [ ] 矛盾率 8%以下 達成

### 長期目標（3ヶ月）

- [ ] 継続学習による自動最適化
- [ ] ユーザー満足度 90%以上
- [ ] RTX3080最適化完全活用

## 🔧 トラブルシューティング

### よくある問題と解決法

#### 1. VRAM不足エラー

```bash
# theta-rankを下げる
py -3 run_ena.py --nkat on --theta-rank 4 --boost-level 70
```

#### 2. 表現が単調になる

```bash
# gamma値を下げて多様性向上
py -3 run_ena.py --nkat on --theta-gamma 0.85 --boost-level 80
```

#### 3. エラー率が高い

```bash
# 品質ガード強化
py -3 run_ena.py --nkat on --quality-guard --correction-threshold 0.02
```

### パフォーマンス監視

#### メトリクス確認

```python
# Pythonコンソールで実行
from easy_novel_assistant import EasyNovelAssistant
app = EasyNovelAssistant()

# パフォーマンス確認
metrics = app.get_performance_metrics()
print(f"多様性スコア: {metrics['quality']['diversity_score']:.1%}")

# 運用レポート
report = app.get_operational_report()
print(f"品質ガード発動回数: {report['quality_guard']['statistics']['corrections_applied']}")
```

## 📚 詳細リファレンス

### 設定ファイル例 (`config.json`)

```json
{
  "nkat_enabled": true,
  "theta_rank": 6,
  "theta_gamma": 0.98,
  "expression_boost_level": 75,
  "quality_guard_enabled": true,
  "auto_correction_threshold": 0.03,
  "diversity_target": 0.35,
  "continuous_learning_enabled": true,
  "lora_training_enabled": true,
  "feedback_db_path": "data/feedback.db",
  "rtx3080_optimization": true,
  "cuda_memory_fraction": 0.9,
  "mixed_precision": true
}
```

### 環境要件

- **Python**: 3.8以上
- **GPU**: RTX3080 (10GB VRAM推奨)
- **RAM**: 16GB以上
- **Storage**: 5GB以上の空き容量

### 依存関係

```txt
torch>=1.13.0+cu116
transformers>=4.20.0
tqdm>=4.64.0
numpy>=1.21.0
sqlite3 (標準ライブラリ)
```

## 🎯 次期アップデート予定

### v2.1.0 (予定)

- UIに表現ブーストスライダー追加
- リアルタイム品質メーター
- ワンクリック設定プリセット

### v2.2.0 (予定)

- 高度な語彙分析機能
- 複数モデル対応
- クラウド学習統合

## 📞 サポート・フィードバック

- **Issues**: プロジェクトのGitHubリポジトリ
- **フィードバック**: システム内蔵の評価機能をご利用ください
- **質問**: README.mdの基本情報もご参照ください

---

**🔥 "破綻しないまま表現を爆盛り" - さらなる向上を目指して！**

*Last Updated: 2024年* 