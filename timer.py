from __future__ import annotations

from ui import ctk, messagebox, END
from db import Database


class TimerFrame(ctk.CTkFrame):
    def __init__(self, master, app):
        super().__init__(master)
        self.app = app
        self.db: Database = app.db
        self.user_id = app.user["id"]

        self.running = False
        self.timer_job = None
        self.mode = "study"
        self.remaining_seconds = 25 * 60

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        top = ctk.CTkFrame(self)
        top.grid(row=0, column=0, padx=18, pady=18, sticky="ew")
        top.grid_columnconfigure((0, 1, 2), weight=1)
        ctk.CTkLabel(top, text="Pomodoro Timer", font=("Arial", 24, "bold")).grid(row=0, column=0, padx=16, pady=12, sticky="w")
        self.mode_label = ctk.CTkLabel(top, text="Study Session")
        self.mode_label.grid(row=0, column=1, padx=10, pady=12)
        self.status_label = ctk.CTkLabel(top, text="Ready")
        self.status_label.grid(row=0, column=2, padx=16, pady=12, sticky="e")

        body = ctk.CTkFrame(self)
        body.grid(row=1, column=0, padx=18, pady=(0, 18), sticky="nsew")
        body.grid_columnconfigure((0, 1), weight=1)
        body.grid_rowconfigure(0, weight=1)

        left = ctk.CTkFrame(body)
        left.grid(row=0, column=0, padx=(12, 8), pady=12, sticky="nsew")
        left.grid_columnconfigure(0, weight=1)

        self.time_label = ctk.CTkLabel(left, text=self.format_time(self.remaining_seconds), font=("Arial", 44, "bold"))
        self.time_label.grid(row=0, column=0, padx=12, pady=(30, 20), sticky="ew")

        controls = ctk.CTkFrame(left, fg_color="transparent")
        controls.grid(row=1, column=0, padx=12, pady=12, sticky="ew")
        controls.grid_columnconfigure((0, 1, 2), weight=1)
        ctk.CTkButton(controls, text="Start", command=self.start_timer).grid(row=0, column=0, padx=6, sticky="ew")
        ctk.CTkButton(controls, text="Pause", command=self.pause_timer).grid(row=0, column=1, padx=6, sticky="ew")
        ctk.CTkButton(controls, text="Reset", command=self.reset_timer).grid(row=0, column=2, padx=6, sticky="ew")

        settings = ctk.CTkFrame(left)
        settings.grid(row=2, column=0, padx=12, pady=(10, 18), sticky="ew")
        settings.grid_columnconfigure(1, weight=1)
        ctk.CTkLabel(settings, text="Study minutes").grid(row=0, column=0, padx=12, pady=(12, 6), sticky="w")
        self.study_minutes_entry = ctk.CTkEntry(settings)
        self.study_minutes_entry.insert(0, "25")
        self.study_minutes_entry.grid(row=0, column=1, padx=12, pady=(12, 6), sticky="ew")
        ctk.CTkLabel(settings, text="Break minutes").grid(row=1, column=0, padx=12, pady=6, sticky="w")
        self.break_minutes_entry = ctk.CTkEntry(settings)
        self.break_minutes_entry.insert(0, "5")
        self.break_minutes_entry.grid(row=1, column=1, padx=12, pady=6, sticky="ew")
        ctk.CTkButton(settings, text="Apply Settings", command=self.apply_settings).grid(row=2, column=0, columnspan=2, padx=12, pady=(6, 12), sticky="ew")

        right = ctk.CTkFrame(body)
        right.grid(row=0, column=1, padx=(8, 12), pady=12, sticky="nsew")
        right.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(right, text="How it works", font=("Arial", 18, "bold")).grid(row=0, column=0, padx=16, pady=(16, 8), sticky="w")
        info = (
            "1. Start a 25-minute study block.\n"
            "2. When the timer finishes, the app saves a study session.\n"
            "3. A short 5-minute break starts automatically.\n"
            "4. Your study streak and dashboard stats update after each session."
        )
        ctk.CTkLabel(right, text=info, justify="left", wraplength=320).grid(row=1, column=0, padx=16, pady=12, sticky="nw")
        self.summary_label = ctk.CTkLabel(right, text="")
        self.summary_label.grid(row=2, column=0, padx=16, pady=(10, 16), sticky="w")

        self.refresh_summary()

    def apply_settings(self):
        try:
            study = int(self.study_minutes_entry.get())
            brk = int(self.break_minutes_entry.get())
            if study <= 0 or brk <= 0:
                raise ValueError
        except ValueError:
            messagebox.showerror("Invalid input", "Enter positive whole numbers for the timer settings.")
            return
        self.study_minutes = study
        self.break_minutes = brk
        if not self.running:
            self.mode = "study"
            self.remaining_seconds = self.study_minutes * 60
            self.update_labels()
        messagebox.showinfo("Saved", "Timer settings updated.")

    @property
    def study_minutes(self):
        try:
            return int(self.study_minutes_entry.get())
        except Exception:
            return 25

    @study_minutes.setter
    def study_minutes(self, value):
        self.study_minutes_entry.delete(0, END)
        self.study_minutes_entry.insert(0, str(value))

    @property
    def break_minutes(self):
        try:
            return int(self.break_minutes_entry.get())
        except Exception:
            return 5

    @break_minutes.setter
    def break_minutes(self, value):
        self.break_minutes_entry.delete(0, END)
        self.break_minutes_entry.insert(0, str(value))

    def refresh_summary(self):
        summary = self.db.get_study_summary(self.user_id)
        self.summary_label.configure(
            text=f"Total study time: {summary['total_minutes']} min\nCurrent streak: {summary['current_streak']} day(s)"
        )
        if hasattr(self.app, "refresh_dashboard"):
            self.app.refresh_dashboard()

    def format_time(self, seconds: int) -> str:
        minutes, secs = divmod(max(0, seconds), 60)
        return f"{minutes:02d}:{secs:02d}"

    def update_labels(self):
        self.time_label.configure(text=self.format_time(self.remaining_seconds))
        self.mode_label.configure(text="Study Session" if self.mode == "study" else "Break Session")

    def start_timer(self):
        if self.running:
            return
        self.running = True
        self.status_label.configure(text="Running")
        self.tick()

    def pause_timer(self):
        self.running = False
        self.status_label.configure(text="Paused")
        if self.timer_job:
            self.after_cancel(self.timer_job)
            self.timer_job = None

    def reset_timer(self):
        self.pause_timer()
        self.mode = "study"
        self.remaining_seconds = self.study_minutes * 60
        self.update_labels()
        self.status_label.configure(text="Ready")

    def tick(self):
        if not self.running:
            return
        self.update_labels()
        if self.remaining_seconds <= 0:
            self.on_session_end()
            return
        self.remaining_seconds -= 1
        if self.winfo_exists():
            self.timer_job = self.after(1000, self.tick)

    def on_session_end(self):
        if self.mode == "study":
            self.db.log_study_session(self.user_id, self.study_minutes, "Pomodoro")
            self.refresh_summary()
            messagebox.showinfo("Great job", "Study session completed. A break will start now.")
            self.mode = "break"
            self.remaining_seconds = self.break_minutes * 60
            self.status_label.configure(text="Break started")
            self.update_labels()
            self.timer_job = self.after(1000, self.tick)
        else:
            self.status_label.configure(text="Break finished")
            messagebox.showinfo("Break over", "Your break is done. Start another study session when ready.")
            self.reset_timer()
