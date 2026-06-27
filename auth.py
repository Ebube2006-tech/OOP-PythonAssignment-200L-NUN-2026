from __future__ import annotations

from ui import ctk, messagebox
from db import Database


class AuthWindow(ctk.CTk):
    def __init__(self, on_success):
        super().__init__()
        self.on_success = on_success
        self.db = Database()

        ctk.set_appearance_mode("System")
        ctk.set_default_color_theme("blue")

        self.title("SmartStudy Hub - Login")
        self.geometry("880x560")
        self.minsize(860, 540)

        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, weight=1)
        self.rowconfigure(0, weight=1)

        left = ctk.CTkFrame(self, corner_radius=0)
        left.grid(row=0, column=0, sticky="nsew")
        left.grid_rowconfigure(0, weight=1)
        left.grid_columnconfigure(0, weight=1)

        right = ctk.CTkFrame(self, corner_radius=24)
        right.grid(row=0, column=1, padx=24, pady=24, sticky="nsew")
        right.grid_columnconfigure(0, weight=1)

        title = ctk.CTkLabel(left, text="SmartStudy Hub", font=("Arial", 34, "bold"))
        title.grid(row=0, column=0, padx=40, pady=(50, 10), sticky="w")

        subtitle = ctk.CTkLabel(
            left,
            text="A student productivity desktop app for tasks, notes, GPA, and study tracking.",
            wraplength=320,
            justify="left",
            font=("Arial", 16),
        )
        subtitle.grid(row=1, column=0, padx=40, sticky="w")

        bullets = ctk.CTkLabel(
            left,
            text="• Task manager\n• Pomodoro timer\n• GPA calculator\n• Notes and study streaks",
            justify="left",
            font=("Arial", 15),
        )
        bullets.grid(row=2, column=0, padx=40, pady=20, sticky="w")

        self.mode = "login"

        self.switch_frame = ctk.CTkFrame(right, fg_color="transparent")
        self.switch_frame.grid(row=0, column=0, padx=24, pady=(20, 10), sticky="ew")
        self.switch_frame.grid_columnconfigure((0, 1), weight=1)

        ctk.CTkButton(self.switch_frame, text="Login", command=self.show_login).grid(row=0, column=0, padx=(0, 6), sticky="ew")
        ctk.CTkButton(self.switch_frame, text="Register", command=self.show_register).grid(row=0, column=1, padx=(6, 0), sticky="ew")

        self.form = ctk.CTkFrame(right, corner_radius=18)
        self.form.grid(row=1, column=0, padx=24, pady=18, sticky="nsew")
        self.form.grid_columnconfigure(0, weight=1)

        self.form_title = ctk.CTkLabel(self.form, text="Login", font=("Arial", 24, "bold"))
        self.form_title.grid(row=0, column=0, padx=20, pady=(22, 14), sticky="w")

        self.username_entry = ctk.CTkEntry(self.form, placeholder_text="Username")
        self.username_entry.grid(row=1, column=0, padx=20, pady=10, sticky="ew")

        self.password_entry = ctk.CTkEntry(self.form, placeholder_text="Password", show="*")
        self.password_entry.grid(row=2, column=0, padx=20, pady=10, sticky="ew")

        self.confirm_entry = ctk.CTkEntry(self.form, placeholder_text="Confirm password", show="*")
        self.confirm_entry.grid(row=3, column=0, padx=20, pady=10, sticky="ew")

        self.action_button = ctk.CTkButton(self.form, text="Login", command=self.submit)
        self.action_button.grid(row=4, column=0, padx=20, pady=(14, 8), sticky="ew")

        self.hint = ctk.CTkLabel(self.form, text="Create an account first if you are new.", wraplength=260)
        self.hint.grid(row=5, column=0, padx=20, pady=(6, 20), sticky="w")

        self.show_login()

    def show_login(self):
        self.mode = "login"
        self.form_title.configure(text="Login")
        self.action_button.configure(text="Login")
        self.confirm_entry.grid_remove()
        self.hint.configure(text="Enter your username and password to continue.")

    def show_register(self):
        self.mode = "register"
        self.form_title.configure(text="Register")
        self.action_button.configure(text="Create Account")
        self.confirm_entry.grid()
        self.hint.configure(text="Choose a username and password to create a new account.")

    def submit(self):
        username = self.username_entry.get().strip()
        password = self.password_entry.get().strip()
        if not username or not password:
            messagebox.showerror("Missing data", "Please fill in the username and password.")
            return

        if self.mode == "register":
            confirm = self.confirm_entry.get().strip()
            if password != confirm:
                messagebox.showerror("Password mismatch", "Passwords do not match.")
                return
            success, msg = self.db.create_user(username, password)
            if success:
                messagebox.showinfo("Success", msg)
                self.show_login()
                self.password_entry.delete(0, "end")
                self.confirm_entry.delete(0, "end")
            else:
                messagebox.showerror("Error", msg)
            return

        user = self.db.authenticate_user(username, password)
        if not user:
            messagebox.showerror("Login failed", "Invalid username or password.")
            return
        messagebox.showinfo("Welcome", f"Welcome back, {username}!")
        self.destroy()
        self.on_success(user)
