import os
import nuke
import nukescripts.toolsets
import toolset_manager

try:
    from PySide6 import QtCore, QtWidgets
    import shiboken6 as shiboken
except ImportError:
    from PySide2 import QtCore, QtWidgets
    import shiboken2 as shiboken


# --------------------------------------------------------------
# TOOLSET MENU COMMANDS
# --------------------------------------------------------------

toolsets_menu = nuke.menu("Nodes").findItem("ToolSets")

if toolsets_menu:
    if toolsets_menu.findItem("Edit Description") is None:
        toolsets_menu.addCommand(
            "Edit Description",
            toolset_manager.edit_description,
            icon="Text.png",
            index=1
        )

nukescripts.toolsets.addToolsetsPanel = (
    toolset_manager.create_toolset_with_description
)

toolset_manager.install_menu_refresh()

toolsets_menu = nuke.menu("Nodes").findItem("ToolSets")

if toolsets_menu:
    if toolsets_menu.findItem("Search ToolSets") is None:
        toolsets_menu.addCommand(
            "Search ToolSets",
            toolset_manager.search_toolsets,
            icon="EdgeDetect.png",
            index=2
        )


# --------------------------------------------------------------
# TOOLTIP INITIALIZATION
# --------------------------------------------------------------

_tooltip_timer = QtCore.QTimer()
_tooltip_timer.setInterval(250)

_tooltip_last_signature = None
_tooltip_stable_checks = 0
_tooltip_checks = 0

_TOOLTIP_REQUIRED_STABLE_CHECKS = 4
_TOOLTIP_MAX_CHECKS = 80


def _check_toolset_menu():
    global _tooltip_last_signature
    global _tooltip_stable_checks
    global _tooltip_checks

    _tooltip_checks += 1

    buttons = []

    for widget in QtWidgets.QApplication.allWidgets():
        try:
            if (
                shiboken.isValid(widget)
                and isinstance(widget, QtWidgets.QToolButton)
                and widget.text() == "ToolSets"
            ):
                buttons.append(widget)
        except RuntimeError:
            continue

    if len(buttons) == 1:
        button = buttons[0]

        try:
            menu = button.menu()

            if (
                button.isVisible()
                and menu is not None
                and shiboken.isValid(menu)
                and menu.title() == "ToolSets"
            ):
                signature = (
                    shiboken.getCppPointer(menu)[0],
                    tuple(
                        shiboken.getCppPointer(action)[0]
                        for action in menu.actions()
                        if shiboken.isValid(action)
                    )
                )

                if signature == _tooltip_last_signature:
                    _tooltip_stable_checks += 1
                else:
                    _tooltip_last_signature = signature
                    _tooltip_stable_checks = 1

                if (
                    _tooltip_stable_checks
                    >= _TOOLTIP_REQUIRED_STABLE_CHECKS
                ):
                    # Stop retrying if the descriptions file
                    # is missing or cannot be loaded.
                    if not os.path.isfile(
                        toolset_manager.JSON_PATH
                    ):
                        toolset_manager.load_descriptions()
                        _tooltip_timer.stop()
                        print(
                            "Toolset Manager: tooltip initialization "
                            "stopped - descriptions.json is missing"
                        )
                        return

                    success = toolset_manager.apply_all_tooltips()

                    if success:
                        _tooltip_timer.stop()
                        print("Toolset Manager: tooltips initialized")
                        return

                    # A readable file can still contain invalid JSON
                    # or fail validation.
                    if getattr(
                        toolset_manager,
                        "_descriptions_error_shown",
                        None
                    ) is not None:
                        _tooltip_timer.stop()
                        print(
                            "Toolset Manager: tooltip initialization "
                            "stopped - descriptions could not be loaded"
                        )
                        return

        except RuntimeError:
            pass

    if _tooltip_checks >= _TOOLTIP_MAX_CHECKS:
        _tooltip_timer.stop()
        print("Toolset Manager: tooltip initialization timed out")


_tooltip_timer.timeout.connect(_check_toolset_menu)
_tooltip_timer.start()
