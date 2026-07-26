import re
import tkinter as tk
from tkinter import ttk
from src.utils.window import get_tibia_windows, TibiaWindow


class ConfigPage(tk.Frame):
    def __init__(self, parent, context):
        super().__init__(parent)
        self.context = context
        self._window_map = {}
        self.windowsFrame = tk.LabelFrame(
            self, text='Tibia window', padx=10, pady=10)
        self.windowsFrame.grid(column=0, row=0, padx=10,
                               pady=10, sticky='nsew')

        self.windowsFrame.rowconfigure(0, weight=1)
        self.windowsFrame.columnconfigure(0, weight=1)

        self.windowsCombobox = ttk.Combobox(
            self.windowsFrame, values=self.getTibiaWindows(), state='readonly')
        self.windowsCombobox.bind(
            "<<ComboboxSelected>>", self.onChangeWindow)
        self.windowsCombobox.grid(row=0, column=0, sticky='ew')

        self.button = ttk.Button(
            self.windowsFrame, text='Atualizar', command=self.refreshWindows)
        self.button.grid(row=0, column=1, padx=10, pady=10)

        self.resolutionFrame = tk.LabelFrame(
            self, text='Resolution', padx=10, pady=10)
        self.resolutionFrame.grid(
            row=0, column=1, padx=10, pady=10, sticky='nsew')

        self.resolutionFrame.rowconfigure(0, weight=1)
        self.resolutionFrame.columnconfigure(0, weight=1)

        resolutions = ['1920x1080']
        self.resolutionsCombobox = ttk.Combobox(
            self.resolutionFrame, values=resolutions, state='readonly')
        self.resolutionsCombobox.set(resolutions[0])
        self.resolutionsCombobox.grid(row=0, column=0, sticky='ew')

        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, weight=1)

    def getTibiaWindows(self):
        windows = get_tibia_windows()
        self._window_map = {w.title: w for w in windows}
        return list(self._window_map.keys())

    def refreshWindows(self):
        self.windowsCombobox['values'] = self.getTibiaWindows()

    def onChangeWindow(self, _):
        selectedWindow = self.windowsCombobox.get()
        if selectedWindow in self._window_map:
            self.context.context['window'] = self._window_map[selectedWindow]
