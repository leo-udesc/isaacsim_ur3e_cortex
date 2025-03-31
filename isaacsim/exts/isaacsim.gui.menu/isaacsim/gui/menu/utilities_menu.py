import omni.kit.menu.utils
from omni.kit.menu.utils import LayoutSourceSearch, MenuItemDescription, MenuLayout


class UtilitiesMenuExtension:
    def __init__(self, ext_id):
        self._menu_placeholder = [MenuItemDescription(name="placeholder", show_fn=lambda: False)]
        omni.kit.menu.utils.add_menu_items(self._menu_placeholder, "Utilities")

        self.__menu_layout = [
            MenuLayout.Menu(
                "Utilities",
                [
                    MenuLayout.Seperator("Profilers & Debuggers"),
                    MenuLayout.Item("OmniGraph Tool Kit", source="Window/Visual Scripting/Toolkit"),
                    MenuLayout.Item("Physics Debugger", source="Window/Physics/Debug"),
                    MenuLayout.Item("Profiler", source="Window/Profiler"),
                    MenuLayout.Item("Statistics"),
                    MenuLayout.Seperator(),
                    MenuLayout.Item("Generate Extension Templates"),
                    MenuLayout.Item("Registered Actions", source="Window/Actions"),
                ],
            )
        ]
        omni.kit.menu.utils.add_layout(self.__menu_layout)

    def __del__(self):
        omni.kit.menu.utils.remove_layout(self.__menu_layout)
        omni.kit.menu.utils.remove_menu_items(self._menu_placeholder, "Utilities")
