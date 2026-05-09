import sqlite3
import hashlib
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "placementor.db")

# Secure Salt for Hashing (In a real app, keep this in environment variables)
SALT = "KLU_PLACEMENTOR_SECURE_2026"

def init_db():
    """Initializes the SQLite database and creates necessary tables."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Users Table
    cursor.execute('''
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
            university TEXT
        )
    ''')
    
    # Ensure columns exist in case table was created before
    cols_to_add = ["security_question", "security_answer", "phone_number", "university"]
    for col in cols_to_add:
        try:
            cursor.execute(f"ALTER TABLE users ADD COLUMN {col} TEXT")
            conn.commit()
        except:
            pass
    
    # Ensure last_login exists in case table was created before
    try:
        cursor.execute("ALTER TABLE users ADD COLUMN last_login TIMESTAMP")
        cursor.execute("UPDATE users SET last_login = CURRENT_TIMESTAMP")
    except:
        pass

    # Quiz Scores Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS quiz_scores (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            category TEXT,
            score INTEGER,
            total INTEGER,
            date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')

    # Skills Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS skills (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            skill_name TEXT,
            proficiency INTEGER,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')

    # Resume Analysis Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS resume_analysis (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            ats_score INTEGER,
            missing_skills TEXT,
            extracted_text TEXT,
            date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')

    # Placement Predictions Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS predictions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            probability REAL,
            result INTEGER,
            date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')

    # Coding Tracker Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS coding_tracker (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            platform TEXT,
            problems INTEGER,
            difficulty TEXT,
            date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')

    # Notices Table (Admin Updates)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS notices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            content TEXT,
            date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Support Tickets Table (Feedback to Dev)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS support_tickets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            subject TEXT,
            message TEXT,
            date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')

    # Login Activity Logs
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS login_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            ip_address TEXT,
            status TEXT,
            date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')

    conn.commit()
    conn.close()

def hash_password(password):
    """Secure Salted SHA-256 Hashing."""
    salted_password = password + SALT
    return hashlib.sha256(salted_password.encode()).hexdigest()

def register_user(username, email, password, university=None, security_q=None, security_a=None, phone=None, role='student'):
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        # Hash security answer for privacy
        hashed_a = hash_password(security_a.lower().strip()) if security_a else None
        cursor.execute("INSERT INTO users (username, email, password, university, security_question, security_answer, phone_number, role, last_login) VALUES (?, ?, ?, ?, ?, ?, ?, ?, datetime('now', '+5 hours', '+30 minutes'))",
                       (username, email, hash_password(password), university, security_q, hashed_a, phone, role))
        conn.commit()
        conn.close()
        return True
    except sqlite3.IntegrityError:
        return False

def login_user(identifier, password):
    """Allows login using either username or email."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, username, role, phone_number, university FROM users 
        WHERE (LOWER(username) = LOWER(?) OR LOWER(email) = LOWER(?)) 
        AND password = ?
    """, (identifier, identifier, hash_password(password)))
    user = cursor.fetchone()
    
    if user:
        # Update last login timestamp in IST
        cursor.execute("UPDATE users SET last_login = datetime('now', '+5 hours', '+30 minutes') WHERE id = ?", (user[0],))
        # Log successful login in IST
        cursor.execute("INSERT INTO login_logs (user_id, ip_address, status, date) VALUES (?, ?, ?, datetime('now', '+5 hours', '+30 minutes'))", 
                       (user[0], "127.0.0.1", "Success"))
        conn.commit()
    else:
        # Log failed attempt if user exists in IST
        cursor.execute("SELECT id FROM users WHERE username = ? OR email = ?", (identifier, identifier))
        target = cursor.fetchone()
        if target:
            cursor.execute("INSERT INTO login_logs (user_id, ip_address, status, date) VALUES (?, ?, ?, datetime('now', '+5 hours', '+30 minutes'))", 
                           (target[0], "127.0.0.1", "Failed Attempt"))
            conn.commit()
        
    conn.close()
    return user

def get_security_logs(user_id):
    """Fetches recent login activity for the user."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT ip_address, status, date FROM login_logs WHERE user_id = ? ORDER BY date DESC LIMIT 5", (user_id,))
    res = cursor.fetchall()
    conn.close()
    return res

def get_community_stats():
    """Returns total registered users and the 5 most recently active users."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM users")
    total = cursor.fetchone()[0]
    cursor.execute("SELECT username, last_login FROM users ORDER BY last_login DESC LIMIT 5")
    recent = cursor.fetchall()
    conn.close()
    return total, recent

def get_security_question(identifier):
    """Fetches the security question for a user."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT security_question FROM users WHERE username = ? OR email = ?", (identifier, identifier))
    res = cursor.fetchone()
    conn.close()
    return res[0] if res else None

def reset_password(identifier, answer, new_password):
    """Resets password if security answer matches."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    hashed_a = hash_password(answer.lower().strip())
    cursor.execute("SELECT id FROM users WHERE (username = ? OR email = ?) AND security_answer = ?", 
                   (identifier, identifier, hashed_a))
    user = cursor.fetchone()
    
    if user:
        cursor.execute("UPDATE users SET password = ? WHERE id = ?", (hash_password(new_password), user[0]))
        conn.commit()
        conn.close()
        return True
    conn.close()
    return False

def save_quiz_score(user_id, category, score, total):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO quiz_scores (user_id, category, score, total, date) VALUES (?, ?, ?, ?, datetime('now', '+5 hours', '+30 minutes'))",
                   (user_id, category, score, total))
    conn.commit()
    conn.close()

def get_user_scores(user_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT category, score, total, date FROM quiz_scores WHERE user_id = ? ORDER BY date DESC", (user_id,))
    scores = cursor.fetchall()
    conn.close()
    return scores

def save_skill(user_id, skill_name, proficiency):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    # Check if skill exists
    cursor.execute("SELECT id FROM skills WHERE user_id = ? AND skill_name = ?", (user_id, skill_name))
    exists = cursor.fetchone()
    if exists:
        cursor.execute("UPDATE skills SET proficiency = ? WHERE id = ?", (proficiency, exists[0]))
    else:
        cursor.execute("INSERT INTO skills (user_id, skill_name, proficiency) VALUES (?, ?, ?)", (user_id, skill_name, proficiency))
    conn.commit()
    conn.close()

def get_user_skills(user_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT skill_name, proficiency FROM skills WHERE user_id = ?", (user_id,))
    skills = cursor.fetchall()
    conn.close()
    return skills

def save_coding_progress(user_id, platform, problems, difficulty):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO coding_tracker (user_id, platform, problems, difficulty, date_solved) VALUES (?, ?, ?, ?, datetime('now', '+5 hours', '+30 minutes'))",
                   (user_id, platform, problems, difficulty))
    conn.commit()
    conn.close()

def get_coding_stats(user_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT SUM(problems) FROM coding_tracker WHERE user_id = ?", (user_id,))
    total = cursor.fetchone()[0] or 0
    cursor.execute("SELECT platform, COUNT(*) FROM coding_tracker WHERE user_id = ? GROUP BY platform", (user_id,))
    platforms = cursor.fetchall()
    conn.close()
    return total, platforms

# --- Real-time Updates & Support Functions ---

def post_notice(content):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO notices (content, date) VALUES (?, datetime('now', '+5 hours', '+30 minutes'))", (content,))
    conn.commit()
    conn.close()

def get_notices():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT id, content, date FROM notices ORDER BY date DESC LIMIT 5")
    res = cursor.fetchall()
    conn.close()
    return res

def delete_notice(notice_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM notices WHERE id = ?", (notice_id,))
    conn.commit()
    conn.close()

def send_feedback(user_id, subject, message):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO support_tickets (user_id, subject, message, date) VALUES (?, ?, ?, datetime('now', '+5 hours', '+30 minutes'))", (user_id, subject, message))
    conn.commit()
    conn.close()

def get_all_feedback():
    conn = sqlite3.connect(DB_PATH)
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

def get_all_user_stats():
    """Aggregates performance stats for all users for the developer dashboard."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    # Join users with counts from other tables
    query = """
        SELECT 
            u.username, 
            u.email, 
            u.last_login,
            (SELECT COUNT(*) FROM coding_tracker WHERE user_id = u.id) as problems,
            (SELECT AVG(score) FROM quiz_scores WHERE user_id = u.id) as avg_quiz,
            (SELECT COUNT(*) FROM skills WHERE user_id = u.id) as skill_count
        FROM users u
        ORDER BY u.last_login DESC
    """
    cursor.execute(query)
    res = cursor.fetchall()
    conn.close()
    return res

def get_security_logs(user_id=None):
    """Retrieves security logs. If user_id is provided, returns only their logs. Otherwise, returns all."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    if user_id:
        cursor.execute("""
            SELECT u.username, l.status, l.date 
            FROM login_logs l
            JOIN users u ON l.user_id = u.id
            WHERE l.user_id = ?
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

if __name__ == "__main__":
    init_db()
    print("Database initialized successfully!")
