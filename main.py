import argparse

from src.gameplay.context import context
from src.gameplay.threads.pyTibia import PyTibiaThread
from src.gameplay.threads.ui import UIThread
from src.ui.context import Context


def main(uiEnabled=True):
    contextInstance = Context(context)
    uiThreadInstance = None
    if uiEnabled:
        uiThreadInstance = UIThread(contextInstance)
        uiThreadInstance.start()
    # Código Linux anterior:
    # pyTibiaThreadInstance = PyTibiaThread(contextInstance)
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
