import customtkinter as ctk
from tkinter import filedialog, messagebox
import os
import json
import threading
import git
import requests
from datetime import datetime

CONFIG_FILE = "git_app_config.json"

def log(message):
    print(f"[LOG] {message}")

class GitFunctions:
    def __init__(self, app: ctk.CTk):
        self.app = app
        self.repo_object = None
        self.source_repo_path = None
        self.target_repo_url = None
        self.active_repo_data = {}
        self.selected_commit_hash = None
        self.full_commit_hashes = {}
        # Konfiqurasiyaya yeni sahələr əlavə edildi
        self.config = {
            "token": "", 
            "last_source_path": "",
            "user_name": "",
            "user_email": ""
        }
        log("GitFunctions obyekti yaradıldı.")

    def _update_status(self, text, color="white"):
        if self.app.winfo_exists():
            self.app.status_bar.configure(text=text, text_color=color)

    def _update_info_labels(self, source_text=None, target_text=None):
        try:
            if source_text is not None: self.app.source_label.configure(text=source_text)
            if target_text is not None: self.app.target_label.configure(text=target_text)
        except Exception as e:
            log(f"!!! UI LABEL UPDATE XƏTASI: {e}")

    def _update_repo_list_ui(self, repos):
        if not self.app.winfo_exists(): return
        for widget in self.app.repo_list_frame.winfo_children():
            widget.destroy()
        for repo in sorted(repos, key=lambda x: x['name']):
            ctk.CTkButton(
                self.app.repo_list_frame, text=repo['name'], fg_color="transparent",
                border_width=1, anchor="w",
                command=self.run_in_thread(self.handle_select_target_repo, repo)
            ).pack(fill="x", padx=5, pady=3)
        self._update_status(f"{len(repos)} depo tapıldı. Əməliyyat üçün seçin.", "lightgreen")

    def _update_commit_history_ui(self, commits, source_type="online"):
        if not self.app.winfo_exists(): return
        self.full_commit_hashes.clear()
        for item in self.app.commit_history_table.get_children():
            self.app.commit_history_table.delete(item)
        if not commits: return
        for commit_data in commits:
            try:
                if source_type == "local" and isinstance(commit_data, git.Commit):
                    sha_full, msg, author, date_str = (commit_data.hexsha, commit_data.summary, commit_data.author.name, datetime.fromtimestamp(commit_data.authored_date).strftime('%Y-%m-%d %H:%M'))
                elif source_type == "online":
                    sha_full, msg, author, date_str = (commit_data['sha'], commit_data['commit']['message'].split('\n')[0], commit_data['commit']['author']['name'], datetime.strptime(commit_data['commit']['author']['date'], "%Y-%m-%dT%H:%M:%SZ").strftime('%Y-%m-%d %H:%M'))
                else: continue
                sha_short = sha_full[:8]
                self.full_commit_hashes[sha_short] = sha_full
                self.app.commit_history_table.insert("", "end", values=(sha_short, msg, author, date_str))
            except Exception as e:
                log(f"!!! COMMIT DATA PARSING ERROR: {e}")

    def run_in_thread(self, func, *args, **kwargs):
        def wrapper():
            log(f"'{func.__name__}' funksiyası üçün yeni thread yaradılır.")
            self.app.connect_button.configure(state="disabled")
            thread = threading.Thread(target=self._run_task_with_finally, args=(func, args, kwargs), daemon=True)
            thread.start()
        return wrapper

    def _run_task_with_finally(self, func, args, kwargs):
        log(f"Thread başladı: '{func.__name__}' icra edilir.")
        try:
            func(*args, **kwargs)
            log(f"Thread uğurla tamamlandı: '{func.__name__}'.")
        except Exception as e:
            log(f"!!! THREAD XƏTASI '{func.__name__}': {e}")
        finally:
            if self.app.winfo_exists():
                self.app.connect_button.configure(state="normal")
            log(f"Thread sonlandı: '{func.__name__}' və düymələr aktiv edildi.")

    def save_config(self):
        log("Konfiqurasiya saxlanılır...")
        self.config['token'] = self.app.token_entry.get()
        self.config['last_source_path'] = self.source_repo_path
        # Yeni məlumatları da yadda saxla
        self.config['user_name'] = self.app.user_name_entry.get()
        self.config['user_email'] = self.app.user_email_entry.get()
        try:
            with open(CONFIG_FILE, "w") as f:
                json.dump(self.config, f, indent=4)
            log(f"Konfiqurasiya '{CONFIG_FILE}' faylına yazıldı.")
            self.app.after(0, self._update_status, "Ayarlar yadda saxlanıldı!", "lightgreen")
        except Exception as e:
            log(f"!!! KONFİQURASİYA SAXLANMA XƏTASI: {e}")

    def load_config(self):
        log("Konfiqurasiya yüklənir...")
        if not os.path.exists(CONFIG_FILE): return
        try:
            with open(CONFIG_FILE, "r") as f:
                self.config = json.load(f)
            log("Konfiqurasiya faylı uğurla oxundu.")
            # Yadda saxlanmış məlumatları UI-a yüklə
            self.app.token_entry.insert(0, self.config.get("token", ""))
            self.app.user_name_entry.insert(0, self.config.get("user_name", ""))
            self.app.user_email_entry.insert(0, self.config.get("user_email", ""))
            
            last_path = self.config.get("last_source_path")
            if last_path and os.path.exists(last_path):
                self.load_source_repo(last_path)
            if self.config.get("token"):
                self.run_in_thread(self.handle_connect_account)()
        except Exception as e:
            log(f"!!! KONFİQURASİYA YÜKLƏNMƏ XƏTASI: {e}")

    def handle_connect_account(self):
        token = self.app.token_entry.get()
        if not token:
            self.app.after(0, self._update_status, "Xəta: Access Token daxil edilməyib.", "orange")
            return
        # ... (bu funksiyanın qalan hissəsi dəyişmir)
        self.app.after(0, self._update_status, "GitHub hesabına qoşulunur...", "yellow")
        headers = {"Authorization": f"token {token}"}
        try:
            repos_data, page = [], 1
            while True:
                url = f"https://api.github.com/user/repos?page={page}&per_page=100"
                response = requests.get(url, headers=headers)
                response.raise_for_status()
                data = response.json()
                if not data: break
                repos_data.extend(data)
                page += 1
            self.app.after(0, self._update_repo_list_ui, repos_data)
            self.save_config()
        except requests.exceptions.RequestException as e:
            self.app.after(0, self._update_status, f"GitHub API xətası: {e}", "orange")

    def handle_select_source_folder(self):
        folder_path = filedialog.askdirectory(title="Lokal Git anbarını seçin")
        if folder_path: self.load_source_repo(folder_path)

    # --- YENİ MƏNTİQ: GIT AYARLARINI TƏTBİQ ET ---
    def _apply_git_config(self):
        """Proqramdakı istifadəçi məlumatlarını lokal anbarın konfiqurasiyasına yazır."""
        if not self.repo_object: return False
        user_name = self.config.get("user_name")
        user_email = self.config.get("user_email")
        if not user_name or not user_email:
            self.app.after(0, messagebox.showwarning, "Eksik Məlumat", "Davam etmək üçün 'Git İstifadəçi Məlumatları' bölməsini doldurun və yadda saxlayın.")
            return False
        
        try:
            log(f"Anbar üçün Git konfiqurasiyası təyin edilir: {user_name} <{user_email}>")
            with self.repo_object.config_writer() as cw:
                cw.set_value("user", "name", user_name)
                cw.set_value("user", "email", user_email)
            return True
        except Exception as e:
            log(f"!!! GIT KONFİQURASİYA XƏTASI: {e}")
            return False

    def load_source_repo(self, path):
        log(f"Lokal anbar yüklənir: {path}")
        try:
            if not os.path.exists(os.path.join(path, '.git')):
                if messagebox.askyesno("Git Anbarı Tapılmadı", f"'{os.path.basename(path)}' qovluğu bir Git anbarı deyil.\nYeni bir anbar yaradılsınmı?"):
                    self.repo_object = git.Repo.init(path)
                    log("Yeni lokal anbar yaradıldı.")
                else: return False
            else:
                self.repo_object = git.Repo(path)

            # --- DƏYİŞİKLİK: Git ayarlarını dərhal tətbiq et ---
            if not self._apply_git_config():
                self.repo_object = None # Ayarlar səhvdirsə, anbarı yükləmə
                return False

            self.source_repo_path = path
            self.app.after(0, self._update_info_labels, f"Mənbə (Lokal): {os.path.basename(path)}", None)
            self.app.after(0, self.app.source_path_label.configure, {"text": path, "text_color": "white"})
            self.run_in_thread(self.populate_local_commit_history)()
            self.save_config()
            return True
        except Exception as e:
            log(f"!!! LOKAL ANBAR YÜKLƏMƏ XƏTASI: {e}")
            messagebox.showerror("Xəta", f"Anbarı yükləmək mümkün olmadı: {e}")
            return False

    def populate_local_commit_history(self):
        # ... (bu funksiya dəyişmir)
        if not self.repo_object: return
        try:
            commits = list(self.repo_object.iter_commits('main', max_count=100))
            self.app.after(0, self._update_commit_history_ui, commits, "local")
        except git.exc.GitCommandError:
            self.app.after(0, self._update_commit_history_ui, [], "local")

    def handle_select_target_repo(self, repo_data):
        # ... (bu funksiya dəyişmir)
        self.target_repo_url = repo_data['clone_url']
        self.active_repo_data = repo_data
        self.app.after(0, self._update_info_labels, None, f"Hədəf (Onlayn): {repo_data['name']}")
        self.run_in_thread(self.fetch_online_commits, repo_data)()

    def fetch_online_commits(self, repo_data):
        # ... (bu funksiya dəyişmir)
        token = self.app.token_entry.get()
        headers = {"Authorization": f"token {token}"}
        url = repo_data['commits_url'].replace('{/sha}', '')
        try:
            response = requests.get(f"{url}?per_page=100", headers=headers)
            response.raise_for_status()
            commits = response.json()
            self.app.after(0, self._update_commit_history_ui, commits, "online")
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 409:
                self.app.after(0, self._update_commit_history_ui, [], "online")
                self.app.after(0, self._update_status, f"'{repo_data['name']}' anbarı boşdur.", "gray")

    def handle_commit_selection_event(self, event):
        # ... (bu funksiya dəyişmir)
        if not self.app.commit_history_table.selection(): return
        selected_item = self.app.commit_history_table.selection()[0]
        item_values = self.app.commit_history_table.item(selected_item, "values")
        sha_short, message = item_values[0], item_values[1]
        self.selected_commit_hash = self.full_commit_hashes.get(sha_short)
        if self.selected_commit_hash:
            self.app.selected_commit_label.configure(text=f"Seçildi: {sha_short} - {message}", text_color="cyan")

    def handle_pull(self):
        self.run_in_thread(self._pull_task)()

    # git_functions.py faylında _pull_task funksiyasını tapıb bununla əvəz edin

    def _pull_task(self):
        if not all([self.source_repo_path, self.target_repo_url]):
            self.app.after(0, messagebox.showwarning, "Eksik Məlumat", "Əməliyyat üçün Mənbə və Hədəf seçin.")
            return
        if not self.repo_object:
            return
            
        try:
            log("Pull əməliyyatı başladı...")
            self.app.after(0, self._update_status, "Onlayn dəyişikliklər çəkilir (pull)...", "yellow")
            
            remote_name = "hədəf_depo"
            remote = None
            if remote_name in [r.name for r in self.repo_object.remotes]:
                remote = self.repo_object.remote(name=remote_name)
                if remote.url != self.target_repo_url:
                    remote.set_url(self.target_repo_url)
            else:
                remote = self.repo_object.create_remote(remote_name, self.target_repo_url)

            # --- DƏYİŞİKLİK BURADADIR ---
            # Açıq şəkildə 'main' filialını çəkdiyimizi bildiririk
            log(f"'{remote.name}' anbarından 'main' filialı çəkilir...")
            remote.pull(refspec='main', allow_unrelated_histories=True)
            # --- SON ---
            
            self.app.after(0, self._update_status, "Dəyişikliklər uğurla çəkildi!", "lightgreen")
            self.populate_local_commit_history()
            
        except git.exc.GitCommandError as e:
            log(f"!!! PULL XƏTASI: {e}")
            error_message = str(e)
            if "conflict" in error_message.lower():
                 self.app.after(0, messagebox.showwarning, "Merge Conflict", "Pull əməliyyatı zamanı 'merge conflict' baş verdi.\n\nZəhmət olmasa, konflikləri VS Code kimi bir redaktorda həll edib, dəyişiklikləri yenidən commit edin.")
            elif "couldn't find remote ref main" in error_message.lower():
                 self.app.after(0, messagebox.showwarning, "Filial Tapılmadı", "Onlayn anbarda 'main' adlı filial tapılmadı. Depo boş ola bilər. Əvvəlcə bir dəfə 'Push' etməyə cəhd edin.")
            else:
                self.app.after(0, messagebox.showerror, "Pull Xətası", f"Dəyişiklikləri çəkmək mümkün olmadı:\n\n{e}")
        except Exception as e:
            log(f"!!! GÖZLƏNİLMƏZ PULL XƏTASI: {e}")
            self.app.after(0, messagebox.showerror, "Gözlənilməz Xəta", str(e))
    def handle_commit_and_push(self):
        # ... (bu funksiya dəyişmir)
        self.run_in_thread(self._commit_and_push_task)()

    def _commit_and_push_task(self):
        msg = self.app.commit_message_entry.get()
        if not all([self.source_repo_path, self.target_repo_url, msg]):
            self.app.after(0, messagebox.showwarning, "Eksik Məlumat", "Əməliyyat üçün Mənbə, Hədəf seçin və Commit mesajı yazın.")
            return
        if not self.repo_object or self.repo_object.working_dir != self.source_repo_path:
            if not self.load_source_repo(self.source_repo_path): return
        try:
            self.repo_object.git.add(A=True)
            self.repo_object.index.commit(msg)

            # --- DÜZƏLİŞ EDİLMİŞ REMOTE MƏNTİQİ ---
            remote_name = "hədəf_depo"
            remote = None
            if remote_name in [r.name for r in self.repo_object.remotes]:
                remote = self.repo_object.remote(name=remote_name)
                if remote.url != self.target_repo_url:
                    remote.set_url(self.target_repo_url)
            else:
                remote = self.repo_object.create_remote(remote_name, self.target_repo_url)
            # -----------------------------------

            log("Təhlükəsiz push cəhd edilir...")
            push_info = remote.push(refspec='HEAD:main', set_upstream=True)
            
            push_error = False
            for info in push_info:
                if info.flags & (info.ERROR | info.REJECTED):
                    log(f"!!! PUSH FAILED/REJECTED: {info.summary}")
                    self.app.after(0, messagebox.showerror, "Push Rədd Edildi", f"Push əməliyyatı rədd edildi:\n\n{info.summary}\n\nBu, adətən onlayn depoda sizdə olmayan dəyişikliklər olduqda baş verir.\nZəhmət olmasa, əvvəlcə 'Dəyişiklikləri Çək (Pull)' düyməsinə basın.")
                    push_error = True
                    break
            
            if not push_error:
                self.app.after(0, self._update_status, "Dəyişikliklər uğurla göndərildi!", "lightgreen")
                self.app.after(0, self.app.commit_message_entry.delete, 0, 'end')
                self.populate_local_commit_history()
                self.run_in_thread(self.fetch_online_commits, self.active_repo_data)()
        except Exception as e:
            log(f"!!! GÖZLƏNİLMƏZ PUSH XƏTASI: {e}")
            self.app.after(0, messagebox.showerror, "Gözlənilməz Xəta", str(e))
    # handle_zip_commit, _download_commit_zip_task, handle_load_commit, _load_commit_task
    # funksiyaları dəyişmir, olduğu kimi qalır...

    def handle_zip_commit(self):
        if not self.selected_commit_hash:
            messagebox.showwarning("Seçim Yoxdur", "Əvvəlcə tarixçədən bir commit seçin.")
            return
        if not self.active_repo_data:
            messagebox.showwarning("Hədəf Seçilməyib", "'.zip' əməliyyatı üçün onlayn hədəf anbarı seçməlisiniz.")
            return
        zip_path = filedialog.asksaveasfilename(
            defaultextension=".zip", filetypes=[("Zip Arxiv", "*.zip")],
            initialfile=f"{self.active_repo_data.get('name', 'arxiv')}-{self.selected_commit_hash[:8]}.zip",
            title="Commit Arxivini Harada Saxlamalı?")
        if not zip_path: return
        self.run_in_thread(self._download_commit_zip_task, zip_path)()

    def _download_commit_zip_task(self, zip_path):
        try:
            self.app.after(0, self._update_status, f"'{self.selected_commit_hash[:8]}' onlayn arxivdən endirilir...", "yellow")
            token = self.app.token_entry.get()
            headers = {"Authorization": f"token {token}", "Accept": "application/vnd.github.v3+json"}
            url = f"https://api.github.com/repos/{self.active_repo_data['full_name']}/zipball/{self.selected_commit_hash}"
            with requests.get(url, headers=headers, stream=True) as r:
                r.raise_for_status()
                with open(zip_path, 'wb') as f:
                    for chunk in r.iter_content(chunk_size=8192): f.write(chunk)
            self.app.after(0, self._update_status, "Commit uğurla .zip olaraq endirildi!", "lightgreen")
        except Exception as e:
            self.app.after(0, messagebox.showerror, "Endirmə Xətası", f"Arxivi endirmək mümkün olmadı:\n\n{e}")

    def handle_load_commit(self):
        if not self.selected_commit_hash:
            messagebox.showwarning("Seçim Yoxdur", "Əvvəlcə tarixçədən bir commit seçin.")
            return
        if not self.source_repo_path:
            messagebox.showwarning("Mənbə Seçilməyib", "'Reset' əməliyyatı üçün lokal mənbə anbarı seçməlisiniz.")
            return
        if messagebox.askyesno("Təsdiq", f"'{self.selected_commit_hash[:8]}' commit-inə qayıtmaq istəyirsiniz?\nBÜTÜN SONRAKI DƏYİŞİKLİKLƏR SİLİNƏCƏK!"):
            self.run_in_thread(self._load_commit_task)()

    def _load_commit_task(self):
        try:
            self.repo_object.git.reset('--hard', self.selected_commit_hash)
            self.populate_local_commit_history()
            self.app.after(0, self._update_status, "Anbar uğurla geri qaytarıldı!", "lightgreen")
        except Exception as e:
            self.app.after(0, messagebox.showerror, "Reset Xətası", str(e))