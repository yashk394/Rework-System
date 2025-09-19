# --- UPDATED do_rework() FUNCTION ---
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

            submit_btn.config(state="normal")

        else:
            messagebox.showerror("Error", "PCB ID not found in entries or rework logs.")
            for widget in [
                model_entry,
                date_entry,
                stage_entry,
                details_entry,
            ]:
                widget.config(state="normal")
                widget.delete(0, tk.END)
                widget.config(state="readonly")
            submit_btn.config(state="disabled")

    def fetch_details(event=None):
        nonlocal job
        if job:
            rework_win.after_cancel(job)
        job = rework_win.after(500, run_fetch_details)

    def submit(event=None):
        pcbid = pcb_entry.get().strip()

        # Rework reason is taken directly from the "Rejection Details" entry
        final_reason = details_entry.get().strip()

        if not pcbid:
            messagebox.showerror("Invalid", "PCB ID is required.")
            return

        if not final_reason:
            messagebox.showerror("Invalid", "Rejection Details cannot be blank.")
            return

        global current_user
        user = current_user if current_user else "unknown"

        try:
            entry = search_entry_by_pcbid(pcbid)
            if entry:
                insert_rework(pcbid, final_reason, user)
                delete_entry_by_pcb_id(pcbid)
                messagebox.showinfo("✅ Success", f"Rework saved for PCB ID {pcbid}.")
                rework_win.destroy()
            else:
                insert_rework(pcbid, final_reason, user)
                messagebox.showinfo("✅ Success", f"Rework saved for PCB ID {pcbid}.")
                fetch_details()
                rework_win.destroy()

        except Exception as e:
            messagebox.showerror("Database Error", f"Insert failed: {e}")

    pcb_entry.bind("<KeyRelease>", fetch_details)
    submit_btn.config(command=submit)
