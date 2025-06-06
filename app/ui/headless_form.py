class HeadlessForm:
    def __init__(self, ctx):
        self.win = None
        self.input_area = type('obj', (), {'open_tab': lambda *a, **k: None, 'update': lambda *a, **k: None})()

    def run(self):
        pass

