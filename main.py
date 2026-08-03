import argparse
from threading import Thread

from src.gameplay.context import context
from src.gameplay.threads.pyTibia import PyTibiaThread
# Código original:
# from src.gameplay.threads.ui import UIThread
from src.ui.context import Context


# Código original:
# def main():
#     contextInstance = Context(context)
#     uiThreadInstance = UIThread(contextInstance)
#     uiThreadInstance.start()
#     pyTibiaThreadInstance = PyTibiaThread(contextInstance)
#     pyTibiaThreadInstance.mainloop()
def main(uiEnabled=True):
    contextInstance = Context(context)
    pyTibiaThreadInstance = PyTibiaThread(
        contextInstance,
        uiEnabled=uiEnabled,
    )

    if not uiEnabled:
        try:
            pyTibiaThreadInstance.mainloop()
        finally:
            contextInstance.context['shutdown'] = True
            contextInstance.pause()
        return

    import tkinter as tk
    from src.ui.application import Application

    app = Application(contextInstance)
    gameplayThread = Thread(
        target=pyTibiaThreadInstance.mainloop,
        name='PyTibiaGameplay',
    )
    gameplayThread.start()
    try:
        app.mainloop()
    finally:
        contextInstance.context['shutdown'] = True
        contextInstance.pause()
        try:
            if app.winfo_exists():
                app.destroy()
        except tk.TclError:
            pass
        gameplayThread.join()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--cli',
        action='store_true',
        help='Executa sem a interface Tkinter.',
    )
    args = parser.parse_args()
    main(uiEnabled=not args.cli)
