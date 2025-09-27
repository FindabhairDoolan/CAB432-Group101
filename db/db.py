import os, time, sys
import mariadb

DB_HOST = os.environ.get("DB_HOST", "db")
DB_USER = os.environ.get("DB_USER", "user")
DB_PASSWORD = os.environ.get("DB_PASSWORD", "pass")
DB_NAME = os.environ.get("DB_NAME", "videodb")
DB_PORT = int(os.environ.get("DB_PORT", 3306))

def get_connection(retries=12, wait=3):
    attempt = 0
    while True:
        try:
            conn = mariadb.connect(
                host=DB_HOST,
                user=DB_USER,
                password=DB_PASSWORD,
                database=DB_NAME,
                port=DB_PORT
            )
            return conn
        except mariadb.Error as e:
            attempt += 1
            if attempt >= retries:
                print(f"DB connection failed after {attempt} tries: {e}")
                sys.exit(1)
            print(f"DB not ready yet ({e}), waiting {wait}s... (attempt {attempt}/{retries})")
            time.sleep(wait)

def init_db():
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS files (
              id INT PRIMARY KEY AUTO_INCREMENT,
              filename VARCHAR(255) NOT NULL,
              storage_path VARCHAR(1024) NOT NULL,
              size BIGINT,
              uploaded_by VARCHAR(255),
              created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
              id INT PRIMARY KEY AUTO_INCREMENT,
              file_id INT NOT NULL,
              preset VARCHAR(64),
              status VARCHAR(32),
              output_path VARCHAR(1024),
              error TEXT,
              started_at TIMESTAMP NULL,
              finished_at TIMESTAMP NULL,
              FOREIGN KEY (file_id) REFERENCES files(id) ON DELETE CASCADE
            );
        """)
        conn.commit()
        print("DB initialized (tables ensured).")
    except Exception as e:
        print("DB init failed:", e)
    finally:
        cur.close()
        conn.close()


# initialize on import
init_db()
