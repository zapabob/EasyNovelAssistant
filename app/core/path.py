﻿import os
import re
import time
import sys


class Path:
    path_regex = re.compile(r'[\n\r<>:"/\\|?* ]')

    # EXE化対応: 実行ファイルの場所を基準にパスを設定
    if hasattr(sys, '_MEIPASS'):  # PyInstaller環境
        # EXE実行時は一時ディレクトリから実行される
        exe_dir = os.path.dirname(sys.executable)
        cwd = exe_dir
        # PyInstallerのバンドルディレクトリ
        bundle_dir = sys._MEIPASS
        app = os.path.join(bundle_dir, "EasyNovelAssistant")
    else:
        # 通常のPython実行環境
        cwd = os.getcwd()
        app = os.path.join(cwd, "EasyNovelAssistant")

    config = os.path.join(cwd, "config.json")
    llm = os.path.join(cwd, "llm.json")
    llm_sequence = os.path.join(cwd, "llm_sequence.json")

    # 実際のビルドディレクトリのパス
    build = os.path.join(cwd, "build")
    res = os.path.join(build, "res")
    default_config = os.path.join(res, "default_config.json")
    default_llm = os.path.join(res, "default_llm.json")
    default_llm_sequence = os.path.join(res, "default_llm_sequence.json")

    # KoboldCppのパス（external/に移動、EXE実行時も考慮）
    if hasattr(sys, '_MEIPASS'):  # PyInstaller環境
        # EXE実行時はEXEと同じディレクトリのKoboldCppを参照
        kobold_cpp = os.path.join(cwd, "external", "KoboldCpp")
    else:
        kobold_cpp = os.path.join(cwd, "external", "KoboldCpp")
    
    kobold_cpp_win = os.path.join(kobold_cpp, "koboldcpp.exe")
    kobold_cpp_linux = os.path.join(kobold_cpp, "koboldcpp-linux-x64-cuda1150")

    style_bert_vits2 = os.path.join(cwd, "external", "Style-Bert-VITS2")
    style_bert_vits2_config = os.path.join(style_bert_vits2, "config.yml")
    style_bert_vits2_setup = os.path.join(build, "Setup-Style-Bert-VITS2.bat")
    style_bert_vits2_run = os.path.join(build, "Run-Style-Bert-VITS2.bat")
    style_bert_vits2_app = os.path.join(style_bert_vits2, "App.bat")
    style_bert_vits2_editor = os.path.join(style_bert_vits2, "Editor.bat")

    sample = os.path.join(cwd, "sample")

    YYYYMMDD = time.strftime("%Y%m%d", time.localtime())

    log = os.path.join(cwd, "log")
    daily_log = os.path.join(log, YYYYMMDD)
    os.makedirs(daily_log, exist_ok=True)

    YYYYMMDD_HHMMSS = time.strftime("%Y%m%d_%H%M%S", time.localtime())
    generate_log = os.path.join(daily_log, f"{YYYYMMDD_HHMMSS}-generate.txt")
    output_log = os.path.join(daily_log, f"{YYYYMMDD_HHMMSS}-output.txt")

    speech = os.path.join(cwd, "speech")
    daily_speech = os.path.join(speech, YYYYMMDD)

    movie = os.path.join(cwd, "movie")
    os.makedirs(movie, exist_ok=True)
    venv = os.path.join(cwd, "venv")
    scripts = os.path.join(venv, "Scripts")
    ffmpeg = os.path.join(scripts, "ffmpeg.exe")
    ffplay = os.path.join(scripts, "ffplay.exe")

    @classmethod
    def init(cls, ctx):
        pass

    @classmethod
    def get_path_name(cls, name):
        return cls.path_regex.sub("_", name.strip()).replace("___", "_").replace("__", "_")
