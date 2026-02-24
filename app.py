from flask import Flask, render_template, request, redirect, url_for, flash, send_from_directory
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from database import init_db
from models import User, Event, Sermon
import os

app = Flask(__name__)
app.secret_key = 'clayville-sda-secret-key-change-this-in-production'

# Serve static files
@app.route('/static/<path:filename>')
def serve_static(filename):
    return send_from_directory('static', filename)

# Flask-Login setup
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'admin_login'

@login_manager.user_loader
def load_user(user_id):
    return User.get(user_id)

# Public routes
@app.route('/')
def home():
    """Home page with hero slider and featured content"""
    events = Event.get_recent(3)
    sermons = Sermon.get_recent(3)
    return render_template('home.html', events=events, sermons=sermons)

@app.route('/about')
def about():
    """About page"""
    return render_template('about.html')

@app.route('/services')
def services():
    """Services page"""
    return render_template('services.html')

@app.route('/events')
def events():
    """Events page"""
    all_events = Event.get_all()
    return render_template('events.html', events=all_events)

@app.route('/sermons')
def sermons():
    """Sermons page"""
    all_sermons = Sermon.get_all()
    return render_template('sermons.html', sermons=all_sermons)

@app.route('/contact')
def contact():
    """Contact page"""
    return render_template('contact.html')

@app.route('/gallery')
def gallery():
    """Photo gallery page"""
    # List of photos with captions and dates
    photos = [
        {'url': '/static/gallery/photo1.jpg', 'caption': 'Church Fellowship', 'date': 'January 2024'},
        {'url': '/static/gallery/photo2.jpg', 'caption': 'Youth Ministry', 'date': 'January 2024'},
        {'url': '/static/gallery/photo3.jpg', 'caption': 'Community Service', 'date': 'December 2023'},
        {'url': '/static/gallery/photo4.jpg', 'caption': 'Worship Service', 'date': 'December 2023'},
        {'url': '/static/gallery/photo5.jpg', 'caption': 'Sabbath School', 'date': 'November 2023'},
        {'url': '/static/gallery/photo6.jpg', 'caption': 'Prayer Meeting', 'date': 'November 2023'},
        {'url': '/static/gallery/photo7.jpg', 'caption': 'Church Event', 'date': 'October 2023'},
        {'url': '/static/gallery/photo8.jpg', 'caption': 'Fellowship Meal', 'date': 'October 2023'},
        {'url': '/static/gallery/photo9.jpg', 'caption': 'Baptism Ceremony', 'date': 'September 2023'},
        {'url': '/static/gallery/photo10.jpg', 'caption': 'Pathfinder Club', 'date': 'September 2023'},
        {'url': '/static/gallery/photo11.jpg', 'caption': 'Community Outreach', 'date': 'August 2023'},
        {'url': '/static/gallery/photo12.jpg', 'caption': 'Church Anniversary', 'date': 'August 2023'},
        {'url': '/static/gallery/photo13.jpg', 'caption': 'Bible Study', 'date': 'July 2023'},
        {'url': '/static/gallery/photo14.jpg', 'caption': 'Youth Camp', 'date': 'July 2023'},
        {'url': '/static/gallery/photo15.jpg', 'caption': 'Adventurer Club', 'date': 'June 2023'},
        {'url': '/static/gallery/photo16.jpg', 'caption': 'Church Family', 'date': 'June 2023'},
        {'url': '/static/gallery/photo17.jpg', 'caption': 'Evangelism', 'date': 'May 2023'},
        {'url': '/static/gallery/photo18.jpg', 'caption': 'Special Event', 'date': 'May 2023'},
        # Add more photos here as you upload them
    ]
    return render_template('gallery.html', photos=photos)

# Admin routes
@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    """Admin login page"""
    if current_user.is_authenticated:
        return redirect(url_for('admin_dashboard'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = User.authenticate(username, password)
        if user:
            login_user(user)
            flash('Login successful!', 'success')
            return redirect(url_for('admin_dashboard'))
        else:
            flash('Invalid username or password', 'error')
    
    return render_template('admin_login.html')

@app.route('/admin')
@login_required
def admin_dashboard():
    """Admin dashboard"""
    events = Event.get_all()
    sermons = Sermon.get_all()
    return render_template('admin_dashboard.html', events=events, sermons=sermons)

@app.route('/admin/logout')
@login_required
def admin_logout():
    """Logout admin"""
    logout_user()
    flash('Logged out successfully', 'success')
    return redirect(url_for('home'))

@app.route('/admin/add-event', methods=['POST'])
@login_required
def add_event():
    """Add new event"""
    title = request.form.get('title')
    date = request.form.get('date')
    description = request.form.get('description')
    image_url = request.form.get('image_url', '')
    
    Event.create(title, date, description, image_url)
    flash('Event added successfully!', 'success')
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/delete-event/<int:event_id>', methods=['POST'])
@login_required
def delete_event(event_id):
    """Delete event"""
    Event.delete(event_id)
    flash('Event deleted successfully!', 'success')
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/add-sermon', methods=['POST'])
@login_required
def add_sermon():
    """Add new sermon"""
    title = request.form.get('title')
    preacher = request.form.get('preacher')
    date = request.form.get('date')
    youtube_url = request.form.get('youtube_url', '')
    description = request.form.get('description')
    
    Sermon.create(title, preacher, date, youtube_url, description)
    flash('Sermon added successfully!', 'success')
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/delete-sermon/<int:sermon_id>', methods=['POST'])
@login_required
def delete_sermon(sermon_id):
    """Delete sermon"""
    Sermon.delete(sermon_id)
    flash('Sermon deleted successfully!', 'success')
    return redirect(url_for('admin_dashboard'))

# Main entry point
if __name__ == '__main__':
    # Initialize database
    init_db()
    
    # Check if running on Render (production) or locally (development)
    if os.environ.get('RENDER'):
        # Production mode on Render
        app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 10000)))
    else:
        # Development mode (local)
        print("\n" + "="*60)
        print("CLAYVILLE GARDENS SDA CHURCH WEBSITE")
        print("="*60)
        print("\nStarting server at http://localhost:5000")
        print("\nADMIN LOGIN:")
        print("  URL: http://localhost:5000/admin")
        print("  Username: admin")
        print("  Password: Clayville007")
        print("\nPress CTRL+C to stop the server")
        print("="*60 + "\n")
        app.run(debug=True, port=5000)
