from __future__ import annotations

from ui import ctk, ttk, messagebox, END
from db import Database, GRADE_POINTS


class GpaFrame(ctk.CTkFrame):
    def __init__(self, master, app):
        super().__init__(master)
        self.app = app
        self.db: Database = app.db
        self.user_id = app.user["id"]
        self.selected_record_id = None

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        top = ctk.CTkFrame(self)
        top.grid(row=0, column=0, padx=18, pady=18, sticky="ew")
        top.grid_columnconfigure((0, 1, 2, 3), weight=1)
        ctk.CTkLabel(top, text="GPA Calculator", font=("Arial", 24, "bold")).grid(row=0, column=0, padx=16, pady=12, sticky="w")
        self.total_label = ctk.CTkLabel(top, text="Total Credits: 0 | GPA: 0.00")
        self.total_label.grid(row=0, column=3, padx=16, pady=12, sticky="e")

        body = ctk.CTkFrame(self)
        body.grid(row=1, column=0, padx=18, pady=(0, 18), sticky="nsew")
        body.grid_columnconfigure(1, weight=1)
        body.grid_rowconfigure(0, weight=1)

        form = ctk.CTkFrame(body)
        form.grid(row=0, column=0, padx=(12, 8), pady=12, sticky="nsw")
        form.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(form, text="Course Name").grid(row=0, column=0, padx=12, pady=(12, 6), sticky="w")
        self.course_entry = ctk.CTkEntry(form, placeholder_text="e.g. CPE 102")
        self.course_entry.grid(row=1, column=0, padx=12, pady=6, sticky="ew")

        ctk.CTkLabel(form, text="Credit Units").grid(row=2, column=0, padx=12, pady=6, sticky="w")
        self.credit_entry = ctk.CTkEntry(form, placeholder_text="e.g. 3")
        self.credit_entry.grid(row=3, column=0, padx=12, pady=6, sticky="ew")

        ctk.CTkLabel(form, text="Grade").grid(row=4, column=0, padx=12, pady=6, sticky="w")
        self.grade_box = ctk.CTkComboBox(form, values=list(GRADE_POINTS.keys()))
        self.grade_box.set("A")
        self.grade_box.grid(row=5, column=0, padx=12, pady=6, sticky="ew")

        btns = ctk.CTkFrame(form, fg_color="transparent")
        btns.grid(row=6, column=0, padx=12, pady=12, sticky="ew")
        btns.grid_columnconfigure((0, 1), weight=1)
        ctk.CTkButton(btns, text="Add Course", command=self.add_record).grid(row=0, column=0, padx=6, sticky="ew")
        ctk.CTkButton(btns, text="Delete", command=self.delete_record).grid(row=0, column=1, padx=6, sticky="ew")
        ctk.CTkButton(form, text="Clear Fields", command=self.clear_form).grid(row=7, column=0, padx=12, pady=(0, 12), sticky="ew")

        list_frame = ctk.CTkFrame(body)
        list_frame.grid(row=0, column=1, padx=(8, 12), pady=12, sticky="nsew")
        list_frame.grid_rowconfigure(1, weight=1)
        list_frame.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(list_frame, text="Saved Courses", font=("Arial", 18, "bold")).grid(row=0, column=0, padx=12, pady=(12, 6), sticky="w")

        self.tree = ttk.Treeview(list_frame, columns=("id", "course", "credit", "grade", "points"), show="headings", height=14)
        for col, title, width in [
            ("id", "ID", 60),
            ("course", "Course", 180),
            ("credit", "Credits", 90),
            ("grade", "Grade", 90),
            ("points", "Points", 110),
        ]:
            self.tree.heading(col, text=title)
            self.tree.column(col, width=width, anchor="center")
        self.tree.grid(row=1, column=0, padx=12, pady=6, sticky="nsew")
        self.tree.bind("<<TreeviewSelect>>", self.on_select)

        self.refresh_records()

    def clear_form(self):
        self.selected_record_id = None
        self.course_entry.delete(0, END)
        self.credit_entry.delete(0, END)
        self.grade_box.set("A")
        self.tree.selection_remove(self.tree.selection())

    def refresh_records(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        records = self.db.fetch_gpa_records(self.user_id)
        for record in records:
            self.tree.insert(
                "",
                END,
                values=(record["id"], record["course_name"], record["credit_units"], record["grade"], record["total_points"]),
            )
        gpa, credits, _ = self.db.calculate_gpa(self.user_id)
        self.total_label.configure(text=f"Total Credits: {credits:.1f} | GPA: {gpa:.2f}")
        if hasattr(self.app, "refresh_dashboard"):
            self.app.refresh_dashboard()

    def on_select(self, _event=None):
        selected = self.tree.selection()
        if not selected:
            return
        values = self.tree.item(selected[0], "values")
        self.selected_record_id = int(values[0])
        self.course_entry.delete(0, END)
        self.course_entry.insert(0, values[1])
        self.credit_entry.delete(0, END)
        self.credit_entry.insert(0, values[2])
        self.grade_box.set(values[3])

    def add_record(self):
        success, msg = self.db.add_gpa_record(
            self.user_id,
            self.course_entry.get(),
            self.credit_entry.get(),
            self.grade_box.get(),
        )
        if success:
            messagebox.showinfo("Saved", msg)
            self.clear_form()
            self.refresh_records()
        else:
            messagebox.showerror("Error", msg)

    def delete_record(self):
        if not self.selected_record_id:
            messagebox.showwarning("Select a course", "Choose a course first.")
            return
        if not messagebox.askyesno("Delete course", "Delete this GPA record?"):
            return
        self.db.delete_gpa_record(self.selected_record_id, self.user_id)
        self.clear_form()
        self.refresh_records()
