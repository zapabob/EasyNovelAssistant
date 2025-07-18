import time
import re
import pickle
import os
from path import Path
import datetime
import traceback
import threading

from job_queue import JobQueue


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

        self.recursive_mode = False
        self.recursive_state_path = os.path.join(Path.log, "recursive_session.pkl")
        self.recursive_history = []
        self.recursive_step = 0
        self.recursive_max_steps = 50  # デフォルト最大ステップ数
        self.recursive_last_input = None
        self.recursive_job = None  # ← 追加

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
        # 再帰モード切替時に状態リセット
        if getattr(self, "recursive_mode", False) and self.recursive_job is None and self.recursive_step == 0:
            self.recursive_history = []
            self.recursive_step = 0
            self.recursive_last_input = None
            self.recursive_job = None
        if getattr(self, "recursive_mode", False):
            self._update_recursive()
            return
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
                            append_text = result[len(self.gen_area_text) :]

                            # 修正: linesがNoneやNever型にならないように明示的にstr型を保証
                            lines = (self.last_line + append_text).splitlines() if (self.last_line + append_text) else []
                            if len(lines) > 0:
                                for line in lines[:-1]:
                                    self._auto_speech(line)
                                self.last_line = lines[-1]
                                if append_text.endswith("\n"):
                                    self._auto_speech(self.last_line)
                                    self.last_line = ""
                            self.ctx.form.gen_area.append_text(append_text)
                        else:
                            # 修正: linesがNoneやNever型にならないように明示的にstr型を保証
                            lines = result.splitlines() if result else []
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

    def _make_cot_prompt(self, story_so_far):
        if not story_so_far:
            story_so_far = ""
        short_story = story_so_far[-500:] if len(story_so_far) > 500 else story_so_far
        return (
            f"これまでのストーリー:\n{short_story}\n\n"
            "次に何が起こるかを考え、その後に本文を書いてください。\n"
            "【思考】\n"
            "（ここに次の展開や理由を考えてください）\n"
            "【本文】\n"
            "（ここに本文を書いてください）\n"
        )

    def _update_recursive(self):
        try:
            # セッション復旧
            if self.recursive_step == 0 and os.path.exists(self.recursive_state_path):
                try:
                    with open(self.recursive_state_path, "rb") as f:
                        state = pickle.load(f)
                    self.recursive_history = state["history"]
                    self.recursive_step = state["step"]
                    self.recursive_last_input = state["last_input"]
                except Exception:
                    self.recursive_history = []
                    self.recursive_step = 0
                    self.recursive_last_input = None
            # 1回目: 入力欄のテキストをそのまま推論
            if self.recursive_step == 0:
                input_text = self.ctx.form.input_area.get_prompt_text()
                if not input_text:
                    print("[DEBUG] 入力が空のため再帰推論をスキップ")
                    return
                print(f"[DEBUG] Step 0 input: {input_text}")
                def first_infer():
                    try:
                        result = self._generate(input_text)
                        self.ctx.form.win.after(0, lambda: self._after_recursive_step(input_text, result, 0))
                    except Exception as exc:
                        print("[ERROR] 例外発生:", exc)
                        traceback.print_exc()
                        self.ctx.form.win.after(0, lambda exc=exc: self._after_recursive_error(exc))
                threading.Thread(target=first_infer, daemon=True).start()
                return
            # 2回目以降: 直前の出力（種）をCoTテンプレートでラップ
            last_seed = self.recursive_last_input
            prompt = self._make_cot_prompt(last_seed)
            print(f"[DEBUG] Step {self.recursive_step} prompt: {prompt}")
            def next_infer():
                try:
                    result = self._generate(prompt)
                    self.ctx.form.win.after(0, lambda: self._after_recursive_step(prompt, result, self.recursive_step))
                except Exception as exc:
                    print("[ERROR] 例外発生:", exc)
                    traceback.print_exc()
                    self.ctx.form.win.after(0, lambda exc=exc: self._after_recursive_error(exc))
            threading.Thread(target=next_infer, daemon=True).start()
        except Exception as exc:
            print("[ERROR] 例外発生:", exc)
            traceback.print_exc()
            self.ctx.form.output_area.append_output("【自動停止】例外発生により停止しました。\n" + str(exc))
            self._finalize_recursive()

    def _after_recursive_step(self, prompt, result, step):
        self.ctx.form.output_area.append_output(f"[Step {step}] 入力: {prompt}")
        self.ctx.form.output_area.append_output(f"[Step {step}] 出力: {result}")
        self.recursive_history.append(prompt)
        self.recursive_history.append(result)
        self.recursive_step += 1
        self.recursive_last_input = result
        # 停止条件
        if self._check_stop_condition_relaxed(result):
            self.ctx.form.output_area.append_output("【自動停止】停止条件に達しました。")
            self._finalize_recursive()
            return
        if self.recursive_step >= self.recursive_max_steps:
            self.ctx.form.output_area.append_output("【自動停止】最大ステップ数に達しました。")
            self._finalize_recursive()
            return
        self.ctx.form.win.after(100, self._update_recursive)

    def _after_recursive_error(self, e):
        self.ctx.form.output_area.append_output("【自動停止】例外発生により停止しました。\n" + str(e))
        self._finalize_recursive()

    def _check_stop_condition(self, text):
        import re
        return re.search(r'(.)\1\1\1', text) is not None

    def _finalize_recursive(self):
        # セッション保存・実装ログ出力など
        pass

    def _write_recursive_log(self, reason):
        date_str = datetime.datetime.now().strftime("%Y-%m-%d")
        log_path = os.path.join("_docs", f"{date_str}_recursive_inference_mode.md")
        try:
            with open(log_path, "w", encoding="utf-8-sig") as f:
                f.write(f"# 再帰推論モード 実装ログ ({date_str})\n")
                f.write(f"- 停止理由: {reason}\n")
                f.write(f"- ステップ数: {self.recursive_step}\n")
                f.write(f"- 入出力履歴:\n\n")
                for i, text in enumerate(self.recursive_history):
                    f.write(f"## Step {i}\n\n{text}\n\n")
                f.write("---\n自動生成ログ\n")
        except Exception as e:
            print(f"[再帰推論ログ出力エラー] {e}")

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
        return self.ctx.kobold_cpp.generate(input_text)

    def _check(self):
        return self.ctx.kobold_cpp.check()

    def _get_last_line(self, text):
        if text == "":
            return ""
        if text.endswith("\n"):
            return ""
        return text.splitlines()[-1]

    def _has_four_consecutive_chars(self, text):
        return re.search(r'(.)\1\1\1', text) is not None

    def _check_stop_condition_relaxed(self, text):
        # 2連続同一文字で停止（デバッグ用に緩和）
        import re
        return re.search(r'(.)\1', text) is not None

    def abort(self):
        self.check_queue.push(self.ctx.kobold_cpp.abort)
