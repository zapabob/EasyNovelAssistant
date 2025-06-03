# -*- coding: utf-8 -*-
"""
EasyNovelAssistant システム構成最適化モジュール
プロジェクト構造の整理、モジュール分離、設定管理の改善を行う
"""

import json
import os
import shutil
import sys
from pathlib import Path
from typing import Dict, List, Optional, Any
import logging
from datetime import datetime


class SystemOptimizer:
    """システム構成最適化クラス"""
    
    def __init__(self, project_root: str = None):
        self.project_root = Path(project_root) if project_root else Path.cwd()
        self.logger = self._setup_logging()
        
        # 推奨ディレクトリ構成
        self.recommended_structure = {
            "src": {
                "description": "メインソースコード",
                "subdirs": {
                    "ui": "ユーザーインターフェース関連",
                    "engines": "推論エンジン（KoboldCpp等）統合",
                    "models": "モデル管理・最適化",
                    "utils": "汎用ユーティリティ",
                    "nkat": "NKAT統合モジュール"
                }
            },
            "config": {
                "description": "設定ファイル",
                "subdirs": {
                    "templates": "設定テンプレート",
                    "models": "モデル別設定",
                    "optimization": "最適化設定"
                }
            },
            "data": {
                "description": "データファイル",
                "subdirs": {
                    "models": "モデルファイル",
                    "cache": "キャッシュデータ",
                    "temp": "一時ファイル"
                }
            },
            "logs": {
                "description": "ログファイル",
                "subdirs": {
                    "app": "アプリケーションログ",
                    "performance": "パフォーマンスログ",
                    "errors": "エラーログ"
                }
            },
            "scripts": {
                "description": "起動・管理スクリプト",
                "subdirs": {
                    "install": "インストールスクリプト",
                    "update": "更新スクリプト",
                    "optimization": "最適化スクリプト"
                }
            },
            "docs": {
                "description": "ドキュメント",
                "subdirs": {
                    "api": "APIドキュメント",
                    "user": "ユーザーマニュアル",
                    "dev": "開発者向けドキュメント"
                }
            }
        }
        
    def _setup_logging(self) -> logging.Logger:
        """ログ設定"""
        logger = logging.getLogger("SystemOptimizer")
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            # コンソールハンドラ
            console_handler = logging.StreamHandler()
            console_formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            console_handler.setFormatter(console_formatter)
            logger.addHandler(console_handler)
            
            # ファイルハンドラ
            log_dir = self.project_root / "logs" / "system_optimizer"
            log_dir.mkdir(parents=True, exist_ok=True)
            
            file_handler = logging.FileHandler(
                log_dir / f"optimization_{datetime.now().strftime('%Y%m%d')}.log",
                encoding='utf-8'
            )
            file_formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            file_handler.setFormatter(file_formatter)
            logger.addHandler(file_handler)
            
        return logger
        
    def analyze_current_structure(self) -> Dict[str, Any]:
        """現在のプロジェクト構造を分析"""
        self.logger.info("プロジェクト構造の分析を開始...")
        
        analysis = {
            "total_files": 0,
            "python_files": [],
            "config_files": [],
            "script_files": [],
            "log_files": [],
            "model_files": [],
            "issues": [],
            "recommendations": []
        }
        
        # ファイル種別の分析
        for file_path in self.project_root.rglob("*"):
            if file_path.is_file():
                analysis["total_files"] += 1
                
                suffix = file_path.suffix.lower()
                relative_path = file_path.relative_to(self.project_root)
                
                if suffix == ".py":
                    analysis["python_files"].append(str(relative_path))
                elif suffix in [".json", ".yaml", ".yml", ".ini", ".cfg"]:
                    analysis["config_files"].append(str(relative_path))
                elif suffix in [".bat", ".sh", ".ps1"]:
                    analysis["script_files"].append(str(relative_path))
                elif suffix in [".log", ".txt"] and "log" in str(file_path).lower():
                    analysis["log_files"].append(str(relative_path))
                elif suffix in [".gguf", ".bin", ".safetensors", ".pt", ".pth"]:
                    analysis["model_files"].append(str(relative_path))
        
        # 問題点の特定
        self._identify_issues(analysis)
        
        # 推奨事項の生成
        self._generate_recommendations(analysis)
        
        self.logger.info(f"分析完了: {analysis['total_files']} ファイル検出")
        return analysis
        
    def _identify_issues(self, analysis: Dict[str, Any]):
        """構造上の問題点を特定"""
        issues = []
        
        # ルートディレクトリに散在するPythonファイル
        root_python_files = [f for f in analysis["python_files"] 
                           if "/" not in f and "\\" not in f]
        if len(root_python_files) > 5:
            issues.append(f"ルートディレクトリにPythonファイルが{len(root_python_files)}個散在しています")
        
        # 設定ファイルの散在
        root_config_files = [f for f in analysis["config_files"] 
                           if "/" not in f and "\\" not in f]
        if len(root_config_files) > 3:
            issues.append(f"ルートディレクトリに設定ファイルが{len(root_config_files)}個散在しています")
        
        # ログファイルの管理
        if len(analysis["log_files"]) > 10:
            issues.append("ログファイルが多数あります。アーカイブ化を検討してください")
        
        # モデルファイルの場所
        model_locations = set()
        for model_file in analysis["model_files"]:
            model_locations.add(str(Path(model_file).parent))
        if len(model_locations) > 3:
            issues.append("モデルファイルが複数の場所に分散しています")
        
        analysis["issues"] = issues
        
    def _generate_recommendations(self, analysis: Dict[str, Any]):
        """改善推奨事項を生成"""
        recommendations = []
        
        # モジュール分離
        if len(analysis["python_files"]) > 10:
            recommendations.append("Pythonファイルを機能別のディレクトリに分離することを推奨")
        
        # 設定管理の改善
        if len(analysis["config_files"]) > 5:
            recommendations.append("設定ファイルを`config/`ディレクトリに統合することを推奨")
        
        # スクリプト整理
        if len(analysis["script_files"]) > 5:
            recommendations.append("起動・管理スクリプトを`scripts/`ディレクトリに整理することを推奨")
        
        # ログ管理
        if len(analysis["log_files"]) > 5:
            recommendations.append("ログファイルを日付別・種類別に整理することを推奨")
        
        analysis["recommendations"] = recommendations
        
    def create_optimized_structure(self, backup: bool = True) -> bool:
        """最適化されたディレクトリ構造を作成"""
        self.logger.info("最適化されたディレクトリ構造の作成を開始...")
        
        try:
            # バックアップ作成
            if backup:
                self._create_backup()
            
            # 新しいディレクトリ構造作成
            self._create_directory_structure()
            
            # ファイル移動・整理
            self._reorganize_files()
            
            # 設定ファイル統合
            self._consolidate_configs()
            
            # スクリプト整理
            self._organize_scripts()
            
            self.logger.info("ディレクトリ構造の最適化完了")
            return True
            
        except Exception as e:
            self.logger.error(f"構造最適化エラー: {e}")
            return False
            
    def _create_backup(self):
        """現在の構造をバックアップ"""
        backup_dir = self.project_root / f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        backup_dir.mkdir(exist_ok=True)
        
        important_files = [
            "*.py", "*.json", "*.bat", "*.sh", "*.ps1", "*.txt", "*.md"
        ]
        
        for pattern in important_files:
            for file_path in self.project_root.glob(pattern):
                if file_path.is_file():
                    shutil.copy2(file_path, backup_dir / file_path.name)
        
        self.logger.info(f"バックアップ作成: {backup_dir}")
        
    def _create_directory_structure(self):
        """推奨ディレクトリ構造を作成"""
        for main_dir, info in self.recommended_structure.items():
            main_path = self.project_root / main_dir
            main_path.mkdir(exist_ok=True)
            
            if "subdirs" in info:
                for subdir, description in info["subdirs"].items():
                    sub_path = main_path / subdir
                    sub_path.mkdir(exist_ok=True)
                    
                    # README作成
                    readme_path = sub_path / "README.md"
                    if not readme_path.exists():
                        with open(readme_path, 'w', encoding='utf-8') as f:
                            f.write(f"# {subdir}\n\n{description}\n")
                            
    def _reorganize_files(self):
        """ファイルの再配置"""
        file_mappings = {
            # UIファイル
            "form.py": "src/ui/",
            "input_area.py": "src/ui/",
            "output_area.py": "src/ui/",
            "gen_area.py": "src/ui/",
            
            # エンジンファイル
            "kobold_cpp.py": "src/engines/",
            "style_bert_vits2.py": "src/engines/",
            
            # モデル管理
            "generator.py": "src/models/",
            "model_add_dialog.py": "src/models/",
            
            # ユーティリティ
            "const.py": "src/utils/",
            "context.py": "src/utils/",
            "path.py": "src/utils/",
            "job_queue.py": "src/utils/",
            
            # NKAT
            "nkat_integration.py": "src/nkat/",
            "optimize_config.py": "src/nkat/",
            
            # 設定
            "config.json": "config/",
            "llm.json": "config/models/",
            "llm_sequence.json": "config/models/",
        }
        
        for source_file, target_dir in file_mappings.items():
            source_path = self.project_root / source_file
            target_path = self.project_root / target_dir / source_file
            
            if source_path.exists() and not target_path.exists():
                target_path.parent.mkdir(parents=True, exist_ok=True)
                shutil.move(str(source_path), str(target_path))
                self.logger.info(f"移動: {source_file} -> {target_dir}")
                
    def _consolidate_configs(self):
        """設定ファイルの統合"""
        config_dir = self.project_root / "config"
        
        # メイン設定ファイル統合
        main_config = {}
        
        config_files = [
            "config.json",
            "llm.json", 
            "llm_sequence.json"
        ]
        
        for config_file in config_files:
            config_path = self.project_root / config_file
            if config_path.exists():
                try:
                    with open(config_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        main_config[config_file.replace('.json', '')] = data
                except Exception as e:
                    self.logger.warning(f"設定ファイル読み込みエラー {config_file}: {e}")
        
        # 統合設定ファイル作成
        if main_config:
            consolidated_path = config_dir / "consolidated_config.json"
            with open(consolidated_path, 'w', encoding='utf-8') as f:
                json.dump(main_config, f, indent=4, ensure_ascii=False)
            
            self.logger.info(f"統合設定ファイル作成: {consolidated_path}")
            
    def _organize_scripts(self):
        """スクリプトファイルの整理"""
        scripts_dir = self.project_root / "scripts"
        
        script_categories = {
            "install": ["Install-", "Setup-"],
            "update": ["Update-", "Upgrade-"],
            "run": ["Run-", "Start-", "Launch-"],
            "optimization": ["Optimize-", "RTX-", "CUDA-"]
        }
        
        for script_file in self.project_root.glob("*.bat"):
            moved = False
            for category, prefixes in script_categories.items():
                if any(script_file.name.startswith(prefix) for prefix in prefixes):
                    target_dir = scripts_dir / category
                    target_dir.mkdir(parents=True, exist_ok=True)
                    
                    target_path = target_dir / script_file.name
                    if not target_path.exists():
                        shutil.move(str(script_file), str(target_path))
                        self.logger.info(f"スクリプト移動: {script_file.name} -> scripts/{category}/")
                        moved = True
                        break
            
            if not moved:
                # 未分類スクリプト
                misc_dir = scripts_dir / "misc"
                misc_dir.mkdir(parents=True, exist_ok=True)
                target_path = misc_dir / script_file.name
                if not target_path.exists():
                    shutil.move(str(script_file), str(target_path))
                    
    def generate_module_interfaces(self):
        """モジュールインターフェース定義を生成"""
        interfaces_dir = self.project_root / "src" / "interfaces"
        interfaces_dir.mkdir(parents=True, exist_ok=True)
        
        # 基本インターフェース
        base_interface = '''# -*- coding: utf-8 -*-
"""
EasyNovelAssistant モジュールインターフェース定義
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional


class EasyNovelModule(ABC):
    """すべてのモジュールの基底クラス"""
    
    def __init__(self, context):
        self.ctx = context
        self.logger = self._setup_logging()
    
    @abstractmethod
    def initialize(self) -> bool:
        """モジュールの初期化"""
        pass
    
    @abstractmethod
    def update(self):
        """モジュールの更新処理"""
        pass
    
    @abstractmethod
    def cleanup(self):
        """モジュールのクリーンアップ"""
        pass
    
    def _setup_logging(self):
        """ログ設定（サブクラスでオーバーライド可能）"""
        import logging
        return logging.getLogger(self.__class__.__name__)


class TextGenerator(EasyNovelModule):
    """テキスト生成インターフェース"""
    
    @abstractmethod
    def generate(self, prompt: str, **kwargs) -> str:
        """テキスト生成"""
        pass
    
    @abstractmethod
    def get_model_info(self) -> Dict[str, Any]:
        """モデル情報取得"""
        pass


class UIComponent(EasyNovelModule):
    """UIコンポーネントインターフェース"""
    
    @abstractmethod
    def render(self):
        """UIレンダリング"""
        pass
    
    @abstractmethod
    def handle_event(self, event: Any):
        """イベント処理"""
        pass


class OptimizationEngine(EasyNovelModule):
    """最適化エンジンインターフェース"""
    
    @abstractmethod
    def optimize(self, target: str, **params) -> Dict[str, Any]:
        """最適化実行"""
        pass
    
    @abstractmethod
    def get_performance_stats(self) -> Dict[str, Any]:
        """パフォーマンス統計取得"""
        pass
'''
        
        with open(interfaces_dir / "base_interfaces.py", 'w', encoding='utf-8') as f:
            f.write(base_interface)
        
        self.logger.info("モジュールインターフェース定義を生成しました")
        
    def create_unified_launcher(self):
        """統一起動スクリプトを作成"""
        launcher_content = '''# -*- coding: utf-8 -*-
"""
EasyNovelAssistant 統一起動スクリプト
最適化されたディレクトリ構造に対応
"""

import sys
import os
from pathlib import Path

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / "src"))

# 設定読み込み
def load_config():
    config_path = project_root / "config" / "consolidated_config.json"
    if config_path.exists():
        import json
        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    else:
        # フォールバック：従来の設定
        fallback_path = project_root / "config.json"
        if fallback_path.exists():
            import json
            with open(fallback_path, 'r', encoding='utf-8') as f:
                return {"config": json.load(f)}
    return {}

# メイン実行
if __name__ == "__main__":
    try:
        # 最適化モジュール読み込み
        from nkat.optimize_config import RTX3080Optimizer
        from nkat.nkat_integration import integrate_nkat_with_easy_novel_assistant
        
        # 従来のメイン処理
        from easy_novel_assistant import EasyNovelAssistant
        
        print("EasyNovelAssistant起動中（最適化版）...")
        
        # RTX 3080最適化適用
        optimizer = RTX3080Optimizer()
        optimization_result = optimizer.optimize_for_rtx3080()
        print(f"RTX 3080最適化完了: {optimization_result['expected_performance']['estimated_tokens_per_sec']} tokens/sec 予想")
        
        # アプリケーション起動
        app = EasyNovelAssistant()
        
        # NKAT統合（オプション）
        if hasattr(app.ctx, 'nkat_enabled') and app.ctx.nkat_enabled:
            integrate_nkat_with_easy_novel_assistant(app.ctx)
        
        app.run()
        
    except Exception as e:
        print(f"起動エラー: {e}")
        print("従来の起動方法にフォールバック...")
        
        # フォールバック起動
        try:
            from easy_novel_assistant import EasyNovelAssistant
            app = EasyNovelAssistant()
            app.run()
        except Exception as fallback_error:
            print(f"フォールバック起動もエラー: {fallback_error}")
            input("Enterキーで終了...")
'''
        
        launcher_path = self.project_root / "launch_optimized.py"
        with open(launcher_path, 'w', encoding='utf-8') as f:
            f.write(launcher_content)
            
        self.logger.info("統一起動スクリプトを作成しました")
        
    def validate_optimization(self) -> Dict[str, Any]:
        """最適化結果の検証"""
        validation = {
            "structure_compliance": False,
            "file_organization": False,
            "config_consolidation": False,
            "script_organization": False,
            "interface_definitions": False,
            "launcher_creation": False,
            "issues": [],
            "score": 0
        }
        
        # 構造準拠チェック
        required_dirs = ["src", "config", "data", "logs", "scripts", "docs"]
        existing_dirs = [d.name for d in self.project_root.iterdir() if d.is_dir()]
        
        if all(d in existing_dirs for d in required_dirs):
            validation["structure_compliance"] = True
        else:
            missing = [d for d in required_dirs if d not in existing_dirs]
            validation["issues"].append(f"不足ディレクトリ: {missing}")
        
        # ファイル整理チェック
        src_files = list((self.project_root / "src").rglob("*.py")) if (self.project_root / "src").exists() else []
        if len(src_files) > 5:
            validation["file_organization"] = True
        else:
            validation["issues"].append("ソースファイルが適切に整理されていません")
        
        # 設定統合チェック
        consolidated_config = self.project_root / "config" / "consolidated_config.json"
        if consolidated_config.exists():
            validation["config_consolidation"] = True
        else:
            validation["issues"].append("設定ファイルが統合されていません")
        
        # スコア計算
        total_checks = 6
        passed_checks = sum([
            validation["structure_compliance"],
            validation["file_organization"], 
            validation["config_consolidation"],
            validation["script_organization"],
            validation["interface_definitions"],
            validation["launcher_creation"]
        ])
        
        validation["score"] = int((passed_checks / total_checks) * 100)
        
        return validation


if __name__ == "__main__":
    # システム最適化のテスト実行
    optimizer = SystemOptimizer()
    
    print("=== EasyNovelAssistant システム構成最適化 ===")
    
    # 現在の構造分析
    analysis = optimizer.analyze_current_structure()
    print(f"\n分析結果:")
    print(f"  総ファイル数: {analysis['total_files']}")
    print(f"  Pythonファイル: {len(analysis['python_files'])}")
    print(f"  設定ファイル: {len(analysis['config_files'])}")
    print(f"  問題点: {len(analysis['issues'])}")
    
    if analysis['issues']:
        print("\n検出された問題:")
        for issue in analysis['issues']:
            print(f"  - {issue}")
    
    if analysis['recommendations']:
        print("\n推奨事項:")
        for rec in analysis['recommendations']:
            print(f"  - {rec}")
    
    # 最適化実行確認
    if input("\n最適化を実行しますか？ (y/N): ").lower() == 'y':
        if optimizer.create_optimized_structure():
            optimizer.generate_module_interfaces()
            optimizer.create_unified_launcher()
            
            # 検証
            validation = optimizer.validate_optimization()
            print(f"\n最適化完了! スコア: {validation['score']}/100")
            
            if validation['issues']:
                print("残った問題:")
                for issue in validation['issues']:
                    print(f"  - {issue}")
        else:
            print("最適化に失敗しました") 