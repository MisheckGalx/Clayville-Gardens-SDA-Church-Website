from flask import Flask, render_template, request, redirect, url_for, flash, send_from_directory
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.utils import secure_filename
from database import init_db
from models import User, Event, Sermon
import os

app = Flask(__name__)
app.secret_key = 'clayville-sda-secret-key-change-this-in-production'

# File upload configuration
UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg', 'gif', 'webp'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max

# Create upload folder if it doesn't exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

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
    """Add new event with file uploads"""
    title = request.form.get('title')
    date = request.form.get('date')
    description = request.form.get('description')
    image_url = request.form.get('image_url', '')
    
    # Handle image upload
    if 'image_file' in request.files:
        file = request.files['image_file']
        if file and file.filename and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            # Add timestamp to avoid conflicts
            import time
            timestamp = str(int(time.time()))
            name, ext = os.path.splitext(filename)
            filename = f"{name}_{timestamp}{ext}"
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            image_url = f'/static/uploads/{filename}'
    
    # Handle PDF upload
    pdf_url = None
    if 'pdf_file' in request.files:
        file = request.files['pdf_file']
        if file and file.filename and file.filename.endswith('.pdf'):
            filename = secure_filename(file.filename)
            # Add timestamp
            import time
            timestamp = str(int(time.time()))
            name, ext = os.path.splitext(filename)
            filename = f"{name}_{timestamp}{ext}"
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            pdf_url = f'/static/uploads/{filename}'
    
    Event.create(title, date, description, image_url, pdf_url)
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

if __name__ == '__main__':
    print("\n" + "="*60)
    print("CLAYVILLE GARDENS SDA CHURCH WEBSITE")
    print("="*60)
    init_db()
    print("\nStarting server at http://localhost:5000")
    print("\nADMIN LOGIN:")
    print("  URL: http://localhost:5000/admin")
    print("  Username: admin")
    print("  Password: Clayville007")
    print("\nPress CTRL+C to stop the server")
    print("="*60 + "\n")
    
    app.run(debug=True, port=5000)
