import sqlite3

def init_db():
    """Initialize the database with tables and sample data"""
    conn = sqlite3.connect('clayville.db')
    c = conn.cursor()
    
    # Create events table
    c.execute('''CREATE TABLE IF NOT EXISTS events
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  title TEXT NOT NULL,
                  date TEXT NOT NULL,
                  description TEXT,
                  image_url TEXT,
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
    
    # Insert sample events if table is empty
    c.execute("SELECT COUNT(*) FROM events")
    if c.fetchone()[0] == 0:
        sample_events = [
            ('Youth Fellowship Night', '2024-02-15', 
             'Join us for an inspiring evening of worship, games, and fellowship with our youth community.',
             'https://images.unsplash.com/photo-1511632765486-a01980e01a18?w=800'),
            
            ('Community Food Drive', '2024-02-22', 
             'Serving our community with love. Bring non-perishable food items to support local families in need.',
             'https://images.unsplash.com/photo-1559027615-cd4628902d4a?w=800'),
            
            ('Midweek Prayer Meeting', '2024-02-28', 
             'Come together for prayer, worship, and Bible study. All are welcome to join us.',
             'https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=800'),
            
            ('Women\'s Ministry Brunch', '2024-03-05', 
             'Ladies, join us for a special morning of fellowship, inspiration, and delicious food.',
             'https://images.unsplash.com/photo-1517457373958-b7bdd4587205?w=800'),
            
            ('Family Fun Day', '2024-03-12', 
             'Bring the whole family for games, activities, food, and fun for all ages!',
             'https://images.unsplash.com/photo-1511895426328-dc8714191300?w=800'),
            
            ('Health & Wellness Seminar', '2024-03-19', 
             'Learn practical tips for healthy living from medical professionals in our community.',
             'https://images.unsplash.com/photo-1505751172876-fa1923c5c528?w=800')
        ]
        c.executemany("INSERT INTO events (title, date, description, image_url) VALUES (?, ?, ?, ?)", 
                     sample_events)
        print(f"✓ Added {len(sample_events)} sample events")
    
    # Insert sample sermons if table is empty
    c.execute("SELECT COUNT(*) FROM sermons")
    if c.fetchone()[0] == 0:
        sample_sermons = [
            ('The Power of Grace', 'Pastor John Smith', '2024-02-10',
             'https://www.youtube.com/embed/dQw4w9WgXcQ',
             'Understanding God\'s amazing grace and how it transforms our lives daily.'),
            
            ('Walking by Faith', 'Elder Mary Johnson', '2024-02-03',
             'https://www.youtube.com/embed/dQw4w9WgXcQ',
             'Living a life of faith and complete trust in God\'s promises.'),
            
            ('Hope for Tomorrow', 'Pastor David Lee', '2024-01-27',
             'https://www.youtube.com/embed/dQw4w9WgXcQ',
             'Finding hope and assurance in Christ\'s soon return.'),
            
            ('Love in Action', 'Pastor John Smith', '2024-01-20',
             'https://www.youtube.com/embed/dQw4w9WgXcQ',
             'Practical ways to show Christ\'s love in our daily interactions.'),
            
            ('The Sabbath Rest', 'Elder Sarah Williams', '2024-01-13',
             'https://www.youtube.com/embed/dQw4w9WgXcQ',
             'Discovering the blessing and peace of God\'s holy Sabbath day.'),
            
            ('Prayer That Moves Mountains', 'Pastor David Lee', '2024-01-06',
             'https://www.youtube.com/embed/dQw4w9WgXcQ',
             'Unlocking the power of effectual, fervent prayer in our lives.')
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
