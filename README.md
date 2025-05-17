# YAML-Text-Viewer-Editor
This tool allows you to browse a folder containing YAML files (.yaml or .yml), view all string values within those files along with their hierarchical keys, and edit these string values directly.

### Python Requirements

 install Python 3.6 or newer, 

1.  install library:

    ```bash
        pip install PyYAML
    ```

---

### How to Use the YAML Text Viewer/Editor


**1. Launching the tool:**
   ```bash
   python Yaml-Text-Viewer-Editor.py
   ```


**2. Selecting a Folder:**
   *   At the top of the window, you'll see a "Folder:" label, an empty (or previously selected) path field, and a "Browse..." button.
   *   Click the **"Browse..."** button.
   *   A system dialog will open, allowing you to navigate your file system and select a folder that contains the YAML files you want to work with.
   *   Once you select a folder and click "OK" (or "Select Folder"), the path to this folder will appear in the entry field.

**3. Loading and Viewing YAML Text Items:**
   *   After selecting a folder, the tool will automatically scan it for files with `.yaml` and `.yml` extensions.
   *   It will parse each YAML file and recursively extract all string values.
   *   The main text area below the folder selection will populate with entries for each found string. Each entry is formatted as:
     ```
     filename.yaml :: path.to.your.key :: First 100 characters of the string value...
     ```
     *   **`filename.yaml`** (green): The name of the YAML file where the text is located.
     *   **`::`** (grey): A separator.
     *   **`path.to.your.key`** (red): The full dot-separated path to the key within the YAML structure.
     *   **`::`** (grey): Another separator.
     *   **`First 100 characters...`** (black): A preview of the actual string value. If the string is longer than 100 characters, it will be truncated with "..." for display in this list. Newlines in the original string are replaced with spaces for this preview.
   *   You can use the scrollbar on the right to navigate through all the loaded text items.
   *   The **Status Bar** at the bottom of the window will update to show how many text items were loaded from how many YAML files (e.g., "Loaded 150 text items from 5 YAML files."). It will also display errors if any YAML files could not be parsed.

**4. Editing a Text Item:**
   *   To edit a specific string value, **double-click** on its corresponding line in the main text display area.
   *   An "Edit Text" dialog window will pop up. This window will show:
     *   The **File** and **Key Path** of the item you are editing.
     *   A **multi-line text editor** (ScrolledText widget) containing the *full, original* string value associated with that key.
   *   You can now modify the text in this editor.

**5. Saving or Canceling Edits:**
   *   In the "Edit Text" dialog:
     *   **Save Button:**
       *   Click "Save" to apply your changes.
       *   The application will:
         1.  Re-read the original YAML file.
         2.  Update the specific key's value with your new text.
         3.  Write the entire modified YAML content back to the file, attempting to preserve formatting (like key order and indentation) as much as PyYAML allows.
         4.  Update the corresponding line in the main application's text display area with the new preview.
         5.  The edited line in the main display will be highlighted (selected) and brought into view.
         6.  The "Edit Text" dialog will close.
         7.  The status bar will show a confirmation message (e.g., "Saved changes to 'key.path' in filename.yaml").
     *   **Cancel Button:**
       *   Click "Cancel" to discard any changes you made in the "Edit Text" dialog.
       *   The dialog will close, and the original YAML file and the main display will remain unchanged.
   *   If any error occurs during saving (e.g., the file was modified externally and the key path is no longer valid), an error message box will appear.

**6. Working with Other Folders:**
   *   If you want to work with YAML files in a different folder, simply click the "Browse..." button again and select a new folder. The main display area will clear and then populate with the text items from the newly selected folder.

**Example Workflow:**
1.  Run the script.
2.  Click "Browse...", navigate to `C:\MyProjects\ConfigFolder`, and select it.
3.  The main area shows lines like:
    ```
    english.yaml :: welcome_message :: Hello, welcome to our application!
    english.yaml :: errors.not_found :: The requested item could not be found.
    french.yaml :: welcome_message :: Bonjour, bienvenue dans notre application!
    ```
4.  You want to change the English "not_found" message. Double-click the line: `english.yaml :: errors.not_found :: The requested item...`.
5.  The "Edit Text" dialog appears. The text box shows "The requested item could not be found."
6.  You change it to "Sorry, we couldn't find what you were looking for."
7.  Click "Save".
8.  The dialog closes. The line in the main window updates to: `english.yaml :: errors.not_found :: Sorry, we couldn't find what you...`
9.  The `english.yaml` file on your disk is now updated with the new message.

This tool is particularly useful for managing localization files or any YAML-based configuration where you need to quickly find and modify text strings across multiple files without manually opening each one and navigating complex structures.
