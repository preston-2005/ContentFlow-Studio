import mysql.connector
import os
from dotenv import load_dotenv

# Load settings from .env
load_dotenv()

def setup_mysql_database():
    """
    Connects to the MySQL server and ensures the ContentFlow database 
    and required tables exist.
    """
    host = os.getenv("MYSQL_HOST")
    user = os.getenv("MYSQL_USER")
    password = os.getenv("MYSQL_PASSWORD")
    db_name = os.getenv("MYSQL_DB")

    print(f"🔗 Connecting to MySQL server at {host}...")
    
    try:
        # Connect without a specific DB first to create it
        conn = mysql.connector.connect(
            host=host,
            user=user,
            password=password
        )
        cursor = conn.cursor()

        # 1. Create the database
        print(f"📂 Ensuring database '{db_name}' exists...")
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {db_name}")
        
        # 2. Switch to the database
        cursor.execute(f"USE {db_name}")

        # 3. Create the users table
        print("🏗️ Ensuring 'users' table is initialized...")
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INT AUTO_INCREMENT PRIMARY KEY,
                username VARCHAR(255) UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
        print("\n✨ --- SETUP SUCCESSFUL ---")
        print(f"Your MySQL environment is ready. You can now run 'python app/main.py'")
        print("and use the 'Register New Agency' button to add your logins!")
        
    except mysql.connector.Error as err:
        print(f"\n❌ MYSQL ERROR: {err}")
        print("Please check your .env file credentials and ensure MySQL is running.")

if __name__ == "__main__":
    setup_mysql_database()
