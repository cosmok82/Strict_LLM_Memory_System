# -*- coding: utf-8 -*-
"""
Created on Fri Jun  5 21:16:56 2026

@author: Cosimo Orlando (CosOr)
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog
import os
import re
import json
import sys

# Prova a usare ruamel.yaml per round-trip perfetto, altrimenti fallback a PyYAML
try:
    from ruamel.yaml import YAML
    from ruamel.yaml.scalarstring import DoubleQuotedScalarString
    USE_RUAMEL = True
except ImportError:
    import yaml
    USE_RUAMEL = False

# --- Configuration Constants ---
THEMES = {
    "Light": {
        "bg": "#f0f0f0", "fg": "#000000", "accent": "#0078d7",
        "text_bg": "#ffffff", "text_fg": "#000000",
        "header_fg": "#333333", "label_fg": "#333333",
        "canvas_bg": "#f0f0f0", "scroll_bg": "#e0e0e0", "scroll_trough": "#f0f0f0",
        "combo_arrow": "#000000", "select_bg": "#0078d7", "select_fg": "#ffffff"
    },
    "Dark": {
        "bg": "#2b2b2b", "fg": "#e0e0e0", "accent": "#007acc",
        "text_bg": "#3c3c3c", "text_fg": "#e0e0e0",
        "header_fg": "#cccccc", "label_fg": "#b0b0b0",
        "canvas_bg": "#2b2b2b", "scroll_bg": "#555555", "scroll_trough": "#2b2b2b",
        "combo_arrow": "#e0e0e0", "select_bg": "#007acc", "select_fg": "#ffffff"
    },
    "Solarized Light": {
        "bg": "#fdf6e3", "fg": "#586e75", "accent": "#268bd2",
        "text_bg": "#eee8d5", "text_fg": "#586e75",
        "header_fg": "#073642", "label_fg": "#586e75",
        "canvas_bg": "#fdf6e3", "scroll_bg": "#93a1a1", "scroll_trough": "#fdf6e3",
        "combo_arrow": "#586e75", "select_bg": "#268bd2", "select_fg": "#fdf6e3"
    },
    "Solarized Dark": {
        "bg": "#002b36", "fg": "#839496", "accent": "#268bd2",
        "text_bg": "#073642", "text_fg": "#839496",
        "header_fg": "#93a1a1", "label_fg": "#839496",
        "canvas_bg": "#002b36", "scroll_bg": "#586e75", "scroll_trough": "#002b36",
        "combo_arrow": "#839496", "select_bg": "#268bd2", "select_fg": "#002b36"
    }
}

FONT_OPTIONS = [
    "Consolas", "Courier New", "Helvetica", "Arial", 
    "Segoe UI", "Tahoma", "Verdana", "Calibri"
]

DEFAULT_CONFIG = {
    "theme": "Light",
    "font_family": "Consolas",
    "font_size": 10
}


class PromptEditorApp:
    def __init__(self, root, yaml_path):
        self.root = root
        self.root.title("SOTA Prompt Compiler GUI")
        self.root.geometry("1100x850")
        
        self.yaml_path = yaml_path
        self.config_path = os.path.join(os.path.dirname(os.path.abspath(yaml_path)), "config.json")
        
        # State tracking
        self.widget_states = {}
        self.text_widgets = []
        self.header_labels = []
        self.header_font_sizes = {}
        self.list_labels = []
        self.title_label = None
        self.saved_values = {}
        
        # Load config
        self.config = self.load_config()
        self.normalize_config()
        
        # Auto-paths
        current_dir = os.getcwd()
        self.memory_dir = current_dir
        self.auto_memory_name = os.path.basename(current_dir)
        self.auto_root_path = os.path.dirname(current_dir).replace('\\', '/')

        # Load YAML
        self.data = self.load_yaml()
        self.apply_auto_paths()

        # Setup UI
        self.setup_ui()
        self.build_dynamic_ui(self.scrollable_frame, self.data)
        self.apply_theme()

    # --- Config Management ---
    def load_config(self):
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    cfg = json.load(f)
                    for k, v in DEFAULT_CONFIG.items():
                        cfg.setdefault(k, v)
                    return cfg
            except Exception:
                return DEFAULT_CONFIG.copy()
        return DEFAULT_CONFIG.copy()

    def normalize_config(self):
        theme = str(self.config.get("theme", "Light"))
        theme_matched = False
        for key in THEMES:
            if key.lower() == theme.lower():
                self.config["theme"] = key
                theme_matched = True
                break
        if not theme_matched:
            self.config["theme"] = "Light"
        
        font = str(self.config.get("font_family", "Consolas"))
        font_matched = False
        for f in FONT_OPTIONS:
            if f.lower() == font.lower():
                self.config["font_family"] = f
                font_matched = True
                break
        if not font_matched:
            self.config["font_family"] = "Consolas"
        
        try:
            self.config["font_size"] = max(8, min(24, int(self.config.get("font_size", 10))))
        except (ValueError, TypeError):
            self.config["font_size"] = 10
        
        self.save_config()

    def save_config(self):
        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2)
        except Exception as e:
            print(f"Error saving config: {e}")

    def on_theme_change(self):
        self.config["theme"] = self.theme_combo.get()
        self.save_config()
        self.apply_theme()

    def on_font_change(self):
        self.config["font_family"] = self.font_combo.get()
        self.save_config()
        self.apply_theme()

    def apply_theme(self):
        theme = THEMES[self.config["theme"]]
        self.root.configure(bg=theme["bg"])
        
        if self.title_label:
            self.title_label.configure(bg=theme["bg"], fg=theme["header_fg"])
        
        style = ttk.Style()
        try:
            style.theme_use('clam')
        except tk.TclError:
            pass
        
        style.configure('.', background=theme["bg"], foreground=theme["fg"])
        style.configure('TFrame', background=theme["bg"])
        style.configure('TLabel', background=theme["bg"], foreground=theme["label_fg"])
        style.configure('TButton', background=theme["text_bg"], foreground=theme["fg"])
        style.map('TButton', background=[('active', theme["accent"])])
        
        # Scrollbar
        style.configure('TScrollbar', 
                       background=theme["scroll_bg"], 
                       troughcolor=theme["scroll_trough"], 
                       arrowcolor=theme["fg"])
        
        # FIX 2: Improved combobox styling
        style.configure('TCombobox',
                       fieldbackground=theme["text_bg"],
                       background=theme["text_bg"],
                       foreground=theme["text_fg"],
                       arrowcolor=theme["combo_arrow"],
                       selectbackground=theme["select_bg"],
                       selectforeground=theme["select_fg"],
                       bordercolor=theme["accent"],
                       lightcolor=theme["text_bg"],
                       darkcolor=theme["text_bg"])
        
        style.map('TCombobox',
                 fieldbackground=[
                     ('readonly', theme["text_bg"]),
                     ('disabled', theme["bg"]),
                     ('pressed', theme["text_bg"]),
                     ('active', theme["text_bg"])
                 ],
                 foreground=[
                     ('readonly', theme["text_fg"]),
                     ('disabled', theme["label_fg"])
                 ],
                 selectbackground=[('readonly', theme["select_bg"]), ('!focus', theme["select_bg"])],
                 selectforeground=[('readonly', theme["select_fg"]), ('!focus', theme["select_fg"])])
        
        if hasattr(self, 'canvas'):
            self.canvas.configure(bg=theme["canvas_bg"], highlightbackground=theme["bg"])
        
        for text_widget in self.text_widgets:
            text_widget.configure(
                bg=theme["text_bg"],
                fg=theme["text_fg"],
                insertbackground=theme["fg"],
                selectbackground=theme["accent"],
                selectforeground=theme["bg"]
            )
        
        for widget in self.header_labels:
            widget.configure(foreground=theme["header_fg"])
        
        for widget in self.list_labels:
            widget.configure(foreground=theme["label_fg"])
        
        # FIX 2: Popdown window styling (Windows-specific)
        if sys.platform == "win32":
            try:
                for combo in [self.theme_combo, self.font_combo]:
                    if combo.winfo_exists():
                        # Configura la popdown (il menu a tendina)
                        combo.tk.eval(f'''
                            set popwin [ttk::combobox::PopdownWindow {combo}]
                            set listbox [$popwin.popdown.f.l]
                            $listbox configure -background {theme["text_bg"]} -foreground {theme["text_fg"]}
                            $listbox configure -selectbackground {theme["select_bg"]} -selectforeground {theme["select_fg"]}
                        ''')
            except Exception:
                pass
        
        self.apply_font_to_widgets()

    def apply_font_to_widgets(self):
        style = ttk.Style()
        font = (self.config["font_family"], self.config["font_size"])
        
        style.configure('TLabel', font=font)
        style.configure('TButton', font=font)
        style.configure('TCombobox', font=font)
        
        for text_widget in self.text_widgets:
            text_widget.configure(font=font)
        
        for widget in self.header_labels:
            current_size = self.header_font_sizes.get(widget, self.config["font_size"])
            widget.configure(font=(self.config["font_family"], current_size, "bold"))
        
        for widget in self.list_labels:
            widget.configure(font=(self.config["font_family"], 12, "bold"))

    # --- YAML & UI Setup ---
    def load_yaml(self):
        try:
            with open(self.yaml_path, 'r', encoding='utf-8') as f:
                if USE_RUAMEL:
                    yaml_parser = YAML()
                    yaml_parser.preserve_quotes = True
                    return yaml_parser.load(f)
                else:
                    return yaml.safe_load(f)
        except Exception as e:
            messagebox.showerror("Error", f"Unable to load YAML file:\n{e}")
            return {}

    def apply_auto_paths(self):
        if "variables" in self.data:
            if "root" in self.data["variables"]:
                self.data["variables"]["root"] = self.auto_root_path
            if "memory" in self.data["variables"]:
                self.data["variables"]["memory"] = self.auto_memory_name

    def setup_ui(self):
        top_frame = ttk.Frame(self.root, padding=10)
        top_frame.pack(fill=tk.X)
        
        theme_colors = THEMES[self.config["theme"]]
        title_lbl = tk.Label(top_frame, text="SOTA Prompt Compiler", 
                            font=(self.config["font_family"], 16, "bold"),
                            bg=theme_colors["bg"],
                            fg=theme_colors["header_fg"])
        title_lbl.pack(side=tk.LEFT)
        self.title_label = title_lbl
        self.header_labels.append(title_lbl)
        self.header_font_sizes[title_lbl] = 16

        toolbar = ttk.Frame(top_frame)
        toolbar.pack(side=tk.LEFT, padx=30)

        ttk.Label(toolbar, text="Theme:").pack(side=tk.LEFT, padx=(0, 5))
        self.theme_combo = ttk.Combobox(toolbar, values=list(THEMES.keys()), state="readonly", width=15)
        self.theme_combo.set(self.config["theme"])
        self.theme_combo.pack(side=tk.LEFT, padx=(0, 15))
        self.theme_combo.bind("<<ComboboxSelected>>", lambda e: self.on_theme_change())

        ttk.Label(toolbar, text="Font:").pack(side=tk.LEFT, padx=(0, 5))
        self.font_combo = ttk.Combobox(toolbar, values=FONT_OPTIONS, state="readonly", width=15)
        self.font_combo.set(self.config["font_family"])
        self.font_combo.pack(side=tk.LEFT, padx=(0, 15))
        self.font_combo.bind("<<ComboboxSelected>>", lambda e: self.on_font_change())

        ttk.Button(top_frame, text="Save Compiled Leggenda", command=self.save_data).pack(side=tk.RIGHT)

        container = ttk.Frame(self.root)
        container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        self.canvas = tk.Canvas(container, borderwidth=0, highlightthickness=0)
        scrollbar = ttk.Scrollbar(container, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = ttk.Frame(self.canvas)

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )

        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw", width=1050)
        self.canvas.configure(yscrollcommand=scrollbar.set)

        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.canvas.bind_all("<MouseWheel>", lambda e: self.canvas.yview_scroll(int(-1*(e.delta/120)), "units"))

    def build_dynamic_ui(self, parent, data, level=0, parent_key=None, path=None):
        if path is None:
            path = []
            
        if isinstance(data, dict):
            for key, value in data.items():
                font_size = max(10, 14 - level*2)
                lbl = ttk.Label(parent, text=f"{key}:", 
                              font=(self.config["font_family"], font_size, "bold"))
                lbl.pack(anchor="w", pady=(10 if level==0 else 2, 0))
                self.header_labels.append(lbl)
                self.header_font_sizes[lbl] = font_size
                
                if isinstance(value, (dict, list)):
                    sub_frame = ttk.Frame(parent, padding=(20, 0, 0, 0))
                    sub_frame.pack(fill=tk.X, expand=True)
                    self.build_dynamic_ui(sub_frame, value, level + 1, parent_key=key, path=path + [key])
                else:
                    current_path = path + [key]
                    self.create_text_field(parent, str(value), key_ref=data, key_name=key, path=current_path)
                    
        elif isinstance(data, list):
            is_attachments = (parent_key == "attachments")
            
            for i, item in enumerate(data):
                list_frame = ttk.Frame(parent)
                list_frame.pack(fill=tk.X, expand=True, pady=2)
                
                list_lbl = ttk.Label(list_frame, text="- ", 
                                    font=(self.config["font_family"], 12, "bold"))
                list_lbl.pack(side=tk.LEFT, anchor="n")
                self.list_labels.append(list_lbl)
                
                current_path = path + [i]
                self.create_text_field(list_frame, str(item), key_ref=data, key_name=i, path=current_path)
                
                if is_attachments:
                    btn_frame = ttk.Frame(list_frame)
                    btn_frame.pack(side=tk.LEFT, padx=5, anchor="n")
                    ttk.Button(btn_frame, text="+", width=2, 
                              command=lambda d=data, idx=i: self.add_attachment_row(d, idx)).pack(side=tk.LEFT, padx=1)
                    ttk.Button(btn_frame, text="−", width=2, 
                              command=lambda d=data, idx=i: self.remove_attachment_row(d, idx)).pack(side=tk.LEFT, padx=1)

    def create_text_field(self, parent, text, key_ref, key_name, path=None):
        text_widget = tk.Text(parent, height=max(2, text.count('\n') + 1), wrap=tk.WORD)
        text_widget.pack(fill=tk.X, expand=True, pady=2, padx=5)
        self.text_widgets.append(text_widget)
        
        path_tuple = tuple(path) if path else None
        if path_tuple and path_tuple in self.saved_values:
            saved = self.saved_values[path_tuple]
            tokens = saved["tokens"]
            values = saved["values"].copy()
        else:
            parts = re.split(r"(<placeholder>\.md|<placeholder>|<description>)", text)
            tokens = []
            values = {}
            idx = 0
            
            for part in parts:
                if part in ["<placeholder>.md", "<placeholder>", "<description>"]:
                    tokens.append({"type": "interactive", "id": idx, "original": part})
                    values[idx] = part
                    idx += 1
                elif part:
                    tokens.append({"type": "text", "text": part})
                
        self.widget_states[text_widget] = {
            "tokens": tokens,
            "values": values,
            "key_ref": key_ref,
            "key_name": key_name,
            "path": path
        }
        
        text_widget.tag_configure("interactive_link", foreground="blue", underline=True)
        text_widget.tag_bind("interactive_link", "<Enter>", lambda e, tw=text_widget: tw.config(cursor="hand2"))
        text_widget.tag_bind("interactive_link", "<Leave>", lambda e, tw=text_widget: tw.config(cursor=""))
        text_widget.tag_bind("interactive_link", "<Button-1>", lambda e, tw=text_widget: self.on_tag_click(e, tw))
        
        self.render_widget(text_widget)

    def render_widget(self, text_widget):
        text_widget.config(state=tk.NORMAL)
        text_widget.delete("1.0", tk.END)
        state = self.widget_states[text_widget]
        
        for token in state["tokens"]:
            if token["type"] == "text":
                text_widget.insert(tk.END, token["text"])
            elif token["type"] == "interactive":
                current_value = state["values"][token["id"]]
                start_idx = text_widget.index(tk.END + "-1c")
                text_widget.insert(tk.END, current_value)
                end_idx = text_widget.index(tk.END + "-1c")
                
                tag_id = f"token_{token['id']}"
                text_widget.tag_add("interactive_link", start_idx, end_idx)
                text_widget.tag_add(tag_id, start_idx, end_idx)
                
        text_widget.config(state=tk.DISABLED)

    def on_tag_click(self, event, text_widget):
        index = text_widget.index(f"@{event.x},{event.y}")
        tags = text_widget.tag_names(index)
        
        if "interactive_link" in tags:
            token_id = None
            for tag in tags:
                if tag.startswith("token_"):
                    token_id = int(tag.split("_")[1])
                    break
                    
            if token_id is not None:
                state = self.widget_states[text_widget]
                
                token_orig = ""
                for t in state["tokens"]:
                    if t.get("id") == token_id:
                        token_orig = t["original"]
                        break
                        
                if token_orig == "<placeholder>.md":
                    filepath = filedialog.askopenfilename(
                        initialdir=self.memory_dir,
                        title="Select File",
                        filetypes=[("Markdown files", "*.md"), ("All files", "*.*")]
                    )
                    if filepath:
                        filename = os.path.basename(filepath)
                        basename = os.path.splitext(filename)[0]
                        state["values"][token_id] = filename
                        for t in state["tokens"]:
                            if t.get("original") == "<placeholder>":
                                state["values"][t["id"]] = basename
                        self.render_widget(text_widget)
                        
                elif token_orig == "<placeholder>":
                    current_val = state["values"][token_id]
                    init_val = current_val if current_val != "<placeholder>" else ""
                    user_input = simpledialog.askstring("Input", "Enter text for <placeholder>:", 
                                                       initialvalue=init_val, parent=self.root)
                    if user_input is not None:
                        state["values"][token_id] = user_input if user_input.strip() else "<placeholder>"
                        self.render_widget(text_widget)
                        
                elif token_orig == "<description>":
                    current_val = state["values"][token_id]
                    init_val = current_val if current_val != "<description>" else ""
                    user_input = simpledialog.askstring("Input", "Enter text for <description>:", 
                                                       initialvalue=init_val, parent=self.root)
                    if user_input is not None:
                        state["values"][token_id] = user_input if user_input.strip() else "<description>"
                        self.render_widget(text_widget)

    # --- Attachment Management ---
    def collect_current_values(self):
        saved = {}
        for text_widget, state in list(self.widget_states.items()):
            if not text_widget.winfo_exists():
                continue
            path = state.get("path")
            if path:
                saved[tuple(path)] = {
                    "tokens": state["tokens"],
                    "values": state["values"].copy()
                }
        return saved

    def rebuild_ui(self, saved_values=None):
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()
        self.widget_states = {}
        self.text_widgets = []
        self.header_labels = []
        self.header_font_sizes = {}
        self.list_labels = []
        self.saved_values = saved_values or {}
        self.build_dynamic_ui(self.scrollable_frame, self.data)
        self.apply_theme()

    def add_attachment_row(self, data_list, index):
        saved = self.collect_current_values()
        
        new_saved = {}
        for path_tuple, data in saved.items():
            path_list = list(path_tuple)
            for j in range(len(path_list) - 1):
                if path_list[j] == "attachments" and isinstance(path_list[j+1], int):
                    if path_list[j+1] > index:
                        path_list[j+1] += 1
                    break
            new_saved[tuple(path_list)] = data
        
        # FIX 1: Forza apici doppi usando DoubleQuotedScalarString (se disponibile)
        default_item = "[<placeholder>](${memory}/<placeholder>.md): <description>"
        if USE_RUAMEL:
            new_item = DoubleQuotedScalarString(default_item)
        else:
            new_item = default_item
        
        data_list.insert(index + 1, new_item)
        self.rebuild_ui(saved_values=new_saved)

    def remove_attachment_row(self, data_list, index):
        if len(data_list) <= 1:
            messagebox.showwarning("Warning", "There must be at least one attachment!")
            return
        saved = self.collect_current_values()
        
        new_saved = {}
        for path_tuple, data in saved.items():
            path_list = list(path_tuple)
            should_skip = False
            for j in range(len(path_list) - 1):
                if path_list[j] == "attachments" and isinstance(path_list[j+1], int):
                    if path_list[j+1] == index:
                        should_skip = True
                    elif path_list[j+1] > index:
                        path_list[j+1] -= 1
                    break
            if not should_skip:
                new_saved[tuple(path_list)] = data
        
        data_list.pop(index)
        self.rebuild_ui(saved_values=new_saved)

    # --- Save ---
    def sync_all_data(self):
        for text_widget, state in list(self.widget_states.items()):
            if not text_widget.winfo_exists():
                continue
            final_text = ""
            for token in state["tokens"]:
                if token["type"] == "text":
                    final_text += token["text"]
                elif token["type"] == "interactive":
                    final_text += state["values"][token["id"]]
            
            key_ref = state["key_ref"]
            key_name = state["key_name"]
            try:
                # FIX 1: Preserva quoting per stringhe ruamel
                if USE_RUAMEL and isinstance(key_ref[key_name], DoubleQuotedScalarString):
                    key_ref[key_name] = DoubleQuotedScalarString(final_text)
                else:
                    key_ref[key_name] = final_text
            except (IndexError, KeyError):
                pass

    def save_data(self):
        self.sync_all_data()
        
        save_path = filedialog.asksaveasfilename(
            defaultextension=".yaml",
            initialfile="leggenda[compiled].yaml",
            title="Save Compiled Leggenda",
            filetypes=[("YAML files", "*.yaml"), ("Text files", "*.txt")]
        )
        
        if save_path:
            try:
                with open(save_path, 'w', encoding='utf-8') as f:
                    if USE_RUAMEL:
                        yaml_writer = YAML()
                        yaml_writer.preserve_quotes = True
                        yaml_writer.width = 4096
                        yaml_writer.indent(mapping=2, sequence=4, offset=2)
                        yaml_writer.dump(self.data, f)
                    else:
                        yaml.dump(self.data, f, 
                                 allow_unicode=True, 
                                 default_flow_style=False, 
                                 sort_keys=False,
                                 width=float('inf'))
                
                msg = "Leggenda saved successfully!"
                if not USE_RUAMEL:
                    msg += "\n\nNote: Install 'ruamel.yaml' (pip install ruamel.yaml) to perfectly preserve the original format."
                messagebox.showinfo("Success", msg)
            except Exception as e:
                messagebox.showerror("Error", f"Error during saving:\n{e}")


if __name__ == "__main__":
    test_yaml = "leggenda.yaml"
    if not os.path.exists(test_yaml):
        print(f"Error: Save your leggenda in {test_yaml} before launching the editor.")
    else:
        root = tk.Tk()
        app = PromptEditorApp(root, test_yaml)
        root.mainloop()