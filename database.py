import sqlite3

def init_db():
    """Initialize the database with tables and sample data"""
    conn = sqlite3.connect('clayville.db')
    c = conn.cursor()
    
    # Create events table WITH PDF SUPPORT
    c.execute('''CREATE TABLE IF NOT EXISTS events
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  title TEXT NOT NULL,
                  date TEXT NOT NULL,
                  description TEXT,
                  image_url TEXT,
                  pdf_url TEXT,
                  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    
    # Create sermons table
    c.execute('''CREATE TABLE IF NOT EXISTS sermons
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  title TEXT NOT NULL,
                  preacher TEXT NOT NULL,
                  date TEXT NOT NULL,
                  youtube_url TEXT,
                  description TEXT,
                  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    
    # Create users table
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  username TEXT UNIQUE NOT NULL,
                  password_hash TEXT NOT NULL)''')
    
    # Check if admin user exists
    c.execute("SELECT * FROM users WHERE username='admin'")
    if not c.fetchone():
        from werkzeug.security import generate_password_hash
        password_hash = generate_password_hash('Clayville007')
        c.execute("INSERT INTO users (username, password_hash) VALUES (?, ?)", 
                 ('admin', password_hash))
        print("✓ Admin user created (username: admin, password: Clayville007)")
    
    # Check if pdf_url column exists, if not add it
    c.execute("PRAGMA table_info(events)")
    columns = [column[1] for column in c.fetchall()]
    if 'pdf_url' not in columns:
        c.execute('ALTER TABLE events ADD COLUMN pdf_url TEXT')
        print("✓ Added pdf_url column to events table")
    
    # Insert sample events if table is empty
    c.execute("SELECT COUNT(*) FROM events")
    if c.fetchone()[0] == 0:
        sample_events = [
            
        ]
        c.executemany("INSERT INTO events (title, date, description, image_url, pdf_url) VALUES (?, ?, ?, ?, ?)", 
                     sample_events)
        print(f"✓ Added {len(sample_events)} sample events")
    
    # Insert sample sermons if table is empty
    c.execute("SELECT COUNT(*) FROM sermons")
    if c.fetchone()[0] == 0:
        sample_sermons = [
            ('In Crisis, Keep God First', 'Pastor Randy Skeete', '2024-01-06',
             'https://www.youtube.com/embed/O55TNDg4AU4',
             'A powerful message about keeping God first in every storm of life.'),
        ]
        c.executemany("INSERT INTO sermons (title, preacher, date, youtube_url, description) VALUES (?, ?, ?, ?, ?)",
                     sample_sermons)
        print(f"✓ Added {len(sample_sermons)} sample sermons")
    
    conn.commit()
    conn.close()
    print("✓ Database initialized successfully")

def get_db():
    """Get database connection"""
    conn = sqlite3.connect('clayville.db')
    conn.row_factory = sqlite3.Row
    return conn

if __name__ == '__main__':
    init_db()
