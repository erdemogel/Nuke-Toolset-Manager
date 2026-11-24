# Nuke Toolset Manager

A custom ToolSet management extension for Foundry Nuke.

Enhances Nuke's built-in ToolSets with descriptions, a search panel, and menu tooltips.

## Features

- Create ToolSets with descriptions
- Add or edit descriptions for existing ToolSets
- Search ToolSets by name or description
- Display descriptions as tooltips in the ToolSets menu

## Installation

1. Download the plugin and ensure the folder is named `ToolsetManager`.
2. Place the folder inside your Nuke configuration directory:
   - **Windows:** `C:\Users\<username>\.nuke\`
   - **Linux:** `~/.nuke/`
3. Open your existing `init.py` file in the `.nuke` directory, or create one if it does not exist.
4. Add the following code:

```python
import nuke
nuke.pluginAddPath("./ToolsetManager")
```

If `import nuke` already exists, do not add it again.

5. Restart Nuke.

Your directory structure should look like this:

```text
.nuke/
├── init.py
└── ToolsetManager/
    ├── menu.py
    ├── toolset_manager.py
    ├── descriptions.json
    └── README.md
```

You do not need to modify your existing `.nuke/menu.py`.

No additional Python packages are required.

## Included Files

- `toolset_manager.py` — Main plugin implementation
- `menu.py` — Nuke menu integration
- `descriptions.json` — Stores ToolSet descriptions
- `README.md` — Installation and usage documentation

## Usage

Open Nuke's **ToolSets** menu to access:

- **Create** — Create a ToolSet and assign a description.
- **Edit Description** — Select an existing ToolSet to add or modify its description.
- **Search ToolSets** — Search by ToolSet name or description, then double-click a result to load it.
-   Hover over a ToolSet in the menu to view its description.

## Description Storage

Descriptions are stored locally in `descriptions.json`, inside the plugin directory.

**Important:** Do not delete or overwrite `descriptions.json` when updating the plugin if you want to preserve your existing descriptions.

## Compatibility

Supports both PySide2 and PySide6.

Tested on:

- **Nuke 14.1v8** — Linux, PySide2
- **Nuke 16.0v6** — Windows, PySide6

Other Nuke versions and operating systems may work but have not yet been verified.

## Notes

- Toolset Manager extends Nuke's existing ToolSets system.
- ToolSets remain stored and loaded through Nuke's native functionality.
- Descriptions are stored separately from the `.nk` ToolSet files.