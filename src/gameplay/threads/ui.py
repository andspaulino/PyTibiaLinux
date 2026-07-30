import gc
import tkinter as tk
from threading import Event, Thread

# Código Linux anterior:
# from src.ui.application import Application
from src.ui.application import Application


class UIThread(Thread):
    # TODO: add typings
    def __init__(self, context):
        Thread.__init__(self)
        self.context = context
        self.app = None
        self.closeRequested = Event()

    def run(self):
        # Código Linux anterior:
        # app = Application(self.context)
        # app.mainloop()
        # pass
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
                del app
                gc.collect()

    def _monitorCloseRequest(self):
        app = self.app
        if app is None:
            return
        if (
            self.closeRequested.is_set()
            or self.context.context.get('shutdown', False)
        ):
            app.close()
            return
        app.after(50, self._monitorCloseRequest)

    def requestClose(self):
        self.closeRequested.set()
