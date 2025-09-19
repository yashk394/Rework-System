CREATE TABLE IF NOT EXISTS admins (
    username TEXT NOT NULL UNIQUE,
    password TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS operators (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE,
    password TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS models (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    model_name TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS entries (
    sr_no INTEGER PRIMARY KEY AUTOINCREMENT,
    pcb_id TEXT NOT NULL UNIQUE,
    model TEXT NOT NULL,
    timestamp TEXT NOT NULL,
    rejection_stage TEXT,
    rejection_details TEXT
);

CREATE TABLE IF NOT EXISTS rework_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    pcb_id TEXT NOT NULL,
    rework_no INTEGER NOT NULL,
    rework_action TEXT NOT NULL,
    rework_date TEXT NOT NULL,
    rework_done_by TEXT NOT NULL,
    FOREIGN KEY(pcb_id) REFERENCES entries(pcb_id)
);

INSERT OR IGNORE INTO admins (username, password) VALUES ('admin', 'admin@123');