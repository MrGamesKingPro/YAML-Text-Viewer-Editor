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

        self.text_display_area = tk.Text(main_frame, yscrollcommand=self.scrollbar.set,
                                         font=("Courier New", 10), wrap=tk.NONE, state=tk.DISABLED)
        self.text_display_area.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.scrollbar.config(command=self.text_display_area.yview)

        # Event bindings
        self.text_display_area.bind("<Double-1>", self.on_double_click)
        # Add new binding for single mouse press
        self.text_display_area.bind("<ButtonPress-1>", self.on_mouse_press)


        # Define color tags for the Text widget
        self.text_display_area.tag_configure("filename_color", foreground="green")
        self.text_display_area.tag_configure("messagekey_color", foreground="red")
        self.text_display_area.tag_configure("text_preview_color", foreground="black") # "Color as is"
        self.text_display_area.tag_configure("separator_color", foreground="grey50") # For " :: "
        # Add new tag for line highlighting
        self.text_display_area.tag_configure("line_highlight", background="light sky blue")


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
                    
                    display_text_preview = str(value).replace('\n', ' ').replace('\r', '')
                    
                    self.text_display_area.insert(tk.END, filename, "filename_color")
                    self.text_display_area.insert(tk.END, " :: ", "separator_color")
                    self.text_display_area.insert(tk.END, message_key_path, "messagekey_color")
                    self.text_display_area.insert(tk.END, " :: ", "separator_color")
                    
                    preview = display_text_preview[:100]
                    if len(display_text_preview) > 100:
                        preview += "..."
                    self.text_display_area.insert(tk.END, preview, "text_preview_color")
                    self.text_display_area.insert(tk.END, "\n")

                    self._item_count_for_status += 1
                elif isinstance(value, dict):
                    self._extract_texts_recursive(value, new_path_parts, filepath, filename)

    def load_files_from_folder(self, folder_path):
        self.text_display_area.config(state=tk.NORMAL) 
        self.text_display_area.delete("1.0", tk.END)   
        
        self.text_data = []
        self._item_count_for_status = 0

        yaml_files = glob.glob(os.path.join(folder_path, "*.yaml"))
        yaml_files.extend(glob.glob(os.path.join(folder_path, "*.yml")))

        if not yaml_files:
            self.status_var.set(f"No YAML files found in {folder_path}")
            self.text_display_area.config(state=tk.DISABLED)
            return

        for filepath in yaml_files:
            filename = os.path.basename(filepath)
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    data = yaml.safe_load(f)
                
                if data is None: 
                    continue
                
                self._extract_texts_recursive(data, [], filepath, filename)

            except yaml.YAMLError as e:
                error_msg = f"Error parsing {filename}: {str(e)[:100]}"
                self.status_var.set(error_msg)
                print(f"Error parsing {filepath}: {e}")
            except Exception as e:
                error_msg = f"Error reading {filename}: {str(e)[:100]}"
                self.status_var.set(error_msg)
                print(f"Error reading {filepath}: {e}")
        
        self.text_display_area.config(state=tk.DISABLED) 
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
        if isinstance(current_level, dict) and last_key in current_level:
            current_level[last_key] = value_to_set
            return True
        return False

    # New method to handle mouse press for line highlighting
    def on_mouse_press(self, event):
        current_widget_state = self.text_display_area.cget("state")
        if current_widget_state == tk.DISABLED:
            self.text_display_area.config(state=tk.NORMAL)

        # Remove any existing custom line highlight from all lines
        self.text_display_area.tag_remove("line_highlight", "1.0", tk.END)

        try:
            # Get the index of the character at the click, then the start of that line
            # e.g., "5.0" for the start of the 5th line
            line_start_index = self.text_display_area.index(f"@{event.x},{event.y} linestart")
            
            # Get the line number (1-based) as an integer
            line_number = int(line_start_index.split('.')[0])

            # Ensure this line number corresponds to an actual item in self.text_data
            # self.text_data is 0-based, Text widget lines are 1-based
            if 1 <= line_number <= len(self.text_data):
                # Define the end of the line (before the newline character)
                line_end_index = f"{line_number}.end" # e.g. "5.end"
                
                # Add the highlight tag to the current line
                self.text_display_area.tag_add("line_highlight", line_start_index, line_end_index)
            # If the click is on an empty line or beyond actual content, no highlight is applied
            # as the previous highlight was already removed.

        except tk.TclError:
            # This can happen if clicking in an empty area of the Text widget
            # (e.g., below all text). In this case, we do nothing.
            pass
        finally:
            # Restore the original state of the text widget if it was changed
            if current_widget_state == tk.DISABLED:
                self.text_display_area.config(state=tk.DISABLED)

    def on_double_click(self, event):
        try:
            text_widget_index = self.text_display_area.index(f"@{event.x},{event.y} linestart")
            line_number_str = text_widget_index.split('.')[0]
            line_number = int(line_number_str)
            selected_0_based_index = line_number - 1 
        except (tk.TclError, ValueError):
            return

        if 0 <= selected_0_based_index < len(self.text_data):
            item_data = self.text_data[selected_0_based_index]
            self.open_edit_dialog(selected_0_based_index, item_data)
        else:
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
        text_widget_editor.focus_set()

        button_frame = tk.Frame(edit_window)
        button_frame.pack(pady=10)

        def save_changes():
            new_text = text_widget_editor.get("1.0", tk.END).rstrip('\n')

            try:
                with open(item_data['filepath'], 'r', encoding='utf-8') as f:
                    yaml_content = yaml.safe_load(f)
                
                if not self._set_value_by_path(yaml_content, item_data['message_key'], new_text):
                    messagebox.showerror("Save Error", f"Failed to update the value at path '{item_data['message_key']}'. The file structure may have changed.", parent=edit_window)
                    return

                with open(item_data['filepath'], 'w', encoding='utf-8') as f:
                    yaml.dump(yaml_content, f, sort_keys=False, default_flow_style=False, allow_unicode=True, indent=2)

                self.text_data[item_0_based_index]['original_text'] = new_text 
                
                self.text_display_area.config(state=tk.NORMAL)
                
                target_line_1_based = item_0_based_index + 1
                
                self.text_display_area.delete(f"{target_line_1_based}.0", f"{target_line_1_based + 1}.0")

                filename_part = os.path.basename(item_data['filepath'])
                message_key_part = item_data['message_key']
                display_text_updated_preview = str(new_text).replace('\n', ' ').replace('\r', '')
                preview_updated = display_text_updated_preview[:100]
                if len(display_text_updated_preview) > 100:
                    preview_updated += "..."
                
                insert_start_pos = f"{target_line_1_based}.0"

                self.text_display_area.insert(insert_start_pos, filename_part, "filename_color")
                self.text_display_area.insert(tk.INSERT, " :: ", "separator_color")
                self.text_display_area.insert(tk.INSERT, message_key_part, "messagekey_color")
                self.text_display_area.insert(tk.INSERT, " :: ", "separator_color")
                self.text_display_area.insert(tk.INSERT, preview_updated, "text_preview_color")
                self.text_display_area.insert(tk.INSERT, "\n")

                self.text_display_area.tag_remove(tk.SEL, "1.0", tk.END) 
                start_sel = f"{target_line_1_based}.0"
                end_sel = f"{target_line_1_based}.end" 
                self.text_display_area.tag_add(tk.SEL, start_sel, end_sel)
                self.text_display_area.see(start_sel) 

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
