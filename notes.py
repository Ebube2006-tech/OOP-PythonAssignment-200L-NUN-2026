from __future__ import annotations

from ui import ctk, ttk, messagebox, StringVar, END
from db import Database


class NotesFrame(ctk.CTkFrame):
    def __init__(self, master, app):
        super().__init__(master)
        self.app = app
        self.db: Database = app.db
        self.user_id = app.user["id"]
        self.selected_note_id = None

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        header = ctk.CTkFrame(self)
        header.grid(row=0, column=0, padx=18, pady=18, sticky="ew")
        header.grid_columnconfigure(1, weight=1)
        ctk.CTkLabel(header, text="Notes", font=("Arial", 24, "bold")).grid(row=0, column=0, padx=16, pady=12, sticky="w")
        self.search_var = StringVar()
        ctk.CTkEntry(header, textvariable=self.search_var, placeholder_text="Search notes...").grid(row=0, column=1, padx=10, pady=12, sticky="ew")
        ctk.CTkButton(header, text="Search", command=self.refresh_notes).grid(row=0, column=2, padx=10, pady=12)
        ctk.CTkButton(header, text="Clear", command=self.clear_filters).grid(row=0, column=3, padx=10, pady=12)

        body = ctk.CTkFrame(self)
        body.grid(row=1, column=0, padx=18, pady=(0, 18), sticky="nsew")
        body.grid_columnconfigure(1, weight=1)
        body.grid_rowconfigure(2, weight=1)

        left = ctk.CTkFrame(body)
        left.grid(row=0, column=0, rowspan=3, padx=(12, 8), pady=12, sticky="nsw")
        left.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(left, text="Title").grid(row=0, column=0, padx=12, pady=(12, 6), sticky="w")
        self.title_entry = ctk.CTkEntry(left, placeholder_text="Note title")
        self.title_entry.grid(row=1, column=0, padx=12, pady=6, sticky="ew")

        ctk.CTkLabel(left, text="Content").grid(row=2, column=0, padx=12, pady=6, sticky="w")
        self.content_box = ctk.CTkTextbox(left, width=320, height=220)
        self.content_box.grid(row=3, column=0, padx=12, pady=6, sticky="nsew")

        btns = ctk.CTkFrame(left, fg_color="transparent")
        btns.grid(row=4, column=0, padx=12, pady=12, sticky="ew")
        btns.grid_columnconfigure((0, 1), weight=1)
        ctk.CTkButton(btns, text="Save Note", command=self.save_note).grid(row=0, column=0, padx=6, sticky="ew")
        ctk.CTkButton(btns, text="Delete", command=self.delete_note).grid(row=0, column=1, padx=6, sticky="ew")
        ctk.CTkButton(left, text="New / Clear", command=self.clear_form).grid(row=5, column=0, padx=12, pady=(0, 12), sticky="ew")

        right = ctk.CTkFrame(body)
        right.grid(row=0, column=1, rowspan=3, padx=(8, 12), pady=12, sticky="nsew")
        right.grid_rowconfigure(1, weight=1)
        right.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(right, text="Saved Notes", font=("Arial", 18, "bold")).grid(row=0, column=0, padx=12, pady=(12, 6), sticky="w")
        self.tree = ttk.Treeview(right, columns=("id", "title", "updated"), show="headings", height=14)
        self.tree.heading("id", text="ID")
        self.tree.heading("title", text="Title")
        self.tree.heading("updated", text="Updated")
        self.tree.column("id", width=70, anchor="center")
        self.tree.column("title", width=250)
        self.tree.column("updated", width=160, anchor="center")
        self.tree.grid(row=1, column=0, padx=12, pady=6, sticky="nsew")
        self.tree.bind("<<TreeviewSelect>>", self.on_select)

        self.refresh_notes()

    def clear_filters(self):
        self.search_var.set("")
        self.refresh_notes()

    def clear_form(self):
        self.selected_note_id = None
        self.title_entry.delete(0, END)
        self.content_box.delete("1.0", END)
        self.tree.selection_remove(self.tree.selection())

    def refresh_notes(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        notes = self.db.fetch_notes(self.user_id, self.search_var.get().strip())
        for note in notes:
            self.tree.insert("", END, values=(note["id"], note["title"], note["updated_at"]))
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
        self.selected_note_id = int(values[0])
        note = next((n for n in self.db.fetch_notes(self.user_id) if n["id"] == self.selected_note_id), None)
        if not note:
            return
        self.title_entry.delete(0, END)
        self.title_entry.insert(0, note["title"])
        self.content_box.delete("1.0", END)
        self.content_box.insert("1.0", note["content"] or "")

    def save_note(self):
        title = self.title_entry.get()
        content = self.content_box.get("1.0", END)
        if self.selected_note_id:
            success, msg = self.db.update_note(self.selected_note_id, self.user_id, title, content)
        else:
            success, msg = self.db.add_note(self.user_id, title, content)
        if success:
            messagebox.showinfo("Saved", msg)
            self.clear_form()
            self.refresh_notes()
        else:
            messagebox.showerror("Error", msg)

    def delete_note(self):
        if not self.selected_note_id:
            messagebox.showwarning("Select a note", "Choose a note first.")
            return
        if not messagebox.askyesno("Delete note", "Are you sure you want to delete this note?"):
            return
        self.db.delete_note(self.selected_note_id, self.user_id)
        self.clear_form()
        self.refresh_notes()
