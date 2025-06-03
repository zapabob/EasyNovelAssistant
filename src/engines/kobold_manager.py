#!/usr/bin/env python3
"""
KoboldCppエンジン管理システム
EasyNovelAssistantからKoboldCppを統合管理する
"""

import os
import sys
import json
import subprocess
import threading
import time
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import logging

# プロジェクトルートを設定
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# 自作モジュールのインポート
try:
    from scripts.update.kobold_updater import KoboldCppUpdater
except ImportError:
    KoboldCppUpdater = None

class KoboldCppManager:
    """KoboldCppエンジン統合管理クラス"""
    
    def __init__(self, config_path: str = None):
        """
        初期化
        
        Args:
            config_path: 設定ファイルパス
        """
        self.logger = self._setup_logger()
        self.config_path = config_path or str(project_root / "config" / "kobold_config.json")
        self.config = self._load_config()
        
        # KoboldCpp関連パス
        self.kobold_dir = project_root / self.config['paths']['kobold_directory']
        self.kobold_exe = self.kobold_dir / "koboldcpp.exe"
        
        # プロセス管理
        self.kobold_process = None
        self.is_running = False
        self.auto_updater = None
        
        # 更新システム初期化
        if KoboldCppUpdater:
            self.updater = KoboldCppUpdater(self.kobold_dir)
        else:
            self.updater = None
            self.logger.warning("KoboldCppUpdater not available")
        
        # 自動更新スレッド
        self.update_thread = None
        self.stop_update_thread = False
        
        self._ensure_directories()
    
    def _setup_logger(self) -> logging.Logger:
        """ログ設定"""
        logger = logging.getLogger('KoboldManager')
        logger.setLevel(logging.INFO)
        
        # ログディレクトリ作成
        log_dir = project_root / "logs" / "engines"
        log_dir.mkdir(parents=True, exist_ok=True)
        
        # ハンドラー設定
        handler = logging.FileHandler(
            log_dir / f"kobold_manager_{datetime.now().strftime('%Y%m%d')}.log",
            encoding='utf-8'
        )
        formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        
        return logger
    
    def _load_config(self) -> Dict:
        """設定ファイル読み込み"""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            self.logger.warning(f"設定ファイル読み込みエラー: {e}")
            return self._get_default_config()
    
    def _get_default_config(self) -> Dict:
        """デフォルト設定"""
        return {
            "kobold_settings": {
                "auto_update": True,
                "update_check_interval": "daily",
                "backup_count": 5,
                "download_timeout": 300,
                "verify_downloads": True,
                "use_prerelease": False
            },
            "paths": {
                "kobold_directory": "KoboldCpp",
                "backup_directory": "KoboldCpp/backups",
                "log_directory": "logs",
                "temp_directory": "temp"
            },
            "notifications": {
                "enabled": True,
                "update_available": True,
                "update_complete": True,
                "update_failed": True
            }
        }
    
    def _save_config(self):
        """設定ファイル保存"""
        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
        except Exception as e:
            self.logger.error(f"設定ファイル保存エラー: {e}")
    
    def _ensure_directories(self):
        """必要なディレクトリを作成"""
        directories = [
            self.kobold_dir,
            self.kobold_dir / "backups",
            project_root / self.config['paths']['log_directory'],
            project_root / self.config['paths']['temp_directory']
        ]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
    
    def check_installation(self) -> bool:
        """KoboldCppがインストール済みかチェック"""
        return self.kobold_exe.exists()
    
    def get_current_version(self) -> Optional[str]:
        """現在のバージョンを取得"""
        try:
            version_file = self.kobold_dir / "version.txt"
            if version_file.exists():
                return version_file.read_text(encoding='utf-8').strip()
            return None
        except Exception as e:
            self.logger.error(f"バージョン取得エラー: {e}")
            return None
    
    def install_or_update(self, force_update: bool = False) -> bool:
        """KoboldCppをインストールまたは更新"""
        if not self.updater:
            self.logger.error("更新システムが利用できません")
            return False
        
        try:
            self.logger.info("KoboldCpp更新チェックを開始")
            
            if force_update:
                # 強制更新
                latest_info = self.updater.check_latest_version()
                if latest_info and latest_info.get('download_url'):
                    success = self.updater.download_update(latest_info)
                    if success:
                        self.logger.info("KoboldCpp更新完了")
                        self._update_config_version(latest_info['version'])
                        return True
                else:
                    self.logger.error("更新可能なバージョンが見つかりません")
                    return False
            else:
                # 必要時のみ更新
                success = self.updater.update_if_needed()
                if success:
                    latest_info = self.updater.check_latest_version()
                    if latest_info:
                        self._update_config_version(latest_info['version'])
                    return True
                
        except Exception as e:
            self.logger.error(f"インストール/更新エラー: {e}")
            return False
        
        return False
    
    def _update_config_version(self, version: str):
        """設定ファイルのバージョン情報を更新"""
        self.config['version_info']['current_version'] = version
        self.config['version_info']['last_update'] = datetime.now().isoformat()
        self._save_config()
    
    def start_kobold(self, args: List[str] = None) -> bool:
        """KoboldCppを起動"""
        if self.is_running:
            self.logger.warning("KoboldCppは既に実行中です")
            return True
        
        if not self.check_installation():
            self.logger.error("KoboldCppがインストールされていません")
            return False
        
        try:
            cmd = [str(self.kobold_exe)]
            if args:
                cmd.extend(args)
            
            self.logger.info(f"KoboldCpp起動: {' '.join(cmd)}")
            
            # プロセス起動
            self.kobold_process = subprocess.Popen(
                cmd,
                cwd=str(self.kobold_dir),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding='utf-8'
            )
            
            self.is_running = True
            self.logger.info("KoboldCpp起動完了")
            
            # 出力監視スレッド開始
            self._start_output_monitor()
            
            return True
            
        except Exception as e:
            self.logger.error(f"KoboldCpp起動エラー: {e}")
            return False
    
    def stop_kobold(self) -> bool:
        """KoboldCppを停止"""
        if not self.is_running or not self.kobold_process:
            self.logger.warning("KoboldCppは実行されていません")
            return True
        
        try:
            self.logger.info("KoboldCpp停止中...")
            
            # プロセス終了
            self.kobold_process.terminate()
            
            # 5秒待機
            try:
                self.kobold_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                # 強制終了
                self.kobold_process.kill()
                self.kobold_process.wait()
            
            self.is_running = False
            self.kobold_process = None
            self.logger.info("KoboldCpp停止完了")
            
            return True
            
        except Exception as e:
            self.logger.error(f"KoboldCpp停止エラー: {e}")
            return False
    
    def _start_output_monitor(self):
        """出力監視スレッドを開始"""
        def monitor_output():
            if not self.kobold_process:
                return
            
            try:
                for line in iter(self.kobold_process.stdout.readline, ''):
                    if line:
                        self.logger.info(f"KoboldCpp出力: {line.strip()}")
                    
                    # プロセス終了チェック
                    if self.kobold_process.poll() is not None:
                        break
                
                # プロセス終了処理
                self.is_running = False
                return_code = self.kobold_process.returncode
                self.logger.info(f"KoboldCppプロセス終了 (終了コード: {return_code})")
                
            except Exception as e:
                self.logger.error(f"出力監視エラー: {e}")
        
        # 監視スレッド開始
        monitor_thread = threading.Thread(target=monitor_output, daemon=True)
        monitor_thread.start()
    
    def get_status(self) -> Dict:
        """現在の状態を取得"""
        return {
            'is_installed': self.check_installation(),
            'is_running': self.is_running,
            'current_version': self.get_current_version(),
            'last_update': self.config.get('version_info', {}).get('last_update'),
            'auto_update_enabled': self.config.get('kobold_settings', {}).get('auto_update', False)
        }
    
    def start_auto_update_monitor(self):
        """自動更新監視を開始"""
        if not self.config.get('kobold_settings', {}).get('auto_update', False):
            self.logger.info("自動更新は無効です")
            return
        
        if self.update_thread and self.update_thread.is_alive():
            self.logger.warning("自動更新監視は既に実行中です")
            return
        
        def update_monitor():
            self.logger.info("自動更新監視開始")
            interval = self.config.get('kobold_settings', {}).get('update_check_interval', 'daily')
            
            # 間隔設定
            if interval == 'daily':
                check_interval = 24 * 3600  # 24時間
            elif interval == 'weekly':
                check_interval = 7 * 24 * 3600  # 1週間
            else:
                check_interval = 24 * 3600  # デフォルト：24時間
            
            while not self.stop_update_thread:
                try:
                    # 更新チェック実行
                    if self.updater:
                        latest_info = self.updater.check_latest_version()
                        if latest_info and self.updater.is_update_needed(latest_info):
                            self.logger.info("新しいバージョンが利用可能です")
                            
                            # 実行中でない場合のみ更新
                            if not self.is_running:
                                self.install_or_update()
                            else:
                                self.logger.info("KoboldCpp実行中のため、更新を延期します")
                    
                    # 指定間隔待機
                    for _ in range(check_interval):
                        if self.stop_update_thread:
                            break
                        time.sleep(1)
                        
                except Exception as e:
                    self.logger.error(f"自動更新監視エラー: {e}")
                    time.sleep(3600)  # エラー時は1時間待機
            
            self.logger.info("自動更新監視終了")
        
        self.stop_update_thread = False
        self.update_thread = threading.Thread(target=update_monitor, daemon=True)
        self.update_thread.start()
    
    def stop_auto_update_monitor(self):
        """自動更新監視を停止"""
        self.stop_update_thread = True
        if self.update_thread and self.update_thread.is_alive():
            self.update_thread.join(timeout=5)
        self.logger.info("自動更新監視停止完了")
    
    def cleanup(self):
        """クリーンアップ"""
        self.stop_auto_update_monitor()
        if self.is_running:
            self.stop_kobold()

def main():
    """テスト用メイン関数"""
    manager = KoboldCppManager()
    
    # 状態確認
    status = manager.get_status()
    print(f"KoboldCpp状態: {status}")
    
    # インストール確認
    if not status['is_installed']:
        print("KoboldCppをインストール中...")
        if manager.install_or_update():
            print("インストール完了")
        else:
            print("インストール失敗")
            return
    
    # 更新チェック
    print("更新チェック中...")
    if manager.install_or_update():
        print("更新チェック完了")
    
    # 自動更新監視開始
    print("自動更新監視開始")
    manager.start_auto_update_monitor()
    
    try:
        # 1分間監視
        time.sleep(60)
    except KeyboardInterrupt:
        pass
    finally:
        manager.cleanup()
        print("管理システム終了")

if __name__ == "__main__":
    main() 