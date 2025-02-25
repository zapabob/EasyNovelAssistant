import tkinter as tk  
  
  
class GenMenu:  
    def __init__(self, form, ctx):  
        self.form = form  
        self.ctx = ctx  
        self.menu = tk.Menu(form.win, tearoff=False)  
        self.form.menu_bar.add_cascade(label="生成", menu=self.menu)  
        self.menu.configure(postcommand=self.on_menu_open)  
  
    def on_menu_open(self):  
        self.menu.delete(0, tk.END)  
        self.menu.add_command(label="生成を開始", command=lambda: None) 
