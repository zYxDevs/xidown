import customtkinter as ctk
import json
import os
import sys
import webbrowser
import shutil 
import threading
from tkinter import filedialog
from datetime import datetime

# [MARIBEL] Import version info
from xidown.core.version import APP_NAME, APP_VER
import xidown.core.setup as setup_core

# NAVIGATION FIX (Ensure pointing to Root, not package)
if getattr(sys, 'frozen', False):
    # If run as EXE (frozen)
    BASE_DIR = os.path.dirname(sys.executable)
else:
    # If run as Python script (Development)
    # Location of this file: xidown/xidown/gui/settings.py
    current_dir = os.path.dirname(os.path.abspath(__file__)) # .../xidown/gui
    package_dir = os.path.dirname(current_dir)                   # .../xidown (Package)
    BASE_DIR = os.path.dirname(package_dir)                      # .../xidown (ROOT)

DATA_DIR = os.path.join(os.path.expanduser("~"), "Videos", "xidown")
if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)

CONFIG_FILE = os.path.join(DATA_DIR, "config.json")

# HELPER FUNCTIONS
def load_config():
    default_conf = {
        "quality": "excellent", 
        "save_path": "", 
        "use_default_path": True, 
        "threads": 2,
        "parallel_count": 1, 
        "cookie_path": "" 
    }
    
    if not os.path.exists(CONFIG_FILE):
        return default_conf
    try:
        with open(CONFIG_FILE, "r") as f:
            data = json.load(f)
            for key, val in default_conf.items():
                if key not in data:
                    data[key] = val
            if data.get("quality") not in ["excellent", "best"]:
                data["quality"] = "best"
            return data
    except:
        return default_conf

def save_config(data):
    try:
        with open(CONFIG_FILE, "w") as f:
            json.dump(data, f, indent=4)
    except Exception as e:
        print(f"Config save error: {e}")

# SETTINGS WINDOW
class SettingsWindow(ctk.CTkToplevel):
    def __init__(self, parent):
        super().__init__(parent)
        
        self.withdraw()
        self.parent = parent
        self.config = load_config()
        
        self.title("Settings")
        self.resizable(False, False)
        self.configure(fg_color="#121212")

        w_width, w_height = 490, 360 
        p_x = parent.winfo_x(); p_y = parent.winfo_y()
        p_w = parent.winfo_width(); p_h = parent.winfo_height()
        pos_x = p_x + (p_w // 2) - (w_width // 2)
        pos_y = p_y + (p_h // 2) - (w_height // 2)
        self.geometry(f"{w_width}x{w_height}+{int(pos_x)}+{int(pos_y)}")

        import xidown.core.utils as utils
        self.icon_path = utils.get_icon_path()

        def force_icon():
            try:
                if self.icon_path and os.path.exists(self.icon_path): self.iconbitmap(self.icon_path)
            except Exception: pass
        force_icon(); self.after(200, force_icon)   

        self.transient(parent)
        self.grab_set()

        self.grid_columnconfigure(0, weight=0) 
        self.grid_columnconfigure(1, weight=1) 
        self.grid_rowconfigure(0, weight=1)

        # --- Sidebar ---
        self.frame_sidebar = ctk.CTkFrame(self, width=120, corner_radius=0, fg_color="#1a1a1a")
        self.frame_sidebar.grid(row=0, column=0, sticky="nsew")
        self.frame_sidebar.grid_rowconfigure(9, weight=1) 

        self.lbl_menu = ctk.CTkLabel(self.frame_sidebar, text="SETTINGS", font=("Terminal", 12, "bold"), text_color="gray")
        self.lbl_menu.grid(row=0, column=0, padx=5, pady=(12, 5)) 

        self.btn_about = self.create_sidebar_button("About", 1, self.show_about)
        self.btn_cache = self.create_sidebar_button("Cache & Temp", 2, self.show_cache)
        self.btn_connection = self.create_sidebar_button("Connection", 3, self.show_connection)
        self.btn_cookies = self.create_sidebar_button("Cookies", 4, self.show_cookies)
        self.btn_resolution = self.create_sidebar_button("Resolution", 5, self.show_resolution)
        self.btn_storage = self.create_sidebar_button("Storage", 6, self.show_storage)
        self.btn_engine = self.create_sidebar_button("yt-dlp Engine", 7, self.show_engine)

        self.btn_save_all = ctk.CTkButton(
            self.frame_sidebar, text="Save", width=90, height=26, 
            fg_color="#db2777", hover_color="#be185d", corner_radius=0,
            font=("Terminal", 12, "bold"), command=self.save_all
        )
        self.btn_save_all.grid(row=10, column=0, padx=8, pady=12, sticky="s")

        self.frame_content = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        self.frame_content.grid(row=0, column=1, sticky="nsew", padx=12, pady=10) 

        self.setup_about()
        self.setup_cache()
        self.setup_connection()
        self.setup_cookies()
        self.setup_resolution()
        self.setup_storage()
        self.setup_engine()

        self.show_about()
        self.after(50, self.deiconify)


    def create_sidebar_button(self, text, row, command):
        btn = ctk.CTkButton(
            self.frame_sidebar, text=text, fg_color="transparent", 
            text_color=("gray10", "gray90"), hover_color=("gray70", "gray30"),
            anchor="w", command=command, height=26, font=("Terminal", 11, "bold"), corner_radius=0
        )
        btn.grid(row=row, column=0, sticky="ew", padx=5, pady=2) 
        return btn

    def reset_highlight(self):
        buttons = [self.btn_about, self.btn_cache, self.btn_connection, self.btn_cookies, self.btn_resolution, self.btn_storage, self.btn_engine]
        for btn in buttons:
            btn.configure(fg_color="transparent", text_color="gray90")

    def set_active(self, btn):
        self.reset_highlight()
        btn.configure(fg_color="#333333", text_color="white")
        for widget in self.frame_content.winfo_children():
            widget.pack_forget()

    # --- Content Pages ---

    # 1. ABOUT
    def setup_about(self):
        self.page_about = ctk.CTkFrame(self.frame_content, fg_color="transparent")
        ctk.CTkLabel(self.page_about, text=APP_NAME, font=("Terminal", 24, "bold"), text_color="#db2777").pack(pady=(15, 0))
        ctk.CTkLabel(self.page_about, text=APP_VER, font=("Terminal", 12, "bold"), text_color="gray").pack(pady=0)
        
        # Dev row (packed side-by-side to stay close)
        dev_row = ctk.CTkFrame(self.page_about, fg_color="transparent")
        dev_row.pack(pady=(12, 4))
        ctk.CTkLabel(dev_row, text="Dev: ", font=("Terminal", 11, "bold")).pack(side="left")
        l = ctk.CTkLabel(dev_row, text="Indra Voyager", font=("Terminal", 11, "underline", "bold"), text_color="#61afef", cursor="hand2")
        l.pack(side="left")
        l.bind("<Button-1>", lambda e: webbrowser.open("https://github.com/indravoyager/xidown"))

        # Contributors row (names placed below the title)
        contrib_frame = ctk.CTkFrame(self.page_about, fg_color="transparent")
        contrib_frame.pack(pady=(4, 10))
        ctk.CTkLabel(contrib_frame, text="Contributors:", font=("Terminal", 11, "bold"), text_color="white").pack()
        ctk.CTkLabel(contrib_frame, text="cyrene, merry, mitsuki31", font=("Terminal", 11, "bold"), text_color="white").pack()

        # Trakteer Button
        self.btn_trakteer = ctk.CTkButton(
            self.page_about, 
            text="♥ Support on Trakteer", 
            fg_color="#c1272d", 
            hover_color="#9e1b20", 
            corner_radius=4,
            font=("Terminal", 11, "bold"), 
            height=28,
            command=lambda: webbrowser.open("https://trakteer.id/indravoyager")
        )
        self.btn_trakteer.pack(pady=(2, 10))

    def show_about(self): self.set_active(self.btn_about); self.page_about.pack(fill="both", expand=True)

    # 2. CACHE & TEMP
    def setup_cache(self):
        self.page_cache = ctk.CTkFrame(self.frame_content, fg_color="transparent")
        ctk.CTkLabel(self.page_cache, text="Cleaner Manager", font=("Terminal", 14, "bold")).pack(anchor="w", pady=(0, 8))
        
        ctk.CTkLabel(
            self.page_cache, 
            text="This will delete:\n1. Thumbnail Images (Cache)\n2. Incomplete Downloads (.part, .ytdl)", 
            font=("Terminal", 11), text_color="gray", justify="left"
        ).pack(anchor="w", pady=(0, 15))
        
        self.lbl_cache_size = ctk.CTkLabel(self.page_cache, text="Calculating...", font=("Terminal", 12), text_color="#db2777")
        self.lbl_cache_size.pack(anchor="w", pady=(0, 10))

        self.btn_clear_cache = ctk.CTkButton(
            self.page_cache, text="Clean All Trash", 
            fg_color="#444", hover_color="#c0392b", corner_radius=0,
            font=("Terminal", 11, "bold"), height=32,
            command=self.action_clear_cache
        )
        self.btn_clear_cache.pack(anchor="w")

    def get_download_path(self):
        folder_bulan = f"{datetime.now().year}_{datetime.now().month:02d}"
        default_path = os.path.join(DATA_DIR, folder_bulan)
        if self.config.get("use_default_path", True):
            return default_path
        custom = self.config.get("save_path", "").strip()
        return custom if custom else default_path

    def calculate_cache(self):
        thumb_dir = os.path.join(DATA_DIR, "thumbs")
        total_size = 0
        count = 0
        if os.path.exists(thumb_dir):
            for f in os.listdir(thumb_dir):
                fp = os.path.join(thumb_dir, f)
                try:
                    total_size += os.path.getsize(fp)
                    count += 1
                except: pass
        
        dl_path = self.get_download_path()
        process_path = os.path.join(dl_path, "process")
        target_folders = [dl_path, process_path]
        junk_exts = ('.part', '.ytdl', '.aria2', '.temp', '.tmp')
        
        for folder in target_folders:
            if os.path.exists(folder):
                try:
                    for f in os.listdir(folder):
                        if f.endswith(junk_exts):
                            fp = os.path.join(folder, f)
                            total_size += os.path.getsize(fp)
                            count += 1
                except: pass

        mb_size = total_size / (1024 * 1024)
        self.lbl_cache_size.configure(text=f"Junk Detected: {mb_size:.2f} MB ({count} files)")

    def action_clear_cache(self):
        thumb_dir = os.path.join(DATA_DIR, "thumbs")
        deleted_count = 0
        
        if os.path.exists(thumb_dir):
            try:
                for filename in os.listdir(thumb_dir):
                    file_path = os.path.join(thumb_dir, filename)
                    try:
                        if os.path.isfile(file_path) or os.path.islink(file_path):
                            os.unlink(file_path)
                            deleted_count += 1
                        elif os.path.isdir(file_path):
                            shutil.rmtree(file_path)
                            deleted_count += 1
                    except Exception as e: pass
            except: pass

        dl_path = self.get_download_path()
        process_path = os.path.join(dl_path, "process")
        target_folders = [dl_path, process_path]
        junk_exts = ('.part', '.ytdl', '.aria2', '.temp', '.tmp')
        
        for folder in target_folders:
            if os.path.exists(folder):
                try:
                    for f in os.listdir(folder):
                        if f.endswith(junk_exts):
                            fp = os.path.join(folder, f)
                            try:
                                os.remove(fp)
                                deleted_count += 1
                            except: pass
                except: pass
            
        self.calculate_cache()
        self.btn_clear_cache.configure(text="All Clean!", fg_color="#27ae60")
        self.after(2000, lambda: self.btn_clear_cache.configure(text="Clean All Trash", fg_color="#444"))

    def show_cache(self): 
        self.set_active(self.btn_cache)
        self.page_cache.pack(fill="both", expand=True)
        self.calculate_cache() 

    # 3. CONNECTION
    def setup_connection(self):
        self.page_conn = ctk.CTkFrame(self.frame_content, fg_color="transparent")
        
        ctk.CTkLabel(self.page_conn, text="Threads (Parts per File)", font=("Terminal", 13, "bold")).pack(anchor="w", pady=(0, 5))
        
        self.threads_var = ctk.IntVar(value=self.config.get("threads", 2))
        f_thread = ctk.CTkFrame(self.page_conn, fg_color="transparent")
        f_thread.pack(fill="x", pady=(0, 12))
        for i, (t, v) in enumerate([(  "1 Part", 1), ("2 Parts", 2), ("4 Parts", 4)]):
            f_thread.grid_columnconfigure(i, weight=1)
        self._thread_btns = []
        for i, (t, v) in enumerate([("1 Part", 1), ("2 Parts", 2), ("4 Parts", 4)]):
            btn = ctk.CTkButton(f_thread, text=t, height=30, corner_radius=0, font=("Terminal", 11, "bold"),
                fg_color="#db2777" if self.threads_var.get() == v else "#2b2b2b",
                hover_color="#be185d" if self.threads_var.get() == v else "#3a3a3a",
                command=lambda val=v: self._set_threads(val))
            btn.grid(row=0, column=i, sticky="ew", padx=(0 if i == 0 else 1, 0))
            btn._val = v
            self._thread_btns.append(btn)

        ctk.CTkLabel(self.page_conn, text="Parallel (Downloads)", font=("Terminal", 13, "bold")).pack(anchor="w", pady=(0, 5))
        self.parallel_var = ctk.IntVar(value=self.config.get("parallel_count", 1))
        f_parallel = ctk.CTkFrame(self.page_conn, fg_color="transparent")
        f_parallel.pack(fill="x", pady=(0, 5))
        self._parallel_btns = []
        for i, (t, v) in enumerate([("1", 1), ("2", 2), ("3", 3)]):
            f_parallel.grid_columnconfigure(i, weight=1)
            btn = ctk.CTkButton(f_parallel, text=t, height=30, corner_radius=0, font=("Terminal", 11, "bold"),
                fg_color="#db2777" if self.parallel_var.get() == v else "#2b2b2b",
                hover_color="#be185d" if self.parallel_var.get() == v else "#3a3a3a",
                command=lambda val=v: self._set_parallel(val))
            btn.grid(row=0, column=i, sticky="ew", padx=(0 if i == 0 else 1, 0))
            btn._val = v
            self._parallel_btns.append(btn)

    def _set_threads(self, val):
        self.threads_var.set(val)
        for btn in self._thread_btns:
            if btn._val == val:
                btn.configure(fg_color="#db2777", hover_color="#be185d")
            else:
                btn.configure(fg_color="#2b2b2b", hover_color="#3a3a3a")

    def _set_parallel(self, val):
        self.parallel_var.set(val)
        for btn in self._parallel_btns:
            if btn._val == val:
                btn.configure(fg_color="#db2777", hover_color="#be185d")
            else:
                btn.configure(fg_color="#2b2b2b", hover_color="#3a3a3a")

    def show_connection(self): self.set_active(self.btn_connection); self.page_conn.pack(fill="both", expand=True)

    # 4. COOKIES
    def setup_cookies(self):
        self.page_cookies = ctk.CTkFrame(self.frame_content, fg_color="transparent")
        ctk.CTkLabel(self.page_cookies, text="Global Cookies", font=("Terminal", 14, "bold")).pack(anchor="w", pady=(0, 5))
        ctk.CTkLabel(self.page_cookies, text="Auto-managed per domain.\nSelect global fallback if needed.", font=("Terminal", 10), text_color="gray", justify="left").pack(anchor="w", pady=(0, 8))
        
        f_ck = ctk.CTkFrame(self.page_cookies, fg_color="transparent")
        f_ck.pack(fill="x")
        self.entry_cookie = ctk.CTkEntry(f_ck, placeholder_text="Path to cookies.txt...", font=("Terminal", 11, "bold"), height=26, corner_radius=0)
        self.entry_cookie.pack(side="left", fill="x", expand=True, padx=(0, 5))
        self.entry_cookie.insert(0, self.config.get("cookie_path", ""))
        self.btn_browse_cookie = ctk.CTkButton(f_ck, text="Folder", width=50, height=26, fg_color="#565f89", font=("Terminal", 11, "bold"), corner_radius=0, command=self.select_cookie_file)
        self.btn_browse_cookie.pack(side="right")
        self.btn_clear_cookie = ctk.CTkButton(self.page_cookies, text="Clear Path", fg_color="#444", hover_color="#666", height=26, font=("Terminal", 11, "bold"), corner_radius=0, command=lambda: self.entry_cookie.delete(0, "end"))
        self.btn_clear_cookie.pack(anchor="w", pady=8)

    def select_cookie_file(self):
        f = filedialog.askopenfilename(filetypes=[("Text Files", "*.txt"), ("All Files", "*.*")])
        if f: self.entry_cookie.delete(0, "end"); self.entry_cookie.insert(0, f)

    def show_cookies(self): self.set_active(self.btn_cookies); self.page_cookies.pack(fill="both", expand=True)

    # 5. RESOLUTION
    def setup_resolution(self):
        self.page_res = ctk.CTkFrame(self.frame_content, fg_color="transparent")
        ctk.CTkLabel(self.page_res, text="Video Quality", font=("Terminal", 14, "bold")).pack(anchor="w", pady=(0, 8))
        self.quality_var = ctk.StringVar(value=self.config.get("quality", "excellent"))
        
        self._res_btns = []
        for t, v in [("Excellent", "excellent"), ("Standard", "best")]:
            btn = ctk.CTkButton(self.page_res, text=t, height=30, corner_radius=0, font=("Terminal", 11, "bold"),
                anchor="w",
                fg_color="#db2777" if self.quality_var.get() == v else "#2b2b2b",
                hover_color="#be185d" if self.quality_var.get() == v else "#3a3a3a",
                command=lambda val=v: self._set_quality(val))
            btn.pack(fill="x", pady=1)
            btn._val = v
            self._res_btns.append(btn)

    def _set_quality(self, val):
        self.quality_var.set(val)
        for btn in self._res_btns:
            if btn._val == val:
                btn.configure(fg_color="#db2777", hover_color="#be185d")
            else:
                btn.configure(fg_color="#2b2b2b", hover_color="#3a3a3a")

    def show_resolution(self): self.set_active(self.btn_resolution); self.page_res.pack(fill="both", expand=True)

    # 6. STORAGE
    def setup_storage(self):
        self.page_storage = ctk.CTkFrame(self.frame_content, fg_color="transparent")
        ctk.CTkLabel(self.page_storage, text="Download Location", font=("Terminal", 14, "bold")).pack(anchor="w", pady=(0, 8))
        self.use_default_var = ctk.BooleanVar(value=self.config.get("use_default_path", True))
        
        folder_bulan = f"{datetime.now().year}_{datetime.now().month:02d}"
        path_def = f".../Videos/xidown/{folder_bulan}"
        
        self.chk_default = ctk.CTkCheckBox(
            self.page_storage, text=f"Default ({path_def})", variable=self.use_default_var, 
            command=self.toggle_storage_ui, fg_color="#db2777", hover_color="#be185d", font=("Terminal", 11, "bold"), 
            checkbox_width=22, checkbox_height=22, border_width=2, corner_radius=2, border_color="#555555", checkmark_color="white"
        )
        self.chk_default.pack(anchor="w", pady=5)
        f_in = ctk.CTkFrame(self.page_storage, fg_color="transparent")
        f_in.pack(fill="x", pady=5)
        self.entry_path = ctk.CTkEntry(f_in, placeholder_text="Select folder...", height=26, font=("Terminal", 11, "bold"), corner_radius=0)
        self.entry_path.pack(side="left", fill="x", expand=True, padx=(0, 5))
        self.btn_browse = ctk.CTkButton(f_in, text="Folder", width=50, height=26, command=self.select_folder, fg_color="#565f89", font=("Terminal", 11, "bold"), corner_radius=0)
        self.btn_browse.pack(side="right")
        self.toggle_storage_ui()

    def toggle_storage_ui(self):
        folder_bulan = f"{datetime.now().year}_{datetime.now().month:02d}"
        default_full_path = os.path.join(DATA_DIR, folder_bulan)
        if self.use_default_var.get():
            self.entry_path.configure(state="normal")
            self.entry_path.delete(0, "end")
            self.entry_path.insert(0, default_full_path)
            self.entry_path.configure(state="disabled", fg_color="#2b2b2b")
        else:
            self.entry_path.configure(state="normal", fg_color="#343638")
            saved = self.config.get("save_path", "").strip()
            self.entry_path.delete(0, "end")
            if saved and saved != default_full_path:
                self.entry_path.insert(0, saved)

    def select_folder(self):
        f = filedialog.askdirectory()
        if f:
            self.use_default_var.set(False)
            self.toggle_storage_ui()
            self.entry_path.delete(0, "end")
            self.entry_path.insert(0, f)
    
    def show_storage(self): self.set_active(self.btn_storage); self.page_storage.pack(fill="both", expand=True)

    # 7. ENGINE (yt-dlp)
    def setup_engine(self):
        self.page_engine = ctk.CTkFrame(self.frame_content, fg_color="transparent")
        
        ctk.CTkLabel(self.page_engine, text="yt-dlp Engine Manager", font=("Terminal", 14, "bold")).pack(anchor="w", pady=(0, 2))
        ctk.CTkLabel(
            self.page_engine, 
            text="Download engine maintenance & extraction fixes.", 
            font=("Terminal", 10), text_color="gray"
        ).pack(anchor="w", pady=(0, 6))

        # Version display frame
        f_ver = ctk.CTkFrame(self.page_engine, fg_color="#1e1e1e", corner_radius=2, border_width=1, border_color="#333333")
        f_ver.pack(fill="x", pady=(0, 6), ipady=3)
        
        self.lbl_ytdlp_ver = ctk.CTkLabel(f_ver, text="Engine Version: Checking...", font=("Terminal", 11, "bold"), text_color="#db2777")
        self.lbl_ytdlp_ver.pack(anchor="w", padx=10, pady=(2, 0))
        
        self.lbl_engine_status = ctk.CTkLabel(f_ver, text="Ready", font=("Terminal", 10), text_color="#aaaaaa", justify="left", wraplength=310)
        self.lbl_engine_status.pack(anchor="w", padx=10, pady=(0, 4))

        # Channel Selector Row
        f_chan = ctk.CTkFrame(self.page_engine, fg_color="transparent")
        f_chan.pack(fill="x", pady=(0, 6))
        ctk.CTkLabel(f_chan, text="Channel:", font=("Terminal", 10, "bold"), text_color="#aaaaaa").pack(side="left", padx=(0, 6))
        
        self.channel_var = ctk.StringVar(value="stable")
        self._chan_btns = []
        for name, val in [("Stable", "stable"), ("Nightly (Latest)", "nightly")]:
            btn = ctk.CTkButton(
                f_chan, text=name, height=24, corner_radius=0, font=("Terminal", 10, "bold"),
                fg_color="#db2777" if self.channel_var.get() == val else "#2b2b2b",
                hover_color="#be185d" if self.channel_var.get() == val else "#3a3a3a",
                command=lambda v=val: self._set_channel(v)
            )
            btn.pack(side="left", padx=(0, 4))
            btn._val = val
            self._chan_btns.append(btn)

        # Single Action Button
        self.btn_update_engine = ctk.CTkButton(
            self.page_engine, text="Update / Restart yt-dlp", height=32,
            fg_color="#db2777", hover_color="#be185d", corner_radius=0,
            font=("Terminal", 11, "bold"), command=self.action_update_ytdlp
        )
        self.btn_update_engine.pack(fill="x", pady=(4, 0))

    def _set_channel(self, val):
        self.channel_var.set(val)
        for btn in self._chan_btns:
            if btn._val == val:
                btn.configure(fg_color="#db2777", hover_color="#be185d")
            else:
                btn.configure(fg_color="#2b2b2b", hover_color="#3a3a3a")

    def show_engine(self):
        self.set_active(self.btn_engine)
        self.page_engine.pack(fill="both", expand=True)
        self.refresh_engine_version()

    def refresh_engine_version(self):
        def _check():
            ver = setup_core.get_ytdlp_version()
            if ver:
                txt = f"Engine Version: {ver}"
                st = "Ready (Nightly)" if "nightly" in ver.lower() or len(ver.split(".")) > 3 else "Ready (Stable)"
            else:
                txt = "Engine Version: Not Detected"
                st = "Binary missing or not found"
            self.after(0, lambda: self._apply_engine_ver(txt, st))
        threading.Thread(target=_check, daemon=True).start()

    def _apply_engine_ver(self, text_ver, text_status):
        if hasattr(self, 'lbl_ytdlp_ver'):
            self.lbl_ytdlp_ver.configure(text=text_ver)
        if hasattr(self, 'lbl_engine_status'):
            self.lbl_engine_status.configure(text=text_status)

    def action_update_ytdlp(self):
        chosen_chan = self.channel_var.get()
        chan_title = "Nightly" if chosen_chan == "nightly" else "Stable"
        self.btn_update_engine.configure(state="disabled", text="Updating Engine...")
        self.lbl_engine_status.configure(text=f"Updating & refreshing ({chan_title})...", text_color="#00ffcc")
        
        def _task():
            def cb(p, msg):
                self.after(0, lambda: self.lbl_engine_status.configure(text=msg, text_color="#00ffcc"))
            success, msg = setup_core.update_ytdlp(channel=chosen_chan, progress_callback=cb)
            ver = setup_core.get_ytdlp_version()
            self.after(0, lambda: self._on_update_done(success, msg, ver))
        threading.Thread(target=_task, daemon=True).start()

    def _on_update_done(self, success, msg, ver):
        self.btn_update_engine.configure(state="normal", text="Update / Restart yt-dlp")
        color = "#27ae60" if success else "#ff5555"
        self.lbl_engine_status.configure(text=msg, text_color=color)
        if ver:
            self.lbl_ytdlp_ver.configure(text=f"Engine Version: {ver}")
        if hasattr(self.parent, 'reload_tools'):
            self.parent.reload_tools()
        self.after(5000, lambda: self.lbl_engine_status.configure(text_color="#aaaaaa"))

    # --- SAVE ALL ---
    def save_all(self):
        folder_bulan = f"{datetime.now().year}_{datetime.now().month:02d}"
        default_full_path = os.path.join(DATA_DIR, folder_bulan)
        current_path = self.entry_path.get().strip()
        if self.use_default_var.get() or not current_path or current_path == default_full_path:
            final_path = ""
            use_default = True
        else:
            final_path = current_path
            use_default = False

        new_data = {
            "quality": self.quality_var.get(),
            "save_path": final_path,
            "use_default_path": use_default,
            "threads": self.threads_var.get(),
            "parallel_count": self.parallel_var.get(), 
            "cookie_path": self.entry_cookie.get().strip() 
        }
        save_config(new_data)
        if hasattr(self.parent, 'config'): self.parent.config = new_data
        if hasattr(self.parent, 'reload_initial_config'):
            self.parent.reload_initial_config()
        print("[System] Settings saved & synced.")
        self.destroy()