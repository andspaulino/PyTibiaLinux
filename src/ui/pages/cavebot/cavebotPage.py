import tkinter as tk
from copy import deepcopy
from tkinter import messagebox, simpledialog, ttk

from .baseModal import BaseModal
from .refillCheckerModal import RefillCheckerModal
from .refillModal import RefillModal

from src.repositories.radar.core import getCoordinate
from src.routes.draft import RouteDraft
from src.routes.store import DEFAULT_ROUTES_DIRECTORY, RouteStore
from src.utils.core import getScreenshot


class CavebotPage(tk.Frame):
    def __init__(self, parent, context):
        super().__init__(parent)
        self.context = context
        self.routeStore = RouteStore(DEFAULT_ROUTES_DIRECTORY)
        selectedRouteId = context.enabledProfile['config']['cavebot'].get(
            'routeId'
        )
        initialRouteError = None
        try:
            self.routeDraft = (
                RouteDraft.open(self.routeStore, selectedRouteId)
                if selectedRouteId is not None
                else RouteDraft.create('New route')
            )
        except (OSError, ValueError) as error:
            self.routeDraft = RouteDraft.create('Recovered route')
            initialRouteError = str(error)
        self.columnconfigure(0, weight=8)
        self.columnconfigure(1, weight=2)
        self.rowconfigure(2, weight=1)
        self.baseModal = None
        self.refillModal = None
        self.refillCheckerModal = None

        self.routesFrame = tk.LabelFrame(
            self, text='Route', padx=10, pady=10)
        self.routesFrame.grid(
            column=0, row=0, columnspan=2, padx=10, pady=10, sticky='ew')
        self.routesFrame.columnconfigure(1, weight=1)

        tk.Label(self.routesFrame, text='Route:').grid(
            row=0, column=0, padx=5)
        self.routeSelection = tk.StringVar(
            value=self.routeDraft.routeId or '')
        self.routesCombo = ttk.Combobox(
            self.routesFrame,
            textvariable=self.routeSelection,
            state='readonly',
        )
        self.routesCombo.grid(row=0, column=1, padx=5, sticky='ew')
        self.routesCombo.bind(
            '<<ComboboxSelected>>',
            self.onRouteSelected,
        )
        self.newRouteButton = tk.Button(
            self.routesFrame, text='New', command=self.newRoute
        )
        self.newRouteButton.grid(row=0, column=2, padx=5)
        # Código Linux anterior:
        # self.openRouteButton = tk.Button(
        #     self.routesFrame, text='Open', command=self.openSelectedRoute
        # )
        # self.openRouteButton.grid(row=0, column=3, padx=5)
        self.saveRouteButton = tk.Button(
            self.routesFrame, text='Save', command=self.saveRoute
        )
        self.saveRouteButton.grid(row=0, column=3, padx=5)
        self.saveRouteAsButton = tk.Button(
            self.routesFrame, text='Save as', command=self.saveRouteAs
        )
        self.saveRouteAsButton.grid(row=0, column=4, padx=5)
        # Código Linux anterior:
        # self.activateRouteButton = tk.Button(
        #     self.routesFrame, text='Activate', command=self.activateRoute
        # )
        # self.activateRouteButton.grid(row=0, column=6, padx=5)
        self.cavebotEnabled = tk.BooleanVar(
            value=bool(self.context.context['cavebot'].get('enabled', False))
        )
        self.cavebotEnabledCheckbox = tk.Checkbutton(
            self.routesFrame,
            text='Cavebot enabled',
            variable=self.cavebotEnabled,
            command=self.toggleCavebotEnabled,
        )
        self.cavebotEnabledCheckbox.grid(row=0, column=5, padx=5)
        self.activeRouteStatus = tk.StringVar()
        tk.Label(
            self.routesFrame,
            textvariable=self.activeRouteStatus,
            anchor='w',
        ).grid(row=1, column=0, columnspan=6, padx=5, pady=(8, 0), sticky='ew')
        self.refreshRouteChoices()
        self.refreshActiveRouteStatus()
        self.updateRouteSelectionControls()
        if initialRouteError is not None:
            self.after_idle(
                lambda error=initialRouteError: messagebox.showerror(
                    'Unable to open selected route',
                    error,
                    parent=self,
                )
            )

        self.tableFrame = tk.LabelFrame(
            self, text='Waypoints', padx=10, pady=10)
        self.tableFrame.grid(column=0, row=1, rowspan=2, padx=10,
                             pady=10, sticky='nsew')
        self.tableFrame.rowconfigure(0, weight=1)
        self.tableFrame.columnconfigure(0, weight=1)

        self.table = ttk.Treeview(self.tableFrame, columns=(
            'label', 'type', 'coordinate', 'options'))
        self.table.grid(row=0, column=0, rowspan=1, sticky='nsew')
        self.table.bind('<Delete>', self.removeSelectedWaypoints)
        self.table.heading('label', text='Label')
        self.table.heading('type', text='Type')
        self.table.heading('coordinate', text='Coordinate')
        self.table.heading('options', text='Options')
        self.table.column('#0', width=0)
        self.table.column('label', width=100)
        self.table.column('type', width=100)
        self.table.column('coordinate', width=100)
        self.table.column('options', width=100)

        self.table.bind('<Double-1>', self.onWaypointDoubleClick)

        self.refreshWaypointsTable()

        self.waypointDirection = tk.StringVar(value='center')
        self.directionsFrame = tk.LabelFrame(
            self, text='Directions', padx=10, pady=10)
        self.directionsFrame.grid(column=1, row=1, padx=10,
                                  pady=10, sticky='nsew')
        self.directionsFrame.columnconfigure(0, weight=1)
        self.directionsFrame.columnconfigure(1, weight=1)
        self.directionsFrame.columnconfigure(2, weight=1)

        northOption = tk.Radiobutton(self.directionsFrame, variable=self.waypointDirection,
                                     text='North', value='north')
        northOption.grid(row=0, column=1)

        westOption = tk.Radiobutton(self.directionsFrame, variable=self.waypointDirection,
                                    text='West', value='west')
        westOption.grid(row=1, column=0)

        centerOption = tk.Radiobutton(self.directionsFrame, variable=self.waypointDirection,
                                      text='Center', value='center')
        centerOption.grid(row=1, column=1)

        eastOption = tk.Radiobutton(self.directionsFrame, variable=self.waypointDirection,
                                    text='East', value='east')
        eastOption.grid(row=1, column=2)

        southOption = tk.Radiobutton(self.directionsFrame, variable=self.waypointDirection,
                                     text='South', value='south')
        southOption.grid(row=2, column=1)

        self.actionsFrame = tk.LabelFrame(
            self, text='Actions', padx=10, pady=10)
        self.actionsFrame.grid(column=1, row=2, padx=10,
                               pady=10, sticky='nsew')
        self.actionsFrame.columnconfigure(0, weight=1, uniform='equal')
        self.actionsFrame.columnconfigure(1, weight=1, uniform='equal')

        self.walkButton = tk.Button(
            self.actionsFrame, text='Walk', command=lambda: self.addWaypoint('walk'))
        self.walkButton.grid(row=0, column=0, padx=5, pady=5, sticky='nsew')

        self.useTeleportButton = tk.Button(
            self.actionsFrame, text='Use Teleport', command=lambda: self.addWaypoint('useTeleport'))
        self.useTeleportButton.grid(row=0, column=1, padx=5, pady=5, sticky='nsew')

        self.ropeButton = tk.Button(
            self.actionsFrame, text='Rope', command=lambda: self.addWaypoint('useRope'))
        self.ropeButton.grid(row=1, column=0, padx=5, pady=5, sticky='nsew')

        self.shovelButton = tk.Button(
            self.actionsFrame, text='Shovel', command=lambda: self.addWaypoint('useShovel'))
        self.shovelButton.grid(row=1, column=1, padx=5, pady=5, sticky='nsew')

        self.moveUpButton = tk.Button(
            self.actionsFrame, text='Move Up', command=lambda: self.addWaypoint('moveUp'))
        self.moveUpButton.grid(row=2, column=0, padx=5, pady=5, sticky='nsew')
        self.moveDownButton = tk.Button(
            self.actionsFrame, text='Move Down', command=lambda: self.addWaypoint('moveDown'))
        self.moveDownButton.grid(
            row=2, column=1, padx=5, pady=5, sticky='nsew')

        self.depositGoldButton = tk.Button(
            self.actionsFrame, text='Deposit gold', command=lambda: self.addWaypoint('depositGold'))
        self.depositGoldButton.grid(
            row=3, column=0, padx=5, pady=5, sticky='nsew')
        self.depositItemsButton = tk.Button(
            self.actionsFrame, text='Deposit items', command=lambda: self.addWaypoint('depositItems'))
        self.depositItemsButton.grid(
            row=3, column=1, padx=5, pady=5, sticky='nsew')

        self.dropFlasksButton = tk.Button(
            self.actionsFrame, text='Drop flasks', command=lambda: self.addWaypoint('dropFlasks'))
        self.dropFlasksButton.grid(
            row=4, column=0, padx=5, pady=5, sticky='nsew')

        self.useHoleButton = tk.Button(
            self.actionsFrame, text='Use Hole', command=lambda: self.addWaypoint('useHole'))
        self.useHoleButton.grid(
            row=4, column=1, padx=5, pady=5, sticky='nsew')

        self.refillButton = tk.Button(
            self.actionsFrame, text='Refill', command=lambda: self.openRefillModal())
        self.refillButton.grid(
            row=5, column=0, padx=5, pady=5, sticky='nsew')

        self.refillCheckerButton = tk.Button(
            self.actionsFrame, text='Refill checker', command=lambda: self.openRefillCheckerModal())
        self.refillCheckerButton.grid(
            row=5, column=1, padx=5, pady=5, sticky='nsew')

        # Código original:
        # for unsupportedButton in (
        #     self.useTeleportButton,
        #     self.ropeButton,
        #     self.shovelButton,
        #     self.moveUpButton,
        #     self.moveDownButton,
        #     self.depositGoldButton,
        #     self.depositItemsButton,
        #     self.dropFlasksButton,
        #     self.refillButton,
        #     self.refillCheckerButton,
        # ):
        for unsupportedButton in (
            self.depositGoldButton,
            self.depositItemsButton,
            self.dropFlasksButton,
            self.refillButton,
            self.refillCheckerButton,
        ):
            unsupportedButton.configure(state=tk.DISABLED)

    def _requirePaused(self):
        if self.context.context.get('pause', False):
            return True
        messagebox.showerror(
            'Pause required',
            'Pause the bot before editing or activating routes.',
            parent=self,
        )
        return False

    def refreshActiveRouteStatus(self):
        routeId = self.context.getActiveRouteId()
        cavebotEnabled = self.context.context['cavebot'].get('enabled', False)
        status = (
            f'Active route: {routeId or "None"}'
            if cavebotEnabled
            else f'Cavebot disabled (last route: {routeId or "None"})'
        )
        if getattr(self.context, 'routeApplicationPending', False) is True:
            status += ' (saved changes pending application)'
        self.activeRouteStatus.set(status)

    def updateRouteSelectionControls(self):
        isEnabled = bool(self.cavebotEnabled.get())
        self.routesCombo.configure(
            state=tk.DISABLED if isEnabled else 'readonly'
        )
        routeChoiceState = tk.DISABLED if isEnabled else tk.NORMAL
        self.newRouteButton.configure(state=routeChoiceState)
        self.saveRouteAsButton.configure(state=routeChoiceState)

    def onRouteSelected(self, _event=None):
        self.openSelectedRoute()

    def toggleCavebotEnabled(self):
        if not self._requirePaused():
            self.cavebotEnabled.set(
                bool(self.context.context['cavebot'].get('enabled', False))
            )
            self.updateRouteSelectionControls()
            return
        shouldEnable = bool(self.cavebotEnabled.get())
        if shouldEnable:
            if not self.activateRoute(enableCavebot=True):
                self.cavebotEnabled.set(False)
        else:
            try:
                self.context.setCavebotEnabled(False)
            except (OSError, RuntimeError, ValueError) as error:
                messagebox.showerror(
                    'Unable to disable Cavebot',
                    str(error),
                    parent=self,
                )
                self.cavebotEnabled.set(True)
        self.refreshActiveRouteStatus()
        self.updateRouteSelectionControls()

    def refreshRouteChoices(self):
        try:
            routeIds = [
                routeFile.removesuffix('.json')
                for routeFile in self.routeStore.listRoutes()
            ]
        except (OSError, ValueError) as error:
            messagebox.showerror('Error', str(error), parent=self)
            return
        self.routesCombo['values'] = routeIds

    def _hasOpenWaypointModal(self):
        return any(
            modal is not None and modal.winfo_exists()
            for modal in (
                self.baseModal,
                self.refillModal,
                self.refillCheckerModal,
            )
        )

    def _canReplaceDraft(self):
        if self._hasOpenWaypointModal():
            messagebox.showerror(
                'Close waypoint editor',
                'Close the open waypoint editor before changing routes.',
                parent=self,
            )
            return False
        if not self.routeDraft.isDirty:
            return True
        return messagebox.askyesno(
            'Discard changes?',
            'The current route has unsaved changes. Discard them?',
            parent=self,
        )

    def _restoreRouteSelection(self):
        self.routeSelection.set(self.routeDraft.routeId or '')

    def refreshWaypointsTable(self):
        for item in self.table.get_children():
            self.table.delete(item)
        for waypoint in self.routeDraft.document['waypoints']:
            self.table.insert('', 'end', values=(
                waypoint['label'],
                waypoint['type'],
                waypoint['coordinate'],
                waypoint['options'],
            ))

    def newRoute(self):
        if not self._requirePaused():
            return
        if not self._canReplaceDraft():
            self._restoreRouteSelection()
            return
        name = simpledialog.askstring(
            'New route',
            'Route name:',
            parent=self,
        )
        if name is None:
            return
        try:
            self.routeDraft = RouteDraft.create(name)
        except ValueError as error:
            messagebox.showerror('Error', str(error), parent=self)
            return
        self.routeSelection.set('')
        self.refreshWaypointsTable()

    def openSelectedRoute(self):
        if not self._requirePaused():
            self._restoreRouteSelection()
            return
        routeId = self.routeSelection.get()
        if routeId == '':
            messagebox.showerror(
                'Error', 'Select a route to open.', parent=self)
            self._restoreRouteSelection()
            return
        if not self._canReplaceDraft():
            self._restoreRouteSelection()
            return
        try:
            self.routeDraft = RouteDraft.open(self.routeStore, routeId)
        except (OSError, ValueError) as error:
            messagebox.showerror('Error', str(error), parent=self)
            self._restoreRouteSelection()
            return
        self.routeSelection.set(routeId)
        self.refreshWaypointsTable()

    def saveRoute(self):
        if not self._requirePaused():
            return
        if self.routeDraft.routeId is None:
            self.saveRouteAs()
            return
        isActiveRoute = (
            self.context.context['cavebot'].get('enabled', False)
            and self.routeDraft.routeId == self.context.getActiveRouteId()
        )
        if isActiveRoute and not messagebox.askyesno(
            'Save and apply active route?',
            'This route is active. Save and apply its changes now?',
            parent=self,
        ):
            return
        previousPendingState = getattr(
            self.context,
            'routeApplicationPending',
            False,
        )
        if isActiveRoute:
            self.context.routeApplicationPending = True
        try:
            self.routeDraft.save(self.routeStore)
        except (OSError, ValueError) as error:
            self.context.routeApplicationPending = previousPendingState
            messagebox.showerror('Error', str(error), parent=self)
            self.refreshActiveRouteStatus()
            return
        if isActiveRoute:
            try:
                self.context.activateRoute(
                    self.routeDraft.routeId,
                    routeStore=self.routeStore,
                )
            except (OSError, RuntimeError, ValueError) as error:
                messagebox.showerror(
                    'Route saved but not applied',
                    str(error),
                    parent=self,
                )
                self.refreshActiveRouteStatus()
                return
        self.routeSelection.set(self.routeDraft.routeId)
        self.refreshRouteChoices()
        self.refreshActiveRouteStatus()

    def saveRouteAs(self):
        if not self._requirePaused():
            return
        routeId = simpledialog.askstring(
            'Save route as',
            'Route ID:',
            initialvalue=self.routeDraft.routeId or '',
            parent=self,
        )
        if routeId is None:
            return
        name = simpledialog.askstring(
            'Save route as',
            'Route name:',
            initialvalue=self.routeDraft.document['name'],
            parent=self,
        )
        if name is None:
            return
        routeFile = f'{routeId}.json'
        try:
            routeAlreadyExists = routeFile in self.routeStore.listRoutes()
        except (OSError, ValueError) as error:
            messagebox.showerror('Error', str(error), parent=self)
            return
        if (
            routeId != self.routeDraft.routeId
            and routeAlreadyExists
            and not messagebox.askyesno(
                'Overwrite route?',
                f'{routeFile} already exists. Replace it?',
                parent=self,
            )
        ):
            return
        isActiveRoute = (
            self.context.context['cavebot'].get('enabled', False)
            and routeId == self.context.getActiveRouteId()
        )
        if isActiveRoute and not messagebox.askyesno(
            'Save and apply active route?',
            'This route is active. Save and apply its changes now?',
            parent=self,
        ):
            return
        previousPendingState = getattr(
            self.context,
            'routeApplicationPending',
            False,
        )
        if isActiveRoute:
            self.context.routeApplicationPending = True
        try:
            self.routeDraft.saveAs(self.routeStore, routeId, name)
        except (OSError, ValueError) as error:
            self.context.routeApplicationPending = previousPendingState
            messagebox.showerror('Error', str(error), parent=self)
            self.refreshActiveRouteStatus()
            return
        if isActiveRoute:
            try:
                self.context.activateRoute(
                    routeId,
                    routeStore=self.routeStore,
                )
            except (OSError, RuntimeError, ValueError) as error:
                messagebox.showerror(
                    'Route saved but not applied',
                    str(error),
                    parent=self,
                )
                self.refreshActiveRouteStatus()
                return
        self.routeSelection.set(routeId)
        self.refreshRouteChoices()
        self.refreshWaypointsTable()
        self.refreshActiveRouteStatus()

    def activateRoute(self, enableCavebot=None):
        if not self._requirePaused():
            return False
        if self.routeDraft.isDirty:
            messagebox.showerror(
                'Unsaved route',
                'Save or discard the route changes before activating it.',
                parent=self,
            )
            return False
        routeId = self.routeDraft.routeId
        if routeId is None:
            messagebox.showerror(
                'Unsaved route',
                'Save the route before activating it.',
                parent=self,
            )
            return False
        try:
            self.context.activateRoute(
                routeId,
                routeStore=self.routeStore,
                enableCavebot=enableCavebot,
            )
        except (OSError, RuntimeError, ValueError) as error:
            messagebox.showerror('Unable to activate route', str(error), parent=self)
            self.refreshActiveRouteStatus()
            return False
        self.refreshActiveRouteStatus()
        return True

    def _getNextWaypointLabel(self, waypointType):
        highestSuffix = 0
        for waypoint in self.routeDraft.document['waypoints']:
            if waypoint['type'] != waypointType:
                continue
            label = waypoint['label']
            if not label.startswith(waypointType):
                continue
            suffix = label[len(waypointType):]
            if suffix.isdigit():
                highestSuffix = max(highestSuffix, int(suffix))
        return f'{waypointType}{highestSuffix + 1:03d}'

    def openBaseModal(self):
        if self.baseModal is None or not self.baseModal.winfo_exists():
            self.baseModal = BaseModal(self, onConfirm=lambda label, options: self.addWaypoint(
                'refill', options))

    def openRefillModal(self):
        if self.refillModal is None or not self.refillModal.winfo_exists():
            self.refillModal = RefillModal(self, onConfirm=lambda label, options: self.addWaypoint(
                'refill', options))

    def openRefillCheckerModal(self):
        waypointsLabels = self.context.getAllWaypointLabels()
        if len(waypointsLabels) == 0:
            messagebox.showerror(
                'Erro', 'There must be at least one labeled waypoint!')
        if self.refillCheckerModal is None or not self.refillCheckerModal.winfo_exists():
            self.refillCheckerModal = RefillCheckerModal(self, onConfirm=lambda label, options: self.addWaypoint(
                'refillChecker', options), waypointsLabels=waypointsLabels)

    # TODO: verificar se a coordenada é walkable
    # Código original:
    # def addWaypoint(self, waypointType, options={}):
    def addWaypoint(self, waypointType, options=None):
        if not self._requirePaused():
            return
        waypointOptions = {} if options is None else deepcopy(options)
        screenshot = getScreenshot()
        coordinate = getCoordinate(screenshot)
        if coordinate is None:
            messagebox.showerror(
                'Erro', 'The Tibia minimap needs to be visible!')
            return
        waypointDirection = self.waypointDirection.get()
        if waypointDirection == 'north':
            coordinate = (coordinate[0], coordinate[1] - 1, coordinate[2])
        elif waypointDirection == 'south':
            coordinate = (coordinate[0], coordinate[1] + 1, coordinate[2])
        elif waypointDirection == 'east':
            coordinate = (coordinate[0] + 1, coordinate[1], coordinate[2])
        elif waypointDirection == 'west':
            coordinate = (coordinate[0] - 1, coordinate[1], coordinate[2])
        waypoint = {
            'label': self._getNextWaypointLabel(waypointType),
            'type': waypointType,
            'coordinate': coordinate,
            'options': waypointOptions,
        }
        if waypointType == 'moveUp' or waypointType == 'moveDown':
            if waypointDirection == 'center':
                messagebox.showerror(
                    'Erro', 'Move Down or Move Up waypoint always needs a direction(North, West, East, South)')
                return
            waypoint['options']['direction'] = waypointDirection
        # Código original:
        # self.context.addWaypoint(waypoint)
        # self.table.insert('', 'end', values=(
        #     waypoint['label'], waypoint['type'], waypoint['coordinate'], waypoint['options']))
        try:
            self.routeDraft.addWaypoint(waypoint)
        except ValueError as error:
            messagebox.showerror('Error', str(error), parent=self)
            return
        self.refreshWaypointsTable()

    def removeSelectedWaypoints(self, _):
        if not self._requirePaused():
            return
        if self._hasOpenWaypointModal():
            messagebox.showerror(
                'Close waypoint editor',
                'Close the open waypoint editor before removing waypoints.',
                parent=self,
            )
            return
        selectedWaypoints = self.table.selection()
        selectedIndexes = sorted(
            (self.table.index(waypoint) for waypoint in selectedWaypoints),
            reverse=True,
        )
        # Código original:
        # for waypoint in selectedWaypoints:
        #     index = self.table.index(waypoint)
        #     self.table.delete(waypoint)
        #     self.context.removeWaypointByIndex(index)
        for index in selectedIndexes:
            self.routeDraft.removeWaypoint(index)
        self.refreshWaypointsTable()

    def onWaypointDoubleClick(self, event):
        if not self._requirePaused():
            return
        item = self.table.identify_row(event.y)
        if item:
            index = self.table.index(item)
            # Código original:
            # waypoint = self.context.context['cavebot']['waypoints']['items'][index]
            waypoint = self.routeDraft.document['waypoints'][index]
            if waypoint['type'] == 'refill':
                if self.refillModal is None or not self.refillModal.winfo_exists():
                    self.refillModal = RefillModal(
                        self, waypoint=waypoint, onConfirm=lambda label, options: self.updateWaypointByIndex(index, label=label, options=options))
            elif waypoint['type'] == 'refillChecker':
                if self.refillCheckerModal is None or not self.refillCheckerModal.winfo_exists():
                    waypointsLabels = self.context.getAllWaypointLabels()
                    self.refillCheckerModal = RefillCheckerModal(
                        self, waypoint=waypoint, onConfirm=lambda label, options: self.updateWaypointByIndex(index, label=label, options=options), waypointsLabels=waypointsLabels)
            else:
                if self.baseModal is None or not self.baseModal.winfo_exists():
                    self.baseModal = BaseModal(
                        self, waypoint=waypoint, onConfirm=lambda label, options: self.updateWaypointByIndex(index, label=label, options=options))

    # Código original:
    # def updateWaypointByIndex(self, index, label=None, options={}):
    def updateWaypointByIndex(self, index, label=None, options=None):
        if not self._requirePaused():
            return
        # Código original:
        # self.context.updateWaypointByIndex(
        #     index, label=label, options=options)
        # selecionado = self.table.focus()
        # if selecionado:
        #     currentValues = self.table.item(selecionado)['values']
        #     if label is not None:
        #         currentValues[0] = label
        #     currentValues[3] = options
        #     self.table.item(selecionado, values=currentValues)
        #     self.table.update()
        try:
            waypoint = deepcopy(
                self.routeDraft.document['waypoints'][index]
            )
        except IndexError as error:
            messagebox.showerror('Error', str(error), parent=self)
            return
        if label is not None:
            waypoint['label'] = label
        if options is not None:
            waypoint['options'] = deepcopy(options)
        try:
            self.routeDraft.updateWaypoint(index, waypoint)
        except (IndexError, ValueError) as error:
            messagebox.showerror('Error', str(error), parent=self)
            return
        self.refreshWaypointsTable()
