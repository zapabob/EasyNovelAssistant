import time

from job_queue import JobQueue
from PySide6.QtWidgets import QDialog, QVBoxLayout, QComboBox, QLineEdit, QPushButton, QLabel


class Generator:
    def __init__(self, ctx):
        self.ctx = ctx
        
        self.gen_queue = JobQueue()
        self.check_queue = JobQueue()
        
        self.enabled = False
        self.generate_job = None
        self.check_job = None
        
        self.pre_check_time = time.perf_counter()
        self.gen_area_text = ""
        self.last_line = ""
        self.last_chat_prompt = None
        
        self.gen_queue.push(self.initial_launch)

    def initial_launch(self):
        model_name = self.ctx.kobold_cpp.get_model()
        if model_name is None:
            result = self.ctx.kobold_cpp.launch_server()
            if result is not None:
                print(result)
        else:
            self.enabled = True
            self.ctx.form.update_title()

    def update(self):
        if self.enabled:
            if self.generate_job is None:
                input_text = self.ctx.form.input_area.get_prompt_text()
                if input_text != "":
                    self.generate_job = self.gen_queue.push(self._generate, input_text=input_text)
            elif self.generate_job.successful():
                result = self.generate_job.result
                if result is None:
                    if self.ctx.kobold_cpp.abort() is None:
                        self.enabled = False
                        self.ctx.form.update_title()
                else:
                    # チャットモードでの応答処理を確実に行う
                    if self.ctx.get("chat_mode", False) and hasattr(self.ctx, 'chat_mode'):
                        self.ctx.chat_mode.add_message('assistant', result)
                        chat_history = self.ctx.chat_mode.get_formatted_history()
                        self.ctx.form.output_area.set_text(chat_history)
                        self.ctx.form.input_area.clear_current()  # 入力欄をクリア
                    else:
                        # 通常のノベルモード処理
                        result = self._get_last_line(self.generate_job.args["input_text"]) + result
                        self.ctx.form.output_area.append_output(result)
                self.generate_job = None
            elif self.generate_job.canceled():
                self.generate_job = None

            if self.check_job is None:
                now_time = time.perf_counter()
                if now_time - self.pre_check_time > self.ctx["check_interval"]:
                    self.check_job = self.check_queue.push(self._check)
                    self.pre_check_time = now_time
            elif self.check_job.successful():
                result = self.check_job.result
                if result is not None:
                    if self.generate_job is not None:
                        result = self._get_last_line(self.generate_job.args["input_text"]) + result
                    if result != self.gen_area_text:
                        if result.startswith(self.gen_area_text):
                            append_text = result[len(self.gen_area_text):]
                            
                            lines = (self.last_line + append_text).splitlines()
                            if len(lines) > 0:
                                for line in lines[:-1]:
                                    self._auto_speech(line)
                                self.last_line = lines[-1]
                                if append_text.endswith("\n"):
                                    self._auto_speech(self.last_line)
                                    self.last_line = ""
                            self.ctx.form.gen_area.append_text(append_text)
                        else:
                            lines = result.splitlines()
                            if len(lines) > 0:
                                for line in lines[:-1]:
                                    self._auto_speech(line)
                                self.last_line = lines[-1]
                                if result.endswith("\n"):
                                    self._auto_speech(self.last_line)
                                    self.last_line = ""
                            else:
                                self.last_line = ""
                            self.ctx.form.gen_area.set_text(result)
                        self.gen_area_text = result
                self.check_job = None
            elif self.check_job.canceled():
                self.check_job = None
        else:
            if self.generate_job is not None:
                self.ctx.kobold_cpp.abort()
                self.gen_queue.cancel(self.generate_job)
                self.generate_job = None

            if self.check_job is not None:
                self.check_queue.cancel(self.check_job)
                self.check_job = None

        self.check_queue.update()
        self.gen_queue.update()

    def _auto_speech(self, text):
        if text == "":
            return
        if "「" in text:
            name = text.split("「", 1)[0]
            if self.ctx["char_name"] in name:
                if self.ctx["auto_speech_char"]:
                    self.ctx.style_bert_vits2.generate(text)
                    return
            elif self.ctx["user_name"] in name:
                if self.ctx["auto_speech_user"]:
                    self.ctx.style_bert_vits2.generate(text)
                    return
        if self.ctx["auto_speech_other"]:
            self.ctx.style_bert_vits2.generate(text)

    def _generate(self, input_text):
        """テキスト生成の実行"""
        return self.ctx.kobold_cpp.generate(input_text)

    def _check(self):
        """生成状態のチェック"""
        return self.ctx.kobold_cpp.check()

    def _get_last_line(self, text):
        """テキストの最後の行を取得"""
        if text == "":
            return ""
        if text.endswith("\n"):
            return ""
        return text.splitlines()[-1]

    def set_prompt(self, prompt):
        """生成用のプロンプトを直接設定"""
        if self.enabled:
            if self.generate_job is None:
                # チャットモードの場合、応答を履歴に追加する設定を付与
                if self.ctx.get("chat_mode", False):
                    self.last_chat_prompt = prompt  # プロンプトを保持
                self.generate_job = self.gen_queue.push(self._generate, input_text=prompt)

    def clear(self):
        """生成状態をクリア"""
        self.gen_area_text = ""
        self.last_line = ""
        self.last_chat_prompt = None
        if self.generate_job is not None:
            self.ctx.kobold_cpp.abort()
            self.gen_queue.cancel(self.generate_job)
            self.generate_job = None
        
        if self.check_job is not None:
            self.check_queue.cancel(self.check_job)
            self.check_job = None

    def abort(self):
        """生成を中断する"""
        result = self.check_queue.push(self.ctx.kobold_cpp.abort)
        if self.generate_job is not None:
            self.gen_queue.cancel(self.generate_job)
            self.generate_job = None
        return result

class LLMSetupDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("ローカルLLMセットアップ")
        layout = QVBoxLayout(self)

        self.llm_combo = QComboBox()
        self.llm_combo.addItems(["koboldcpp", "LocalAI", "llama.cpp"])
        layout.addWidget(QLabel("利用するローカルLLM:"))
        layout.addWidget(self.llm_combo)

        self.path_edit = QLineEdit()
        layout.addWidget(QLabel("実行ファイルのパスまたはAPIエンドポイント:"))
        layout.addWidget(self.path_edit)

        self.save_btn = QPushButton("保存")
        self.save_btn.clicked.connect(self.accept)
        layout.addWidget(self.save_btn)

    def get_settings(self):
        return {
            "llm_type": self.llm_combo.currentText(),
            "llm_path": self.path_edit.text()
        }