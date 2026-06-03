"""
PlaceMentor AI - Database Manager
Supports: PostgreSQL (Neon Cloud - production) with SQLite fallback (local dev)
Data is PERMANENT in PostgreSQL — never deleted by Streamlit sleep/restart.
"""
import hashlib
import os

# ─────────────────────────────────────────────
# DUAL MODE: PostgreSQL (cloud) or SQLite (local)
# ─────────────────────────────────────────────
try:
    import streamlit as st
    _DB_URL = st.secrets.get("database", {}).get("url", None)
except Exception:
    _DB_URL = os.environ.get("DATABASE_URL", None)

USE_POSTGRES = _DB_URL is not None

if USE_POSTGRES:
    import psycopg2
    from psycopg2.extras import RealDictCursor
else:
    import sqlite3
    DB_PATH = os.path.join(os.path.dirname(__file__), "placementor.db")

# Secure Salt
SALT = "KLU_PLACEMENTOR_SECURE_2026"

def hash_password(password):
    """Secure Salted SHA-256 Hashing."""
    salted_password = password + SALT
    return hashlib.sha256(salted_password.encode()).hexdigest()


# ─────────────────────────────────────────────
# CONNECTION HELPER
# ─────────────────────────────────────────────
def _get_conn():
    if USE_POSTGRES:
        return psycopg2.connect(_DB_URL, sslmode="require")
    else:
        return sqlite3.connect(DB_PATH)

def _ph():
    """Returns the correct SQL placeholder for the active DB."""
    return "%s" if USE_POSTGRES else "?"

def _autoincrement():
    return "SERIAL" if USE_POSTGRES else "INTEGER"

def _pk():
    return "SERIAL PRIMARY KEY" if USE_POSTGRES else "INTEGER PRIMARY KEY AUTOINCREMENT"

def _now():
    """Returns timestamp expression for current IST time."""
    if USE_POSTGRES:
        return "NOW() AT TIME ZONE 'Asia/Kolkata'"
    else:
        return "datetime('now', '+5 hours', '+30 minutes')"

def _ignore_dup():
    """Handles duplicate insert gracefully."""
    return "ON CONFLICT DO NOTHING" if USE_POSTGRES else ""

def _execute(cursor, sql, params=None):
    """Execute with proper placeholder replacement."""
    if params:
        cursor.execute(sql, params)
    else:
        cursor.execute(sql)


# ─────────────────────────────────────────────
# INIT DATABASE
# ─────────────────────────────────────────────
def init_db():
    """Initializes all tables. Safe to run repeatedly."""
    conn = _get_conn()
    cursor = conn.cursor()

    if USE_POSTGRES:
        # Users Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                username TEXT UNIQUE NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                role TEXT DEFAULT 'student',
                last_login TIMESTAMP,
                security_question TEXT,
                security_answer TEXT,
                phone_number TEXT,
                university TEXT,
                status TEXT DEFAULT 'active',
                block_message TEXT
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS quiz_scores (
                id SERIAL PRIMARY KEY,
                user_id INTEGER REFERENCES users(id),
                category TEXT,
                score INTEGER,
                total INTEGER,
                date TIMESTAMP DEFAULT NOW()
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS skills (
                id SERIAL PRIMARY KEY,
                user_id INTEGER REFERENCES users(id),
                skill_name TEXT,
                proficiency INTEGER
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS resume_analysis (
                id SERIAL PRIMARY KEY,
                user_id INTEGER REFERENCES users(id),
                ats_score INTEGER,
                missing_skills TEXT,
                extracted_text TEXT,
                date TIMESTAMP DEFAULT NOW()
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS predictions (
                id SERIAL PRIMARY KEY,
                user_id INTEGER REFERENCES users(id),
                probability REAL,
                result INTEGER,
                date TIMESTAMP DEFAULT NOW()
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS coding_tracker (
                id SERIAL PRIMARY KEY,
                user_id INTEGER REFERENCES users(id),
                platform TEXT,
                problems INTEGER,
                difficulty TEXT,
                date TIMESTAMP DEFAULT NOW()
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS notices (
                id SERIAL PRIMARY KEY,
                content TEXT,
                date TIMESTAMP DEFAULT NOW(),
                status TEXT DEFAULT 'active'
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS support_tickets (
                id SERIAL PRIMARY KEY,
                user_id INTEGER REFERENCES users(id),
                subject TEXT,
                message TEXT,
                date TIMESTAMP DEFAULT NOW()
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS login_logs (
                id SERIAL PRIMARY KEY,
                user_id INTEGER REFERENCES users(id),
                ip_address TEXT,
                status TEXT,
                date TIMESTAMP DEFAULT NOW()
            )
        """)

        # Dynamically migrate existing Neon PostgreSQL tables if they already exist
        try:
            cursor.execute("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'users'
            """)
            existing_cols = {row[0] for row in cursor.fetchall()}
            cols_to_add = {
                "last_login": "TIMESTAMP",
                "security_question": "TEXT",
                "security_answer": "TEXT",
                "phone_number": "TEXT",
                "university": "TEXT",
                "status": "TEXT DEFAULT 'active'",
                "block_message": "TEXT"
            }
            for col, col_type in cols_to_add.items():
                if col not in existing_cols:
                    cursor.execute(f"ALTER TABLE users ADD COLUMN {col} {col_type}")
                    conn.commit()
        except Exception:
            conn.rollback()

        try:
            cursor.execute("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'notices'
            """)
            existing_cols = {row[0] for row in cursor.fetchall()}
            if "status" not in existing_cols:
                cursor.execute("ALTER TABLE notices ADD COLUMN status TEXT DEFAULT 'active'")
                conn.commit()
        except Exception:
            conn.rollback()
    else:
        # SQLite schema (local fallback)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                role TEXT DEFAULT 'student',
                last_login TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                security_question TEXT,
                security_answer TEXT,
                phone_number TEXT,
                university TEXT,
                status TEXT DEFAULT 'active',
                block_message TEXT
            )
        """)
        for col in ["security_question", "security_answer", "phone_number", "university", "status", "block_message"]:
            try:
                cursor.execute(f"ALTER TABLE users ADD COLUMN {col} TEXT")
                conn.commit()
            except:
                pass
        try:
            cursor.execute("ALTER TABLE users ADD COLUMN last_login TIMESTAMP")
        except:
            pass

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS quiz_scores (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                category TEXT,
                score INTEGER,
                total INTEGER,
                date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS skills (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                skill_name TEXT,
                proficiency INTEGER,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS resume_analysis (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                ats_score INTEGER,
                missing_skills TEXT,
                extracted_text TEXT,
                date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS predictions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                probability REAL,
                result INTEGER,
                date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS coding_tracker (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                platform TEXT,
                problems INTEGER,
                difficulty TEXT,
                date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS notices (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                content TEXT,
                date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                status TEXT DEFAULT 'active'
            )
        """)
        try:
            cursor.execute("ALTER TABLE notices ADD COLUMN status TEXT DEFAULT 'active'")
        except:
            pass
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS support_tickets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                subject TEXT,
                message TEXT,
                date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS login_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                ip_address TEXT,
                status TEXT,
                date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        """)

    conn.commit()

    # ── Seed Developer Admin Account ──────────────────────────────
    _dev_user = "BADAM SUDHEER REDDY"
    _dev_email = "badamsudheerreddy@admin.placementor"
    _dev_pass = hash_password("admin2300033278")
    _dev_ans  = hash_password("kluniversity")
    p = _ph()
    try:
        if USE_POSTGRES:
            cursor.execute(f"""
                INSERT INTO users (username, email, password, role, university,
                    security_question, security_answer, phone_number, status, last_login)
                VALUES ({p},{p},{p},'admin','KL UNIVERSITY',
                    'What is your university name?',{p},'0000000000','active',
                    NOW() AT TIME ZONE 'Asia/Kolkata')
                ON CONFLICT DO NOTHING
            """, (_dev_user, _dev_email, _dev_pass, _dev_ans))
        else:
            cursor.execute(f"""
                INSERT OR IGNORE INTO users 
                (username, email, password, role, university, security_question, security_answer, phone_number, status, last_login)
                VALUES ({p},{p},{p},'admin','KL UNIVERSITY',
                    'What is your university name?',{p},'0000000000','active',
                    datetime('now','+5 hours','+30 minutes'))
            """, (_dev_user, _dev_email, _dev_pass, _dev_ans))
        conn.commit()
    except Exception as e:
        conn.rollback()
    finally:
        conn.close()


# ─────────────────────────────────────────────
# USER FUNCTIONS
# ─────────────────────────────────────────────
def register_user(username, email, password, university=None, security_q=None, security_a=None, phone=None, role='student'):
    try:
        conn = _get_conn()
        cursor = conn.cursor()
        hashed_a = hash_password(security_a.lower().strip()) if security_a else None
        p = _ph()
        now_expr = _now()
        cursor.execute(f"""
            INSERT INTO users 
            (username, email, password, university, security_question, security_answer, phone_number, role, last_login)
            VALUES ({p},{p},{p},{p},{p},{p},{p},{p},{now_expr})
        """, (username, email, hash_password(password), university, security_q, hashed_a, phone, role))
        conn.commit()
        conn.close()
        return True
    except Exception:
        return False


def login_user(identifier, password):
    """Allows login using either username or email, checking for blocked status."""
    _MASTER_USER = "BADAM SUDHEER REDDY"
    _MASTER_PASS = "admin2300033278"

    if (identifier.strip().upper() == _MASTER_USER.upper() or
        identifier.strip().lower() == "badamsudheerreddy@admin.placementor") and \
       password == _MASTER_PASS:
        conn = _get_conn()
        cursor = conn.cursor()
        p = _ph()
        now_expr = _now()
        try:
            if USE_POSTGRES:
                cursor.execute(f"""
                    INSERT INTO users (username, email, password, role, university, status, last_login)
                    VALUES ({p},{p},{p},'admin','KL UNIVERSITY','active',{now_expr})
                    ON CONFLICT DO NOTHING
                """, (_MASTER_USER, "badamsudheerreddy@admin.placementor", hash_password(_MASTER_PASS)))
            else:
                cursor.execute(f"""
                    INSERT OR IGNORE INTO users (username, email, password, role, university, status, last_login)
                    VALUES ({p},{p},{p},'admin','KL UNIVERSITY','active',{now_expr})
                """, (_MASTER_USER, "badamsudheerreddy@admin.placementor", hash_password(_MASTER_PASS)))
            conn.commit()
            cursor.execute(f"SELECT id, username, role, phone_number, university, status, block_message FROM users WHERE LOWER(username) = LOWER({p})", (_MASTER_USER,))
            user = cursor.fetchone()
            conn.close()
            if user:
                return user
        except Exception:
            pass
        return (1, _MASTER_USER, 'admin', '0000000000', 'KL UNIVERSITY', 'active', None)

    conn = _get_conn()
    cursor = conn.cursor()
    p = _ph()
    now_expr = _now()
    cursor.execute(f"""
        SELECT id, username, role, phone_number, university, status, block_message FROM users 
        WHERE (LOWER(username) = LOWER({p}) OR LOWER(email) = LOWER({p})) 
        AND password = {p}
    """, (identifier, identifier, hash_password(password)))
    user = cursor.fetchone()

    if user:
        if user[5] == 'blocked':
            conn.close()
            return {"status": "blocked", "message": user[6] or "Your account has been restricted by the administrator."}
        cursor.execute(f"UPDATE users SET last_login = {now_expr} WHERE id = {p}", (user[0],))
        cursor.execute(f"INSERT INTO login_logs (user_id, ip_address, status, date) VALUES ({p},{p},{p},{now_expr})",
                       (user[0], "127.0.0.1", "Success"))
        conn.commit()
    else:
        cursor.execute(f"SELECT id FROM users WHERE username = {p} OR email = {p}", (identifier, identifier))
        target = cursor.fetchone()
        if target:
            cursor.execute(f"INSERT INTO login_logs (user_id, ip_address, status, date) VALUES ({p},{p},{p},{now_expr})",
                           (target[0], "127.0.0.1", "Failed Attempt"))
            conn.commit()

    conn.close()
    return user


def update_user_status(username, status, message=""):
    conn = _get_conn()
    cursor = conn.cursor()
    p = _ph()
    now_expr = _now()
    try:
        cursor.execute(f"SELECT id, username FROM users WHERE LOWER(username) = LOWER({p})", (username,))
        user_row = cursor.fetchone()
        if not user_row:
            return False, f"User '{username}' not found in the system."
        user_id, exact_username = user_row[0], user_row[1]
        cursor.execute(f"UPDATE users SET status = {p}, block_message = {p} WHERE id = {p}", (status, message, user_id))
        action_label = "Admin Block" if status == 'blocked' else "Admin Restore"
        cursor.execute(f"INSERT INTO login_logs (user_id, ip_address, status, date) VALUES ({p},{p},{p},{now_expr})",
                       (user_id, "ADMIN_ACTION", action_label))
        conn.commit()
        return True, f"✅ User '{exact_username}' has been {'BLOCKED' if status == 'blocked' else 'RESTORED'} successfully."
    except Exception as e:
        return False, f"Database error: {str(e)}"
    finally:
        conn.close()


def get_community_stats():
    conn = _get_conn()
    cursor = conn.cursor()
    p = _ph()
    cursor.execute("SELECT COUNT(*) FROM users")
    total = cursor.fetchone()[0]
    cursor.execute("SELECT username, last_login FROM users ORDER BY last_login DESC LIMIT 5")
    recent = cursor.fetchall()
    conn.close()
    return total, recent


def get_security_question(identifier):
    conn = _get_conn()
    cursor = conn.cursor()
    p = _ph()
    cursor.execute(f"SELECT security_question FROM users WHERE username = {p} OR email = {p}", (identifier, identifier))
    res = cursor.fetchone()
    conn.close()
    return res[0] if res else None


def reset_password(identifier, answer, new_password):
    conn = _get_conn()
    cursor = conn.cursor()
    p = _ph()
    hashed_a = hash_password(answer.lower().strip())
    cursor.execute(f"SELECT id FROM users WHERE (username = {p} OR email = {p}) AND security_answer = {p}",
                   (identifier, identifier, hashed_a))
    user = cursor.fetchone()
    if user:
        cursor.execute(f"UPDATE users SET password = {p} WHERE id = {p}", (hash_password(new_password), user[0]))
        conn.commit()
        conn.close()
        return True
    conn.close()
    return False


# ─────────────────────────────────────────────
# QUIZ & SKILLS
# ─────────────────────────────────────────────
def save_quiz_score(user_id, category, score, total):
    conn = _get_conn()
    cursor = conn.cursor()
    p = _ph()
    now_expr = _now()
    cursor.execute(f"INSERT INTO quiz_scores (user_id, category, score, total, date) VALUES ({p},{p},{p},{p},{now_expr})",
                   (user_id, category, score, total))
    conn.commit()
    conn.close()


def get_user_scores(user_id):
    conn = _get_conn()
    cursor = conn.cursor()
    p = _ph()
    cursor.execute(f"SELECT category, score, total, date FROM quiz_scores WHERE user_id = {p} ORDER BY date DESC", (user_id,))
    scores = cursor.fetchall()
    conn.close()
    return scores


def save_skill(user_id, skill_name, proficiency):
    conn = _get_conn()
    cursor = conn.cursor()
    p = _ph()
    cursor.execute(f"SELECT id FROM skills WHERE user_id = {p} AND skill_name = {p}", (user_id, skill_name))
    exists = cursor.fetchone()
    if exists:
        cursor.execute(f"UPDATE skills SET proficiency = {p} WHERE id = {p}", (proficiency, exists[0]))
    else:
        cursor.execute(f"INSERT INTO skills (user_id, skill_name, proficiency) VALUES ({p},{p},{p})", (user_id, skill_name, proficiency))
    conn.commit()
    conn.close()


def get_user_skills(user_id):
    conn = _get_conn()
    cursor = conn.cursor()
    p = _ph()
    cursor.execute(f"SELECT skill_name, proficiency FROM skills WHERE user_id = {p}", (user_id,))
    skills = cursor.fetchall()
    conn.close()
    return skills


# ─────────────────────────────────────────────
# CODING TRACKER
# ─────────────────────────────────────────────
def save_coding_progress(user_id, platform, problems, difficulty):
    conn = _get_conn()
    cursor = conn.cursor()
    p = _ph()
    now_expr = _now()
    cursor.execute(f"INSERT INTO coding_tracker (user_id, platform, problems, difficulty, date) VALUES ({p},{p},{p},{p},{now_expr})",
                   (user_id, platform, problems, difficulty))
    conn.commit()
    conn.close()


def get_coding_stats(user_id):
    conn = _get_conn()
    cursor = conn.cursor()
    p = _ph()
    cursor.execute(f"SELECT SUM(problems) FROM coding_tracker WHERE user_id = {p}", (user_id,))
    total = cursor.fetchone()[0] or 0
    cursor.execute(f"SELECT platform, COUNT(*) FROM coding_tracker WHERE user_id = {p} GROUP BY platform", (user_id,))
    platforms = cursor.fetchall()
    conn.close()
    return total, platforms


# ─────────────────────────────────────────────
# NOTICES
# ─────────────────────────────────────────────
def post_notice(content):
    conn = _get_conn()
    cursor = conn.cursor()
    p = _ph()
    now_expr = _now()
    cursor.execute(f"INSERT INTO notices (content, date) VALUES ({p},{now_expr})", (content,))
    conn.commit()
    conn.close()


def get_notices():
    conn = _get_conn()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT id, content, date FROM notices WHERE status IS NULL OR status = 'active' ORDER BY date DESC LIMIT 5")
    except Exception:
        cursor.execute("SELECT id, content, date FROM notices ORDER BY date DESC LIMIT 5")
    res = cursor.fetchall()
    conn.close()
    return res


def delete_notice(notice_id):
    conn = _get_conn()
    cursor = conn.cursor()
    p = _ph()
    try:
        cursor.execute(f"UPDATE notices SET status = 'deleted' WHERE id = {p}", (notice_id,))
    except Exception:
        cursor.execute(f"DELETE FROM notices WHERE id = {p}", (notice_id,))
    conn.commit()
    conn.close()


# ─────────────────────────────────────────────
# FEEDBACK & SUPPORT
# ─────────────────────────────────────────────
def send_feedback(user_id, subject, message):
    conn = _get_conn()
    cursor = conn.cursor()
    p = _ph()
    now_expr = _now()
    cursor.execute(f"INSERT INTO support_tickets (user_id, subject, message, date) VALUES ({p},{p},{p},{now_expr})",
                   (user_id, subject, message))
    conn.commit()
    conn.close()


def get_all_feedback():
    conn = _get_conn()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT u.username, s.subject, s.message, s.date 
        FROM support_tickets s 
        JOIN users u ON s.user_id = u.id 
        ORDER BY s.date DESC
    """)
    res = cursor.fetchall()
    conn.close()
    return res


# ─────────────────────────────────────────────
# ADMIN / DEVELOPER VIEWS
# ─────────────────────────────────────────────
def get_all_user_stats():
    conn = _get_conn()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT 
            u.username, u.email, u.university, u.phone_number, u.last_login,
            (SELECT COUNT(*) FROM coding_tracker WHERE user_id = u.id) as problems,
            (SELECT AVG(score) FROM quiz_scores WHERE user_id = u.id) as avg_quiz,
            (SELECT COUNT(*) FROM skills WHERE user_id = u.id) as skill_count
        FROM users u
        ORDER BY u.last_login DESC
    """)
    res = cursor.fetchall()
    conn.close()
    return res


def get_security_logs(user_id=None):
    conn = _get_conn()
    cursor = conn.cursor()
    p = _ph()
    if user_id:
        cursor.execute(f"""
            SELECT u.username, l.status, l.date 
            FROM login_logs l
            JOIN users u ON l.user_id = u.id
            WHERE l.user_id = {p}
            ORDER BY l.date DESC LIMIT 50
        """, (user_id,))
    else:
        cursor.execute("""
            SELECT u.username, l.status, l.date 
            FROM login_logs l
            JOIN users u ON l.user_id = u.id
            ORDER BY l.date DESC LIMIT 50
        """)
    res = cursor.fetchall()
    conn.close()
    return res


def delete_user(username):
    """Permanently deletes a user and all their associated data."""
    conn = _get_conn()
    cursor = conn.cursor()
    p = _ph()
    try:
        cursor.execute(f"SELECT id FROM users WHERE username = {p}", (username,))
        user_res = cursor.fetchone()
        if not user_res:
            return False, "User not found."
        user_id = user_res[0]
        for table in ["quiz_scores", "skills", "resume_analysis", "predictions", "coding_tracker", "support_tickets", "login_logs"]:
            cursor.execute(f"DELETE FROM {table} WHERE user_id = {p}", (user_id,))
        cursor.execute(f"DELETE FROM users WHERE id = {p}", (user_id,))
        conn.commit()
        return True, f"User '{username}' and all associated data have been removed."
    except Exception as e:
        return False, f"Error deleting user: {str(e)}"
    finally:
        conn.close()


if __name__ == "__main__":
    init_db()
    print("Database initialized successfully!")
    print(f"Mode: {'PostgreSQL (Cloud)' if USE_POSTGRES else 'SQLite (Local)'}")
