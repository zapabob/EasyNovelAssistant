import json
import os

from path import Path


class Context:
    def __init__(self):
        self.cfg = None
        self.llm = None
        self.llm_sequence = None
        self._load_config()

    def _load_config(self):
        # 設定ファイルの読み込み
        self.cfg = {}
        if not os.path.exists(Path.default_config):
            print(f"⚠️ デフォルト設定ファイルが見つかりません: {Path.default_config}")
            # 最低限の設定を作成
            self.cfg = self._create_minimal_config()
        else:
            try:
                with open(Path.default_config, "r", encoding="utf-8-sig") as f:
                    self.cfg = json.load(f)
            except Exception as e:
                print(f"⚠️ デフォルト設定ファイル読み込みエラー: {e}")
                self.cfg = self._create_minimal_config()
        
        if os.path.exists(Path.config):
            try:
                with open(Path.config, "r", encoding="utf-8-sig") as f:
                    self.cfg.update(json.load(f))
            except Exception as e:
                print(f"⚠️ 設定ファイル読み込みエラー: {e}")
        else:
            try:
                with open(Path.config, "w", encoding="utf-8-sig") as f:
                    json.dump(self.cfg, f, indent=4, ensure_ascii=False)
            except Exception as e:
                print(f"⚠️ 設定ファイル作成エラー: {e}")

        # LLM設定の読み込み
        self.llm = {}
        if not os.path.exists(Path.default_llm):
            print(f"⚠️ デフォルトLLM設定ファイルが見つかりません: {Path.default_llm}")
            self.llm = self._create_minimal_llm()
        else:
            try:
                with open(Path.default_llm, "r", encoding="utf-8-sig") as f:
                    self.llm = json.load(f)
            except Exception as e:
                print(f"⚠️ デフォルトLLM設定ファイル読み込みエラー: {e}")
                self.llm = self._create_minimal_llm()
        
        if os.path.exists(Path.llm):
            try:
                with open(Path.llm, "r", encoding="utf-8-sig") as f:
                    self.llm.update(json.load(f))
            except Exception as e:
                print(f"⚠️ LLM設定ファイル読み込みエラー: {e}")
        else:
            try:
                with open(Path.llm, "w", encoding="utf-8-sig") as f:
                    f.write("{}")
            except Exception as e:
                print(f"⚠️ LLM設定ファイル作成エラー: {e}")

        # LLMシーケンス設定の読み込み
        self.llm_sequence = {}
        if not os.path.exists(Path.default_llm_sequence):
            print(f"⚠️ デフォルトLLMシーケンス設定ファイルが見つかりません: {Path.default_llm_sequence}")
            self.llm_sequence = self._create_minimal_llm_sequence()
        else:
            try:
                with open(Path.default_llm_sequence, "r", encoding="utf-8-sig") as f:
                    self.llm_sequence = json.load(f)
            except Exception as e:
                print(f"⚠️ デフォルトLLMシーケンス設定ファイル読み込みエラー: {e}")
                self.llm_sequence = self._create_minimal_llm_sequence()
        
        if os.path.exists(Path.llm_sequence):
            try:
                with open(Path.llm_sequence, "r", encoding="utf-8-sig") as f:
                    self.llm_sequence.update(json.load(f))
            except Exception as e:
                print(f"⚠️ LLMシーケンス設定ファイル読み込みエラー: {e}")
        else:
            try:
                with open(Path.llm_sequence, "w", encoding="utf-8-sig") as f:
                    f.write("{}")
            except Exception as e:
                print(f"⚠️ LLMシーケンス設定ファイル作成エラー: {e}")

    def _create_minimal_config(self):
        """最低限の設定を作成"""
        return {
            "input_text": "",
            "llm_name": "[元祖] LightChatAssistant-TypeB-2x7B-IQ4_XS",
            "llm_gpu_layer": 0,
            "llm_context_size": 4096,
            "max_length": 128,
            "temperature": 0.7,
            "top_p": 0.9,
            "rep_pen": 1.1,
            "rep_pen_range": 512,
            "rep_pen_slope": 0.7,
            "tfs": 1.0,
            "top_a": 0.0,
            "top_k": 40,
            "typical": 1.0,
            "min_p": 0.0,
            "sampler_order": [6, 0, 1, 3, 4, 2, 5],
            "koboldcpp_arg": "",
            "koboldcpp_command_timeout": 10
        }

    def _create_minimal_llm(self):
        """最低限のLLM設定を作成"""
        return {
            "[元祖] LightChatAssistant-TypeB-2x7B-IQ4_XS": {
                "context_size": 4096,
                "file_name": "LightChatAssistant-TypeB-2x7B-IQ4_XS.gguf",
                "urls": [],
                "info_url": "",
                "name": "LightChatAssistant-TypeB-2x7B-IQ4_XS"
            }
        }

    def _create_minimal_llm_sequence(self):
        """最低限のLLMシーケンス設定を作成"""
        return {
            "default": {
                "model_names": ["LightChatAssistant"],
                "instruct": {
                    "input_prefix": "",
                    "input_suffix": "",
                    "output_prefix": "",
                    "output_suffix": ""
                },
                "stop": []
            }
        }

    def __getitem__(self, item):
        return self.cfg.get(item, None)

    def __setitem__(self, key, value):
        self.cfg[key] = value

    def get(self, key, default=None):
        """辞書のget()メソッドと同じ機能を提供"""
        return self.cfg.get(key, default)

    def finalize(self):
        if not self.form.file_menu.ask_save():  # TODO: すべて閉じる
            return
        self.form.update_config()

        with open(Path.config, "w", encoding="utf-8-sig") as f:
            json.dump(self.cfg, f, indent=4, ensure_ascii=False)

        self.form.win.destroy()

        if self.generator.enabled:
            self.kobold_cpp.abort()
