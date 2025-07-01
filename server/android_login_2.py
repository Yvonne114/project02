
import psycopg2
import sys

try:
    app = psycopg2.connect(
        host="localhost",
        port="5433",  # PostgreSQL 預設 port
        user="postgres",  # 你的 PostgreSQL 使用者
        password="1111",  # 請替換成你的密碼
        database="app"
    )
except Exception as e:
    sys.exit(f"Error connecting to the database. Please check your inputs. Details: {e}")

db_cursor = app.cursor()

# login Table
try:
    db_cursor.execute("""
        CREATE TABLE IF NOT EXISTS login (
            id SERIAL PRIMARY KEY,
            first_name VARCHAR(50) NOT NULL,
            last_name VARCHAR(50) NOT NULL,
            username VARCHAR(50) NOT NULL UNIQUE,
            password VARCHAR(50) NOT NULL,
            registration_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)
    app.commit()
    print("login table created successfully.")
except psycopg2.DatabaseError as e:
    app.rollback()
    sys.exit(f"Error creating the table: {e}")

# Describe table (PostgreSQL 沒有 DESCRIBE，要改用 information_schema 或 cursor.description)
try:
    db_cursor.execute("SELECT column_name, data_type FROM information_schema.columns WHERE table_name = 'login'")
    records = db_cursor.fetchall()
    for record in records:
        print(record)
except Exception as e:
    print(f"Error describing table: {e}")
