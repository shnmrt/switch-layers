# -*- coding: utf-8 -*-
"""
/***************************************************************************
 SwitchLayers
                                 A QGIS plugin
 This plugin switches the layers that are grouped
 Generated by Plugin Builder: http://g-sherman.github.io/Qgis-Plugin-Builder/
                              -------------------
        begin                : 2023-07-16
        git sha              : $Format:%H$
        copyright            : (C) 2023 by Murat Sahin
        email                : sahinmurat3@gmail.com
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""
from qgis.PyQt.QtCore import QSettings, QTranslator, QCoreApplication, Qt
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QAction

from qgis.core import QgsProject, QgsLayerTreeGroup, QgsLayerTreeLayer
# Initialize Qt resources from file resources.py
from .resources import *

# Import the code for the DockWidget
from .switch_layers_dockwidget import SwitchLayersDockWidget
import os.path


class SwitchLayers:
    """QGIS Plugin Implementation."""

    def __init__(self, iface):
        """Constructor.

        :param iface: An interface instance that will be passed to this class
            which provides the hook by which you can manipulate the QGIS
            application at run time.
        :type iface: QgsInterface
        """
        # Save reference to the QGIS interface
        self.iface = iface
        # Project state
        self.root = QgsProject.instance().layerTreeRoot()

        # initialize plugin directory
        self.plugin_dir = os.path.dirname(__file__)

        # initialize locale
        locale = QSettings().value('locale/userLocale')[0:2]
        locale_path = os.path.join(
            self.plugin_dir,
            'i18n',
            'SwitchLayers_{}.qm'.format(locale))

        if os.path.exists(locale_path):
            self.translator = QTranslator()
            self.translator.load(locale_path)
            QCoreApplication.installTranslator(self.translator)

        # Declare instance attributes
        self.actions = []
        self.menu = self.tr(u'&Switch Layers')
        # TODO: We are going to let the user set this up in a future iteration
        self.toolbar = self.iface.addToolBar(u'SwitchLayers')
        self.toolbar.setObjectName(u'SwitchLayers')

        self.pluginIsActive = False
        self.dockwidget = None


    # noinspection PyMethodMayBeStatic
    def tr(self, message):
        """Get the translation for a string using Qt translation API.

        We implement this ourselves since we do not inherit QObject.

        :param message: String for translation.
        :type message: str, QString

        :returns: Translated version of message.
        :rtype: QString
        """
        # noinspection PyTypeChecker,PyArgumentList,PyCallByClass
        return QCoreApplication.translate('SwitchLayers', message)


    def add_action(
        self,
        icon_path,
        text,
        callback,
        enabled_flag=True,
        add_to_menu=True,
        add_to_toolbar=True,
        status_tip=None,
        whats_this=None,
        parent=None):
        """Add a toolbar icon to the toolbar.

        :param icon_path: Path to the icon for this action. Can be a resource
            path (e.g. ':/plugins/foo/bar.png') or a normal file system path.
        :type icon_path: str

        :param text: Text that should be shown in menu items for this action.
        :type text: str

        :param callback: Function to be called when the action is triggered.
        :type callback: function

        :param enabled_flag: A flag indicating if the action should be enabled
            by default. Defaults to True.
        :type enabled_flag: bool

        :param add_to_menu: Flag indicating whether the action should also
            be added to the menu. Defaults to True.
        :type add_to_menu: bool

        :param add_to_toolbar: Flag indicating whether the action should also
            be added to the toolbar. Defaults to True.
        :type add_to_toolbar: bool

        :param status_tip: Optional text to show in a popup when mouse pointer
            hovers over the action.
        :type status_tip: str

        :param parent: Parent widget for the new action. Defaults None.
        :type parent: QWidget

        :param whats_this: Optional text to show in the status bar when the
            mouse pointer hovers over the action.

        :returns: The action that was created. Note that the action is also
            added to self.actions list.
        :rtype: QAction
        """

        icon = QIcon(icon_path)
        action = QAction(icon, text, parent)
        action.triggered.connect(callback)
        action.setEnabled(enabled_flag)

        if status_tip is not None:
            action.setStatusTip(status_tip)

        if whats_this is not None:
            action.setWhatsThis(whats_this)

        if add_to_toolbar:
            self.toolbar.addAction(action)

        if add_to_menu:
            self.iface.addPluginToMenu(
                self.menu,
                action)

        self.actions.append(action)

        return action


    def initGui(self):
        """Create the menu entries and toolbar icons inside the QGIS GUI."""

        icon_path = ':/plugins/switch_layers/icon.png'
        self.add_action(
            icon_path,
            text=self.tr(u'Switch Layers'),
            callback=self.run,
            parent=self.iface.mainWindow())

    #--------------------------------------------------------------------------

    def onClosePlugin(self):
        """Cleanup necessary items here when plugin dockwidget is closed"""

        # disconnects
        self.dockwidget.closingPlugin.disconnect(self.onClosePlugin)

        self.pluginIsActive = False


    def unload(self):
        """Removes the plugin menu item and icon from QGIS GUI."""

        for action in self.actions:
            self.iface.removePluginMenu(
                self.tr(u'&Switch Layers'),
                action)
            self.iface.removeToolBarIcon(action)
        # remove the toolbar
        del self.toolbar
        del self.root

    #--------------------------------------------------------------------------

    def run(self):
        """Run method that loads and starts the plugin"""

        if not self.pluginIsActive:
            self.pluginIsActive = True
            #print "** STARTING SwitchLayers"

            # dockwidget may not exist if:
            #    first run of plugin
            #    removed on close (see self.onClosePlugin method)
            if self.dockwidget == None:
                # Create the dockwidget (after translation) and keep reference
                self.dockwidget = SwitchLayersDockWidget()
            

            # connect to provide cleanup on closing of dockwidget
            self.dockwidget.closingPlugin.connect(self.onClosePlugin)

            # show the dockwidget
            # TODO: fix to allow choice of dock location
            self.iface.addDockWidget(Qt.LeftDockWidgetArea, self.dockwidget)
            self.dockwidget.cbGroup.clear()
            self.dockwidget.cbGroup.addItems(self.getGroupNames())
            self.dockwidget.show()

        # layer state
        self.layers = []
        self.layerIndex = 0
        self.dockwidget.cbGroup.currentIndexChanged.connect(self.updateGroupVisibility)
        self.dockwidget.horizontalSlider.valueChanged.connect(self.updateLayerVisibility)


    def getGroups(self):
        groups = []
        for child in self.root.children():
            if isinstance(child, QgsLayerTreeGroup):
                groups.append(child)
        return groups
    

    def getGroupNames(self):
        names = [grp.name() for grp in self.getGroups()]
        names.insert(0, " ")
        return names


    def updateGroupVisibility(self, index):
        if index != 0:
            groups = self.getGroups()
            for group in groups:
                group.setItemVisibilityChecked(False)
            groups[index-1].setItemVisibilityChecked(True)
            self.setLayers(groups[index-1])
            self.activateSlider()


    def activateSlider(self):
        self.dockwidget.horizontalSlider.setMaximum(len(self.layers)-1)
        self.updateLayerVisibility(self.layerIndex)


    def setLayers(self, group):
        layers = []
        for child in group.children():
            if isinstance(child, QgsLayerTreeLayer):
                layers.append(child)
        self.layers = layers[::-1]


    def updateLayerVisibility(self, index):
        for layer in self.layers:
            layer.setItemVisibilityChecked(False)
        self.layers[index].setItemVisibilityChecked(True)
        self.layerIndex = index 
        self.setLayerName()


    def setLayerName(self):
        print(self.dockwidget.labelName.text())
        self.dockwidget.labelName.setText(self.layers[self.layerIndex].name())