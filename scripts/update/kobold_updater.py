#!/usr/bin/env python3
"""
KoboldCpp自動更新システム
最新版を確認し、必要に応じて差分更新を実行する
"""

import os
import sys
import json
import requests
import subprocess
import hashlib
import zipfile
import tempfile
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional
import logging
from packaging import version
import shutil

# プロジェクトルートを設定
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

class KoboldCppUpdater:
    """KoboldCpp自動更新管理クラス"""
    
    def __init__(self, kobold_dir: Path = None):
        """
        初期化
        
        Args:
            kobold_dir: KoboldCppディレクトリパス
        """
        self.logger = self._setup_logger()
        self.kobold_dir = kobold_dir or (project_root / "KoboldCpp")
        self.config_file = project_root / "config" / "kobold_config.json"
        self.update_log = project_root / "logs" / "kobold_updates.json"
        
        # GitHub API設定
        self.github_api_url = "https://api.github.com/repos/LostRuins/koboldcpp"
        self.github_releases_url = f"{self.github_api_url}/releases"
        
        # 現在のバージョン情報
        self.current_version = None
        self.current_hash = None
        
        self._ensure_directories()
        self._load_current_info()
    
    def _setup_logger(self) -> logging.Logger:
        """ログ設定"""
        logger = logging.getLogger('KoboldUpdater')
        logger.setLevel(logging.INFO)
        
        # ログディレクトリ作成
        log_dir = project_root / "logs" / "system_optimizer"
        log_dir.mkdir(parents=True, exist_ok=True)
        
        # ハンドラー設定
        handler = logging.FileHandler(
            log_dir / f"kobold_updater_{datetime.now().strftime('%Y%m%d')}.log",
            encoding='utf-8'
        )
        formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        
        # コンソール出力
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
        
        return logger
    
    def _ensure_directories(self):
        """必要なディレクトリを作成"""
        directories = [
            self.kobold_dir,
            self.config_file.parent,
            self.update_log.parent
        ]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
    
    def _load_current_info(self):
        """現在のバージョン情報を読み込み"""
        try:
            # バージョンファイルを確認
            version_file = self.kobold_dir / "version.txt"
            if version_file.exists():
                self.current_version = version_file.read_text(encoding='utf-8').strip()
            
            # 実行ファイルのハッシュを計算
            exe_file = self.kobold_dir / "koboldcpp.exe"
            if exe_file.exists():
                self.current_hash = self._calculate_hash(exe_file)
            
            self.logger.info(f"現在のバージョン: {self.current_version}")
            self.logger.info(f"現在のハッシュ: {self.current_hash}")
            
        except Exception as e:
            self.logger.warning(f"現在のバージョン情報読み込みエラー: {e}")
    
    def _calculate_hash(self, file_path: Path) -> str:
        """ファイルのSHA256ハッシュを計算"""
        hash_sha256 = hashlib.sha256()
        try:
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_sha256.update(chunk)
            return hash_sha256.hexdigest()
        except Exception as e:
            self.logger.error(f"ハッシュ計算エラー: {e}")
            return ""
    
    def check_latest_version(self) -> Dict:
        """最新バージョンを確認"""
        try:
            self.logger.info("最新バージョンを確認中...")
            
            # GitHub APIから最新リリース情報を取得
            response = requests.get(
                f"{self.github_releases_url}/latest",
                timeout=30
            )
            response.raise_for_status()
            
            release_data = response.json()
            
            latest_info = {
                'version': release_data['tag_name'],
                'name': release_data['name'],
                'published_at': release_data['published_at'],
                'download_url': None,
                'assets': []
            }
            
            # アセット情報を取得
            for asset in release_data['assets']:
                asset_info = {
                    'name': asset['name'],
                    'size': asset['size'],
                    'download_url': asset['browser_download_url']
                }
                latest_info['assets'].append(asset_info)
                
                # Windows用実行ファイルを優先選択
                if asset['name'] == 'koboldcpp.exe':
                    latest_info['download_url'] = asset['browser_download_url']
            
            self.logger.info(f"最新バージョン: {latest_info['version']}")
            return latest_info
            
        except Exception as e:
            self.logger.error(f"最新バージョン確認エラー: {e}")
            return {}
    
    def is_update_needed(self, latest_info: Dict) -> bool:
        """更新が必要かチェック"""
        if not latest_info or not latest_info.get('version'):
            return False
        
        # バージョン比較
        if self.current_version:
            try:
                current_ver = version.parse(self.current_version.lstrip('v'))
                latest_ver = version.parse(latest_info['version'].lstrip('v'))
                
                if latest_ver > current_ver:
                    self.logger.info(f"新しいバージョンが利用可能: {latest_info['version']}")
                    return True
                else:
                    self.logger.info("最新バージョンです")
                    return False
            except Exception as e:
                self.logger.warning(f"バージョン比較エラー: {e}")
        
        # ファイルが存在しない場合は更新が必要
        exe_file = self.kobold_dir / "koboldcpp.exe"
        if not exe_file.exists():
            self.logger.info("実行ファイルが存在しないため更新が必要")
            return True
        
        return False
    
    def download_update(self, latest_info: Dict) -> bool:
        """更新ファイルをダウンロード"""
        if not latest_info.get('download_url'):
            self.logger.error("ダウンロードURLが見つかりません")
            return False
        
        try:
            url = latest_info['download_url']
            self.logger.info(f"ダウンロード開始: {url}")
            
            # 一時ファイルにダウンロード
            with tempfile.NamedTemporaryFile(delete=False, suffix='.exe') as temp_file:
                response = requests.get(url, stream=True, timeout=300)
                response.raise_for_status()
                
                total_size = int(response.headers.get('content-length', 0))
                downloaded = 0
                
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        temp_file.write(chunk)
                        downloaded += len(chunk)
                        
                        if total_size > 0:
                            progress = (downloaded / total_size) * 100
                            if downloaded % (1024 * 1024) == 0:  # 1MBごとに進捗表示
                                self.logger.info(f"ダウンロード進捗: {progress:.1f}%")
                
                temp_file_path = temp_file.name
            
            # ダウンロード完了
            self.logger.info("ダウンロード完了")
            
            # ファイルの検証
            if not self._verify_download(temp_file_path):
                os.unlink(temp_file_path)
                return False
            
            # バックアップと更新
            return self._apply_update(temp_file_path, latest_info['version'])
            
        except Exception as e:
            self.logger.error(f"ダウンロードエラー: {e}")
            return False
    
    def _verify_download(self, file_path: str) -> bool:
        """ダウンロードファイルの検証"""
        try:
            # ファイルサイズチェック
            file_size = os.path.getsize(file_path)
            if file_size < 1024 * 1024:  # 1MB未満は異常
                self.logger.error("ダウンロードファイルサイズが異常です")
                return False
            
            # 実行ファイルかチェック（簡易）
            with open(file_path, 'rb') as f:
                header = f.read(2)
                if header != b'MZ':  # DOS/Windowsヘッダー
                    self.logger.error("無効な実行ファイル形式")
                    return False
            
            self.logger.info("ダウンロードファイル検証OK")
            return True
            
        except Exception as e:
            self.logger.error(f"ファイル検証エラー: {e}")
            return False
    
    def _apply_update(self, new_file_path: str, new_version: str) -> bool:
        """更新を適用"""
        try:
            exe_file = self.kobold_dir / "koboldcpp.exe"
            backup_file = self.kobold_dir / f"koboldcpp_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.exe"
            
            # 現在のファイルをバックアップ
            if exe_file.exists():
                shutil.copy2(exe_file, backup_file)
                self.logger.info(f"バックアップ作成: {backup_file.name}")
            
            # 新しいファイルをコピー
            shutil.copy2(new_file_path, exe_file)
            
            # バージョンファイル更新
            version_file = self.kobold_dir / "version.txt"
            version_file.write_text(new_version, encoding='utf-8')
            
            # 一時ファイル削除
            os.unlink(new_file_path)
            
            # 更新ログ記録
            self._log_update(new_version)
            
            self.logger.info(f"更新完了: {new_version}")
            return True
            
        except Exception as e:
            self.logger.error(f"更新適用エラー: {e}")
            return False
    
    def _log_update(self, new_version: str):
        """更新ログを記録"""
        try:
            update_record = {
                'timestamp': datetime.now().isoformat(),
                'from_version': self.current_version,
                'to_version': new_version,
                'success': True
            }
            
            # 既存ログ読み込み
            if self.update_log.exists():
                try:
                    with open(self.update_log, 'r', encoding='utf-8') as f:
                        logs = json.load(f)
                except:
                    logs = []
            else:
                logs = []
            
            logs.append(update_record)
            
            # 最新10件まで保持
            logs = logs[-10:]
            
            # ログファイル書き込み
            with open(self.update_log, 'w', encoding='utf-8') as f:
                json.dump(logs, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            self.logger.warning(f"更新ログ記録エラー: {e}")
    
    def cleanup_old_backups(self, keep_count: int = 5):
        """古いバックアップファイルを削除"""
        try:
            backup_pattern = "koboldcpp_backup_*.exe"
            backup_files = list(self.kobold_dir.glob(backup_pattern))
            
            if len(backup_files) > keep_count:
                # 作成日時でソート
                backup_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
                
                # 古いファイルを削除
                for old_backup in backup_files[keep_count:]:
                    old_backup.unlink()
                    self.logger.info(f"古いバックアップ削除: {old_backup.name}")
                    
        except Exception as e:
            self.logger.warning(f"バックアップクリーンアップエラー: {e}")
    
    def update_if_needed(self) -> bool:
        """必要に応じて更新を実行"""
        try:
            # 最新バージョン確認
            latest_info = self.check_latest_version()
            if not latest_info:
                return False
            
            # 更新判定
            if not self.is_update_needed(latest_info):
                return True  # 更新不要（成功扱い）
            
            # 更新実行
            if self.download_update(latest_info):
                self.cleanup_old_backups()
                return True
            else:
                return False
                
        except Exception as e:
            self.logger.error(f"更新プロセスエラー: {e}")
            return False

def main():
    """メイン関数"""
    updater = KoboldCppUpdater()
    
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command == 'check':
            # バージョン確認のみ
            latest_info = updater.check_latest_version()
            if latest_info:
                print(f"最新バージョン: {latest_info['version']}")
                print(f"現在のバージョン: {updater.current_version or 'unknown'}")
                if updater.is_update_needed(latest_info):
                    print("更新が利用可能です")
                else:
                    print("最新バージョンです")
            
        elif command == 'update':
            # 強制更新
            latest_info = updater.check_latest_version()
            if latest_info and latest_info.get('download_url'):
                success = updater.download_update(latest_info)
                if success:
                    print("更新が完了しました")
                    updater.cleanup_old_backups()
                else:
                    print("更新に失敗しました")
            else:
                print("更新可能なバージョンが見つかりません")
        
        elif command == 'auto':
            # 自動更新（必要時のみ）
            success = updater.update_if_needed()
            if success:
                print("更新チェック完了")
            else:
                print("更新に問題が発生しました")
        
        else:
            print(f"不明なコマンド: {command}")
            print("使用可能コマンド: check, update, auto")
    
    else:
        # デフォルトは自動更新
        success = updater.update_if_needed()
        return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main()) 