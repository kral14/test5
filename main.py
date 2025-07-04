import customtkinter as ctk
from tkinter import messagebox, ttk
from git_functions import GitFunctions

class GitApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Git İdarəetmə Paneli")
        self.geometry("1200x800")
        self.minsize(1000, 700)

        self.functions = GitFunctions(self)

        ctk.set_appearance_mode("Dark")
        ctk.set_default_color_theme("blue")

        self.style = ttk.Style(self)
        self.style.theme_use("default")
        self.style.configure("Treeview",
            background="#2a2d2e",
            foreground="white",
            rowheight=25,
            fieldbackground="#343638",
            bordercolor="#343638",
            borderwidth=0)
        self.style.map('Treeview', background=[('selected', '#22559b')])
        self.style.configure("Treeview.Heading",
            background="#565b5e",
            foreground="white",
            relief="flat")
        self.style.map("Treeview.Heading",
            background=[('active', '#3484F0')])

        self.grid_columnconfigure(1, weight=3)
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.create_left_sidebar()
        self.create_right_main_area()

        self.status_bar = ctk.CTkLabel(self, text="Hazır vəziyyətdə.", anchor="w")
        self.status_bar.grid(row=1, column=0, columnspan=2, padx=20, pady=(5, 10), sticky="ew")

        self.after(100, self.functions.load_config)

    def create_left_sidebar(self):
        sidebar_frame = ctk.CTkFrame(self, width=280, corner_radius=10)
        sidebar_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        sidebar_frame.grid_rowconfigure(3, weight=1) # repo_list_frame üçün

        # Hesab və İstifadəçi Məlumatları Paneli
        control_frame = ctk.CTkFrame(sidebar_frame)
        control_frame.grid(row=0, column=0, padx=15, pady=15, sticky="ew")
        
        ctk.CTkLabel(control_frame, text="GitHub Access Token", font=ctk.CTkFont(weight="bold")).pack(anchor="w", padx=10, pady=(10,0))
        self.token_entry = ctk.CTkEntry(control_frame, placeholder_text="ghp_...")
        self.token_entry.pack(fill="x", padx=10, pady=5)
        self.connect_button = ctk.CTkButton(control_frame, text="Hesaba Bağlan", command=self.functions.run_in_thread(self.functions.handle_connect_account))
        self.connect_button.pack(fill="x", padx=10, pady=(0,15))
        
        # --- YENİ İSTİFADƏÇİ MƏLUMATLARI BÖLMƏSİ ---
        ctk.CTkLabel(control_frame, text="Git İstifadəçi Məlumatları (Commit üçün)", font=ctk.CTkFont(weight="bold")).pack(anchor="w", padx=10, pady=(10,0))
        
        ctk.CTkLabel(control_frame, text="Ad Soyad:", anchor="w").pack(anchor="w", padx=10, pady=(5,0))
        self.user_name_entry = ctk.CTkEntry(control_frame, placeholder_text="Məs: Nesib Memmedov")
        self.user_name_entry.pack(fill="x", padx=10, pady=2)
        
        ctk.CTkLabel(control_frame, text="E-poçt Ünvanı:", anchor="w").pack(anchor="w", padx=10, pady=(5,0))
        self.user_email_entry = ctk.CTkEntry(control_frame, placeholder_text="Məs: nesib@example.com")
        self.user_email_entry.pack(fill="x", padx=10, pady=2)

        self.save_config_button = ctk.CTkButton(control_frame, text="Bu Məlumatları Yadda Saxla", command=self.functions.save_config)
        self.save_config_button.pack(fill="x", padx=10, pady=(10,10))
        # ---------------------------------------------

        # Lokal Anbar
        local_repo_frame = ctk.CTkFrame(sidebar_frame)
        local_repo_frame.grid(row=1, column=0, padx=15, pady=(0,15), sticky="ew")
        
        ctk.CTkLabel(local_repo_frame, text="Lokal Anbar (Mənbə)", font=ctk.CTkFont(weight="bold")).pack(anchor="w", padx=10, pady=(5,0))
        self.select_source_button = ctk.CTkButton(local_repo_frame, text="Commit üçün Qovluq Seç...", command=self.functions.handle_select_source_folder)
        self.select_source_button.pack(fill="x", padx=10, pady=5)
        self.source_path_label = ctk.CTkLabel(local_repo_frame, text="Qovluq seçilməyib", text_color="gray", anchor="w", wraplength=220)
        self.source_path_label.pack(fill="x", padx=10, pady=(0, 10))

        # Onlayn Anbarlar
        repo_list_label = ctk.CTkLabel(sidebar_frame, text="Onlayn Depolar (Hədəf)", font=ctk.CTkFont(weight="bold"))
        repo_list_label.grid(row=2, column=0, padx=15, pady=(0, 5), sticky="w")
        self.repo_list_frame = ctk.CTkScrollableFrame(sidebar_frame, corner_radius=5)
        self.repo_list_frame.grid(row=3, column=0, padx=15, pady=(0, 15), sticky="nsew")
        
        ctk.CTkLabel(self.repo_list_frame, text="Hesaba qoşulun...").pack(pady=20)

    def create_right_main_area(self):
        # Bu funksiyada dəyişiklik yoxdur, olduğu kimi qalır
        right_frame = ctk.CTkFrame(self, corner_radius=10)
        right_frame.grid(row=0, column=1, padx=(0, 10), pady=10, sticky="nsew")
        right_frame.grid_rowconfigure(1, weight=1)
        right_frame.grid_columnconfigure(0, weight=1)
        
        info_frame = ctk.CTkFrame(right_frame)
        info_frame.grid(row=0, column=0, padx=15, pady=15, sticky="ew")
        
        self.source_label = ctk.CTkLabel(info_frame, text="Mənbə (Lokal): Heç bir qovluq seçilməyib", anchor="w")
        self.source_label.pack(fill="x", padx=10, pady=5)
        self.target_label = ctk.CTkLabel(info_frame, text="Hədəf (Onlayn): Heç bir depo seçilməyib", anchor="w")
        self.target_label.pack(fill="x", padx=10, pady=5)
        
        table_frame = ctk.CTkFrame(right_frame, fg_color="transparent")
        table_frame.grid(row=1, column=0, padx=15, pady=10, sticky="nsew")
        table_frame.grid_columnconfigure(0, weight=1)
        table_frame.grid_rowconfigure(0, weight=1)

        columns = ("hash", "message", "author", "date")
        self.commit_history_table = ttk.Treeview(table_frame, columns=columns, show="headings", selectmode="browse")
        
        self.commit_history_table.heading("hash", text="Hash")
        self.commit_history_table.heading("message", text="Mesaj")
        self.commit_history_table.heading("author", text="Müəllif")
        self.commit_history_table.heading("date", text="Tarix")
        
        self.commit_history_table.column("hash", width=100, stretch=False)
        self.commit_history_table.column("message", width=400, stretch=True)
        self.commit_history_table.column("author", width=150, stretch=False)
        self.commit_history_table.column("date", width=150, stretch=False)

        self.commit_history_table.grid(row=0, column=0, sticky="nsew")

        scrollbar = ctk.CTkScrollbar(table_frame, command=self.commit_history_table.yview)
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.commit_history_table.configure(yscrollcommand=scrollbar.set)
        
        self.commit_history_table.bind("<<TreeviewSelect>>", self.functions.handle_commit_selection_event)

        action_frame = ctk.CTkFrame(right_frame)
        action_frame.grid(row=2, column=0, padx=15, pady=15, sticky="ew")
        action_frame.grid_columnconfigure(0, weight=1)

        pull_push_frame = ctk.CTkFrame(action_frame, fg_color="transparent")
        pull_push_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=(10, 0))
        pull_push_frame.grid_columnconfigure(1, weight=1)
        
        self.pull_button = ctk.CTkButton(pull_push_frame, text="Dəyişiklikləri Çək (Pull)", command=self.functions.handle_pull)
        self.pull_button.grid(row=0, column=0, padx=(0,10))
        
        self.commit_push_button = ctk.CTkButton(pull_push_frame, text="Commit et və Göndər (Push)", command=self.functions.handle_commit_and_push)
        self.commit_push_button.grid(row=0, column=2, padx=(10,0))
        
        commit_message_frame = ctk.CTkFrame(action_frame, fg_color="transparent")
        commit_message_frame.grid(row=1, column=0, sticky="ew", padx=10, pady=10)
        commit_message_frame.grid_columnconfigure(0, weight=1)
        self.commit_message_entry = ctk.CTkEntry(commit_message_frame, placeholder_text="Commit üçün mesaj daxil edin...")
        self.commit_message_entry.grid(row=0, column=0, sticky="ew")

        archive_frame = ctk.CTkFrame(action_frame, fg_color="transparent")
        archive_frame.grid(row=2, column=0, sticky="ew", padx=10, pady=(0,10))
        archive_frame.grid_columnconfigure(0, weight=1)
        self.selected_commit_label = ctk.CTkLabel(archive_frame, text="Əməliyyat üçün tarixçədən commit seçin", text_color="gray", anchor="w")
        self.selected_commit_label.grid(row=0, column=0, sticky="ew")
        
        button_sub_frame = ctk.CTkFrame(archive_frame, fg_color="transparent")
        button_sub_frame.grid(row=0, column=1, sticky="e")
        self.zip_commit_button = ctk.CTkButton(button_sub_frame, text="Commit'i .zip Yüklə", command=self.functions.handle_zip_commit)
        self.zip_commit_button.pack(side="right", padx=(10,0))
        self.load_commit_button = ctk.CTkButton(button_sub_frame, text="Commitə Qayıt (Reset)", command=self.functions.handle_load_commit)
        self.load_commit_button.pack(side="right")


if __name__ == "__main__":
    try:
        import git
        import requests
    except ImportError:
        messagebox.showerror("Kitabxana Xətası", "Zəhmət olmasa, tələb olunan kitabxanaları quraşdırın:\npip install customtkinter GitPython requests")
        exit()
        
    app = GitApp()
    app.mainloop()