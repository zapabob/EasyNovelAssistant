import tkinter as tk
import webbrowser
import urllib.parse


class HelpMenu:
    def __init__(self, form, ctx):
        self.form = form
        self.ctx = ctx
        self.menu = tk.Menu(form.win, tearoff=False)
        self.form.menu_bar.add_cascade(label="ヘルプ", menu=self.menu)
        self.menu.configure(postcommand=self.on_menu_open)

    def _get_safe_label(self, url):
        """安全にURLからラベルを取得"""
        try:
            parsed = urllib.parse.urlparse(url)
            # URLパスを'/'で分割し、空でない部分のみを保持
            parts = [part for part in parsed.path.split('/') if part]

            # GitHub URLの場合
            if 'github.com' in parsed.netloc and len(parts) >= 2:
                return f"{parts[0]}/{parts[1]}"
                
            # Hugging Face URLの場合
            if 'huggingface.co' in parsed.netloc and len(parts) >= 2:
                return f"{parts[0]}/{parts[1]}"
                
            # 一般的なURLの場合
            if len(parts) >= 2:
                return f"{parts[-2]}/{parts[-1]}"
            elif len(parts) == 1:
                return parts[0]
            else:
                return parsed.netloc
        except:
            return url

    def on_menu_open(self):
        self.menu.delete(0, tk.END)

        sample_menu = tk.Menu(self.menu, tearoff=False)
        self.menu.add_cascade(label="サンプル原典", menu=sample_menu)

        cmd = lambda: self._show_url("https://kakuyomu.jp/works/16818093074043995181")
        sample_menu.add_command(label="最新AI Claude 3で長編小説執筆支援【GPT-4を超えた!?】", command=cmd)

        cmd = lambda: self._show_url("https://kakuyomu.jp/works/16818093074043995181/episodes/16818093074305285059")
        sample_menu.add_command(label="↑ のプロンプトまとめ", command=cmd)

        cmd = lambda: self._show_url("https://rentry.org/gpt0721")
        sample_menu.add_command(label="5ch プロンプトまとめ", command=cmd)

        reference_menu = tk.Menu(self.menu, tearoff=False)
        self.menu.add_cascade(label="参照", menu=reference_menu)

        cmd = lambda: self._show_url("https://github.com/LostRuins/koboldcpp")
        reference_menu.add_command(label="LostRuins/KoboldCpp", command=cmd)
        reference_menu.add_separator()

        info_urls = set()  # 重複を避けるためにsetを使用
        for llm in self.ctx.llm.values():
            if "info_url" in llm and llm["info_url"]:
                info_urls.add(llm["info_url"])

        for info_url in sorted(info_urls):
            if info_url.strip():  # 空文字列やスペースのみの場合をスキップ
                label = self._get_safe_label(info_url)
                cmd = lambda url=info_url: self._show_url(url)
                reference_menu.add_command(label=label, command=cmd)

        reference_menu.add_separator()
        self._show_hf_url(reference_menu, "kaunista/kaunista-style-bert-vits2-models")
        self._show_hf_url(reference_menu, "RinneAi/Rinne_Style-Bert-VITS2")

        self.menu.add_separator()
        cmd = lambda: self._show_url("https://github.com/Zuntan03/EasyNovelAssistant")
        self.menu.add_command(label="EasyNovelAssistant", command=cmd)

    def _show_hf_url(self, menu, hf_name):
        """Hugging Face URLのメニュー項目を追加"""
        cmd = lambda: self._show_url(f"https://huggingface.co/{hf_name}")
        menu.add_command(label=hf_name, command=cmd)

    def _show_url(self, url):
        """URLを開く"""
        webbrowser.open(url)