import tkinter as tk
from tkinter import messagebox, simpledialog, ttk
import os
import shutil
import datetime
import xlsxwriter
import sqlite3
import sys
import pandas as pd


# Add this helper function at the top of main.py
def resource_path(relative_path):
    """Get absolute path to resource, works for dev and for PyInstaller"""
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)


# Then, update your db_handler import and all other code as it was.
from db_handler import (
    init_db,
    get_connection,
    validate_admin,
    validate_operator,
    insert_model,
    get_all_models,
    insert_entry,
    search_entry_by_pcbid,
    get_all_reworks_by_pcbid,
    insert_rework,
    add_operator,
    list_all_operators,
    fetch_with_rework,
    fetch_before_rework,
    delete_entry_by_pcb_id,
    get_rework_log_by_pcbid,
    get_conn_and_cursor,
    fetch_all_entries,
)


# Run this ONCE at startup
init_db()
current_user = None


# ---------- Centering Function ----------
def center_window(win, width=600, height=500):
    win.update_idletasks()
    screen_width = win.winfo_screenwidth()
    screen_height = win.winfo_screenheight()
    x = (screen_width // 2) - (width // 2)
    y = (screen_height // 2) - (height // 2)
    win.geometry(f"{width}x{height}+{x}+{y}")


# ---------- Login Windows ----------
def show_login_window():
    login = tk.Tk()
    login.title("Admin Login")
    center_window(login, 600, 500)

    # Username field
    tk.Label(login, text="Admin Username:").pack(pady=(30, 5))
    username_entry = tk.Entry(login)
    username_entry.pack()
    username_entry.focus_set()

    # Password field
    tk.Label(login, text="Password:").pack(pady=5)
    password_entry = tk.Entry(login, show="*")
    password_entry.pack()

    def try_login(event=None):
        global current_user
        if validate_admin(username_entry.get(), password_entry.get()):
            current_user = "admin"
            login.destroy()
            open_admin_dashboard()
        else:
            messagebox.showerror("Login Failed", "Invalid admin credentials")
            username_entry.delete(0, tk.END)
            password_entry.delete(0, tk.END)
            username_entry.focus_set()

    tk.Button(login, text="Login", command=try_login).pack(pady=20)
    login.bind("<Return>", try_login)
    login.lift()
    login.attributes("-topmost", True)
    login.after(100, lambda: login.attributes("-topmost", False))
    login.focus_force()
    login.mainloop()


def login_operator(parent_win):
    login_win = tk.Toplevel()
    login_win.title("Operator Login")
    center_window(login_win, 600, 400)

    tk.Label(login_win, text="Operator Username:").pack(pady=(30, 5))
    username_entry = tk.Entry(login_win)
    username_entry.pack()
    login_win.grab_set()
    username_entry.focus_set()

    tk.Label(login_win, text="Password:").pack(pady=5)
    password_entry = tk.Entry(login_win, show="*")
    password_entry.pack()

    def try_login(event=None):
        username = username_entry.get().strip()
        password = password_entry.get().strip()
        global current_user

        if validate_operator(username, password):
            current_user = username
            login_win.destroy()
            parent_win.destroy()
            open_admin_dashboard()
        else:
            messagebox.showerror("Login Failed", "Invalid credentials")
            username_entry.delete(0, tk.END)
            password_entry.delete(0, tk.END)
            username_entry.focus_set()

    tk.Button(login_win, text="Login", command=try_login).pack(pady=20)
    login_win.bind("<Return>", try_login)
    login_win.wait_window()


# ---------- Admin Dashboard ----------
def open_admin_dashboard():
    admin_win = tk.Tk()
    admin_win.title("Dashboard")
    center_window(admin_win, 600, 500)

    # Welcome Message
    tk.Label(admin_win, text=f"Hi, {current_user}!", font=("Arial", 14)).pack(pady=10)

    if current_user == "admin":
        tk.Button(
            admin_win, text="📦 Add New Model", width=25, command=add_new_model
        ).pack(pady=10)
    tk.Button(admin_win, text="📝 Add New Entry", width=25, command=add_new_entry).pack(
        pady=10
    )
    tk.Button(admin_win, text="📄 View Entries", width=25, command=view_entries).pack(
        pady=10
    )

    tk.Button(admin_win, text="➕ Do Rework", width=25, command=do_rework).pack(pady=10)

    tk.Button(
        admin_win,
        text="🔍 View Rework Logs",
        width=25,
        command=lambda: view_rework_logs(admin_win),
    ).pack(pady=10)

    if current_user == "admin":
        tk.Button(
            admin_win, text="👤 Add New Operator", width=25, command=db_add_operator
        ).pack(pady=10)
        tk.Button(
            admin_win, text="📋 View Operator List", width=25, command=view_operators
        ).pack(pady=10)
        # Add the new button here
        tk.Button(
            admin_win,
            text="🚨 Clear All Data",
            width=25,
            fg="red",
            command=clear_all_data,
        ).pack(pady=10)

    tk.Button(
        admin_win,
        text="🚪 Logout",
        width=25,
        fg="red",
        command=lambda: logout(admin_win),
    ).pack(pady=20)
    admin_win.mainloop()


def view_entries():
    entries_win = tk.Toplevel()
    entries_win.title("All Entries")
    center_window(entries_win, 800, 500)
    entries_win.grab_set()

    tk.Button(
        entries_win,
        text="← Back",
        command=entries_win.destroy,
        relief="flat",
        fg="blue",
        cursor="hand2",
    ).pack(anchor="nw", padx=10, pady=10)
    # ---- Title Label ----
    title_label = tk.Label(
        entries_win, text="PCB Entries Data", font=("Helvetica", 16, "bold")
    )
    title_label.pack(pady=10)

    columns = (
        "Sr No",
        "PCB ID",
        "Model",
        "Date Added",
        "Rejection Stage",
        "Rejection Details",
    )
    tree = ttk.Treeview(entries_win, columns=columns, show="headings", height=15)

    for col in columns:
        tree.heading(col, text=col)
        tree.column(col, width=130, anchor="center")
    tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

    # Add scrollbar
    scrollbar = ttk.Scrollbar(entries_win, orient="vertical", command=tree.yview)
    tree.configure(yscroll=scrollbar.set)
    scrollbar.pack(side="right", fill="y")

    try:
        conn, cursor = get_conn_and_cursor()
        if conn and cursor:
            cursor.execute(
                """
                SELECT sr_no, pcb_id, model, timestamp, 
                       COALESCE(rejection_stage, ''), 
                       COALESCE(rejection_details, '') 
                FROM entries
            """
            )
            rows = cursor.fetchall()
            conn.close()

            for row in rows:
                tree.insert("", "end", values=row)
    except Exception as e:
        messagebox.showerror("Database Error", f"Could not fetch entries:\n{e}")


def logout(admin_win):
    if messagebox.askyesno("Confirm Logout", "Are you sure you want to logout?"):
        admin_win.destroy()
        start_selection_window()


def clear_all_data():
    """Clears all data from the entries and rework_log tables."""
    admin_pass = ask_admin_password()
    if not admin_pass:
        return

    if messagebox.askyesno(
        "Confirm Data Deletion",
        "Are you sure you want to delete ALL testing data from the database? This action is irreversible.",
    ):
        try:
            conn, cursor = get_conn_and_cursor()
            if conn and cursor:
                cursor.execute("DELETE FROM entries")
                cursor.execute("DELETE FROM rework_log")
                cursor.execute("DELETE FROM Models")
                conn.commit()
                messagebox.showinfo(
                    "Success",
                    "All testing data has been cleared from the database & Models.",
                )
        except Exception as e:
            messagebox.showerror("Error", f"Failed to clear data: {e}")
        finally:
            if conn:
                conn.close()


def add_new_model():
    model_win = tk.Toplevel()
    model_win.title("Add New Model")
    center_window(model_win, 300, 150)
    model_win.resizable(False, False)

    tk.Label(model_win, text="Enter New Model Name:").pack(pady=10)
    entry_model = tk.Entry(model_win, width=30)
    entry_model.pack()
    model_win.after(100, lambda: entry_model.focus_set())

    def submit_model(event=None):
        model_name = entry_model.get().strip()
        if not model_name:
            messagebox.showwarning("Input Error", "Model name cannot be empty.")
            entry_model.focus_set()
            return

        success, message = insert_model(model_name)
        if success:
            messagebox.showinfo("Success", f"Model '{model_name}' added successfully.")
            model_win.destroy()
        else:
            messagebox.showerror("Error", message)
            entry_model.delete(0, tk.END)
            entry_model.focus_set()

    def cancel():
        model_win.destroy()

    btn_frame = tk.Frame(model_win)
    btn_frame.pack(pady=15)
    tk.Button(btn_frame, text="Submit", command=submit_model, width=10).pack(
        side="left", padx=10
    )
    tk.Button(btn_frame, text="Cancel", command=cancel, width=10).pack(
        side="right", padx=10
    )
    model_win.bind("<Return>", submit_model)


def add_new_entry():
    entry_win = tk.Toplevel()
    entry_win.title("Add New Entry")
    center_window(entry_win, 400, 450)
    entry_win.resizable(False, False)

    models = get_all_models()
    model_list = [row[0] for row in models]
    model_list.insert(0, "--Select Model--")

    reasons = [
        "COMPONENT DAMAGE",
        "MISALIGNMENT",
        "UPSIDE-DOWN COMPONENT",
        "WRONG COMPONENT",
        "BILLBOARD",
        "WRONG POLARITY",
        "COMPONENT SHIFT",
        "SOLDER BRIDGE",
        "EXCESS SOLDER",
        "LESS SOLDER",
        "SOLDER BALL",
        "COLD SOLDER",
        "DRY SOLDER",
        "PAD LIFT",
        "SOLDER CRACK",
        "INSUFFICIENT TROUGH HOLE",
        "OTHER",
    ]
    reasons.insert(0, "--SELECT REASON--")

    tk.Label(entry_win, text="PCB ID:").pack(pady=(10, 0))
    entry_pcb_id = tk.Entry(entry_win, width=40)
    entry_pcb_id.pack()
    entry_pcb_id.focus_set()

    tk.Label(entry_win, text="Model:").pack(pady=(10, 0))
    model_var = tk.StringVar()
    model_var.set(model_list[0])
    model_dropdown = ttk.Combobox(
        entry_win, textvariable=model_var, values=model_list, state="readonly", width=35
    )
    model_dropdown.pack()

    tk.Label(entry_win, text="Rejection Stage:").pack(pady=(10, 0))
    entry_stage = tk.Entry(entry_win, width=40)
    entry_stage.pack()

    tk.Label(entry_win, text="Rejection Details:").pack(pady=(10, 0))
    reasons_var = tk.StringVar()
    reasons_var.set(reasons[0])
    reason_dropdown = ttk.Combobox(
        entry_win, textvariable=reasons_var, values=reasons, state="readonly", width=35
    )
    reason_dropdown.pack()

    def submit_entry(event=None):
        pcb_id = entry_pcb_id.get().strip()
        model = model_var.get()
        rejection_stage = entry_stage.get().strip()
        rejection_details = reasons_var.get().strip()  # Use the selected reason
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        if not pcb_id:
            messagebox.showwarning("Input Error", "PCB ID cannot be empty.")
            entry_pcb_id.focus_set()
            return
        if not model or model == "--Select Model--":
            messagebox.showwarning("Input Error", "Please select a model.")
            model_dropdown.focus_set()
            return
        if not rejection_stage:
            messagebox.showwarning("Input Error", "Rejection Stage cannot be empty.")
            entry_stage.focus_set()
            return
        if not rejection_details or rejection_details == "--SELECT REASON--":
            messagebox.showwarning("Input Error", "Please select a rejection reason.")
            reason_dropdown.focus_set()
            return

        try:
            insert_entry(pcb_id, model, timestamp, rejection_stage, rejection_details)
            messagebox.showinfo("Success", f"New entry for PCB ID '{pcb_id}' added.")
            entry_win.destroy()
        except sqlite3.IntegrityError:
            messagebox.showerror("Duplicate Error", "This PCB ID already exists.")
            entry_pcb_id.focus_set()
        except Exception as e:
            messagebox.showerror("Database Error", f"Failed to add entry:\n{e}")

    def cancel():
        entry_win.destroy()

    btn_frame = tk.Frame(entry_win)
    btn_frame.pack(pady=20)
    tk.Button(btn_frame, text="Submit", command=submit_entry, width=12).pack(
        side="left", padx=10
    )
    tk.Button(btn_frame, text="Cancel", command=cancel, width=12).pack(
        side="right", padx=10
    )
    entry_win.bind("<Return>", submit_entry)


def do_rework():
    rework_win = tk.Toplevel()
    rework_win.title("Do Rework")
    center_window(rework_win, 600, 600)
    rework_win.grab_set()
    rework_win.focus_force()

    tk.Button(
        rework_win,
        text="← Back",
        command=rework_win.destroy,
        relief="flat",
        fg="blue",
        cursor="hand2",
    ).pack(anchor="nw", padx=10, pady=10)

    tk.Label(rework_win, text="Enter PCB ID:").pack()
    pcb_entry = tk.Entry(rework_win)
    pcb_entry.pack()
    pcb_entry.focus_set()

    tk.Label(rework_win, text="Model:").pack()
    model_entry = tk.Entry(rework_win, state="readonly")
    model_entry.pack()

    tk.Label(rework_win, text="Date:").pack()
    date_entry = tk.Entry(rework_win, state="readonly")
    date_entry.pack()

    tk.Label(rework_win, text="Rejection Stage:").pack()
    stage_entry = tk.Entry(rework_win, state="readonly")
    stage_entry.pack()

    tk.Label(rework_win, text="Rejection Details:").pack()
    details_entry = tk.Entry(rework_win, state="readonly")
    details_entry.pack()

    # New entry field for user-entered details
    tk.Label(rework_win, text="Rework Action Taken:").pack(pady=(10, 0))
    action_entry = tk.Entry(rework_win, width=40)
    action_entry.pack()

    submit_btn = tk.Button(rework_win, text="Submit")
    submit_btn.pack(pady=10)

    tk.Label(rework_win, text="Previous Reworks:").pack()
    previous_rework_text = tk.Text(rework_win, height=8, width=60, state="disabled")
    previous_rework_text.pack(pady=5)

    job = None

    def show_previous_reworks(pcbid):
        try:
            all_reworks = get_all_reworks_by_pcbid(pcbid)
        except Exception as e:
            messagebox.showerror("Database Error", f"Could not fetch reworks: {e}")
            return

        previous_rework_text.config(state="normal")
        previous_rework_text.delete(1.0, tk.END)

        if all_reworks:
            for row in all_reworks:
                rework_no, action, date, done_by = row
                previous_rework_text.insert(
                    tk.END,
                    f"Rework {rework_no}: {action} (Date: {date}, By: {done_by})\n",
                )
        else:
            previous_rework_text.insert(tk.END, "No previous reworks found.")

        previous_rework_text.config(state="disabled")

    def run_fetch_details():
        pcbid = pcb_entry.get().strip()
        if not pcbid:
            return

        for widget in [model_entry, date_entry, stage_entry, details_entry]:
            widget.config(state="normal")
            widget.delete(0, tk.END)
            widget.config(state="readonly")

        action_entry.delete(0, tk.END)
        action_entry.config(state="normal")
        submit_btn.config(state="normal")

        previous_rework_text.config(state="normal")
        previous_rework_text.delete(1.0, tk.END)
        previous_rework_text.config(state="disabled")

        entry = search_entry_by_pcbid(pcbid)
        all_reworks = get_all_reworks_by_pcbid(pcbid)

        if entry:
            _, _, model, timestamp, stage, details = entry[0]

            model_entry.config(state="normal")
            model_entry.insert(0, model)
            model_entry.config(state="readonly")

            date_entry.config(state="normal")
            date_entry.insert(0, timestamp)
            date_entry.config(state="readonly")

            stage_entry.config(state="normal")
            stage_entry.insert(0, stage if stage else "")
            stage_entry.config(state="readonly")

            details_entry.config(state="normal")
            details_entry.insert(0, details if details else "")
            details_entry.config(state="readonly")

            submit_btn.config(command=submit)

            show_previous_reworks(pcbid)

        elif all_reworks:
            latest_rework = all_reworks[-1]
            rework_no, reason, date, done_by = latest_rework

            show_previous_reworks(pcbid)

            model_entry.config(state="normal")
            model_entry.insert(0, "Already Reworked")
            model_entry.config(state="readonly")

            date_entry.config(state="normal")
            date_entry.insert(0, date)
            date_entry.config(state="readonly")

            stage_entry.config(state="normal")
            stage_entry.insert(0, "N/A")
            stage_entry.config(state="readonly")

            details_entry.config(state="normal")
            details_entry.insert(0, reason)
            details_entry.config(state="readonly")

            action_entry.config(state="normal")
            submit_btn.config(state="normal")

        else:
            messagebox.showerror("Error", "PCB ID not found in entries or rework logs.")
            for widget in [
                model_entry,
                date_entry,
                stage_entry,
                details_entry,
                action_entry,
            ]:
                widget.config(state="normal")
                widget.delete(0, tk.END)
                widget.config(state="readonly" if widget != action_entry else "normal")
            submit_btn.config(state="disabled")

    def fetch_details(event=None):
        nonlocal job
        if job:
            rework_win.after_cancel(job)
        job = rework_win.after(500, run_fetch_details)

    def submit(event=None):
        pcbid = pcb_entry.get().strip()
        rework_action = action_entry.get().strip()

        if not pcbid:
            messagebox.showerror("Invalid", "PCB ID is required.")
            return

        if not rework_action:
            messagebox.showerror("Invalid", "Rework Action Taken cannot be blank.")
            return

        global current_user
        user = current_user if current_user else "unknown"

        try:
            entry = search_entry_by_pcbid(pcbid)
            if entry:
                insert_rework(pcbid, rework_action, user)
                delete_entry_by_pcb_id(pcbid)
                messagebox.showinfo("✅ Success", f"Rework saved for PCB ID {pcbid}.")
                rework_win.destroy()
            else:
                insert_rework(pcbid, rework_action, user)
                messagebox.showinfo("✅ Success", f"Rework saved for PCB ID {pcbid}.")
                fetch_details()
                rework_win.destroy()

        except Exception as e:
            messagebox.showerror("Database Error", f"Insert failed: {e}")

    pcb_entry.bind("<KeyRelease>", fetch_details)
    submit_btn.config(command=submit)


def take_backup():
    try:
        # ensure main backup folder exists
        backup_root = "backups"
        os.makedirs(backup_root, exist_ok=True)

        # create datewise folder (YYYY-MM-DD)
        today_str = datetime.datetime.now().strftime("%Y-%m-%d")
        backup_dir = os.path.join(backup_root, today_str)
        os.makedirs(backup_dir, exist_ok=True)

        # fetch data from DB
        conn = get_connection()
        df = pd.read_sql_query("SELECT * FROM rework_log", conn)
        conn.close()

        # filename with timestamp inside datewise folder
        filename = os.path.join(
            backup_dir,
            f"backup_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
        )

        # save to Excel
        df.to_excel(filename, index=False)

        # success popup
        messagebox.showinfo("✅ Backup Success", f"Backup saved:\n{filename}")

    except Exception as e:
        # error popup
        messagebox.showerror("❌ Backup Failed", str(e))


def db_add_operator():
    operator_win = tk.Toplevel()
    operator_win.title("Add Operator")
    center_window(operator_win, 600, 500)

    tk.Button(
        operator_win,
        text="← Back",
        command=operator_win.destroy,
        relief="flat",
        fg="blue",
        cursor="hand2",
    ).pack(anchor="nw", padx=10, pady=10)

    tk.Label(operator_win, text="Username:").pack()
    username_entry = tk.Entry(operator_win)
    username_entry.pack()
    operator_win.after(100, lambda: username_entry.focus_set())

    tk.Label(operator_win, text="Password:").pack()
    password_entry = tk.Entry(operator_win, show="*")
    password_entry.pack()

    def save_operator(event=None):
        username = username_entry.get().strip()
        password = password_entry.get().strip()

        if not username or not password:
            messagebox.showerror("Error", "Username & Password required")
            username_entry.delete(0, tk.END)
            username_entry.focus_set()
            return

        if add_operator(username, password):
            messagebox.showinfo("Success", "Operator added")
            operator_win.destroy()
        else:
            messagebox.showerror("Error", "Username already exists")
            username_entry.delete(0, tk.END)
            password_entry.delete(0, tk.END)
            username_entry.focus_set()

    tk.Button(operator_win, text="Add", command=save_operator).pack(pady=10)
    operator_win.bind("<Return>", save_operator)


def ask_admin_password():
    dialog = tk.Toplevel()
    dialog.title("Verify Admin")
    center_window(dialog, 400, 200)
    dialog.grab_set()
    dialog.resizable(False, False)

    tk.Label(dialog, text="Enter Admin Password:", font=("Arial", 14)).pack(pady=15)
    password_entry = tk.Entry(dialog, show="*", width=40, font=("Arial", 12))
    password_entry.pack(pady=5)
    password_entry.focus_set()

    result = {"password": None}

    def on_submit():
        entered_password = password_entry.get()
        if validate_admin("admin", entered_password):
            result["password"] = entered_password
            dialog.destroy()
        else:
            messagebox.showerror("Error", "Incorrect password")
            password_entry.delete(0, tk.END)
            password_entry.focus_set()

    def on_cancel():
        dialog.destroy()

    tk.Button(dialog, text="Submit", width=10, command=on_submit).pack(pady=10)
    tk.Button(dialog, text="Cancel", width=10, command=on_cancel).pack()

    dialog.bind("<Return>", lambda e: on_submit())
    dialog.bind("<Escape>", lambda e: on_cancel())
    dialog.wait_window()
    return result["password"]


def view_operators():
    admin_pass = ask_admin_password()
    if not admin_pass:
        return

    operators_win = tk.Toplevel()
    operators_win.title("All Operators")
    center_window(operators_win, 600, 500)

    tk.Button(
        operators_win,
        text="← Back",
        command=operators_win.destroy,
        relief="flat",
        fg="blue",
        cursor="hand2",
    ).pack(anchor="nw", padx=10, pady=10)

    tk.Label(
        operators_win,
        text="Operator List (Username | Password)",
        font=("Arial", 10, "bold"),
    ).pack(pady=5)

    columns = ("username", "password")
    tree = ttk.Treeview(operators_win, columns=columns, show="headings", height=15)
    tree.heading("username", text="Username")
    tree.heading("password", text="Password")
    tree.column("username", width=200, anchor="center")
    tree.column("password", width=200, anchor="center")
    tree.pack(padx=20, pady=10, fill="both", expand=True)

    operators = list_all_operators()
    for op in operators:
        tree.insert("", "end", values=op)

    scrollbar = ttk.Scrollbar(operators_win, orient="vertical", command=tree.yview)
    tree.configure(yscroll=scrollbar.set)
    scrollbar.pack(side="right", fill="y")


def view_rework_logs(admin_window):
    logs_win = tk.Toplevel()
    logs_win.title("Rework Log Viewer")
    center_window(logs_win, 900, 500)
    logs_win.grab_set()

    # Back Button
    tk.Button(
        logs_win,
        text="← Back",
        command=logs_win.destroy,
        relief="flat",
        fg="blue",
        cursor="hand2",
    ).pack(anchor="nw", padx=10, pady=10)

    # Title
    tk.Label(logs_win, text="Rework Logs", font=("Arial", 16, "bold")).pack(pady=10)

    # Treeview
    columns = (
        "id",
        "pcb_id",
        "rework_no",
        "rework_action",
        "rework_date",
        "rework_done_by",
    )
    tree = ttk.Treeview(logs_win, columns=columns, show="headings")

    for col in columns:
        tree.heading(col, text=col.replace("_", " ").title())
        tree.column(col, width=130, anchor="center")

    tree.pack(fill="both", expand=True)

    # Load data from DB
    def load_data():
        try:
            conn, cur = get_conn_and_cursor()
            if conn and cur:
                cur.execute(
                    "SELECT id, pcb_id, rework_no, rework_action, rework_date, rework_done_by FROM rework_log"
                )
                rows = cur.fetchall()
                conn.close()

                for row in rows:
                    tree.insert("", "end", values=row)
        except Exception as e:
            messagebox.showerror("Database Error", f"Could not load data:\n{e}")

    load_data()

    if current_user == "admin":
        tk.Button(logs_win, text="💾 Take Backup", width=25, command=take_backup).pack(
            pady=10
        )


def start_selection_window():
    selection_win = tk.Tk()
    selection_win.title("Rework System")
    center_window(selection_win, 600, 500)

    tk.Label(selection_win, text="Login as:", font=("Arial", 12)).pack(pady=10)

    tk.Button(
        selection_win,
        text="👑 Admin",
        command=lambda: [selection_win.destroy(), show_login_window()],
    ).pack(pady=10)

    tk.Button(
        selection_win,
        text="👷 Operator",
        command=lambda: login_operator(selection_win),
    ).pack(pady=10)

    selection_win.mainloop()


if __name__ == "__main__":
    start_selection_window()
