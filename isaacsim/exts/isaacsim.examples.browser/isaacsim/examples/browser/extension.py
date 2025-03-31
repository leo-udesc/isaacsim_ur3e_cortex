# Copyright (c) 2022-2024, NVIDIA CORPORATION. All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto. Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
#

from typing import Optional

import carb.settings
import omni.ext
import omni.kit.menu.utils
import omni.ui as ui
from omni.kit.browser.folder.core import TreeFolderBrowserWidgetEx

from .model import ExampleBrowserModel
from .window import ExampleBrowserWindow

_extension_instance = None
BROWSER_MENU_ROOT = "Window"
SETTING_ROOT = "/exts/isaacsim.examples.browser/"
SETTING_VISIBLE_AFTER_STARTUP = SETTING_ROOT + "visible_after_startup"


class ExampleBrowserExtension(omni.ext.IExt):
    @property
    def window(self) -> Optional[ExampleBrowserWindow]:
        return self._window

    @property
    def browser_widget(self) -> Optional[TreeFolderBrowserWidgetEx]:
        return self._window._widget

    def on_startup(self, ext_id):
        self._browser_model = ExampleBrowserModel()

        self._window = None
        ui.Workspace.set_show_window_fn(
            ExampleBrowserWindow.WINDOW_TITLE,
            self._show_window,  # pylint: disable=unnecessary-lambda
        )
        self._register_menuitem()

        visible = carb.settings.get_settings().get_as_bool(SETTING_VISIBLE_AFTER_STARTUP)
        if visible:
            self._show_window(True)

        global _extension_instance
        _extension_instance = self

    def on_shutdown(self):
        omni.kit.menu.utils.remove_menu_items(self._menu_entry, name=BROWSER_MENU_ROOT)
        action_registry = omni.kit.actions.core.get_action_registry()
        action_registry.deregister_action("isaacsim.examples.browser", f"open_isaac_sim_examples_browser")

        self._browser_model.destroy()

        if self._window is not None:
            self._window.destroy()
            self._window = None

        global _extension_instance
        _extension_instance = None

    def register_example(self, **kwargs):
        self._browser_model.register_example(**kwargs)

    def deregister_example(self, **kwargs):
        self._browser_model.deregister_example(**kwargs)

    def _show_window(self, visible) -> None:
        if visible:
            if self._window is None:
                self._window = ExampleBrowserWindow(self._browser_model, visible=True)
                self._window.set_visibility_changed_fn(self._on_visibility_changed)
            else:
                self._window.visible = True
        else:
            self._window.visible = False

    def _toggle_window(self):
        self._show_window(not self._is_visible())

    def _register_menuitem(self):
        ## register the menu action
        action_registry = omni.kit.actions.core.get_action_registry()
        action_registry.register_action(
            "isaacsim.examples.browser",
            f"open_isaac_sim_examples_browser",
            lambda: self._show_window(True),
            description=f"Open Isaac Sim Examples Browser",
        )

        self._menu_entry = [
            omni.kit.menu.utils.MenuItemDescription(
                name="Examples",
                sub_menu=[
                    omni.kit.menu.utils.MenuItemDescription(
                        name="Robotics Examples",
                        ticked=True,
                        ticked_fn=self._is_visible,
                        onclick_fn=self._toggle_window,
                    )
                ],
            )
        ]
        omni.kit.menu.utils.add_menu_items(self._menu_entry, BROWSER_MENU_ROOT)

    def _is_visible(self):
        return self._window.visible if self._window else False

    def _on_visibility_changed(self, visible):
        omni.kit.menu.utils.refresh_menu_items(BROWSER_MENU_ROOT)


def get_instance():
    return _extension_instance
