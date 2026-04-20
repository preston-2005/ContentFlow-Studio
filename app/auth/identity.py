import sqlite3
import mysql.connector
from mysql.connector import errorcode
import bcrypt
import os
from dotenv import load_dotenv

load_dotenv()

DB_PATH = os.path.join("export", "contentflow_db.sqlite")

def get_db_connection():
    """
    Returns a database connection. 
    Prioritizes MySQL if credentials exist in .env, else falls back to local SQLite.
    """
    mysql_host = os.getenv("MYSQL_HOST")
    mysql_user = os.getenv("MYSQL_USER")
    mysql_pass = os.getenv("MYSQL_PASSWORD")
    mysql_db = os.getenv("MYSQL_DB")

    if all([mysql_host, mysql_user, mysql_pass, mysql_db]) and mysql_pass != "your_password_here":
        try:
            conn = mysql.connector.connect(
                host=mysql_host,
                user=mysql_user,
                password=mysql_pass,
                database=mysql_db
            )
            return conn, "MYSQL"
        except mysql.connector.Error as err:
            print(f"[AUTH] MySQL Connection Error: {err}. Falling back to SQLite...")
    
    # Fallback to SQLite
    os.makedirs("export", exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    return conn, "SQLITE"

def init_db():
    conn, db_type = get_db_connection()
    cursor = conn.cursor()
    
    if db_type == "MYSQL":
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INT AUTO_INCREMENT PRIMARY KEY,
                username VARCHAR(255) UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
    else:
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
    
    conn.commit()
    conn.close()
    print(f"[AUTH] Identity Vault Initialized ({db_type})")

def create_user(username, plain_password):
    init_db()
    conn, db_type = get_db_connection()
    cursor = conn.cursor()
    
    hashed = bcrypt.hashpw(plain_password.encode(), bcrypt.gensalt()).decode()
    
    query = "INSERT INTO users (username, password_hash) VALUES (%s, %s)" if db_type == "MYSQL" else "INSERT INTO users (username, password_hash) VALUES (?, ?)"
    
    try:
        cursor.execute(query, (username, hashed))
        conn.commit()
        success = True
    except (sqlite3.IntegrityError, mysql.connector.IntegrityError):
        success = False # Username likely exists
    except Exception as e:
        print(f"[AUTH] Error creating user: {e}")
        success = False
        
    conn.close()
    return success

def verify_login(username, input_password):
    conn, db_type = get_db_connection()
    cursor = conn.cursor()
    
    query = "SELECT password_hash FROM users WHERE username = %s" if db_type == "MYSQL" else "SELECT password_hash FROM users WHERE username = ?"
    
    cursor.execute(query, (username,))
    result = cursor.fetchone()
    conn.close()
    
    if not result:
        return False
        
    return bcrypt.checkpw(input_password.encode(), result[0].encode())

# Auto-initialize the default admin if it doesn't exist
def ensure_default_admin():
    init_db()
    conn, db_type = get_db_connection()
    cursor = conn.cursor()
    query = "SELECT id FROM users WHERE username = %s" if db_type == "MYSQL" else "SELECT id FROM users WHERE username = 'admin'"
    if db_type == "MYSQL":
        cursor.execute(query, ('admin',))
    else:
        cursor.execute(query)
        
    if not cursor.fetchone():
        print("[AUTH] Creating default 'admin' account...")
        create_user("admin", "contentflow2026")
    conn.close()

if __name__ == "__main__":
    ensure_default_admin()
