import tkinter as tk
import webbrowser


class HelpMenu:

    def __init__(self, form, ctx):
        self.form = form
        self.ctx = ctx

        self.menu = tk.Menu(form.win, tearoff=False)
        form.menu_bar.add_cascade(label="ヘルプ", menu=self.menu)
        self.menu.configure(postcommand=self.on_menu_open)

    def on_menu_open(self):
        self.menu.delete(0, tk.END)

        # モデルのダウンロードページ
        info_urls = set()
        for llm_name in self.ctx.llm:
            llm = self.ctx.llm[llm_name]
            if not isinstance(llm, dict):
                continue
            
            if "info_url" not in llm:
                continue
            
            if llm["info_url"] not in info_urls:
                info_urls.add(llm["info_url"])
                self.menu.add_command(
                    label=f"{llm_name} のダウンロードページを開く",
                    command=lambda url=llm["info_url"]: webbrowser.open(url)
                )

        self.menu.add_separator()

        # プロジェクトページ
        self.menu.add_command(
            label="EasyNovelAssistant のページを開く",
            command=lambda: webbrowser.open("https://github.com/Aratako/EasyNovelAssistant")
        )

    def _show_hf_url(self, menu, hf_name):
        cmd = lambda: self._show_url(f"https://huggingface.co/{hf_name}")
        menu.add_command(label=hf_name, command=cmd)

    def _show_url(self, url):
        webbrowser.open(url)
