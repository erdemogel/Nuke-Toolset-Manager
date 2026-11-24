import os
import json
import nuke
try:
    from PySide6 import QtWidgets, QtGui
except ImportError:
    from PySide2 import QtWidgets, QtGui

JSON_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "descriptions.json"
)


def load_descriptions():
    global _descriptions_error_shown

    if "_descriptions_error_shown" not in globals():
        _descriptions_error_shown = None

    try:
        with open(JSON_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)

        if not isinstance(data, dict):
            raise ValueError(
                "Descriptions must be a JSON object."
            )

        if not all(
            isinstance(key, str) and isinstance(value, str)
            for key, value in data.items()
        ):
            raise ValueError(
                "All toolset paths and descriptions must be strings."
            )

        _descriptions_error_shown = None
        return data

    except FileNotFoundError:
        error_type = "missing"
        message = (
            "Toolset Manager - Missing File\n\n"
            "The descriptions.json file could not be found.\n\n"
            "Please restore it in the Toolset Manager directory."
        )

    except (json.JSONDecodeError, ValueError):
        error_type = "invalid"
        message = (
            "Toolset Manager - Invalid JSON\n\n"
            "The descriptions.json file contains invalid data.\n\n"
            "Please check or restore the file."
        )

    except OSError as error:
        error_type = "file_error"
        message = (
            "Toolset Manager - File Error\n\n"
            "Unable to read descriptions.json.\n\n"
            "{}".format(error)
        )

    if _descriptions_error_shown != error_type:
        _descriptions_error_shown = error_type
        nuke.message(message)

    return None


def save_descriptions(data, show_error=True):
    import tempfile

    temp_path = None

    try:
        directory = os.path.dirname(JSON_PATH)

        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=directory,
            prefix=".descriptions_",
            suffix=".tmp",
            delete=False
        ) as temp_file:
            temp_path = temp_file.name
            json.dump(data, temp_file, indent=4)
            temp_file.flush()
            os.fsync(temp_file.fileno())

        os.replace(temp_path, JSON_PATH)
        return True

    except (OSError, TypeError, ValueError) as error:
        if show_error:
            nuke.message(
                "Toolset Manager - Save Error\n\n"
                "Unable to save descriptions.json.\n\n"
                "Your existing descriptions have not been intentionally reset.\n\n"
                "{}".format(error)
            )
        else:
            print("Toolset Manager - Save Error:", error)

        return False

    finally:
        if temp_path:
            try:
                os.remove(temp_path)
            except FileNotFoundError:
                pass
            except OSError as error:
                print(
                    "Toolset Manager - Temporary file cleanup failed:",
                    error
                )



def is_toolset_file(path):
    for directory in nuke.pluginPath():
        toolset_file = os.path.join(
            directory,
            "ToolSets",
            *path.split("/")
        ) + ".nk"

        if os.path.isfile(toolset_file):
            return True

    return False


def build_toolset_menu():
    root = QtWidgets.QMenu("Select Toolset")
    source = nuke.menu("Nodes").findItem("ToolSets")

    def add_items(source_menu, target_menu, prefix=""):
        for item in source_menu.items():
            name = item.name()

            if not name.strip() or name == "-":
                continue

            path = prefix + name
            submenu = nuke.menu("Nodes").findItem(
                "ToolSets/" + path
            )

            if submenu and hasattr(submenu, "items"):
                child = target_menu.addMenu(name)
                add_items(submenu, child, path + "/")
            elif is_toolset_file(path):
                action = target_menu.addAction(name)
                action.setData(path)

    if source:
        add_items(source, root)

    return root


def edit_description():
    dialog = QtWidgets.QDialog()
    dialog.setWindowTitle("Edit Toolset Description")
    dialog.resize(450, 220)

    layout = QtWidgets.QVBoxLayout(dialog)
    layout.addWidget(QtWidgets.QLabel("Toolset:"))

    row = QtWidgets.QHBoxLayout()
    toolset_field = QtWidgets.QLineEdit()
    toolset_field.setReadOnly(True)
    select_button = QtWidgets.QPushButton("Select Toolset...")

    row.addWidget(toolset_field)
    row.addWidget(select_button)
    layout.addLayout(row)

    layout.addWidget(QtWidgets.QLabel("Description:"))
    description_field = QtWidgets.QTextEdit()
    layout.addWidget(description_field)

    buttons = QtWidgets.QDialogButtonBox(
        QtWidgets.QDialogButtonBox.Save |
        QtWidgets.QDialogButtonBox.Cancel
    )
    layout.addWidget(buttons)

    def choose_toolset():
        popup = build_toolset_menu()

        if hasattr(popup, "exec"):
            selected = popup.exec(QtGui.QCursor.pos())
        else:
            selected = popup.exec_(QtGui.QCursor.pos())

        if selected:
            path = selected.data()

            descriptions = load_descriptions()

            if descriptions is None:
                return

            toolset_field.setText(path)
            description_field.setPlainText(
                descriptions.get(path, "")
            )

    def save_description():
        path = toolset_field.text().strip()

        if not path:
            nuke.message("Please select a toolset.")
            return

        data = load_descriptions()

        if data is None:
            return

        data[path] = description_field.toPlainText()

        if not save_descriptions(data):
            return

        print("Description saved:", path)
        apply_all_tooltips()
        dialog.accept()

    select_button.clicked.connect(choose_toolset)
    buttons.accepted.connect(save_description)
    buttons.rejected.connect(dialog.reject)

    if hasattr(dialog, "exec"):
        dialog.exec()
    else:
        dialog.exec_()



# --------------------------------------------------------------
# CREATE TOOLSET WITH DESCRIPTION
# --------------------------------------------------------------

import nukescripts.toolsets

class CreateToolsetWithDescription(
    nukescripts.toolsets.CreateToolsetsPanel
):
    def __init__(self):
        super(CreateToolsetWithDescription, self).__init__()

        self.descriptions = load_descriptions()

        self.removeKnob(self.okButton)
        self.removeKnob(self.cancelButton)

        self.description = nuke.Multiline_Eval_String_Knob(
            "description", "Description:"
        )

        self.addKnob(self.description)
        self.addKnob(self.okButton)
        self.addKnob(self.cancelButton)

    def createPreset(self):
        path = str(self.menuPath.value()).strip()
        description = self.description.value()

        data = load_descriptions()

        if data is None:
            return

        if nuke.createToolset(path):
            data[path] = description

            saved = save_descriptions(data, show_error=False)

            if not saved:
                nuke.message(
                    "Toolset Manager - Partial Success\n\n"
                    "The ToolSet was created successfully, "
                    "but its description could not be saved.\n\n"
                    "You can add the description later "
                    "using Edit Description."
                )

            self.finishModalDialog(True)

    def knobChanged(self, knob):
        super(CreateToolsetWithDescription, self).knobChanged(knob)

        menu_path = getattr(self, "menuPath", None)
        description_knob = getattr(self, "description", None)
        descriptions = getattr(self, "descriptions", None)

        if menu_path is None:
            return

        if knob != menu_path:
            return

        if description_knob is None or descriptions is None:
            return

        path = str(menu_path.value()).strip()

        description_knob.setValue(
            descriptions.get(path, "")
        )


def create_toolset_with_description():
    if nuke.nodesSelected():
        panel = CreateToolsetWithDescription()
        result = panel.showModalDialog()

        if result:
            nukescripts.toolsets.refreshToolsetsMenu()
    else:
        nuke.message("No nodes are selected")



# --------------------------------------------------------------
# TOOLSET TOOLTIPS
# --------------------------------------------------------------

def apply_all_tooltips():
    try:
        from PySide6 import QtWidgets
        import shiboken6 as shiboken
    except ImportError:
        from PySide2 import QtWidgets
        import shiboken2 as shiboken

    descriptions = load_descriptions()
    if descriptions is None:
        return False

    widgets = QtWidgets.QApplication.allWidgets()

    menus = [
        w for w in widgets
        if isinstance(w, QtWidgets.QMenu)
        and shiboken.isValid(w)
    ]

    lookup = {}

    for menu in menus:
        try:
            action = menu.menuAction()
            if shiboken.isValid(action):
                lookup[shiboken.getCppPointer(action)[0]] = menu
        except RuntimeError:
            continue

    roots = []

    for button in widgets:
        if not isinstance(button, QtWidgets.QToolButton):
            continue

        if not shiboken.isValid(button):
            continue

        try:
            if button.isVisible() and button.text() == "ToolSets":
                root = button.menu()

                if (
                    root is not None
                    and shiboken.isValid(root)
                    and root.title() == "ToolSets"
                ):
                    roots.append(root)
        except RuntimeError:
            continue

    if len(roots) != 1:
        print("Tooltips skipped: active ToolSets menu not found uniquely")
        return False

    count = 0
    visited = set()

    def process_menu(menu, prefix=""):
        nonlocal count

        if not shiboken.isValid(menu):
            return

        pointer = shiboken.getCppPointer(menu)[0]

        if pointer in visited:
            return

        visited.add(pointer)
        menu.setToolTipsVisible(True)

        for action in menu.actions():
            if not shiboken.isValid(action):
                continue

            name = action.text().replace("&", "")
            path = prefix + name

            action_pointer = shiboken.getCppPointer(action)[0]
            submenu = lookup.get(action_pointer)

            if submenu is not None and shiboken.isValid(submenu):
                process_menu(submenu, path + "/")

            elif path in descriptions:
                action.setToolTip(descriptions[path])
                count += 1

            elif prefix or name not in (
                "Create",
                "Delete",
                "Edit Description",
                "Search ToolSets"
            ):
                action.setToolTip("")

    process_menu(roots[0])
    print("Tooltips applied:", count)
    return True


# --------------------------------------------------------------
# AUTOMATIC TOOLSET MENU RESTORATION
# --------------------------------------------------------------


def install_menu_refresh():
    original = nukescripts.toolsets.refreshToolsetsMenu

    if getattr(original, "_tm_wrapped", False):
        return

    def refresh_with_descriptions(*args, **kwargs):
        result = original(*args, **kwargs)

        menu = nuke.menu("Nodes").findItem("ToolSets")

        if menu and menu.findItem("Edit Description") is None:
            menu.addCommand(
                "Edit Description",
                edit_description,
                icon="Text.png",
                index=1
            )

        if menu and menu.findItem("Search ToolSets") is None:
            menu.addCommand(
                "Search ToolSets",
                search_toolsets,
                icon="EdgeDetect.png",
                index=2
            )

        apply_all_tooltips()
        return result

    refresh_with_descriptions._tm_wrapped = True

    nukescripts.toolsets.refreshToolsetsMenu = (
        refresh_with_descriptions
    )


# --------------------------------------------------------------
# LIVE TOOLSET SEARCH
# --------------------------------------------------------------

def search_toolsets():
    try:
        from PySide6 import QtWidgets
    except ImportError:
        from PySide2 import QtWidgets

    dialog = QtWidgets.QDialog()
    dialog.setWindowTitle("Search ToolSets")
    dialog.resize(450, 400)

    layout = QtWidgets.QVBoxLayout(dialog)

    search_field = QtWidgets.QLineEdit()
    search_field.setPlaceholderText("Search toolsets...")
    layout.addWidget(search_field)

    results_list = QtWidgets.QListWidget()
    layout.addWidget(results_list)

    def collect(menu, prefix=""):
        paths = []

        for item in menu.items():
            name = item.name()

            if not name.strip() or name == "-":
                continue

            path = prefix + name
            submenu = nuke.menu("Nodes").findItem(
                "ToolSets/" + path
            )

            if submenu and hasattr(submenu, "items"):
                paths.extend(collect(submenu, path + "/"))
            elif is_toolset_file(path):
                paths.append(path)

        return paths

    source = nuke.menu("Nodes").findItem("ToolSets")
    paths = collect(source) if source else []

    descriptions = load_descriptions()

    def filter_results(text=""):
        if descriptions is None:
            results_list.clear()
            return

        query = text.strip().lower()
        results_list.clear()

        for path in paths:
            description = descriptions.get(path, "")

            if query in path.lower() or query in description.lower():
                results_list.addItem(path)

    def load_toolset(item):
        path = item.text()
        menu_item = nuke.menu("Nodes").findItem(
            "ToolSets/" + path
        )

        if menu_item:
            menu_item.invoke()
            dialog.accept()

    search_field.textChanged.connect(filter_results)
    results_list.itemDoubleClicked.connect(load_toolset)

    filter_results()
    search_field.setFocus()

    if hasattr(dialog, "exec"):
        dialog.exec()
    else:
        dialog.exec_()
