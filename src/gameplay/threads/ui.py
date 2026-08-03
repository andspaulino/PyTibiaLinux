import tkinter as tk
from threading import Event, Thread

from src.ui.application import Application


class UIThread(Thread):
    # TODO: add typings
    def __init__(self, context):
        Thread.__init__(self)
        self.context = context
        self.app = None
        self.closeRequested = Event()

    def run(self):
        # Código original:
        # app = Application(self.context)
        # app.mainloop()
        try:
            app = Application(self.context)
            self.app = app
            app.after(50, self._monitorCloseRequest)
            app.mainloop()
        finally:
            try:
                self.context.pause()
            finally:
                self.context.context['shutdown'] = True
                app = self.app
                if app is not None:
                    try:
                        if app.winfo_exists():
                            app.destroy()
                    except tk.TclError:
                        pass
                self.app = None

    def _monitorCloseRequest(self):
        app = self.app
        if app is None:
            return
        if (
            self.closeRequested.is_set()
            or self.context.context.get('shutdown', False)
        ):
            try:
                app.destroy()
            except tk.TclError:
                pass
            return
        app.after(50, self._monitorCloseRequest)

    def requestClose(self):
        self.closeRequested.set()
