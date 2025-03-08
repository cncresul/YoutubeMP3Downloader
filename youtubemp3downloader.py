import tkinter as tk
import tkinter.ttk as ttk
import yt_dlp
import os
import threading
import sqlite3
import json
import tkinter.messagebox as messagebox
import tkinter.filedialog as filedialog

class MP3Downloader:
    def __init__(self, root):
        self.root = root
        self.root.title("MP3 İndirici")

        # Veritabanı bağlantısı
        self.conn = sqlite3.connect("settings.db")
        self.cursor = self.conn.cursor()
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT
            )
        """)
        self.conn.commit()

        # Ayarları yükle
        self.settings = self.load_settings()

        # Ayarlar
        self.download_folder = self.settings.get("download_folder", os.path.expanduser("~"))
        self.audio_quality = self.settings.get("audio_quality", "bestaudio/best")
        self.filename_format = self.settings.get("filename_format", "%(title)s.%(ext)s")
        self.max_downloads = int(self.settings.get("max_downloads", 1))  # Tamsayıya dönüştürme

        # Ana çerçeve
        main_frame = ttk.Frame(root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # URL Giriş Bölümü
        url_frame = ttk.Frame(main_frame)
        url_frame.pack(fill=tk.X, pady="5")

        ttk.Label(url_frame, text="URL:").pack(side=tk.LEFT)
        self.url_entry = ttk.Entry(url_frame, width=50)
        self.url_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Button(url_frame, text="Ekle", command=self.add_url).pack(side=tk.LEFT)

        # URL Listesi
        self.url_listbox = tk.Listbox(main_frame, height=10)
        self.url_listbox.pack(fill=tk.BOTH, expand=True, pady="5")

        # İşlem Butonları
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady="5")

        ttk.Button(button_frame, text="İndir", command=self.download).pack(side=tk.LEFT)
        self.stop_button = ttk.Button(button_frame, text="Durdur", command=self.stop_download)
        self.stop_button.pack(side=tk.LEFT)
        ttk.Button(button_frame, text="Temizle", command=self.clear_list).pack(side=tk.LEFT)
        ttk.Button(button_frame, text="Ayarlar", command=self.open_settings).pack(side=tk.LEFT)

        # Hata Mesajı
        self.error_label = ttk.Label(main_frame, text="", foreground="red")
        self.error_label.pack()

        # İndirme işlemini durdurmak için işaretçi
        self.stop_download_flag = False

        # yt-dlp nesnesi
        self.ydl = None

    def load_settings(self):
        self.cursor.execute("SELECT key, value FROM settings")
        rows = self.cursor.fetchall()
        settings = {key: value for key, value in rows}
        return settings

    def save_settings(self, key, value):
        self.cursor.execute("REPLACE INTO settings (key, value) VALUES (?, ?)", (key, value))
        self.conn.commit()

    def add_url(self):
        url = self.url_entry.get()
        if url:
            self.url_listbox.insert(tk.END, url)
            self.url_entry.delete(0, tk.END)

    def download(self):
        if self.url_listbox.size() > 0:
            self.stop_download_flag = False
            urls = self.url_listbox.get(0, tk.END)
            threading.Thread(target=self.download_thread, args=(urls,)).start()

    def download_thread(self, urls):
        downloaded_count = 0
        self.error_label.config(text="İndirme yapılıyor, lütfen bekleyiniz...")
        for url in urls:
            if self.stop_download_flag:
                self.error_label.config(text="İndirme işlemi durduruldu.")
                break
            if downloaded_count >= self.max_downloads:
                break
            ydl_opts = {
                "format": self.audio_quality,
                "extractaudio": True,
                "audioformat": "mp3",
                "outtmpl": os.path.join(self.download_folder, f"{self.filename_format}.%(ext)s"),
            }
            try:
                self.ydl = yt_dlp.YoutubeDL(ydl_opts)
                self.ydl.download([url])
                self.url_listbox.delete(0)
                self.error_label.config(text="")
                downloaded_count += 1
            except yt_dlp.DownloadError as e:
                self.error_label.config(text=f"İndirme hatası: {e}")
                messagebox.showerror("Hata", f"İndirme sırasında bir hata oluştu: {e}")
            except Exception as e:
                self.error_label.config(text=f"Bir hata oluştu: {e}")
                messagebox.showerror("Hata", f"Beklenmeyen bir hata oluştu: {e}")
        self.error_label.config(text="İndirme tamamlandı.")

    def stop_download(self):
        self.stop_download_flag = True
        self.error_label.config(text="İndirme işlemi durduruldu.")

    def clear_list(self):
        self.url_listbox.delete(0, tk.END)

    def open_settings(self):
        settings_window = tk.Toplevel(self.root)
        settings_window.title("Ayarlar")

        # İndirme Klasörü
        ttk.Label(settings_window, text="İndirme Klasörü:").grid(row=0, column=0, padx="5", pady="5")
        folder_entry = ttk.Entry(settings_window, width=40)
        folder_entry.grid(row=0, column=1, padx="5", pady="5")
        folder_entry.insert(0, self.download_folder)

        def browse_folder():
            folder = filedialog.askdirectory()
            if folder:
                folder_entry.delete(0, tk.END)
                folder_entry.insert(0, folder)

        ttk.Button(settings_window, text="Gözat", command=browse_folder).grid(row=0, column=2, padx="5", pady="5")

        # Ses Kalitesi
        ttk.Label(settings_window, text="Ses Kalitesi:").grid(row=1, column=0, padx="5", pady="5")
        quality_combobox = ttk.Combobox(settings_window, values=["bestaudio/best", "192k", "128k", "64k"])
        quality_combobox.grid(row=1, column=1, padx="5", pady="5")
        quality_combobox.set(self.audio_quality)

        # Dosya Adı Formatı
        ttk.Label(settings_window, text="Dosya Adı Formatı:").grid(row=2, column=0, padx="5", pady="5")
        format_entry = ttk.Entry(settings_window, width=40)
        format_entry.grid(row=2, column=1, padx="5", pady="5")
        format_entry.insert(0, self.filename_format)

        # Maksimum İndirme Sayısı
        ttk.Label(settings_window, text="Maksimum İndirme:").grid(row=3, column=0, padx="5", pady="5")
        max_downloads_spinbox = ttk.Spinbox(settings_window, from_=1, to=10)
        max_downloads_spinbox.grid(row=3, column=1, padx="5", pady="5")
        max_downloads_spinbox.delete(0, tk.END)
        max_downloads_spinbox.insert(0, self.max_downloads)

        def save_settings():
            folder = folder_entry.get()
            if not os.path.isdir(folder):
                messagebox.showerror("Hata", "Geçersiz klasör seçildi.")
            else:
                self.download_folder = folder
                self.audio_quality = quality_combobox.get()
                self.filename_format = format_entry.get()
                self.max_downloads = int(max_downloads_spinbox.get())  # Tamsayıya dönüştürme
                self.save_settings("download_folder", self.download_folder)
                self.save_settings("audio_quality", self.audio_quality)
                self.save_settings("filename_format", self.filename_format)
                self.save_settings("max_downloads", self.max_downloads)
                settings_window.destroy()

        ttk.Button(settings_window, text="Kaydet", command=save_settings).grid(row=4, column=0, columnspan=3, pady="10")

if __name__ == "__main__":
    root = tk.Tk()
    app = MP3Downloader(root)
    root.mainloop()