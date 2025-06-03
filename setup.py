# -*- coding: utf-8 -*-
"""
EasyNovelAssistant v3.0 パッケージング設定
KoboldCpp + GGUF統合対応版
"""

from setuptools import setup, find_packages
import os
import sys

# バージョン情報
VERSION = "3.0.0"
DESCRIPTION = "Easy Novel Assistant - AI小説執筆支援システム"
LONG_DESCRIPTION = """
EasyNovelAssistant v3.0 - AI小説執筆支援システム

主要機能:
- KoboldCpp + GGUF統合
- 高度反復抑制システム v3 (90%成功率)
- NKAT理論統合システム
- リアルタイム協調制御
- メモリ効率化システム v3
- Style-Bert-VITS2音声合成統合
- 32K contextトークン対応

サポート形式:
- GGUF（Llama.cpp形式）
- KoboldCpp推論エンジン
- Style-Bert-VITS2音声合成
"""

# 必要パッケージ
REQUIREMENTS = [
    # Core dependencies
    "numpy>=1.21.0",
    "pandas>=1.3.0",
    "tqdm>=4.62.0",
    "requests>=2.26.0",
    
    # GUI dependencies
    "tkinter",
    "Pillow>=8.3.0",
    
    # Natural Language Processing
    "fugashi>=1.1.0",
    "unidic-lite>=1.0.8",
    "mecab-python3>=1.0.4",
    
    # Machine Learning (optional)
    "torch>=1.9.0",
    "transformers>=4.11.0",
    
    # Audio processing (for TTS)
    "librosa>=0.8.0",
    "soundfile>=0.10.0",
    
    # Development dependencies
    "pytest>=6.2.0",
    "black>=21.7.0",
    "flake8>=3.9.0",
    "mypy>=0.910",
    
    # Optimization dependencies
    "psutil>=5.8.0",
    "memory-profiler>=0.58.0",
    
    # Packaging dependencies
    "pyinstaller>=5.0.0",
    "cx-freeze>=6.0",
]

# データファイル（KoboldCpp, GGUF, etc.）
def get_data_files():
    """パッケージに含めるデータファイルを取得"""
    data_files = []
    
    # KoboldCppディレクトリ
    kobold_files = []
    kobold_dir = "KoboldCpp"
    
    if os.path.exists(kobold_dir):
        for root, dirs, files in os.walk(kobold_dir):
            for file in files:
                if file.endswith(('.exe', '.dll', '.bat', '.gguf')):
                    file_path = os.path.join(root, file)
                    kobold_files.append(file_path)
    
    if kobold_files:
        data_files.append(("KoboldCpp", kobold_files))
    
    # 設定ファイル
    config_files = []
    for file in ['config.json', 'llm.json', 'llm_sequence.json']:
        if os.path.exists(file):
            config_files.append(file)
    
    if config_files:
        data_files.append((".", config_files))
    
    # リソースディレクトリ
    for dir_name in ['config', 'data', 'templates', 'logs']:
        if os.path.exists(dir_name):
            for root, dirs, files in os.walk(dir_name):
                if files:
                    rel_path = os.path.relpath(root, '.')
                    dir_files = [os.path.join(root, f) for f in files]
                    data_files.append((rel_path, dir_files))
    
    return data_files

# setuptools設定
setup(
    name="EasyNovelAssistant",
    version=VERSION,
    description=DESCRIPTION,
    long_description=LONG_DESCRIPTION,
    long_description_content_type="text/plain",
    author="EasyNovelAssistant Team",
    author_email="support@easynovelassistant.com",
    url="https://github.com/EasyNovelAssistant/EasyNovelAssistant",
    
    # パッケージ情報
    packages=find_packages(),
    include_package_data=True,
    data_files=get_data_files(),
    
    # 実行ファイル
    entry_points={
        'console_scripts': [
            'easy-novel-assistant=easy_novel_assistant:main',
        ],
        'gui_scripts': [
            'easy-novel-assistant-gui=easy_novel_assistant:main',
        ]
    },
    
    # 依存関係
    install_requires=REQUIREMENTS,
    python_requires=">=3.8",
    
    # 分類
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: End Users/Desktop",
        "Topic :: Text Processing :: Linguistic",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Operating System :: Microsoft :: Windows",
        "Operating System :: MacOS",
        "Operating System :: POSIX :: Linux",
    ],
    
    # キーワード
    keywords="AI, novel writing, japanese nlp, koboldcpp, gguf, text generation",
    
    # プロジェクト情報
    project_urls={
        "Documentation": "https://github.com/EasyNovelAssistant/EasyNovelAssistant/wiki",
        "Source": "https://github.com/EasyNovelAssistant/EasyNovelAssistant",
        "Tracker": "https://github.com/EasyNovelAssistant/EasyNovelAssistant/issues",
    },
    
    # ZIP形式で配布しない
    zip_safe=False,
) 