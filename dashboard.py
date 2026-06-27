from __future__ import annotations

from datetime import date, timedelta

from ui import ctk, messagebox
from db import Database
from streak import streak_status
from tasks import TasksFrame
from notes import NotesFrame
from timer import TimerFrame
from gpa import GpaFrame

try:
    from matplotlib.figure import Figure
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
    HAS_MPL = True
except Exception:
    HAS_MPL = False


class DashboardFrame(ctk.CTkFrame):
    def __init__(self, master, app):
        super().__init__(master)
        self.app = app
        self.db: Database = app.db
        self.user_id = app.user["id"]
        self.canvas_widget = None

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        top = ctk.CTkFrame(self)
        top.grid(row=0, column=0, padx=18, pady=18, sticky="ew")
        top.grid_columnconfigure(0, weight=1)
        self.title_label = ctk.CTkLabel(top, text="Dashboard", font=("Arial", 26, "bold"))
        self.title_label.grid(row=0, column=0, padx=16, pady=(12, 6), sticky="w")
        self.welcome_label = ctk.CTkLabel(top, text="")
        self.welcome_label.grid(row=1, column=0, padx=16, pady=(0, 12), sticky="w")

        cards = ctk.CTkFrame(self)
        cards.grid(row=1, column=0, padx=18, pady=(0, 18), sticky="nsew")
        cards.grid_columnconfigure((0, 1, 2, 3), weight=1)
        cards.grid_rowconfigure((0, 1), weight=1)
        self.card_frames = {}
        labels = [
            ("total_tasks", "Total Tasks"),
            ("completed_tasks", "Completed"),
            ("pending_tasks", "Pending"),
            ("current_streak", "Study Streak"),
            ("notes_count", "Notes"),
            ("gpa", "GPA"),
            ("due_today", "Due Today"),
            ("study_minutes", "Study Minutes"),
        ]
        positions = [(0, 0), (0, 1), (0, 2), (0, 3), (1, 0), (1, 1), (1, 2), (1, 3)]
        for (key, title), (r, c) in zip(labels, positions):
            frame = ctk.CTkFrame(cards)
            frame.grid(row=r, column=c, padx=10, pady=10, sticky="nsew")
            frame.grid_columnconfigure(0, weight=1)
            ctk.CTkLabel(frame, text=title, font=("Arial", 14)).grid(row=0, column=0, padx=12, pady=(12, 4), sticky="w")
            value = ctk.CTkLabel(frame, text="0", font=("Arial", 24, "bold"))
            value.grid(row=1, column=0, padx=12, pady=(0, 12), sticky="w")
            self.card_frames[key] = value

        bottom = ctk.CTkFrame(self)
        bottom.grid(row=2, column=0, padx=18, pady=(0, 18), sticky="nsew")
        bottom.grid_columnconfigure((0, 1), weight=1)
        bottom.grid_rowconfigure(0, weight=1)

        self.summary_frame = ctk.CTkFrame(bottom)
        self.summary_frame.grid(row=0, column=0, padx=(12, 8), pady=12, sticky="nsew")
        self.summary_frame.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(self.summary_frame, text="Study Summary", font=("Arial", 18, "bold")).grid(row=0, column=0, padx=14, pady=(14, 8), sticky="w")
        self.streak_msg = ctk.CTkLabel(self.summary_frame, text="")
        self.streak_msg.grid(row=1, column=0, padx=14, pady=8, sticky="w")
        self.deadline_msg = ctk.CTkLabel(self.summary_frame, text="")
        self.deadline_msg.grid(row=2, column=0, padx=14, pady=8, sticky="w")

        self.chart_frame = ctk.CTkFrame(bottom)
        self.chart_frame.grid(row=0, column=1, padx=(8, 12), pady=12, sticky="nsew")
        self.chart_frame.grid_rowconfigure(1, weight=1)
        self.chart_frame.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(self.chart_frame, text="Productivity Snapshot", font=("Arial", 18, "bold")).grid(row=0, column=0, padx=14, pady=(14, 8), sticky="w")
        self.chart_holder = ctk.CTkFrame(self.chart_frame)
        self.chart_holder.grid(row=1, column=0, padx=12, pady=12, sticky="nsew")

        self.refresh()

    def refresh(self):
        stats = self.db.get_user_stats(self.user_id)
        self.welcome_label.configure(text=f"Welcome, {self.app.user['username']}! Here is your progress overview.")
        self.card_frames["total_tasks"].configure(text=str(stats["total_tasks"]))
        self.card_frames["completed_tasks"].configure(text=str(stats["completed_tasks"]))
        self.card_frames["pending_tasks"].configure(text=str(stats["pending_tasks"]))
        self.card_frames["current_streak"].configure(text=str(stats["current_streak"]))
        self.card_frames["notes_count"].configure(text=str(stats["notes_count"]))
        self.card_frames["gpa"].configure(text=f"{stats['gpa']:.2f}")
        self.card_frames["due_today"].configure(text=str(stats["due_today"]))
        self.card_frames["study_minutes"].configure(text=str(stats["total_study_minutes"]))

        streak_info = streak_status(stats["last_study_date"], stats["current_streak"])
        self.streak_msg.configure(text=streak_info["message"])
        if stats["due_7_days"]:
            self.deadline_msg.configure(text=f"{stats['due_7_days']} task(s) are due within the next 7 days.")
        else:
            self.deadline_msg.configure(text="No upcoming task deadlines within the next 7 days.")

        self._draw_chart(stats)

    def _draw_chart(self, stats):
        for child in self.chart_holder.winfo_children():
            child.destroy()
        if not HAS_MPL:
            ctk.CTkLabel(self.chart_holder, text="Install matplotlib to show charts.").pack(expand=True, fill="both", padx=12, pady=12)
            return

        fig = Figure(figsize=(4.8, 2.6), dpi=100)
        ax = fig.add_subplot(111)
        labels = ["Done", "Pending", "Notes", "Hours"]
        values = [stats["completed_tasks"], stats["pending_tasks"], stats["notes_count"], round(stats["total_study_minutes"] / 60, 1)]
        ax.bar(labels, values)
        ax.set_title("Activity Overview")
        ax.set_ylabel("Count / Hours")
        fig.tight_layout()
        canvas = FigureCanvasTkAgg(fig, master=self.chart_holder)
        canvas.draw()
        canvas.get_tk_widget().pack(expand=True, fill="both")
        self.canvas_widget = canvas


class MainApp(ctk.CTk):
    def __init__(self, user, on_logout):
        super().__init__()
        self.user = user
        self.on_logout = on_logout
        self.db = Database()

        ctk.set_appearance_mode("System")
        ctk.set_default_color_theme("blue")

        self.title("SmartStudy Hub")
        self.geometry("1280x780")
        self.minsize(1120, 720)

        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.sidebar = ctk.CTkFrame(self, width=230, corner_radius=0)
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_rowconfigure(7, weight=1)

        ctk.CTkLabel(self.sidebar, text="SmartStudy Hub", font=("Arial", 22, "bold")).grid(row=0, column=0, padx=18, pady=(20, 10), sticky="w")
        ctk.CTkLabel(self.sidebar, text=f"Logged in as: {self.user['username']}").grid(row=1, column=0, padx=18, pady=(0, 18), sticky="w")

        self.buttons = {}
        items = [
            ("Dashboard", "dashboard"),
            ("Tasks", "tasks"),
            ("Notes", "notes"),
            ("Pomodoro Timer", "timer"),
            ("GPA Calculator", "gpa"),
        ]
        for idx, (text, key) in enumerate(items, start=2):
            btn = ctk.CTkButton(self.sidebar, text=text, command=lambda k=key: self.show_frame(k))
            btn.grid(row=idx, column=0, padx=16, pady=8, sticky="ew")
            self.buttons[key] = btn

        ctk.CTkButton(self.sidebar, text="Logout", fg_color="#8b1e3f", command=self.logout).grid(row=8, column=0, padx=16, pady=(8, 20), sticky="ew")

        self.container = ctk.CTkFrame(self)
        self.container.grid(row=0, column=1, sticky="nsew")
        self.container.grid_rowconfigure(0, weight=1)
        self.container.grid_columnconfigure(0, weight=1)

        self.frames = {}

        self.frames["dashboard"] = DashboardFrame(self.container, self)
        self.frames["tasks"] = TasksFrame(self.container, self)
        self.frames["notes"] = NotesFrame(self.container, self)
        self.frames["timer"] = TimerFrame(self.container, self)
        self.frames["gpa"] = GpaFrame(self.container, self)

        for frame in self.frames.values():
            frame.grid(row=0, column=0, sticky="nsew")

        self.show_frame("dashboard")

    def show_frame(self, name: str):
        self.frames[name].tkraise()
        if hasattr(self.frames[name], "refresh"):
            self.frames[name].refresh()

    def refresh_dashboard(self):
        self.frames["dashboard"].refresh()

    def logout(self):
        if messagebox.askyesno("Logout", "Do you want to log out?"):
            self.destroy()
            self.on_logout()
