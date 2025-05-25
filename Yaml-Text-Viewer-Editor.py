import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext
import os
import glob
# import yaml # PyYAML # Replaced with ruamel.yaml
from ruamel.yaml import YAML
from ruamel.yaml.error import YAMLError # For exception handling
import re

class YamlTextEditorApp:
    def __init__(self, master):
        self.master = master
        master.title("YAML Text Viewer/Editor By MrGamesKingPro")
        master.geometry("800x650") # Increased height for search bar

        # Initialize ruamel.yaml parser
        self.yaml_parser = YAML()
        self.yaml_parser.preserve_quotes = True
        # We rely on ruamel.yaml's round-trip capabilities to preserve existing indentation.
        # If specific default indentation is needed for *newly generated* YAML parts,
        # it can be set e.g., self.yaml_parser.indent(mapping=2, sequence=4, offset=2)
        # but for preserving existing formats, this is often not needed.

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

        # --- Search/Replace Frame ---
        search_frame = tk.Frame(master)
        search_frame.pack(fill=tk.X, padx=10, pady=(0, 5)) # Add some bottom padding

        tk.Label(search_frame, text="Search:").pack(side=tk.LEFT)
        self.search_var = tk.StringVar()
        self.search_entry = tk.Entry(search_frame, textvariable=self.search_var, width=20)
        self.search_entry.pack(side=tk.LEFT, padx=(2, 5))
        self.search_var.trace_add("write", self._on_search_term_change)

        tk.Label(search_frame, text="Replace:").pack(side=tk.LEFT)
        self.replace_var = tk.StringVar()
        self.replace_entry = tk.Entry(search_frame, textvariable=self.replace_var, width=20)
        self.replace_entry.pack(side=tk.LEFT, padx=(2,10))

        self.find_next_button = tk.Button(search_frame, text="Find Next", command=self.find_next_text, state=tk.DISABLED)
        self.find_next_button.pack(side=tk.LEFT, padx=2)

        self.replace_button = tk.Button(search_frame, text="Replace", command=self.replace_text, state=tk.DISABLED)
        self.replace_button.pack(side=tk.LEFT, padx=2)

        self.replace_all_button = tk.Button(search_frame, text="Replace All", command=self.replace_all_text, state=tk.DISABLED)
        self.replace_all_button.pack(side=tk.LEFT, padx=2)

        self.case_sensitive_var = tk.BooleanVar(value=True)
        self.case_sensitive_check = tk.Checkbutton(search_frame, text="Case Sensitive", variable=self.case_sensitive_var)
        self.case_sensitive_check.pack(side=tk.LEFT, padx=(5,0))

        # Search state variables
        self.current_search_result = None  # (item_index, match_start_in_original, match_end_in_original)
        self.last_search_offset = (0, 0)  # (item_idx, char_idx_in_original_text)
        self.last_searched_term_for_find_next = ""


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
        self.text_display_area.bind("<ButtonPress-1>", self.on_mouse_press)


        # Define color tags for the Text widget
        self.text_display_area.tag_configure("filename_color", foreground="green")
        self.text_display_area.tag_configure("messagekey_color", foreground="red")
        self.text_display_area.tag_configure("text_preview_color", foreground="black")
        self.text_display_area.tag_configure("separator_color", foreground="grey50")
        self.text_display_area.tag_configure("line_highlight", background="light sky blue")
        self.text_display_area.tag_configure("symbol_color", foreground="blue") # For special symbols

        # Regex for symbols.
        self.symbol_regex = re.compile(
            r"("
            r"\\(?:aub|kel|her|Com|SINV|sinv)(?:\[[0-9]+\]|[0-9]*[^\s\\]*)"
            r"|"
            r"\\(?:n|c|mar)(?:\[[0-9]+\]|[0-9]*)?"
            r"|"
            r"\\!"       # \!
            r"|<br>"      # <br>
            r"|\\\{"     # \{
            r"|\\\}"     # \}
            r"|\\[\\]"   # [] (literal brackets)
            r"|<>"        # <> (literal angle brackets)
            r"|\\"        # \ (literal backslash, if not part of a longer code)
            r")"
        )


        # --- Status Bar ---
        self.status_var = tk.StringVar()
        self.status_bar = tk.Label(master, textvariable=self.status_var, bd=1, relief=tk.SUNKEN, anchor=tk.W)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        self.status_var.set("Select a folder to load YAML files. Requires 'ruamel.yaml' library.")

    def _on_search_term_change(self, *args):
        search_term = self.search_var.get()
        if search_term:
            self.find_next_button.config(state=tk.NORMAL)
            self.replace_all_button.config(state=tk.NORMAL)
        else:
            self.find_next_button.config(state=tk.DISABLED)
            self.replace_button.config(state=tk.DISABLED)
            self.replace_all_button.config(state=tk.DISABLED)
            self.current_search_result = None
            self.last_search_offset = (0, 0)
            self.last_searched_term_for_find_next = ""
            
            try:
                current_widget_state = self.text_display_area.cget("state")
                if current_widget_state == tk.DISABLED:
                    self.text_display_area.config(state=tk.NORMAL)
                self.text_display_area.tag_remove("line_highlight", "1.0", tk.END)
                if current_widget_state == tk.DISABLED:
                    self.text_display_area.config(state=tk.DISABLED)
            except tk.TclError: 
                pass


    def browse_folder(self):
        folder_selected = filedialog.askdirectory()
        if folder_selected:
            self.current_folder_path.set(folder_selected)
            self.load_files_from_folder(folder_selected)
            self.search_var.set("") 

    def _insert_formatted_preview(self, preview_text):
        last_end = 0
        for match in self.symbol_regex.finditer(preview_text):
            start, end = match.span()
            if start > last_end:
                self.text_display_area.insert(tk.INSERT, preview_text[last_end:start], "text_preview_color")
            self.text_display_area.insert(tk.INSERT, preview_text[start:end], "symbol_color")
            last_end = end
        if last_end < len(preview_text):
            self.text_display_area.insert(tk.INSERT, preview_text[last_end:], "text_preview_color")

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
                    display_text_preview_full = str(value).replace('\n', ' ').replace('\r', '')
                    self.text_display_area.insert(tk.END, filename, "filename_color")
                    self.text_display_area.insert(tk.END, " :: ", "separator_color")
                    self.text_display_area.insert(tk.END, message_key_path, "messagekey_color")
                    self.text_display_area.insert(tk.END, " :: ", "separator_color")
                    preview = display_text_preview_full[:100]
                    if len(display_text_preview_full) > 100: preview += "..."
                    self._insert_formatted_preview(preview) 
                    self.text_display_area.insert(tk.END, "\n")
                    self._item_count_for_status += 1
                elif isinstance(value, dict): 
                    self._extract_texts_recursive(value, new_path_parts, filepath, filename)
                elif isinstance(value, list):
                    for i, item in enumerate(value):
                        indexed_key_str = f"{key_str}[{i}]"
                        new_list_item_path_parts = current_path_parts + [indexed_key_str]
                        if isinstance(item, str):
                            message_key_path = ".".join(new_list_item_path_parts)
                            self.text_data.append({
                                'filepath': filepath,
                                'message_key': message_key_path,
                                'original_text': item
                            })
                            display_text_preview_full = str(item).replace('\n', ' ').replace('\r', '')
                            self.text_display_area.insert(tk.END, filename, "filename_color")
                            self.text_display_area.insert(tk.END, " :: ", "separator_color")
                            self.text_display_area.insert(tk.END, message_key_path, "messagekey_color")
                            self.text_display_area.insert(tk.END, " :: ", "separator_color")
                            preview = display_text_preview_full[:100]
                            if len(display_text_preview_full) > 100: preview += "..."
                            self._insert_formatted_preview(preview)
                            self.text_display_area.insert(tk.END, "\n")
                            self._item_count_for_status += 1
                        elif isinstance(item, dict):
                            self._extract_texts_recursive(item, new_list_item_path_parts, filepath, filename)

    def load_files_from_folder(self, folder_path):
        self.text_display_area.config(state=tk.NORMAL) 
        self.text_display_area.delete("1.0", tk.END)   
        self.text_data = []
        self._item_count_for_status = 0
        self.current_search_result = None
        self.last_search_offset = (0,0)
        self.last_searched_term_for_find_next = ""
        if self.search_var.get(): self._on_search_term_change()
        else: self.replace_button.config(state=tk.DISABLED)

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
                    data = self.yaml_parser.load(f) # Use ruamel.yaml load
                if data is None: # File might be empty, comments-only, or '--- null'
                    continue
                self._extract_texts_recursive(data, [], filepath, filename)
            except YAMLError as e: # Catches ruamel.yaml.error.YAMLError
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
                match = re.fullmatch(r"(.+)\[([0-9]+)\]", key_segment)
                if match and isinstance(current_level, dict):
                    list_name, idx_str = match.groups()
                    idx = int(idx_str)
                    if list_name in current_level and isinstance(current_level[list_name], list) and idx < len(current_level[list_name]):
                        current_level = current_level[list_name][idx]
                    else: return None
                else: return None
        return current_level

    def _set_value_by_path(self, data_dict, path_str, value_to_set):
        keys = path_str.split('.')
        current_level = data_dict
        for i, key_segment in enumerate(keys[:-1]):
            match = re.fullmatch(r"(.+)\[([0-9]+)\]", key_segment)
            if match:
                list_name, idx_str = match.groups()
                idx = int(idx_str)
                if isinstance(current_level, dict) and list_name in current_level and \
                   isinstance(current_level[list_name], list) and idx < len(current_level[list_name]):
                    current_level = current_level[list_name][idx]
                else: return False
            elif isinstance(current_level, dict) and key_segment in current_level:
                current_level = current_level[key_segment]
            else: return False
        
        last_key = keys[-1]
        match_last = re.fullmatch(r"(.+)\[([0-9]+)\]", last_key)
        if match_last:
            list_name, idx_str = match_last.groups()
            idx = int(idx_str)
            if isinstance(current_level, dict) and list_name in current_level and \
               isinstance(current_level[list_name], list) and idx < len(current_level[list_name]):
                current_level[list_name][idx] = value_to_set
                return True
            return False
        elif isinstance(current_level, dict): # Check if last_key should exist or can be created
            current_level[last_key] = value_to_set # This will create key if not exists in dict
            return True
        return False

    def on_mouse_press(self, event):
        current_widget_state = self.text_display_area.cget("state")
        is_disabled = (current_widget_state == tk.DISABLED)
        if is_disabled: self.text_display_area.config(state=tk.NORMAL)
        self.text_display_area.tag_remove("line_highlight", "1.0", tk.END)
        try:
            line_start_index = self.text_display_area.index(f"@{event.x},{event.y} linestart")
            line_number = int(line_start_index.split('.')[0])
            if 1 <= line_number <= len(self.text_data) : 
                line_end_index = f"{line_number}.end"
                self.text_display_area.tag_add("line_highlight", line_start_index, line_end_index)
        except tk.TclError: pass 
        finally:
            if is_disabled: self.text_display_area.config(state=tk.DISABLED)

    def on_double_click(self, event):
        try:
            text_widget_index = self.text_display_area.index(f"@{event.x},{event.y} linestart")
            line_number = int(text_widget_index.split('.')[0])
            selected_0_based_index = line_number - 1 
        except (tk.TclError, ValueError): return 
        if 0 <= selected_0_based_index < len(self.text_data):
            item_data = self.text_data[selected_0_based_index]
            self.open_edit_dialog(selected_0_based_index, item_data)

    def _update_display_line(self, item_0_based_index):
        current_widget_state = self.text_display_area.cget("state")
        is_disabled = (current_widget_state == tk.DISABLED)
        if is_disabled: self.text_display_area.config(state=tk.NORMAL)
        
        target_line_1_based = item_0_based_index + 1
        item_data = self.text_data[item_0_based_index]
        new_text_value = item_data['original_text']
        self.text_display_area.delete(f"{target_line_1_based}.0", f"{target_line_1_based + 1}.0") 
        filename_part = os.path.basename(item_data['filepath'])
        message_key_part = item_data['message_key']
        display_text_updated_preview_full = str(new_text_value).replace('\n', ' ').replace('\r', '')
        preview_updated = display_text_updated_preview_full[:100]
        if len(display_text_updated_preview_full) > 100: preview_updated += "..."
        insert_start_pos = f"{target_line_1_based}.0"
        self.text_display_area.insert(insert_start_pos, filename_part, "filename_color")
        self.text_display_area.insert(tk.INSERT, " :: ", "separator_color")
        self.text_display_area.insert(tk.INSERT, message_key_part, "messagekey_color")
        self.text_display_area.insert(tk.INSERT, " :: ", "separator_color")
        self._insert_formatted_preview(preview_updated) 
        self.text_display_area.insert(tk.INSERT, "\n") 
        if is_disabled: self.text_display_area.config(state=tk.DISABLED)

    def open_edit_dialog(self, item_0_based_index, item_data_at_open):
        edit_window = tk.Toplevel(self.master)
        edit_window.title(f"Edit Text")
        edit_window.geometry("600x400")
        edit_window.transient(self.master) 
        edit_window.grab_set() 
        try:
            current_item_data = self.text_data[item_0_based_index]
            current_text_val = current_item_data['original_text']
        except IndexError:
            messagebox.showerror("Error", "Item index out of bounds.", parent=edit_window)
            edit_window.destroy()
            return
        except Exception as e:
            messagebox.showerror("Error", f"Could not get text for editing: {e}", parent=edit_window)
            edit_window.destroy()
            return
            
        tk.Label(edit_window, text=f"File: {os.path.basename(current_item_data['filepath'])}\nKey Path: {current_item_data['message_key']}", 
                 justify=tk.LEFT, pady=10).pack(anchor=tk.W, padx=10)
        text_widget_editor = scrolledtext.ScrolledText(edit_window, wrap=tk.WORD, height=15, width=70, font=("Arial", 10))
        text_widget_editor.pack(padx=10, pady=5, fill=tk.BOTH, expand=True)
        text_widget_editor.tag_configure("dialog_symbol_color", foreground="blue")
        last_end = 0
        for match in self.symbol_regex.finditer(current_text_val):
            start, end = match.span()
            if start > last_end: text_widget_editor.insert(tk.END, current_text_val[last_end:start])
            text_widget_editor.insert(tk.END, current_text_val[start:end], "dialog_symbol_color")
            last_end = end
        if last_end < len(current_text_val): text_widget_editor.insert(tk.END, current_text_val[last_end:])
        text_widget_editor.focus_set()
        button_frame = tk.Frame(edit_window)
        button_frame.pack(pady=10)

        def save_changes():
            new_text = text_widget_editor.get("1.0", tk.END).rstrip('\n')
            target_item_data_entry = self.text_data[item_0_based_index]
            yaml_content = None
            try:
                with open(target_item_data_entry['filepath'], 'r', encoding='utf-8') as f:
                    yaml_content = self.yaml_parser.load(f) # Use ruamel.yaml load
                if yaml_content is None: # File was empty, comments-only, or '--- null'
                    yaml_content = self.yaml_parser.map() # Create a new CommentedMap
            except FileNotFoundError:
                 messagebox.showerror("Save Error", f"File not found: {target_item_data_entry['filepath']}", parent=edit_window)
                 return
            except YAMLError as e_load: # Covers empty file ParserError, malformed YAML
                 messagebox.showerror("Save Error", f"Cannot load {os.path.basename(target_item_data_entry['filepath'])} to save: {e_load}\nFile might be empty or malformed.", parent=edit_window)
                 # Optionally, ask user if they want to overwrite with a new structure
                 # For now, we just error out if re-load fails.
                 return

            if not self._set_value_by_path(yaml_content, target_item_data_entry['message_key'], new_text):
                messagebox.showerror("Save Error", f"Failed to update value for '{target_item_data_entry['message_key']}'. Path might be incorrect.", parent=edit_window)
                return

            try:
                with open(target_item_data_entry['filepath'], 'w', encoding='utf-8') as f:
                    self.yaml_parser.dump(yaml_content, f) # Use ruamel.yaml dump
                target_item_data_entry['original_text'] = new_text 
                self._update_display_line(item_0_based_index)
                target_line_1_based = item_0_based_index + 1
                current_widget_state = self.text_display_area.cget("state")
                is_disabled = (current_widget_state == tk.DISABLED)
                if is_disabled: self.text_display_area.config(state=tk.NORMAL)
                self.text_display_area.tag_remove("line_highlight", "1.0", tk.END)
                self.text_display_area.tag_add("line_highlight", f"{target_line_1_based}.0", f"{target_line_1_based}.end")
                self.text_display_area.see(f"{target_line_1_based}.0")
                if is_disabled: self.text_display_area.config(state=tk.DISABLED)
                self.status_var.set(f"Saved changes to '{target_item_data_entry['message_key']}' in {os.path.basename(target_item_data_entry['filepath'])}")
                edit_window.destroy()
            except Exception as e_save:
                messagebox.showerror("Save Error", f"Could not save changes to file: {e_save}", parent=edit_window)
                self.status_var.set(f"Error saving: {str(e_save)[:100]}")

        save_button = tk.Button(button_frame, text="Save", command=save_changes, width=10)
        save_button.pack(side=tk.LEFT, padx=5)
        cancel_button = tk.Button(button_frame, text="Cancel", command=edit_window.destroy, width=10)
        cancel_button.pack(side=tk.LEFT, padx=5)

    def find_next_text(self, restart_search_if_term_changed=True):
        search_term = self.search_var.get()
        if not search_term:
            self.status_var.set("Search term is empty.")
            self.replace_button.config(state=tk.DISABLED)
            return False
        current_widget_state = self.text_display_area.cget("state")
        is_disabled = (current_widget_state == tk.DISABLED)
        if is_disabled: self.text_display_area.config(state=tk.NORMAL)
        self.text_display_area.tag_remove("line_highlight", "1.0", tk.END)
        start_item_idx, start_char_idx_in_item_text = self.last_search_offset
        if restart_search_if_term_changed and search_term != self.last_searched_term_for_find_next:
            start_item_idx, start_char_idx_in_item_text = 0, 0
            self.current_search_result = None 
        self.last_searched_term_for_find_next = search_term
        flags = 0 if self.case_sensitive_var.get() else re.IGNORECASE
        try:
            for i in range(start_item_idx, len(self.text_data)):
                item_data = self.text_data[i]
                text_to_search = item_data['original_text']
                current_item_start_char_idx = start_char_idx_in_item_text if i == start_item_idx else 0
                match = re.search(re.escape(search_term), text_to_search[current_item_start_char_idx:], flags)
                if match:
                    actual_match_start_in_original = match.start() + current_item_start_char_idx
                    actual_match_end_in_original = match.end() + current_item_start_char_idx
                    self.current_search_result = (i, actual_match_start_in_original, actual_match_end_in_original)
                    self.last_search_offset = (i, actual_match_end_in_original) 
                    display_line_num = i + 1
                    self.text_display_area.tag_add("line_highlight", f"{display_line_num}.0", f"{display_line_num}.end")
                    self.text_display_area.see(f"{display_line_num}.0")
                    self.replace_button.config(state=tk.NORMAL)
                    self.status_var.set(f"Found '{search_term}' in '{item_data['message_key']}' (line {display_line_num}).")
                    return True 
            if start_item_idx > 0 or start_char_idx_in_item_text > 0 : 
                self.last_search_offset = (0,0) 
                self.status_var.set(f"Reached end. Searching from beginning for '{search_term}'.")
                self.replace_button.config(state=tk.DISABLED) 
                if hasattr(self, '_find_next_wrapped') and self._find_next_wrapped: pass 
                else:
                    self._find_next_wrapped = True 
                    return self.find_next_text(restart_search_if_term_changed=False) 
            self.status_var.set(f"'{search_term}' not found.")
            self.current_search_result = None
            self.replace_button.config(state=tk.DISABLED)
            self.last_search_offset = (0,0) 
            return False
        finally:
            if is_disabled: self.text_display_area.config(state=tk.DISABLED)
            if hasattr(self, '_find_next_wrapped'): del self._find_next_wrapped

    def replace_text(self):
        if self.current_search_result is None:
            self.status_var.set("No active search match. Use 'Find Next' first.")
            return
        search_term, replace_term = self.search_var.get(), self.replace_var.get()
        item_idx, match_start, match_end = self.current_search_result
        item_data = self.text_data[item_idx]
        old_text = item_data['original_text']
        new_text = old_text[:match_start] + replace_term + old_text[match_end:]
        
        yaml_content = None
        try:
            with open(item_data['filepath'], 'r', encoding='utf-8') as f:
                yaml_content = self.yaml_parser.load(f) # Use ruamel.yaml load
            if yaml_content is None: yaml_content = self.yaml_parser.map()
        except FileNotFoundError:
            messagebox.showerror("Replace Error", f"File not found: {item_data['filepath']}")
            return
        except YAMLError as e_load:
            messagebox.showerror("Replace Error", f"Cannot load {os.path.basename(item_data['filepath'])} to replace: {e_load}")
            return

        if not self._set_value_by_path(yaml_content, item_data['message_key'], new_text):
            messagebox.showerror("Save Error", f"Failed to update value for '{item_data['message_key']}'.")
            self.status_var.set(f"Error: Could not set value for '{item_data['message_key']}'.")
            return
        try:
            with open(item_data['filepath'], 'w', encoding='utf-8') as f:
                self.yaml_parser.dump(yaml_content, f) # Use ruamel.yaml dump
            item_data['original_text'] = new_text
            self._update_display_line(item_idx) 
            self.status_var.set(f"Replaced in '{item_data['message_key']}'. Finding next...")
            self.last_search_offset = (item_idx, match_start + len(replace_term))
            self.current_search_result = None 
            self.replace_button.config(state=tk.DISABLED) 
            self.find_next_text(restart_search_if_term_changed=False) 
        except Exception as e_save:
            messagebox.showerror("Replace Error", f"Could not replace text in file: {e_save}")
            self.status_var.set(f"Error during replace: {str(e_save)[:100]}")

    def replace_all_text(self):
        search_term, replace_term = self.search_var.get(), self.replace_var.get()
        if not search_term:
            self.status_var.set("Search term is empty for 'Replace All'.")
            return
        if not self.text_data:
            self.status_var.set("No data loaded for 'Replace All'.")
            return
        if not messagebox.askyesno("Confirm Replace All", 
                               f"Replace all '{search_term}' with '{replace_term}' in all loaded files? This cannot be undone easily.",
                               parent=self.master):
            self.status_var.set("'Replace All' cancelled.")
            return

        modified_files_content = {} 
        total_replacements_count = 0
        flags = 0 if self.case_sensitive_var.get() else re.IGNORECASE

        for item_idx, item_data in enumerate(self.text_data):
            original_doc_text = item_data['original_text']
            new_doc_text, num_replacements_in_item = re.subn(re.escape(search_term), replace_term, original_doc_text, flags=flags)
            if num_replacements_in_item > 0:
                total_replacements_count += num_replacements_in_item
                item_data['original_text'] = new_doc_text 
                if item_data['filepath'] not in modified_files_content:
                    try:
                        with open(item_data['filepath'], 'r', encoding='utf-8') as f:
                            content = self.yaml_parser.load(f) # Use ruamel.yaml load
                            modified_files_content[item_data['filepath']] = content if content is not None else self.yaml_parser.map()
                    except FileNotFoundError:
                        messagebox.showerror("File Read Error", f"File not found: {item_data['filepath']}", parent=self.master)
                        self.status_var.set(f"Error reading {item_data['filepath']}. Aborting Replace All.")
                        return 
                    except YAMLError as e_yaml:
                        messagebox.showerror("File Read Error", f"Could not parse {item_data['filepath']}: {e_yaml}", parent=self.master)
                        self.status_var.set(f"Error parsing {item_data['filepath']}. Aborting Replace All.")
                        return
                    except Exception as e_other: # General fallback
                        messagebox.showerror("File Read Error", f"Unexpected error reading {item_data['filepath']}: {e_other}", parent=self.master)
                        self.status_var.set(f"Error reading {item_data['filepath']}. Aborting Replace All.")
                        return

                if not self._set_value_by_path(modified_files_content[item_data['filepath']], item_data['message_key'], new_doc_text):
                    messagebox.showerror("Update Error", f"Failed to set path '{item_data['message_key']}' in {item_data['filepath']}.", parent=self.master)
                    self.status_var.set(f"Error setting path in {item_data['filepath']}. Aborting.")
                    return 

        if total_replacements_count > 0:
            for filepath, yaml_data_to_write in modified_files_content.items():
                try:
                    with open(filepath, 'w', encoding='utf-8') as f:
                        self.yaml_parser.dump(yaml_data_to_write, f) # Use ruamel.yaml dump
                except Exception as e_write:
                    messagebox.showerror("File Write Error", f"Could not write changes to {filepath}: {e_write}", parent=self.master)
                    self.status_var.set(f"Error writing {filepath}. Some files may not be updated.")
            
            # Reload display area with modified text_data
            current_widget_state = self.text_display_area.cget("state")
            is_disabled = (current_widget_state == tk.DISABLED)
            if is_disabled: self.text_display_area.config(state=tk.NORMAL)
            self.text_display_area.delete("1.0", tk.END) 
            self._item_count_for_status = 0 
            for item_data_reloaded in self.text_data: # self.text_data was updated in-place
                filename = os.path.basename(item_data_reloaded['filepath'])
                message_key_path = item_data_reloaded['message_key']
                value = item_data_reloaded['original_text']
                display_text_preview_full = str(value).replace('\n', ' ').replace('\r', '')
                self.text_display_area.insert(tk.END, filename, "filename_color")
                self.text_display_area.insert(tk.END, " :: ", "separator_color")
                self.text_display_area.insert(tk.END, message_key_path, "messagekey_color")
                self.text_display_area.insert(tk.END, " :: ", "separator_color")
                preview = display_text_preview_full[:100]
                if len(display_text_preview_full) > 100: preview += "..."
                self._insert_formatted_preview(preview) 
                self.text_display_area.insert(tk.END, "\n")
                self._item_count_for_status +=1
            if is_disabled: self.text_display_area.config(state=tk.DISABLED)
            
            self.status_var.set(f"Replaced {total_replacements_count} instance(s) across {len(modified_files_content)} file(s). Display updated.")
            self.current_search_result = None
            self.last_search_offset = (0,0)
            self.replace_button.config(state=tk.DISABLED) 
            self.text_display_area.tag_remove("line_highlight", "1.0", tk.END)
        else:
            self.status_var.set(f"No occurrences of '{search_term}' found to replace.")

if __name__ == "__main__":
    root = tk.Tk()
    try:
        app = YamlTextEditorApp(root)
    except ImportError:
        messagebox.showerror("Dependency Error", "The 'ruamel.yaml' library is required. Please install it (e.g., 'pip install ruamel.yaml') and restart the application.")
        root.destroy() # Close the empty window if import fails
        exit() # Exit the script
    except Exception as e: # Catch any other init errors
        messagebox.showerror("Initialization Error", f"An error occurred during application startup: {e}")
        root.destroy()
        exit()
    root.mainloop()
