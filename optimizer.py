import os
import subprocess
import customtkinter as ctk
from tkinter import messagebox, END, Listbox, SINGLE, MULTIPLE, ttk
import json
import datetime
import webbrowser
from PIL import Image

# --- Настройки интерфейса ---
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

TWEAKS_DIR = "tweaks"
SETTINGS_FILE = "optimizer_settings.json"
LOG_FILE = "optimizer_log.txt"
ICON_PATH = None  # Можно добавить путь к иконке, если есть

SUPPORTED_EXTS = (".bat", ".cmd", ".exe", ".vbs", ".ps1", ".reg", ".pow")

if not os.path.isdir(TWEAKS_DIR):
    ctk.CTk().withdraw()  # скрыть пустое окно
    messagebox.showerror("Ошибка", "Отсутствует папка с твиками!\nПопробуйте скачать или переустановить программу.")
    exit(1)

# --- Вспомогательные функции ---
def get_tweak_content(filepath, max_lines=500):
    try:
        with open(filepath, encoding="utf-8", errors="ignore") as f:
            lines = f.readlines()
            if len(lines) > max_lines:
                return ''.join(lines[:max_lines]) + f"\n... (файл обрезан, всего строк: {len(lines)})"
            return ''.join(lines)
    except Exception as e:
        return f"Ошибка чтения: {e}"

def find_tweaks():
    tweaks = {}
    all_folders = set()
    for root, dirs, files in os.walk(TWEAKS_DIR):
        rel_root = os.path.relpath(root, TWEAKS_DIR)
        rel_root = os.path.normpath(rel_root)
        tws = []
        for file in files:
            if file.lower().endswith(SUPPORTED_EXTS):
                path = os.path.join(root, file)
                tws.append({
                    "name": file,
                    "path": path,
                    "ext": os.path.splitext(file)[1].lower(),
                    "folder": rel_root,
                })
        if tws:
            tweaks[rel_root] = tws
    return tweaks

def save_settings(settings):
    try:
        with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
            json.dump(settings, f)
    except Exception:
        pass

def load_settings():
    try:
        with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}

def log_action(action):
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(f"{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | {action}\n")
    except Exception:
        pass

def get_tweak_info(tw):
    try:
        stat = os.stat(tw["path"])
        size = stat.st_size
        mtime = datetime.datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M:%S')
        return f"Имя: {tw['name']}\nПуть: {tw['path']}\nПапка: {tw['folder']}\nРазмер: {size} байт\nДата изменения: {mtime}\nРасширение: {tw['ext']}"
    except Exception as e:
        return f"Ошибка получения информации: {e}"

# --- GUI ---
class TweakOptimizerApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Windows Tweaks Optimizer")
        if ICON_PATH and os.path.exists(ICON_PATH):
            self.iconbitmap(ICON_PATH)
        self.geometry("1200x800+379+107")
        self.resizable(False, False)
        self.settings = load_settings()
        self.tweaks = find_tweaks()
        self.sorted_categories = sorted(self.tweaks.keys())
        self.selected_category = self.sorted_categories[0] if self.sorted_categories else None
        # --- Переменные поиска и сортировки (создаём до update_tweaks_list) ---
        self.search_var = ctk.StringVar()
        self.sort_var = ctk.StringVar(value="По имени")
        self._build_ui()
        self.load_user_settings()

    def _build_ui(self):
        # --- Верхняя подпись ---
        self.header = ctk.CTkLabel(self, text="UI Created by Faliseven  |  Tweaks Created by scode18", font=("Segoe UI", 13, "bold"), text_color="#3b82f6")
        self.header.pack(side="top", pady=(10, 0))

        # --- Переключатель темы ---
        theme_frame = ctk.CTkFrame(self, fg_color="transparent")
        theme_frame.place(relx=0.99, rely=0.01, anchor="ne")
        ctk.CTkLabel(theme_frame, text="Тема:", font=("Segoe UI", 11)).pack(side="left", padx=(0, 2))
        self.theme_var = ctk.StringVar(value=self.settings.get("theme", "dark"))
        self.theme_switch = ctk.CTkOptionMenu(theme_frame, variable=self.theme_var, values=["dark", "light"], width=70, command=self.change_theme)
        self.theme_switch.pack(side="left")

        # --- Основной фрейм ---
        main_frame = ctk.CTkFrame(self, width=1200, height=800)
        main_frame.pack(fill="both", expand=True, padx=0, pady=(8,0))

        # --- Список категорий слева ---
        self.sidebar = ctk.CTkFrame(main_frame, width=260, height=700, corner_radius=18)
        self.sidebar.pack(side="left", fill="y", padx=(18,0), pady=18)
        ctk.CTkLabel(self.sidebar, text="Категории (папки)", font=("Segoe UI", 18, "bold")).pack(pady=(14,7))
        self.category_listbox = Listbox(self.sidebar, selectmode=SINGLE, exportselection=False, width=28, height=32, font=("Segoe UI", 13), bg="#232a36", fg="#e0e0e0", highlightthickness=0, relief="flat", selectbackground="#3b82f6", selectforeground="#fff")
        self.category_listbox.pack(fill="y", expand=True, padx=8, pady=8)
        for cat in self.sorted_categories:
            self.category_listbox.insert(END, cat)
        if self.selected_category:
            self.category_listbox.select_set(self.sorted_categories.index(self.selected_category))
        self.category_listbox.bind("<<ListboxSelect>>", self.on_category_select)

        # --- Правая часть: список твиков, предпросмотр, терминал ---
        right_frame = ctk.CTkFrame(main_frame, width=900, height=700, corner_radius=18)
        right_frame.pack(side="left", fill="both", expand=True, padx=18, pady=18)

        # --- Терминал ---
        self.terminal_panel = ctk.CTkFrame(right_frame, height=300, corner_radius=18)
        self.terminal_panel.pack(side="bottom", fill="x", padx=0, pady=(16, 0))
        ctk.CTkLabel(self.terminal_panel, text="Терминал", font=("Segoe UI", 15, "bold")).pack(pady=(8,2))
        terminal_top = ctk.CTkFrame(self.terminal_panel, fg_color="transparent")
        terminal_top.pack(fill="x", padx=4, pady=(0,2))
        self.clear_terminal_btn = ctk.CTkButton(terminal_top, text="Очистить", width=80, height=28, font=("Segoe UI", 11), command=self.clear_terminal)
        self.clear_terminal_btn.pack(side="right", padx=2)
        self.terminal_box = ctk.CTkTextbox(self.terminal_panel, height=260, font=("Consolas", 12), wrap="none")
        self.terminal_box.pack(fill="both", expand=True, padx=4, pady=4)
        self.terminal_box.configure(state="disabled")
        self.terminal_box.bind("<Control-c>", lambda e: self.terminal_box.event_generate('<<Copy>>'))

        # --- Список твиков ---
        tweaks_frame = ctk.CTkFrame(right_frame, fg_color="transparent")
        tweaks_frame.pack(side="top", fill="x", expand=False, padx=0, pady=(0, 0))
        self.tweaks_tree = ttk.Treeview(tweaks_frame, columns=("type", "name"), show="headings", selectmode="extended", height=10)
        style = ttk.Style()
        style.theme_use("default")
        style.configure("Treeview",
                        background="#232a36",
                        foreground="#e0e0e0",
                        fieldbackground="#232a36",
                        rowheight=26,
                        font=("Segoe UI", 13))
        style.configure("Treeview.Heading",
                        background="#232a36",
                        foreground="#3b82f6",
                        font=("Segoe UI", 13, "bold"))
        style.map("Treeview",
                  background=[('selected', '#3b82f6')],
                  foreground=[('selected', '#fff')])
        self.tweaks_tree.heading("type", text="Тип")
        self.tweaks_tree.heading("name", text="Имя твика")
        self.tweaks_tree.column("type", width=40, anchor="center")
        self.tweaks_tree.column("name", width=600, anchor="w")
        self.tweaks_tree.pack(fill="both", expand=True, padx=0, pady=(0, 0))
        self.tweaks_tree.bind("<<TreeviewSelect>>", self.on_tweak_select)

        # --- Кнопки действий ---
        btns_frame = ctk.CTkFrame(right_frame, fg_color="transparent")
        btns_frame.pack(side="top", fill="x", pady=(0, 8))
        self.open_btn = ctk.CTkButton(btns_frame, text="Открыть в редакторе", command=self.open_in_editor, width=170)
        self.open_btn.pack(side="left", padx=4)
        self.copy_path_btn = ctk.CTkButton(btns_frame, text="Скопировать путь", command=self.copy_path, width=140)
        self.copy_path_btn.pack(side="left", padx=4)
        self.open_folder_btn = ctk.CTkButton(btns_frame, text="Открыть папку", command=self.open_folder, width=120)
        self.open_folder_btn.pack(side="left", padx=4)
        self.run_btn = ctk.CTkButton(btns_frame, text="\u2705  ПРИМЕНИТЬ ВЫБРАННЫЕ ТВИКИ", command=self.run_selected_tweaks, font=("Segoe UI", 16, "bold"), height=44, corner_radius=14, fg_color="#3b82f6", hover_color="#2563eb", text_color="#fff")
        self.run_btn.pack(side="right", padx=4)

        # --- О программе ---
        self.about_btn = ctk.CTkButton(self, text="О программе", command=self.show_about, width=120)
        self.about_btn.place(relx=0.01, rely=0.01, anchor="nw")

        # --- Поиск и сортировка ---
        filter_frame = ctk.CTkFrame(right_frame, fg_color="transparent")
        filter_frame.pack(fill="x", pady=(0, 8))
        ctk.CTkLabel(filter_frame, text="Поиск:", font=("Segoe UI", 12)).pack(side="left", padx=(0, 5))
        self.search_entry = ctk.CTkEntry(filter_frame, textvariable=self.search_var, placeholder_text="Поиск твика...", width=220, font=("Segoe UI", 13), corner_radius=10)
        self.search_entry.pack(side="left")
        self.search_entry.bind("<KeyRelease>", lambda e: self.update_tweaks_list())
        ctk.CTkLabel(filter_frame, text="Сортировка:", font=("Segoe UI", 12)).pack(side="left", padx=(16, 5))
        self.sort_menu = ctk.CTkOptionMenu(filter_frame, variable=self.sort_var, values=["По имени", "По дате", "По размеру"], width=140, command=lambda _: self.update_tweaks_list())
        self.sort_menu.pack(side="left")

        # --- Только теперь обновляем список твиков ---
        self.update_tweaks_list()

    def update_tweaks_list(self):
        self.tweaks_tree.delete(*self.tweaks_tree.get_children())
        cat = self.get_selected_category()
        tweaks = self.tweaks.get(cat, [])
        search = self.search_var.get().lower()
        if search:
            tweaks = [tw for tw in tweaks if search in tw["name"].lower() or search in tw["folder"].lower()]
        sort_type = self.sort_var.get()
        if sort_type == "По имени":
            tweaks = sorted(tweaks, key=lambda x: x["name"].lower())
        elif sort_type == "По дате":
            tweaks = sorted(tweaks, key=lambda x: os.path.getmtime(x["path"]) if os.path.exists(x["path"]) else 0, reverse=True)
        elif sort_type == "По размеру":
            tweaks = sorted(tweaks, key=lambda x: os.path.getsize(x["path"]) if os.path.exists(x["path"]) else 0, reverse=True)
        for tw in tweaks:
            ext = tw["ext"]
            if ext == ".exe":
                color = "#22c55e"  # зелёный
            elif ext in (".bat", ".cmd"):
                color = "#3b82f6"  # синий
            elif ext == ".vbs":
                color = "#a21caf"  # фиолетовый
            elif ext == ".ps1":
                color = "#f59e42"  # оранжевый
            elif ext == ".reg":
                color = "#a16207"  # коричневый
            elif ext == ".pow":
                color = "#eab308"  # жёлтый
            else:
                color = "#64748b"  # серый
            circle = "●"
            self.tweaks_tree.insert("", "end", iid=tw["path"], values=(circle, tw["name"]), tags=(color,))
        for tag in ["#22c55e", "#3b82f6", "#a21caf", "#f59e42", "#a16207", "#eab308", "#64748b"]:
            self.tweaks_tree.tag_configure(tag, foreground=tag)

    def get_selected_category(self):
        idxs = self.category_listbox.curselection()
        if not idxs:
            return self.sorted_categories[0]
        return self.category_listbox.get(idxs[0])

    def on_category_select(self, event=None):
        self.update_tweaks_list()

    def on_tweak_select(self, event=None):
        selected = self.tweaks_tree.selection()
        if not selected:
            return
        path = selected[0]
        tw = None
        for tweaks in self.tweaks.values():
            tw = next((t for t in tweaks if t["path"] == path), None)
            if tw:
                break
        if tw:
            pass

    def open_in_editor(self):
        selected = self.tweaks_tree.selection()
        cat = self.get_selected_category()
        tweaks = self.tweaks.get(cat, [])
        if not selected:
            return
        idx = self.tweaks_tree.index(selected[0])
        if idx < len(tweaks):
            # Открываем в notepad
            subprocess.Popen(["notepad", tweaks[idx]["path"]])

    def copy_path(self):
        selected = self.tweaks_tree.selection()
        cat = self.get_selected_category()
        tweaks = self.tweaks.get(cat, [])
        if not selected:
            return
        idx = self.tweaks_tree.index(selected[0])
        if idx < len(tweaks):
            self.clipboard_clear()
            self.clipboard_append(tweaks[idx]["path"])
            self.print_terminal(f"Путь скопирован: {tweaks[idx]['path']}")

    def open_folder(self):
        selected = self.tweaks_tree.selection()
        cat = self.get_selected_category()
        tweaks = self.tweaks.get(cat, [])
        if not selected:
            return
        idx = self.tweaks_tree.index(selected[0])
        if idx < len(tweaks):
            folder = os.path.dirname(tweaks[idx]["path"])
            subprocess.Popen(["explorer", folder])

    def run_selected_tweaks(self):
        selected = self.tweaks_tree.selection()
        cat = self.get_selected_category()
        tweaks = self.tweaks.get(cat, [])
        if not selected:
            messagebox.showwarning("Нет твиков", "Выберите хотя бы один твик для запуска.")
            return
        self.clear_terminal()
        errors = []
        for sel in selected:
            idx = self.tweaks_tree.index(sel)
            if idx < len(tweaks):
                tw = tweaks[idx]
                self.print_terminal(f"$ {tw['path']}")
                log_action(f"RUN: {tw['path']}")
                try:
                    proc = subprocess.Popen(tw['path'], shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                    while True:
                        out = proc.stdout.readline()
                        if out:
                            try:
                                out_decoded = out.decode('utf-8').rstrip()
                            except UnicodeDecodeError:
                                out_decoded = out.decode('cp866', errors='replace').rstrip()
                            self.print_terminal(out_decoded)
                        err = proc.stderr.readline()
                        if err:
                            try:
                                err_decoded = err.decode('utf-8').rstrip()
                            except UnicodeDecodeError:
                                err_decoded = err.decode('cp866', errors='replace').rstrip()
                            self.print_terminal(err_decoded)
                        if out == b'' and err == b'' and proc.poll() is not None:
                            break
                    code = proc.poll()
                    if code == 0:
                        self.print_terminal(f"[OK] {tw['name']} завершён успешно")
                    else:
                        self.print_terminal(f"[ERR] {tw['name']} завершён с ошибкой {code}")
                except Exception as e:
                    self.print_terminal(f"[EXCEPTION] {tw['name']}: {e}")
        if errors:
            messagebox.showerror("Ошибки при запуске", "\n".join(errors))

    def print_terminal(self, text, tag=None):
        self.terminal_box.configure(state="normal")
        self.terminal_box.insert("end", text+"\n")
        self.terminal_box.see("end")
        self.terminal_box.configure(state="disabled")

    def clear_terminal(self):
        self.terminal_box.configure(state="normal")
        self.terminal_box.delete("1.0", "end")
        self.terminal_box.configure(state="disabled")

    def show_about(self):
        win = ctk.CTkToplevel(self)
        win.title("О программе")
        win.geometry("500x320")
        ctk.CTkLabel(win, text="Windows Tweaks Optimizer", font=("Segoe UI", 18, "bold"), text_color="#3b82f6").pack(pady=(18, 8))
        ctk.CTkLabel(win, text="UI Created by Faliseven\nTweaks Created by scode18", font=("Segoe UI", 13)).pack(pady=4)
        ctk.CTkLabel(win, text="GitHub: https://github.com/faliseven\nТвики: https://github.com/scode18", font=("Segoe UI", 12)).pack(pady=4)
        ctk.CTkButton(win, text="Открыть GitHub Faliseven", command=lambda: webbrowser.open("https://github.com/faliseven")).pack(pady=8)
        ctk.CTkButton(win, text="Открыть GitHub scode18", command=lambda: webbrowser.open("https://github.com/scode18")).pack(pady=4)
        ctk.CTkLabel(win, text="2025", font=("Segoe UI", 11, "italic"), text_color="#888").pack(side="bottom", pady=8)

    def load_user_settings(self):
        if self.settings.get("theme"):
            ctk.set_appearance_mode(self.settings["theme"])
        if self.settings.get("geometry"):
            self.geometry(self.settings["geometry"])

    def change_theme(self, mode):
        ctk.set_appearance_mode(mode)
        self.settings["theme"] = mode
        save_settings(self.settings)

    def destroy(self):
        self.settings["geometry"] = self.geometry()
        save_settings(self.settings)
        super().destroy()

if __name__ == "__main__":
    app = TweakOptimizerApp()
    app.mainloop() 
