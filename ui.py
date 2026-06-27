from __future__ import annotations

try:
    import customtkinter as ctk  # type: ignore
    from tkinter import ttk, messagebox, StringVar, IntVar, END
    USING_CUSTOMTK = True
except ImportError:
    import tkinter as tk
    from tkinter import ttk, messagebox, StringVar, IntVar, END
    USING_CUSTOMTK = False

    class _NoOp:
        def __getattr__(self, name):
            def _method(*args, **kwargs):
                return None
            return _method

    def _strip_ctk_kwargs(kwargs):
        ignore = {
            "fg_color", "corner_radius", "border_width", "border_color", "hover_color",
            "placeholder_text", "state", "text_color", "text_color_disabled",
            "width", "height", "orientation", "justify", "command",
        }
        return {k: v for k, v in kwargs.items() if k not in ignore}

    class CTk(tk.Tk):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **_strip_ctk_kwargs(kwargs))

    class CTkFrame(tk.Frame):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **_strip_ctk_kwargs(kwargs))

    class CTkLabel(tk.Label):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **_strip_ctk_kwargs(kwargs))

    class CTkButton(tk.Button):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **_strip_ctk_kwargs(kwargs))

    class CTkEntry(tk.Entry):
        def __init__(self, *args, **kwargs):
            kwargs.pop("placeholder_text", None)
            super().__init__(*args, **_strip_ctk_kwargs(kwargs))

    class CTkTextbox(tk.Text):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **_strip_ctk_kwargs(kwargs))

    class CTkScrollbar(tk.Scrollbar):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **_strip_ctk_kwargs(kwargs))

    class CTkComboBox(ttk.Combobox):
        def __init__(self, *args, **kwargs):
            kwargs.pop("placeholder_text", None)
            kwargs.pop("fg_color", None)
            kwargs.pop("button_color", None)
            kwargs.pop("button_hover_color", None)
            kwargs.pop("dropdown_fg_color", None)
            kwargs.pop("dropdown_hover_color", None)
            kwargs.pop("border_color", None)
            kwargs.pop("text_color", None)
            kwargs.pop("state", None)
            kwargs.pop("corner_radius", None)
            kwargs.pop("width", None)
            super().__init__(*args, **kwargs)

    class CTkTabview(tk.Frame):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **_strip_ctk_kwargs(kwargs))

    def set_appearance_mode(*args, **kwargs):
        return None

    def set_default_color_theme(*args, **kwargs):
        return None

    ctk = _NoOp()
    ctk.CTk = CTk
    ctk.CTkFrame = CTkFrame
    ctk.CTkLabel = CTkLabel
    ctk.CTkButton = CTkButton
    ctk.CTkEntry = CTkEntry
    ctk.CTkTextbox = CTkTextbox
    ctk.CTkScrollbar = CTkScrollbar
    ctk.CTkComboBox = CTkComboBox
    ctk.CTkTabview = CTkTabview
    ctk.set_appearance_mode = set_appearance_mode
    ctk.set_default_color_theme = set_default_color_theme

__all__ = [
    "ctk",
    "ttk",
    "messagebox",
    "StringVar",
    "IntVar",
    "END",
    "USING_CUSTOMTK",
]
