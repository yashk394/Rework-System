import sqlite3
import os
from datetime import datetime
import sys
import hashlib


def resource_path(relative_path):
    """Get absolute path to resource, works for dev and for PyInstaller .exe"""
    if hasattr(sys, "_MEIPASS"):  # Running in PyInstaller bundle
        base_path = sys._MEIPASS
    else:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)


DB_NAME = "rework_data.db"
SETUP_SQL_NAME = "setup.sql"


def get_conn_and_cursor():
    """Returns a connection and cursor for the database."""
    try:
        conn = sqlite3.connect(resource_path(DB_NAME))
        return conn, conn.cursor()
    except sqlite3.Error as e:
        print(f"Database connection error: {e}")
        return None, None


def get_db_path():
    """Get path for rework_data.db (always stored next to .exe or script)."""
    if getattr(sys, "frozen", False):
        # Running as .exe → store DB in same folder as the exe
        return os.path.join(os.path.dirname(sys.executable), "rework_data.db")
    else:
        # Running as .py → store DB in current working directory
        return os.path.join(os.path.abspath("."), "rework_data.db")


def get_conn_and_cursor():
    conn = sqlite3.connect(get_db_path())
    return conn, conn.cursor()


def get_connection():
    db_path = get_db_path()
    conn = sqlite3.connect(db_path)
    return conn


def init_db():
    db_path = get_db_path()
    if not os.path.exists(db_path):
        # First run → create db from setup.sql
        try:
            # setup.sql is bundled inside exe → extract correct path
            if getattr(sys, "frozen", False):
                base_path = sys._MEIPASS
            else:
                base_path = os.path.dirname(os.path.abspath(__file__))

            sql_file = os.path.join(base_path, "setup.sql")

            with open(sql_file, "r", encoding="utf-8") as f:
                sql_script = f.read()

            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.executescript(sql_script)
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"DB Init Error: {e}")


def get_rework_log_by_pcbid(pcb_id):
    conn, cursor = get_conn_and_cursor()
    if not conn:
        return None
    cursor.execute("SELECT * FROM rework_log WHERE pcb_id=?", (pcb_id,))
    result = cursor.fetchone()
    conn.close()
    return result


def insert_model(model_name):
    """Inserts a new model into the database."""
    conn, cur = get_conn_and_cursor()
    if not conn:
        return False, "Database connection failed."

    try:
        cur.execute("INSERT INTO models (model_name) VALUES (?)", (model_name,))
        conn.commit()
        return True, "Model added successfully"
    except sqlite3.IntegrityError:
        return False, "Model already exists."
    except Exception as e:
        return False, f"Database Error: {e}"
    finally:
        conn.close()


def get_all_models():
    """Fetches all model names from the database."""
    conn, cur = get_conn_and_cursor()
    if not conn:
        return []

    try:
        cur.execute("SELECT model_name FROM models")
        return cur.fetchall()
    except Exception as e:
        print(f"Error fetching models: {e}")
        return []
    finally:
        conn.close()


def insert_entry(pcb_id, model, timestamp, rejection_stage, rejection_details):
    """Inserts a new entry into the database."""
    conn, cur = get_conn_and_cursor()
    if not conn:
        return False

    try:
        cur.execute(
            """
            INSERT INTO entries (pcb_id, model, timestamp, rejection_stage, rejection_details)
            VALUES (?, ?, ?, ?, ?)
            """,
            (pcb_id, model, timestamp, rejection_stage, rejection_details),
        )
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        raise
    except Exception as e:
        raise
    finally:
        conn.close()


def search_entry_by_pcbid(pcbid):
    """Searches for a single entry by its PCB ID."""
    conn, cur = get_conn_and_cursor()
    if not conn:
        return []

    try:
        cur.execute("SELECT * FROM entries WHERE pcb_id = ?", (pcbid,))
        rows = cur.fetchall()
        return rows
    except Exception as e:
        print(f"Error searching entry by PCB ID: {e}")
        return []
    finally:
        conn.close()


def delete_entry_by_pcb_id(pcbid):
    conn, cur = get_conn_and_cursor()
    if not conn:
        return False
    cur.execute("DELETE FROM entries WHERE pcb_id = ?", (pcbid,))
    conn.commit()
    conn.close()
    return True


def get_all_reworks_by_pcbid(pcbid):
    """Fetches all rework logs for a specific PCB ID."""
    conn, cur = get_conn_and_cursor()
    if not conn:
        return []
    try:
        cur.execute(
            "SELECT rework_no, rework_action, rework_date, rework_done_by FROM rework_log WHERE pcb_id=?",
            (pcbid,),
        )
        return cur.fetchall()
    except Exception as e:
        print(f"Error fetching reworks for PCB ID: {e}")
        return []
    finally:
        conn.close()


def get_rework_count(pcbid):
    """Returns the number of reworks for a given PCB ID."""
    conn, cur = get_conn_and_cursor()
    if not conn:
        return 0

    try:
        cur.execute("SELECT COUNT(*) FROM rework_log WHERE pcb_id = ?", (pcbid,))
        count = cur.fetchone()[0]
        return count
    except Exception as e:
        print(f"Error getting rework count: {e}")
        return 0
    finally:
        conn.close()


def insert_rework(pcbid, reason, operator):
    conn, cursor = get_conn_and_cursor()
    if not conn:
        return
    rework_no = get_rework_count(pcbid) + 1
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    cursor.execute(
        "INSERT INTO rework_log (pcb_id, rework_no, rework_action, rework_date, rework_done_by) VALUES (?, ?, ?, ?, ?)",
        (pcbid, rework_no, reason, now, operator),
    )
    conn.commit()
    conn.close()


def validate_operator(username, password):
    """Validates an operator's credentials."""
    conn, cursor = get_conn_and_cursor()
    if not conn:
        return False

    try:
        cursor.execute(
            "SELECT * FROM operators WHERE username=? AND password=?",
            (username, password),
        )
        result = cursor.fetchone()
        return result is not None
    except Exception as e:
        print(f"Error validating operator: {e}")
        return False
    finally:
        conn.close()


def validate_admin(username, password):
    """Validates admin credentials (hardcoded)."""
    return username == "admin" and password == "admin@123"


def add_operator(username, password):
    """Adds a new operator to the database."""
    conn, cursor = get_conn_and_cursor()
    if not conn:
        return False

    try:
        cursor.execute(
            "INSERT INTO operators (username, password) VALUES (?, ?)",
            (username, password),
        )
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    except Exception as e:
        print(f"Database Error: {e}")
        return False
    finally:
        conn.close()


def list_all_operators():
    """Fetches all operators from the database."""
    conn, cursor = get_conn_and_cursor()
    if not conn:
        return []

    try:
        cursor.execute("SELECT username, password FROM operators")
        results = cursor.fetchall()
        return results
    except Exception as e:
        print(f"Error listing operators: {e}")
        return []
    finally:
        conn.close()


def fetch_with_rework_logs():
    conn, cur = get_conn_and_cursor()
    if not conn:
        return []
    cur.execute(
        """
        SELECT serial_number, product_name, issue, status, rework_done_by, date, details
        FROM rework_log
        WHERE status = 'With Rework'
    """
    )
    rows = cur.fetchall()
    conn.close()
    return rows


def fetch_before_rework_logs():
    conn, cur = get_conn_and_cursor()
    if not conn:
        return []
    cur.execute(
        """
        SELECT serial_number, product_name, issue, status, rework_done_by, date, details
        FROM rework_log
        WHERE status = 'Before Rework'
    """
    )
    rows = cur.fetchall()
    conn.close()
    return rows


def fetch_with_rework():
    """
    Fetches all entries with at least one rework log. The query is
    structured to match the 7 columns of the Treeview widget in main.py.
    """
    conn, cur = get_conn_and_cursor()
    if not conn:
        return []

    try:
        cur.execute(
            """
            SELECT
                e.sr_no,
                e.model,
                COALESCE(e.rejection_details, 'N/A'),
                'Reworked',
                COALESCE(r.rework_done_by, '—'),
                COALESCE(r.rework_date, e.timestamp),
                COALESCE(r.rework_action, '—')
            FROM entries e
            INNER JOIN rework_log r ON e.pcb_id = r.pcb_id
            ORDER BY e.pcb_id, r.rework_no
            """
        )
        rows = cur.fetchall()
        return rows
    except Exception as e:
        print(f"Error fetching data with rework: {e}")
        return []
    finally:
        conn.close()


def fetch_before_rework():
    conn, cur = get_conn_and_cursor()
    if not conn:
        return []
    cur.execute(
        """
        SELECT e.id,
               e.serial_number,
               e.model,
               e.date,
               COALESCE(r.rework_no, 'N/A') AS rework_no,
               COALESCE(r.issue_description, 'N/A') AS issue_description,
               COALESCE(r.date_of_rework, 'N/A') AS date_of_rework
        FROM entries e
        LEFT JOIN rework_log r ON e.serial_number = r.serial_number
        WHERE r.serial_number IS NULL
        ORDER BY e.id DESC
    """
    )
    rows = cur.fetchall()
    conn.close()
    return rows


def fetch_all_entries():
    """
    Fetches all entries, regardless of rework status, with a single query.
    This can be a helpful debug function or for a general 'view all' log.
    """
    conn, cur = get_conn_and_cursor()
    if not conn:
        return []

    try:
        cur.execute(
            """
            SELECT
                e.sr_no,
                e.model,
                COALESCE(e.rejection_details, 'N/A'),
                CASE WHEN r.id IS NULL THEN 'Pending' ELSE 'Reworked' END AS Status,
                COALESCE(r.rework_done_by, '—'),
                COALESCE(r.rework_date, e.timestamp),
                COALESCE(r.rework_action, '—')
            FROM entries e
            LEFT JOIN rework_log r ON e.pcb_id = r.pcb_id
            ORDER BY e.sr_no, r.rework_no
            """
        )
        rows = cur.fetchall()
        return rows
    except Exception as e:
        print(f"Error fetching all entries: {e}")
        return []
    finally:
        conn.close()
