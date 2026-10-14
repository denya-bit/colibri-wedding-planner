#!/usr/bin/env python3
"""Colibri Wedding API - Partner Collaboration v2"""
import json, sqlite3, secrets, time, os
from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

DB_PATH = "/root/colibri/api/data.db"

def get_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    db = sqlite3.connect(DB_PATH)
    db.row_factory = sqlite3.Row
    return db

def init_db():
    db = get_db()
    db.execute("""
        CREATE TABLE IF NOT EXISTS couples (
            code TEXT PRIMARY KEY,
            data TEXT NOT NULL,
            created_at INTEGER,
            updated_at INTEGER
        )
    """)
    db.execute("""
        CREATE TABLE IF NOT EXISTS members (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            couple_code TEXT NOT NULL,
            user_id INTEGER NOT NULL,
            name TEXT,
            role TEXT DEFAULT 'guest',
            joined_at INTEGER,
            UNIQUE(couple_code, user_id)
        )
    """)
    # Миграция: добавляем role если нет
    try:
        db.execute("ALTER TABLE members ADD COLUMN role TEXT DEFAULT 'guest'")
    except:
        pass
    db.commit()
    db.close()

init_db()

@app.route("/api/health")
def health():
    return jsonify({"status": "ok", "time": int(time.time())})

@app.route("/api/couple", methods=["POST"])
def create_couple():
    data = request.json or {}
    user_id = data.get("user_id", 0)
    name = data.get("name", "")
    role = data.get("role", "bride")
    wedding_data = data.get("data", {})
    
    db = get_db()
    
    # AUTO-RESTORE: if user already has a couple, return it with data
    existing = db.execute(
        "SELECT couple_code FROM members WHERE user_id = ? LIMIT 1",
        (user_id,)
    ).fetchone()
    if existing:
        code = existing["couple_code"]
        row = db.execute("SELECT data FROM couples WHERE code = ?", (code,)).fetchone()
        member_data = json.loads(row["data"]) if row and row["data"] else {}
        members = db.execute("SELECT user_id, name, role FROM members WHERE couple_code = ?", (code,)).fetchall()
        db.close()
        return jsonify({"code": code, "status": "existing", "data": member_data, "members": [dict(m) for m in members]})
    
    code = secrets.token_hex(4).upper()
    now = int(time.time())
    
    db.execute(
        "INSERT INTO couples (code, data, created_at, updated_at) VALUES (?, ?, ?, ?)",
        (code, json.dumps(wedding_data), now, now)
    )
    db.execute(
        "INSERT OR REPLACE INTO members (couple_code, user_id, name, role, joined_at) VALUES (?, ?, ?, ?, ?)",
        (code, user_id, name, role, now)
    )
    db.commit()
    db.close()
    
    return jsonify({"code": code, "status": "created"})

@app.route("/api/couple/<code>/join", methods=["POST"])
def join_couple(code):
    data = request.json or {}
    user_id = data.get("user_id", 0)
    name = data.get("name", "")
    role = data.get("role", "guest")
    
    db = get_db()
    couple = db.execute("SELECT * FROM couples WHERE code = ?", (code.upper(),)).fetchone()
    if not couple:
        db.close()
        return jsonify({"error": "Couple not found"}), 404
    
    now = int(time.time())
    db.execute(
        "INSERT OR REPLACE INTO members (couple_code, user_id, name, role, joined_at) VALUES (?, ?, ?, ?, ?)",
        (code.upper(), user_id, name, role, now)
    )
    db.commit()
    
    couple_data = json.loads(couple["data"])
    members = db.execute("SELECT user_id, name, role FROM members WHERE couple_code = ?", (code.upper(),)).fetchall()
    db.close()
    
    return jsonify({
        "code": code.upper(),
        "data": couple_data,
        "members": [dict(m) for m in members],
        "status": "joined"
    })

@app.route("/api/couple/<code>", methods=["GET"])
def get_couple(code):
    user_id = request.args.get("user_id", 0, type=int)
    
    db = get_db()
    couple = db.execute("SELECT * FROM couples WHERE code = ?", (code.upper(),)).fetchone()
    if not couple:
        db.close()
        return jsonify({"error": "Couple not found"}), 404
    
    member = db.execute(
        "SELECT * FROM members WHERE couple_code = ? AND user_id = ?",
        (code.upper(), user_id)
    ).fetchone()
    if not member:
        db.close()
        return jsonify({"error": "Not a member"}), 403
    
    couple_data = json.loads(couple["data"])
    members = db.execute("SELECT user_id, name, role FROM members WHERE couple_code = ?", (code.upper(),)).fetchall()
    db.close()
    
    return jsonify({
        "code": code.upper(),
        "data": couple_data,
        "members": [dict(m) for m in members],
        "updated_at": couple["updated_at"]
    })

@app.route("/api/couple/<code>", methods=["PUT"])
def update_couple(code):
    data = request.json or {}
    user_id = data.get("user_id", 0)
    wedding_data = data.get("data", {})
    
    db = get_db()
    member = db.execute(
        "SELECT * FROM members WHERE couple_code = ? AND user_id = ?",
        (code.upper(), user_id)
    ).fetchone()
    if not member:
        db.close()
        return jsonify({"error": "Not a member"}), 403
    
    now = int(time.time())
    db.execute(
        "UPDATE couples SET data = ?, updated_at = ? WHERE code = ?",
        (json.dumps(wedding_data), now, code.upper())
    )
    db.commit()
    db.close()
    
    return jsonify({"status": "updated", "updated_at": now})

@app.route("/api/couple/<code>/role", methods=["PUT"])
def update_role(code):
    data = request.json or {}
    target_user = data.get("target_user_id", 0)
    new_role = data.get("role", "guest")
    by_user = data.get("user_id", 0)
    
    db = get_db()
    # Only bride/groom can change roles
    admin = db.execute(
        "SELECT * FROM members WHERE couple_code = ? AND user_id = ? AND role IN ('bride','groom')",
        (code.upper(), by_user)
    ).fetchone()
    if not admin:
        db.close()
        return jsonify({"error": "Only bride/groom can change roles"}), 403
    
    db.execute(
        "UPDATE members SET role = ? WHERE couple_code = ? AND user_id = ?",
        (new_role, code.upper(), target_user)
    )
    db.commit()
    db.close()
    
    return jsonify({"status": "role_updated"})

@app.route("/api/couple/<code>/members", methods=["GET"])
def get_members(code):
    db = get_db()
    members = db.execute("SELECT user_id, name, role FROM members WHERE couple_code = ?", (code.upper(),)).fetchall()
    db.close()
    return jsonify({"members": [dict(m) for m in members]})

@app.route("/api/user-data", methods=["POST"])
def save_user_data():
    data = request.json or {}
    user_id = str(data.get("user_id", "0"))
    payload = data.get("payload", {})
    db = get_db()
    now = int(time.time())
    existing = db.execute("SELECT couple_code FROM members WHERE user_id = ? LIMIT 1", (user_id,)).fetchone()
    if existing:
        code = existing["couple_code"]
    else:
        code = "U" + user_id
        db.execute("INSERT OR REPLACE INTO couples (code, data, created_at, updated_at) VALUES (?, ?, ?, ?)", (code, "{}", now, now))
        db.execute("INSERT OR REPLACE INTO members (couple_code, user_id, name, role, joined_at) VALUES (?, ?, ?, ?, ?)", (code, user_id, "User", "bride", now))
    db.execute("UPDATE couples SET data = ?, updated_at = ? WHERE code = ?", (json.dumps(payload), now, code))
    db.commit()
    db.close()
    return jsonify({"ok": True, "code": code})

@app.route("/api/user-data/<user_id>", methods=["GET"])
def get_user_data(user_id):
    db = get_db()
    existing = db.execute("SELECT couple_code FROM members WHERE user_id = ? LIMIT 1", (str(user_id),)).fetchone()
    if not existing:
        db.close()
        return jsonify({"ok": False, "error": "not found"})
    code = existing["couple_code"]
    row = db.execute("SELECT data FROM couples WHERE code = ?", (code,)).fetchone()
    db.close()
    if row and row["data"]:
        return jsonify({"ok": True, "code": code, "data": json.loads(row["data"])})
    return jsonify({"ok": False, "error": "no data"})

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8181, debug=False)


