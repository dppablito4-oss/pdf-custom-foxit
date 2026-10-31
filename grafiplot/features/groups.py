"""Customer groups and colored document tabs."""

import tkinter as tk
from pathlib import Path
from tkinter import messagebox, simpledialog, ttk

from PIL import Image, ImageDraw, ImageFont, ImageTk


class GroupsMixin:
    def _color_group(self, group):
        """Stable colors across tabs; never depend on Python's randomized hash."""
        palette = [
            "#126e82",
            "#a23b3b",
            "#6752ac",
            "#237a57",
            "#9a5b18",
            "#a32273",
            "#3562a1",
            "#737c1d",
            "#76516e",
            "#38756d",
        ]
        group = (group or "").strip()
        if not group:
            return "#5c6069"
        import hashlib

        return palette[
            int(hashlib.sha256(group.casefold().encode("utf-8")).hexdigest()[:8], 16)
            % len(palette)
        ]

    def update_tab_colors(self):
        """Colored native tabs plus a horizontally scrollable selector for large batches."""
        if hasattr(self, "tab_scroll_frame"):
            for child in self.tab_scroll_frame.winfo_children():
                child.destroy()
            self.tab_buttons = {}
        for tabid in self.tabs.tabs():
            state = (
                self._state()
                if tabid == self.active_tab
                else self.tabs_data.get(tabid, {})
            )
            if not state:
                continue
            group = str(state.get("group_name") or state.get("client") or "").strip()
            name = Path(str(state.get("path") or "Documento")).name
            caption = (group[:15] + " · " if group else "") + name[:25]
            bg = self._color_group(group)
            width = max(125, min(305, 24 + len(caption) * 7))
            im = Image.new("RGB", (width, 28), bg)
            d = ImageDraw.Draw(im)
            try:
                font = ImageFont.truetype("arialbd.ttf", 12)
            except OSError:
                font = ImageFont.load_default()
            d.text((8, 6), caption, fill="white", font=font)
            photo = ImageTk.PhotoImage(im, master=self)
            self._tab_images[tabid] = photo
            self.tabs.tab(
                tabid, text="", image=photo, compound="center", padding=(2, 2)
            )
            if hasattr(self, "tab_scroll_frame"):
                active = tabid == self.tabs.select()
                button = tk.Button(
                    self.tab_scroll_frame,
                    text=caption[:34],
                    bg=bg,
                    fg="white",
                    activebackground="#a50e1f",
                    activeforeground="white",
                    font=("Segoe UI", 9, "bold" if active else "normal"),
                    bd=2 if active else 1,
                    relief="sunken" if active else "raised",
                    command=lambda tid=tabid: self.tabs.select(tid),
                )
                button.pack(side="left", padx=2, pady=2)
                button.bind(
                    "<Button-3>",
                    lambda event, tid=tabid: self.show_tab_group_menu(event, tid),
                )
                button.bind("<MouseWheel>", self.scroll_tab_strip)
                button.bind("<Shift-MouseWheel>", self.scroll_tab_strip)
                self.tab_buttons[tabid] = button
        if hasattr(self, "tab_scroll_frame"):
            self.tab_scroll_canvas.configure(
                scrollregion=self.tab_scroll_canvas.bbox("all")
            )
            self.after_idle(lambda: self.focus_tab_strip_item(self.tabs.select()))

    def show_tab_group_menu(self, event, tabid):
        """Context menu on the lower tab strip; only modifies the clicked file."""
        menu = tk.Menu(self, tearoff=False)
        menu.add_command(
            label="Asignar al grupo / cliente…",
            command=lambda tid=tabid: self.assign_tab_to_group(tid),
        )
        current = (
            self._state() if tabid == self.active_tab else self.tabs_data.get(tabid, {})
        )
        current_group = str(
            current.get("group_name") or current.get("client") or ""
        ).strip()
        if current_group:
            menu.add_command(
                label="Quitar de este grupo",
                command=lambda tid=tabid: self.set_tab_group(tid, ""),
            )
        groups = sorted(
            {
                str(v.get("group_name") or v.get("client") or "").strip()
                for k, v in self.tabs_data.items()
                if k != tabid
                and str(v.get("group_name") or v.get("client") or "").strip()
            },
            key=str.casefold,
        )
        if groups:
            submenu = tk.Menu(menu, tearoff=False)
            for name in groups:
                submenu.add_command(
                    label=name[:60],
                    command=lambda name=name, tid=tabid: self.set_tab_group(tid, name),
                )
            menu.add_cascade(label="Asignar a grupo existente", menu=submenu)
        try:
            menu.tk_popup(event.x_root, event.y_root)
        finally:
            menu.grab_release()

    def set_tab_group(self, tabid, group):
        if tabid not in self.tabs_data:
            return
        # Store edits made to currently selected document first.
        if tabid == self.active_tab:
            state = self._state()
            state["group_name"] = group
            state["client"] = group
            self.tabs_data[tabid] = state
            self.group_name.set(group)
            self.client.set(group)
        else:
            self.tabs_data[tabid]["group_name"] = group
            self.tabs_data[tabid]["client"] = group
        self.update_tab_colors()

    def assign_tab_to_group(self, tabid):
        if tabid not in self.tabs_data:
            return
        state = self._state() if tabid == self.active_tab else self.tabs_data[tabid]
        group = simpledialog.askstring(
            "Asignar al grupo",
            "Nombre o número del cliente para este archivo:",
            initialvalue=str(state.get("group_name") or state.get("client") or ""),
            parent=self,
        )
        if group is not None:
            self.set_tab_group(tabid, group.strip())

    def manage_groups(self):
        """Assign tabs to clients and keep submitted-job history when starting a new group."""
        dialog = tk.Toplevel(self)
        dialog.title("Grupos por cliente")
        dialog.geometry("480x290")
        dialog.transient(self)
        ttk.Label(
            dialog, text="Cliente / grupo activo", font=("Segoe UI", 13, "bold")
        ).pack(anchor="w", padx=12, pady=10)
        entry = ttk.Entry(dialog, textvariable=self.group_name)
        entry.pack(fill="x", padx=12)
        ttk.Label(
            dialog,
            text="Todas las pestañas asignadas al mismo grupo se suman en un reporte A4.",
        ).pack(anchor="w", padx=12, pady=8)

        def assign_all():
            name = self.group_name.get().strip()
            if not name:
                return messagebox.showwarning(
                    "Grupo", "Escriba un nombre o número.", parent=dialog
                )
            self.client.set(name)
            for state in self.tabs_data.values():
                state["group_name"] = name
                state["client"] = name
            self.update_tab_colors()
            dialog.destroy()

        def new_group():
            # Keep old tabs and reports; the next newly opened files will belong to the next group.
            if self.active_tab in self.tabs_data:
                self.tabs_data[self.active_tab] = self._state()
                self._skip_save_tab = self.active_tab
            self.group_name.set("")
            self.client.set("")
            self.update_tab_colors()
            dialog.destroy()
            messagebox.showinfo(
                "Nuevo cliente",
                "Escriba el siguiente cliente. Los reportes anteriores permanecen en sus pestañas.",
            )

        ttk.Button(
            dialog,
            text="ASIGNAR TODAS LAS PESTAÑAS ABIERTAS AL GRUPO",
            command=assign_all,
        ).pack(fill="x", padx=12, pady=6)
        ttk.Button(
            dialog, text="EMPEZAR NUEVO GRUPO / CLIENTE", command=new_group
        ).pack(fill="x", padx=12, pady=6)
        ttk.Label(
            dialog,
            text="Se cuentan trabajos enviados; no se verifica la salida física.",
        ).pack(padx=12, pady=6)
