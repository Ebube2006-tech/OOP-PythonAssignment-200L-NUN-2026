from __future__ import annotations

from datetime import datetime

from ui import ctk, ttk, messagebox, StringVar, END
from db import Database


class TasksFrame(ctk.CTkFrame):
    def __init__(self, master, app):
        super().__init__(master)
        self.app = app
        self.db: Database = app.db
        self.user_id = app.user["id"]
        self.selected_task_id = None

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        header = ctk.CTkFrame(self)
        header.grid(row=0, column=0, padx=18, pady=18, sticky="ew")
        header.grid_columnconfigure((0, 1, 2, 3), weight=1)

        ctk.CTkLabel(header, text="Task Manager", font=("Arial", 24, "bold")).grid(row=0, column=0, padx=16, pady=10, sticky="w")
        self.search_var = StringVar()
        self.status_filter_value = StringVar(value="All")
        self.priority_filter_value = StringVar(value="All")

        search = ctk.CTkEntry(header, textvariable=self.search_var, placeholder_text="Search tasks...")
        search.grid(row=0, column=1, padx=10, pady=10, sticky="ew")
        ctk.CTkButton(header, text="Search", command=self.refresh_tasks).grid(row=0, column=2, padx=10, pady=10)
        ctk.CTkButton(header, text="Clear", command=self.clear_filters).grid(row=0, column=3, padx=10, pady=10)

        form = ctk.CTkFrame(self)
        form.grid(row=1, column=0, padx=18, pady=(0, 10), sticky="nsew")
        form.grid_columnconfigure(1, weight=1)
        form.grid_rowconfigure(5, weight=1)

        ctk.CTkLabel(form, text="Title").grid(row=0, column=0, padx=12, pady=(12, 6), sticky="w")
        self.title_entry = ctk.CTkEntry(form, placeholder_text="Task title")
        self.title_entry.grid(row=0, column=1, padx=12, pady=(12, 6), sticky="ew")

        ctk.CTkLabel(form, text="Due Date (YYYY-MM-DD)").grid(row=1, column=0, padx=12, pady=6, sticky="w")
        self.due_entry = ctk.CTkEntry(form, placeholder_text="2026-06-15")
        self.due_entry.grid(row=1, column=1, padx=12, pady=6, sticky="ew")

        ctk.CTkLabel(form, text="Priority").grid(row=2, column=0, padx=12, pady=6, sticky="w")
        self.priority_box = ctk.CTkComboBox(form, values=["Low", "Medium", "High"], width=180)
        self.priority_box.set("Medium")
        self.priority_box.grid(row=2, column=1, padx=12, pady=6, sticky="w")

        ctk.CTkLabel(form, text="Status").grid(row=3, column=0, padx=12, pady=6, sticky="w")
        self.status_box = ctk.CTkComboBox(form, values=["Pending", "In Progress", "Completed"], width=180)
        self.status_box.set("Pending")
        self.status_box.grid(row=3, column=1, padx=12, pady=6, sticky="w")

        ctk.CTkLabel(form, text="Description").grid(row=4, column=0, padx=12, pady=6, sticky="nw")
        self.desc_box = ctk.CTkTextbox(form, height=100)
        self.desc_box.grid(row=4, column=1, padx=12, pady=6, sticky="nsew")

        buttons = ctk.CTkFrame(form, fg_color="transparent")
        buttons.grid(row=5, column=0, columnspan=2, padx=12, pady=12, sticky="ew")
        buttons.grid_columnconfigure((0, 1, 2, 3), weight=1)
        ctk.CTkButton(buttons, text="Add Task", command=self.add_task).grid(row=0, column=0, padx=6, sticky="ew")
        ctk.CTkButton(buttons, text="Update Task", command=self.update_task).grid(row=0, column=1, padx=6, sticky="ew")
        ctk.CTkButton(buttons, text="Mark Completed", command=self.mark_completed).grid(row=0, column=2, padx=6, sticky="ew")
        ctk.CTkButton(buttons, text="Delete Task", command=self.delete_task).grid(row=0, column=3, padx=6, sticky="ew")

        list_frame = ctk.CTkFrame(self)
        list_frame.grid(row=2, column=0, padx=18, pady=(0, 18), sticky="nsew")
        list_frame.grid_rowconfigure(1, weight=1)
        list_frame.grid_columnconfigure(0, weight=1)

        filter_row = ctk.CTkFrame(list_frame, fg_color="transparent")
        filter_row.grid(row=0, column=0, padx=12, pady=(12, 6), sticky="ew")
        filter_row.grid_columnconfigure((1, 3, 5), weight=1)
        ctk.CTkLabel(filter_row, text="Status").grid(row=0, column=0, padx=(0, 6))
        self.status_filter_box = ctk.CTkComboBox(filter_row, values=["All", "Pending", "In Progress", "Completed"], width=160)
        self.status_filter_box.set("All")
        self.status_filter_box.grid(row=0, column=1, padx=(0, 12), sticky="w")
        ctk.CTkLabel(filter_row, text="Priority").grid(row=0, column=2, padx=(0, 6))
        self.priority_filter_box = ctk.CTkComboBox(filter_row, values=["All", "Low", "Medium", "High"], width=160)
        self.priority_filter_box.set("All")
        self.priority_filter_box.grid(row=0, column=3, padx=(0, 12), sticky="w")
        ctk.CTkButton(filter_row, text="Apply Filters", command=self.refresh_tasks).grid(row=0, column=4, padx=6)

        columns = ("id", "title", "due", "priority", "status")
        self.tree = ttk.Treeview(list_frame, columns=columns, show="headings", height=10)
        headings = {"id": "ID", "title": "Title", "due": "Due Date", "priority": "Priority", "status": "Status"}
        widths = {"id": 60, "title": 260, "due": 120, "priority": 110, "status": 120}
        for col in columns:
            self.tree.heading(col, text=headings[col])
            self.tree.column(col, width=widths[col], anchor="center")
        self.tree.grid(row=1, column=0, padx=12, pady=(6, 12), sticky="nsew")
        self.tree.bind("<<TreeviewSelect>>", self.on_select)

        self.refresh_tasks()

    def clear_filters(self):
        self.search_var.set("")
        self.status_filter_box.set("All")
        self.priority_filter_box.set("All")
        self.refresh_tasks()

    def clear_form(self):
        self.selected_task_id = None
        self.title_entry.delete(0, END)
        self.due_entry.delete(0, END)
        self.priority_box.set("Medium")
        self.status_box.set("Pending")
        self.desc_box.delete("1.0", END)
        self.tree.selection_remove(self.tree.selection())

    def refresh_tasks(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        tasks = self.db.fetch_tasks(
            self.user_id,
            search=self.search_var.get().strip(),
            status=self.status_filter_box.get(),
            priority=self.priority_filter_box.get(),
        )
        for task in tasks:
            self.tree.insert(
                "",
                END,
                values=(task["id"], task["title"], task["due_date"] or "", task["priority"], task["status"]),
            )
        if hasattr(self.app, "refresh_dashboard"):
            try:
                if hasattr(self.app, "frames"):
                    self.app.refresh_dashboard()
            except:
                pass

    def on_select(self, _event=None):
        selected = self.tree.selection()
        if not selected:
            return
        values = self.tree.item(selected[0], "values")
        self.selected_task_id = int(values[0])
        task = next((t for t in self.db.fetch_tasks(self.user_id) if t["id"] == self.selected_task_id), None)
        if not task:
            return
        self.title_entry.delete(0, END)
        self.title_entry.insert(0, task["title"])
        self.due_entry.delete(0, END)
        self.due_entry.insert(0, task["due_date"] or "")
        self.priority_box.set(task["priority"])
        self.status_box.set(task["status"])
        self.desc_box.delete("1.0", END)
        self.desc_box.insert("1.0", task["description"] or "")

    def add_task(self):
        due = self.due_entry.get().strip()
        if due:
            try:
                datetime.strptime(due, "%Y-%m-%d")
            except ValueError:
                messagebox.showerror("Invalid date", "Use YYYY-MM-DD format for the due date.")
                return
        success, msg = self.db.add_task(
            self.user_id,
            self.title_entry.get(),
            self.desc_box.get("1.0", END),
            due,
            self.priority_box.get(),
            self.status_box.get(),
        )
        if success:
            messagebox.showinfo("Success", msg)
            self.clear_form()
            self.refresh_tasks()
        else:
            messagebox.showerror("Error", msg)

    def update_task(self):
        if not self.selected_task_id:
            messagebox.showwarning("Select a task", "Choose a task from the list first.")
            return
        due = self.due_entry.get().strip()
        if due:
            try:
                datetime.strptime(due, "%Y-%m-%d")
            except ValueError:
                messagebox.showerror("Invalid date", "Use YYYY-MM-DD format for the due date.")
                return
        success, msg = self.db.update_task(
            self.selected_task_id,
            self.user_id,
            self.title_entry.get(),
            self.desc_box.get("1.0", END),
            due,
            self.priority_box.get(),
            self.status_box.get(),
        )
        if success:
            messagebox.showinfo("Updated", msg)
            self.refresh_tasks()
        else:
            messagebox.showerror("Error", msg)

    def mark_completed(self):
        if not self.selected_task_id:
            messagebox.showwarning("Select a task", "Choose a task from the list first.")
            return
        self.db.set_task_status(self.selected_task_id, self.user_id, "Completed")
        self.status_box.set("Completed")
        messagebox.showinfo("Done", "Task marked as completed.")
        self.refresh_tasks()

    def delete_task(self):
        if not self.selected_task_id:
            messagebox.showwarning("Select a task", "Choose a task from the list first.")
            return
        if not messagebox.askyesno("Delete task", "Are you sure you want to delete this task?"):
            return
        self.db.delete_task(self.selected_task_id, self.user_id)
        self.clear_form()
        self.refresh_tasks()
