import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext
import os
import glob
import yaml # PyYAML

class YamlTextEditorApp:
    def __init__(self, master):
        self.master = master
        master.title("YAML Text Viewer/Editor By MrGamesKingPro")
        master.geometry("800x600")

        self.current_folder_path = tk.StringVar()
        self.text_data = [] # List to store info about each text item
        self._item_count_for_status = 0 # Helper for counting items in load_files_from_folder

        # --- Top Frame for Folder Selection ---
        top_frame = tk.Frame(master)
        top_frame.pack(fill=tk.X, padx=10, pady=5)

        tk.Label(top_frame, text="Folder:").pack(side=tk.LEFT)
        self.folder_entry = tk.Entry(top_frame, textvariable=self.current_folder_path, state='readonly', width=60)
        self.folder_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        self.browse_button = tk.Button(top_frame, text="Browse...", command=self.browse_folder)
        self.browse_button.pack(side=tk.LEFT)

        # --- Main Frame for Text Display Area ---
        main_frame = tk.Frame(master)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        self.scrollbar = tk.Scrollbar(main_frame)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Replaced Listbox with Text widget for colored text
        self.text_display_area = tk.Text(main_frame, yscrollcommand=self.scrollbar.set,
                                         font=("Courier New", 10), wrap=tk.NONE, state=tk.DISABLED)
        self.text_display_area.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.scrollbar.config(command=self.text_display_area.yview)

        self.text_display_area.bind("<Double-1>", self.on_double_click)

        # Define color tags for the Text widget
        self.text_display_area.tag_configure("filename_color", foreground="green")
        self.text_display_area.tag_configure("messagekey_color", foreground="red")
        self.text_display_area.tag_configure("text_preview_color", foreground="black") # "Color as is"
        self.text_display_area.tag_configure("separator_color", foreground="grey50") # For " :: "

        # --- Status Bar ---
        self.status_var = tk.StringVar()
        self.status_bar = tk.Label(master, textvariable=self.status_var, bd=1, relief=tk.SUNKEN, anchor=tk.W)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        self.status_var.set("Select a folder to load YAML files.")

    def browse_folder(self):
        folder_selected = filedialog.askdirectory()
        if folder_selected:
            self.current_folder_path.set(folder_selected)
            self.load_files_from_folder(folder_selected)

    def _extract_texts_recursive(self, yaml_data_node, current_path_parts, filepath, filename):
        """
        Recursively traverses the YAML data to find string values.
        Appends info to self.text_data and inserts styled text into self.text_display_area.
        """
        if isinstance(yaml_data_node, dict):
            for key, value in yaml_data_node.items():
                key_str = str(key)
                new_path_parts = current_path_parts + [key_str]
                
                if isinstance(value, str):
                    message_key_path = ".".join(new_path_parts)
                    
                    self.text_data.append({
                        'filepath': filepath,
                        'message_key': message_key_path,
                        'original_text': value 
                    })
                    
                    # Replace newlines for better display in single-line preview
                    display_text_preview = str(value).replace('\n', ' ').replace('\r', '')
                    
                    # Insert into Text widget with colors
                    self.text_display_area.insert(tk.END, filename, "filename_color")
                    self.text_display_area.insert(tk.END, " :: ", "separator_color")
                    self.text_display_area.insert(tk.END, message_key_path, "messagekey_color")
                    self.text_display_area.insert(tk.END, " :: ", "separator_color")
                    
                    preview = display_text_preview[:100]
                    if len(display_text_preview) > 100:
                        preview += "..."
                    self.text_display_area.insert(tk.END, preview, "text_preview_color")
                    self.text_display_area.insert(tk.END, "\n") # Newline for each item

                    self._item_count_for_status += 1
                elif isinstance(value, dict):
                    self._extract_texts_recursive(value, new_path_parts, filepath, filename)

    def load_files_from_folder(self, folder_path):
        self.text_display_area.config(state=tk.NORMAL) # Enable for modification
        self.text_display_area.delete("1.0", tk.END)   # Clear existing content
        
        self.text_data = []
        self._item_count_for_status = 0

        yaml_files = glob.glob(os.path.join(folder_path, "*.yaml"))
        yaml_files.extend(glob.glob(os.path.join(folder_path, "*.yml")))

        if not yaml_files:
            self.status_var.set(f"No YAML files found in {folder_path}")
            self.text_display_area.config(state=tk.DISABLED) # Disable if no files
            return

        for filepath in yaml_files:
            filename = os.path.basename(filepath)
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    data = yaml.safe_load(f)
                
                if data is None: # Empty file or only comments
                    continue
                
                # Start recursive extraction from the root of the YAML data
                self._extract_texts_recursive(data, [], filepath, filename)

            except yaml.YAMLError as e:
                error_msg = f"Error parsing {filename}: {str(e)[:100]}"
                self.status_var.set(error_msg)
                print(f"Error parsing {filepath}: {e}")
            except Exception as e:
                error_msg = f"Error reading {filename}: {str(e)[:100]}"
                self.status_var.set(error_msg)
                print(f"Error reading {filepath}: {e}")
        
        self.text_display_area.config(state=tk.DISABLED) # Disable after all insertions
        self.status_var.set(f"Loaded {self._item_count_for_status} text items from {len(yaml_files)} YAML files.")

    def _get_value_by_path(self, data_dict, path_str):
        keys = path_str.split('.')
        current_level = data_dict
        for key_segment in keys:
            if isinstance(current_level, dict) and key_segment in current_level:
                current_level = current_level[key_segment]
            else:
                return None 
        return current_level

    def _set_value_by_path(self, data_dict, path_str, value_to_set):
        keys = path_str.split('.')
        current_level = data_dict
        
        for key_segment in keys[:-1]: 
            if isinstance(current_level, dict) and key_segment in current_level:
                current_level = current_level[key_segment]
            else:
                return False 
        
        last_key = keys[-1]
        if isinstance(current_level, dict) and last_key in current_level: # Check if last_key exists
            current_level[last_key] = value_to_set
            return True
        return False

    def on_double_click(self, event):
        # Get the line number at the click position (1-based for Text widget)
        try:
            # Get the beginning of the line clicked
            text_widget_index = self.text_display_area.index(f"@{event.x},{event.y} linestart")
            line_number_str = text_widget_index.split('.')[0]
            line_number = int(line_number_str)
            # Convert to 0-based index for self.text_data
            selected_0_based_index = line_number - 1 
        except (tk.TclError, ValueError): # Click might be outside text content or error parsing index
            return # Ignore click

        if 0 <= selected_0_based_index < len(self.text_data):
            item_data = self.text_data[selected_0_based_index]
            self.open_edit_dialog(selected_0_based_index, item_data)
        else:
            # This can happen if the click is on an empty area after the last line of text
            # or if self.text_data got out of sync (less likely with current design)
            # No error message needed, just ignore the click.
            pass

    def open_edit_dialog(self, item_0_based_index, item_data):
        edit_window = tk.Toplevel(self.master)
        edit_window.title(f"Edit Text")
        edit_window.geometry("600x400")
        edit_window.transient(self.master) 
        edit_window.grab_set() 

        try:
            with open(item_data['filepath'], 'r', encoding='utf-8') as f:
                full_yaml_data = yaml.safe_load(f)
            
            current_text_val = self._get_value_by_path(full_yaml_data, item_data['message_key'])
            
            if current_text_val is None:
                messagebox.showerror("Error", f"Could not find the text at path '{item_data['message_key']}'. The file structure might have changed externally.", parent=edit_window)
                edit_window.destroy()
                return
            if not isinstance(current_text_val, str):
                messagebox.showerror("Error", f"The value at path '{item_data['message_key']}' is no longer a string (Type: {type(current_text_val).__name__}). Cannot edit.", parent=edit_window)
                edit_window.destroy()
                return
                
        except Exception as e:
            messagebox.showerror("Error", f"Could not re-read text for editing: {e}", parent=edit_window)
            edit_window.destroy()
            return
            
        tk.Label(edit_window, text=f"File: {os.path.basename(item_data['filepath'])}\nKey Path: {item_data['message_key']}", 
                 justify=tk.LEFT, pady=10).pack(anchor=tk.W, padx=10)

        text_widget_editor = scrolledtext.ScrolledText(edit_window, wrap=tk.WORD, height=15, width=70, font=("Arial", 10))
        text_widget_editor.pack(padx=10, pady=5, fill=tk.BOTH, expand=True)
        text_widget_editor.insert(tk.END, current_text_val)
        text_widget_editor.focus_set() # Set focus to the text editor

        button_frame = tk.Frame(edit_window)
        button_frame.pack(pady=10)

        def save_changes():
            new_text = text_widget_editor.get("1.0", tk.END).rstrip('\n') # Remove only trailing newline

            try:
                with open(item_data['filepath'], 'r', encoding='utf-8') as f:
                    yaml_content = yaml.safe_load(f)
                
                if not self._set_value_by_path(yaml_content, item_data['message_key'], new_text):
                    messagebox.showerror("Save Error", f"Failed to update the value at path '{item_data['message_key']}'. The file structure may have changed.", parent=edit_window)
                    return

                with open(item_data['filepath'], 'w', encoding='utf-8') as f:
                    # Preserving key order (sort_keys=False) and block style (default_flow_style=False)
                    yaml.dump(yaml_content, f, sort_keys=False, default_flow_style=False, allow_unicode=True, indent=2)

                # Update internal data store
                self.text_data[item_0_based_index]['original_text'] = new_text 
                
                # Update the Text widget display for the modified line
                self.text_display_area.config(state=tk.NORMAL)
                
                target_line_1_based = item_0_based_index + 1
                
                # Delete the old line content including its newline
                # Deletes from start of target_line_1_based to start of the next line
                self.text_display_area.delete(f"{target_line_1_based}.0", f"{target_line_1_based + 1}.0")

                # Prepare new content parts for display
                filename_part = os.path.basename(item_data['filepath'])
                message_key_part = item_data['message_key']
                display_text_updated_preview = str(new_text).replace('\n', ' ').replace('\r', '')
                preview_updated = display_text_updated_preview[:100]
                if len(display_text_updated_preview) > 100:
                    preview_updated += "..."
                
                # Insert new content with tags. tk.INSERT refers to the current cursor position,
                # which automatically advances after each insert on the same line.
                # Start insertion at the beginning of the now-empty line.
                insert_start_pos = f"{target_line_1_based}.0"

                self.text_display_area.insert(insert_start_pos, filename_part, "filename_color")
                self.text_display_area.insert(tk.INSERT, " :: ", "separator_color")
                self.text_display_area.insert(tk.INSERT, message_key_part, "messagekey_color")
                self.text_display_area.insert(tk.INSERT, " :: ", "separator_color")
                self.text_display_area.insert(tk.INSERT, preview_updated, "text_preview_color")
                self.text_display_area.insert(tk.INSERT, "\n") # Add the newline for this logical line

                # Manage selection and view
                self.text_display_area.tag_remove(tk.SEL, "1.0", tk.END) # Clear previous selection (if any)
                start_sel = f"{target_line_1_based}.0"
                # .end on a line refers to the position just BEFORE the newline character of that line.
                end_sel = f"{target_line_1_based}.end" 
                self.text_display_area.tag_add(tk.SEL, start_sel, end_sel)
                self.text_display_area.see(start_sel) # Ensure the updated line is visible

                self.text_display_area.config(state=tk.DISABLED)

                self.status_var.set(f"Saved changes to '{item_data['message_key']}' in {filename_part}")
                edit_window.destroy()

            except Exception as e:
                messagebox.showerror("Save Error", f"Could not save changes: {e}", parent=edit_window)
                self.status_var.set(f"Error saving: {e}")


        save_button = tk.Button(button_frame, text="Save", command=save_changes, width=10)
        save_button.pack(side=tk.LEFT, padx=5)

        cancel_button = tk.Button(button_frame, text="Cancel", command=edit_window.destroy, width=10)
        cancel_button.pack(side=tk.LEFT, padx=5)

if __name__ == "__main__":
    root = tk.Tk()
    app = YamlTextEditorApp(root)
    root.mainloop()
