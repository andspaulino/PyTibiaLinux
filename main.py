import argparse

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
    uiThreadInstance = None
    if uiEnabled:
        from src.gameplay.threads.ui import UIThread
        uiThreadInstance = UIThread(contextInstance)
        uiThreadInstance.start()
    pyTibiaThreadInstance = PyTibiaThread(
        contextInstance,
        uiEnabled=uiEnabled,
    )
    try:
        pyTibiaThreadInstance.mainloop()
    finally:
        contextInstance.context['shutdown'] = True
        contextInstance.pause()
        if uiThreadInstance is not None:
            uiThreadInstance.requestClose()
            uiThreadInstance.join()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--cli',
        action='store_true',
        help='Executa sem a interface Tkinter.',
    )
    args = parser.parse_args()
    main(uiEnabled=not args.cli)
