import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
import requests

API = "http://127.0.0.1:8000/api"

BG = "#eef2f5"
SURFACE = "#ffffff"
TEXT = "#263746"
MUTED = "#667784"
ACCENT = "#5b7c99"
ACCENT_HOVER = "#496a87"
BORDER = "#cbd6df"
SELECT = "#c9dff0"
FONT = "Segoe UI"
FONT_SIZE = 10


class ApiError(Exception):
    pass


def api_request(method, path, **kwargs):
    try:
        response = requests.request(method, API + path, timeout=5, **kwargs)
    except requests.RequestException:
        raise ApiError("Не удалось подключиться к REST-сервису.\n\nСначала запустите сервер командой:\npy -m uvicorn backend:app --reload")
    try:
        data = response.json()
    except ValueError:
        data = {}
    if not response.ok:
        detail = data.get("detail", "Не удалось выполнить операцию.")
        raise ApiError(detail)
    return data


class GrantApplication:
    def __init__(self, root):
        self.root = root
        self.user = None
        self.root.title("Научные гранты")
        self.root.geometry("1180x720")
        self.root.minsize(980, 600)
        self.root.configure(bg=BG)
        self.root.option_add("*Font", (FONT, FONT_SIZE))
        self.style = ttk.Style()
        self.style.theme_use("clam")
        self.style.configure(".", font=(FONT, FONT_SIZE))
        self.style.configure("Treeview", rowheight=34, font=(FONT, 10),
                             background=SURFACE, fieldbackground=SURFACE,
                             foreground=TEXT, borderwidth=0)
        self.style.configure("Treeview.Heading", font=(FONT, 10, "bold"),
                             background="#E9EEF2", foreground=TEXT,
                             relief="flat", padding=(8, 10))
        self.style.map("Treeview", background=[("selected", SELECT)],
                       foreground=[("selected", TEXT)])
        self.style.configure("TEntry", padding=8)
        self.style.configure("TCombobox", padding=7)
        self.show_login()

    def clear_window(self):
        for widget in self.root.winfo_children():
            widget.destroy()

    def button(self, parent, text, command, width=None, primary=True):
        bg = ACCENT if primary else "#E8EDF1"
        fg = "white" if primary else TEXT
        active = ACCENT_HOVER if primary else "#DCE3E9"
        btn = tk.Button(parent, text=text, command=command,
                        font=(FONT, 10, "bold" if primary else "normal"),
                        bg=bg, fg=fg, activebackground=active,
                        activeforeground=fg, relief="flat", bd=0,
                        padx=17, pady=9, cursor="hand2",
                        width=width, highlightthickness=0)
        btn.bind("<Enter>", lambda e: btn.configure(bg=active))
        btn.bind("<Leave>", lambda e: btn.configure(bg=bg))
        return btn

    def label(self, parent, text, **kwargs):
        options = {"bg": kwargs.pop("bg", SURFACE), "fg": kwargs.pop("fg", TEXT),
                   "font": kwargs.pop("font", (FONT, FONT_SIZE))}
        options.update(kwargs)
        return tk.Label(parent, text=text, **options)

    def entry(self, parent, width=38, show=None):
        e = tk.Entry(parent, width=width, font=(FONT, 11), relief="solid",
                     bd=1, highlightthickness=1, highlightbackground=BORDER,
                     highlightcolor=ACCENT, insertbackground=TEXT)
        if show:
            e.configure(show=show)
        return e

    def show_login(self):
        self.clear_window()
        outer = tk.Frame(self.root, bg=BG)
        outer.place(relx=0.5, rely=0.5, anchor="center")
        card = tk.Frame(outer, bg=SURFACE, padx=48, pady=38,
                        highlightbackground=BORDER, highlightthickness=1)
        card.pack()
        self.label(card, "НАУЧНЫЕ ГРАНТЫ", bg=SURFACE,
                   font=(FONT, 22, "bold"), fg=ACCENT).pack(pady=(0, 5))
        # Subtitle intentionally omitted.
        self.label(card, "Электронная почта", bg=SURFACE, fg=TEXT).pack(anchor="w")
        email = self.entry(card, 36)
        email.pack(pady=(5, 16), ipady=4)
        self.label(card, "Пароль", bg=SURFACE).pack(anchor="w")
        password = self.entry(card, 36, "*")
        password.pack(pady=(5, 18), ipady=4)

        def login():
            try:
                self.user = api_request("POST", "/auth/login",
                                        json={"email": email.get().strip(),
                                              "password": password.get()})
                self.show_main()
            except ApiError as e:
                messagebox.showerror("Не удалось войти", str(e), parent=self.root)

        self.button(card, "Войти", login).pack(fill="x", pady=(2, 8))
        self.button(card, "Регистрация исследователя", self.show_register,
                    primary=False).pack(fill="x", pady=4)
        self.button(card, "Продолжить как гость", self.guest_login,
                    primary=False).pack(fill="x", pady=4)
        self.label(card, "Демо-доступ администратора", bg=SURFACE,
                   fg=MUTED, font=(FONT, 9, "bold")).pack(pady=(22, 2))
        self.label(card, "admin@grant.ru  ·  admin123", bg=SURFACE,
                   fg=MUTED, font=(FONT, 9)).pack()
        password.bind("<Return>", lambda event: login())

    def guest_login(self):
        self.user = {"id": None, "fio": "Гость", "role": "Гость"}
        self.show_main()

    def show_register(self):
        win = tk.Toplevel(self.root)
        win.title("Регистрация исследователя")
        win.configure(bg=BG)
        win.geometry("500x600")
        win.resizable(False, False)
        win.transient(self.root)
        win.grab_set()
        card = tk.Frame(win, bg=SURFACE, padx=30, pady=22)
        card.pack(fill="both", expand=True, padx=18, pady=18)
        self.label(card, "Регистрация", bg=SURFACE,
                   font=(FONT, 18, "bold"), fg=ACCENT).pack(anchor="w", pady=(0, 15))
        fields = [("ФИО *", "fio"), ("Специальность *", "specialty"),
                  ("Учёная степень", "degree"), ("Достижения", "achievements"),
                  ("Электронная почта *", "email"), ("Пароль *", "password")]
        entries = {}
        for title, key in fields:
            self.label(card, title, bg=SURFACE, fg=MUTED).pack(anchor="w", pady=(7, 3))
            e = self.entry(card, 48, "*" if key == "password" else None)
            e.pack(fill="x", ipady=3)
            entries[key] = e

        def save():
            payload = {k: v.get().strip() for k, v in entries.items()}
            try:
                api_request("POST", "/researchers", json=payload)
                messagebox.showinfo("Готово", "Регистрация завершена. Теперь можно войти.", parent=win)
                win.destroy()
            except ApiError as e:
                messagebox.showerror("Ошибка", str(e), parent=win)
        self.button(card, "Зарегистрироваться", save).pack(fill="x", pady=(22, 8))
        self.button(card, "Назад", win.destroy, primary=False).pack(fill="x")

    def show_main(self):
        self.clear_window()
        header = tk.Frame(self.root, bg=SURFACE, padx=24, pady=17)
        header.pack(fill="x")
        self.label(header, "Научные гранты", bg=SURFACE,
                   font=(FONT, 19, "bold"), fg=ACCENT).pack(side="left")
        self.label(header, f"{self.user['fio']}   ·   {self.user['role']}",
                   bg=SURFACE, fg=MUTED).pack(side="right")
        body = tk.Frame(self.root, bg=BG, padx=22, pady=18)
        body.pack(fill="both", expand=True)

        search = tk.Frame(body, bg=BG)
        search.pack(fill="x", pady=(0, 14))
        self.label(search, "Поиск по названию или направлению", bg=BG,
                   fg=MUTED).pack(side="left", padx=(0, 10))
        self.search_entry = self.entry(search, 36)
        self.search_entry.pack(side="left", ipady=3)
        self.button(search, "Найти", self.search_grants).pack(side="left", padx=(10, 6))
        self.button(search, "Сбросить", self.refresh_grants, primary=False).pack(side="left")

        table_frame = tk.Frame(body, bg=SURFACE, highlightbackground=BORDER, highlightthickness=1)
        table_frame.pack(fill="both", expand=True)
        columns = ("id", "name", "direction", "amount", "dates", "status")
        self.grant_tree = ttk.Treeview(table_frame, columns=columns, show="headings")
        headings = {"id": ("ID", 55), "name": ("Название гранта", 330),
                    "direction": ("Направление", 200), "amount": ("Сумма, руб.", 125),
                    "dates": ("Сроки", 190), "status": ("Активность", 115)}
        for col, (heading, width) in headings.items():
            self.grant_tree.heading(col, text=heading)
            self.grant_tree.column(col, width=width, anchor="w" if col == "name" else "center")
        scroll = ttk.Scrollbar(table_frame, orient="vertical", command=self.grant_tree.yview)
        self.grant_tree.configure(yscrollcommand=scroll.set)
        self.grant_tree.pack(side="left", fill="both", expand=True, padx=8, pady=8)
        scroll.pack(side="right", fill="y", pady=8, padx=(0, 8))
        self.grant_tree.bind("<Double-1>", lambda event: self.show_grant_details())

        actions = tk.Frame(body, bg=BG)
        actions.pack(fill="x", pady=(16, 0))
        buttons = [("Подробнее", self.show_grant_details, False)]
        if self.user["role"] == "Исследователь":
            buttons += [("Подать заявку", self.submit_application, True),
                        ("Мои заявки", self.my_applications, False),
                        ("Мой профиль", self.show_profile, False)]
        if self.user["role"] == "Администратор":
            buttons += [("Добавить грант", self.add_grant, True),
                        ("Изменить грант", self.edit_grant, False),
                        ("Заявки", self.all_applications, False),
                        ("Исследователи", self.all_researchers, False)]
        buttons += [("Выйти", self.logout, False)]
        for title, command, primary in buttons:
            self.button(actions, title, command, primary=primary).pack(side="left", padx=(0, 8))
        self.refresh_grants()

    def fetch_grants(self, query=""):
        return api_request("GET", "/grants", params={"search": query})

    def fill_grant_table(self, rows):
        for item in self.grant_tree.get_children():
            self.grant_tree.delete(item)
        for row in rows:
            status = "Активен" if row["active"] else "Неактивен"
            self.grant_tree.insert("", "end", values=(
                row["id"], row["name"], row["direction"],
                f'{row["amount"]:,.2f}'.replace(",", " "),
                f'{row["date_start"]} — {row["date_end"]}', status))

    def refresh_grants(self):
        if hasattr(self, "search_entry") and self.search_entry.winfo_exists():
            self.search_entry.delete(0, tk.END)
        try:
            self.fill_grant_table(self.fetch_grants())
        except ApiError as e:
            messagebox.showerror("Ошибка соединения", str(e), parent=self.root)

    def search_grants(self):
        try:
            self.fill_grant_table(self.fetch_grants(self.search_entry.get().strip()))
        except ApiError as e:
            messagebox.showerror("Ошибка", str(e), parent=self.root)

    def selected_grant_id(self):
        selected = self.grant_tree.selection()
        if not selected:
            messagebox.showwarning("Внимание", "Сначала выберите грант.", parent=self.root)
            return None
        return int(self.grant_tree.item(selected[0])["values"][0])

    def get_grant(self, grant_id):
        return api_request("GET", f"/grants/{grant_id}")

    def show_grant_details(self):
        grant_id = self.selected_grant_id()
        if grant_id is None:
            return
        try:
            grant = self.get_grant(grant_id)
        except ApiError as e:
            messagebox.showerror("Ошибка", str(e), parent=self.root)
            return
        win = tk.Toplevel(self.root)
        win.title("Сведения о гранте")
        win.geometry("570x440")
        win.configure(bg=BG)
        card = tk.Frame(win, bg=SURFACE, padx=25, pady=22)
        card.pack(fill="both", expand=True, padx=16, pady=16)
        self.label(card, grant["name"], bg=SURFACE, fg=ACCENT,
                   font=(FONT, 16, "bold"), wraplength=500, justify="left").pack(anchor="w", pady=(0, 12))
        labels = [("Описание", grant["description"]), ("Направление", grant["direction"]),
                  ("Сумма", f'{grant["amount"]:,.2f} руб.'.replace(",", " ")),
                  ("Дата начала", grant["date_start"]), ("Дата окончания", grant["date_end"]),
                  ("Активность", "Активен" if grant["active"] else "Неактивен")]
        for title, value in labels:
            self.label(card, title, bg=SURFACE, fg=MUTED,
                       font=(FONT, 9, "bold")).pack(anchor="w", pady=(8, 1))
            self.label(card, value or "Не указано", bg=SURFACE,
                       wraplength=500, justify="left").pack(anchor="w")

    def grant_form(self, title, grant=None):
        win = tk.Toplevel(self.root)
        win.title(title)
        win.geometry("540x640")
        win.configure(bg=BG)
        win.resizable(False, False)
        card = tk.Frame(win, bg=SURFACE, padx=30, pady=22)
        card.pack(fill="both", expand=True, padx=16, pady=16)
        self.label(card, title, bg=SURFACE, fg=ACCENT,
                   font=(FONT, 17, "bold")).pack(anchor="w", pady=(0, 10))
        fields = [("Название гранта *", "name"), ("Описание", "description"),
                  ("Направление исследования *", "direction"), ("Сумма гранта *", "amount"),
                  ("Дата начала (ГГГГ-ММ-ДД) *", "date_start"),
                  ("Дата окончания (ГГГГ-ММ-ДД) *", "date_end")]
        entries = {}
        for label, key in fields:
            self.label(card, label, bg=SURFACE, fg=MUTED).pack(anchor="w", pady=(7, 2))
            e = self.entry(card, 50)
            e.pack(fill="x", ipady=3)
            entries[key] = e
            if grant:
                e.insert(0, str(grant.get(key, "")))
        active_var = tk.BooleanVar(value=bool(grant["active"]) if grant else True)
        tk.Checkbutton(card, text="Грант активен", variable=active_var,
                       bg=SURFACE, activebackground=SURFACE, font=(FONT, 10)).pack(anchor="w", pady=12)

        def save():
            try:
                payload = {k: v.get().strip() for k, v in entries.items()}
                payload["amount"] = float(payload["amount"].replace(",", "."))
                payload["active"] = active_var.get()
                if grant:
                    api_request("PUT", f'/grants/{grant["id"]}', json=payload)
                else:
                    api_request("POST", "/grants", json=payload)
                win.destroy()
                self.refresh_grants()
            except ValueError:
                messagebox.showerror("Ошибка", "Проверьте сумму: укажите число больше нуля.", parent=win)
            except ApiError as e:
                messagebox.showerror("Ошибка", str(e), parent=win)
        self.button(card, "Сохранить", save).pack(fill="x", pady=(10, 7))
        self.button(card, "Назад", win.destroy, primary=False).pack(fill="x")

    def add_grant(self):
        self.grant_form("Добавить грант")

    def edit_grant(self):
        grant_id = self.selected_grant_id()
        if grant_id is None:
            return
        try:
            self.grant_form("Изменить грант", self.get_grant(grant_id))
        except ApiError as e:
            messagebox.showerror("Ошибка", str(e), parent=self.root)

    def submit_application(self):
        grant_id = self.selected_grant_id()
        if grant_id is None:
            return
        try:
            result = api_request("POST", "/applications",
                                 json={"researcher_id": self.user["id"], "grant_id": grant_id})
            messagebox.showinfo("Готово", result["message"], parent=self.root)
        except ApiError as e:
            messagebox.showerror("Ошибка", str(e), parent=self.root)

    def my_applications(self):
        self.application_window("Мои заявки", mine=True)

    def all_applications(self):
        self.application_window("Заявки исследователей", mine=False)

    def application_window(self, title, mine):
        win = tk.Toplevel(self.root)
        win.title(title)
        win.geometry("1000x500")
        win.configure(bg=BG)
        frame = tk.Frame(win, bg=SURFACE, highlightbackground=BORDER, highlightthickness=1)
        frame.pack(fill="both", expand=True, padx=16, pady=16)
        columns = ("id", "researcher", "grant", "status", "date")
        tree = ttk.Treeview(frame, columns=columns, show="headings")
        heads = [("id", "ID", 60), ("researcher", "Исследователь", 230),
                 ("grant", "Грант", 370), ("status", "Статус", 160),
                 ("date", "Дата подачи", 140)]
        for key, label, width in heads:
            tree.heading(key, text=label)
            tree.column(key, width=width, anchor="center")
        tree.pack(fill="both", expand=True, padx=8, pady=8)

        def reload_rows():
            for item in tree.get_children():
                tree.delete(item)
            params = {"researcher_id": self.user["id"]} if mine else {}
            rows = api_request("GET", "/applications", params=params)
            for row in rows:
                tree.insert("", "end", values=(row["id"], row["researcher"],
                    row["grant"], row["status"], row["date"]))
        try:
            reload_rows()
        except ApiError as e:
            messagebox.showerror("Ошибка", str(e), parent=win)
        if not mine:
            controls = tk.Frame(win, bg=BG)
            controls.pack(pady=(0, 16))
            def decide(status):
                selected = tree.selection()
                if not selected:
                    messagebox.showwarning("Внимание", "Выберите заявку.", parent=win)
                    return
                app_id = tree.item(selected[0])["values"][0]
                try:
                    api_request("PUT", f"/applications/{app_id}/status",
                                params={"status": status})
                    reload_rows()
                except ApiError as e:
                    messagebox.showerror("Ошибка", str(e), parent=win)
            self.button(controls, "Одобрить", lambda: decide("Одобрена")).pack(side="left", padx=5)
            self.button(controls, "Отклонить", lambda: decide("Отклонена"), primary=False).pack(side="left", padx=5)

    def all_researchers(self):
        win = tk.Toplevel(self.root)
        win.title("Исследователи")
        win.geometry("980x460")
        win.configure(bg=BG)
        frame = tk.Frame(win, bg=SURFACE, highlightbackground=BORDER, highlightthickness=1)
        frame.pack(fill="both", expand=True, padx=16, pady=16)
        columns = ("fio", "specialty", "degree", "achievements", "email")
        tree = ttk.Treeview(frame, columns=columns, show="headings")
        heads = [("fio", "ФИО", 190), ("specialty", "Специальность", 170),
                 ("degree", "Учёная степень", 140), ("achievements", "Достижения", 240),
                 ("email", "Электронная почта", 190)]
        for key, label, width in heads:
            tree.heading(key, text=label)
            tree.column(key, width=width, anchor="center")
        tree.pack(fill="both", expand=True, padx=8, pady=8)
        try:
            for row in api_request("GET", "/researchers"):
                tree.insert("", "end", values=(row["fio"], row["specialty"],
                    row["degree"], row["achievements"], row["email"]))
        except ApiError as e:
            messagebox.showerror("Ошибка", str(e), parent=win)

    def show_profile(self):
        win = tk.Toplevel(self.root)
        win.title("Мой профиль")
        win.geometry("520x490")
        win.configure(bg=BG)
        card = tk.Frame(win, bg=SURFACE, padx=30, pady=22)
        card.pack(fill="both", expand=True, padx=16, pady=16)
        self.label(card, "Мой профиль", bg=SURFACE, fg=ACCENT,
                   font=(FONT, 17, "bold")).pack(anchor="w", pady=(0, 12))
        fields = [("ФИО", "fio"), ("Специальность", "specialty"),
                  ("Учёная степень", "degree"), ("Достижения", "achievements")]
        entries = {}
        for label, key in fields:
            self.label(card, label, bg=SURFACE, fg=MUTED).pack(anchor="w", pady=(8, 2))
            e = self.entry(card, 48)
            e.pack(fill="x", ipady=3)
            e.insert(0, self.user.get(key, "") or "")
            entries[key] = e
        self.label(card, "Электронная почта: " + self.user["email"],
                   bg=SURFACE, fg=MUTED).pack(anchor="w", pady=12)

        def save():
            payload = {k: v.get().strip() for k, v in entries.items()}
            try:
                updated = api_request("PUT", f'/researchers/{self.user["id"]}/profile',
                                      json=payload)
                self.user.update(updated)
                win.destroy()
                self.show_main()
            except ApiError as e:
                messagebox.showerror("Ошибка", str(e), parent=win)
        self.button(card, "Сохранить изменения", save).pack(fill="x", pady=(5, 7))
        self.button(card, "Закрыть", win.destroy, primary=False).pack(fill="x")

    def logout(self):
        self.user = None
        self.show_login()


def main():
    root = tk.Tk()
    GrantApplication(root)
    root.mainloop()


if __name__ == "__main__":
    main()
