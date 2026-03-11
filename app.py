from flask import Flask, render_template, request, redirect, url_for, flash, send_from_directory
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from database import init_db
from models import User, Event, Sermon
import os
import re
import uuid
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = 'clayville-sda-secret-key-change-this-in-production'

# ── Upload configuration ──────────────────────────────────────────────────────
UPLOAD_FOLDER = os.path.join('static', 'uploads')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp', 'pdf'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16 MB max

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def convert_youtube_url(url):
    """
    Convert any YouTube URL format to the embeddable format.
    Handles:
      https://www.youtube.com/watch?v=VIDEO_ID
      https://youtu.be/VIDEO_ID
      https://www.youtube.com/embed/VIDEO_ID  (already correct)
    """
    if not url:
        return ''
    # Already an embed URL
    if 'youtube.com/embed/' in url:
        return url
    # youtu.be/VIDEO_ID
    match = re.search(r'youtu\.be/([a-zA-Z0-9_-]{11})', url)
    if match:
        return f'https://www.youtube.com/embed/{match.group(1)}'
    # youtube.com/watch?v=VIDEO_ID
    match = re.search(r'youtube\.com/watch\?.*v=([a-zA-Z0-9_-]{11})', url)
    if match:
        return f'https://www.youtube.com/embed/{match.group(1)}'
    # Return as-is if we can't parse it
    return url

# ── Flask-Login setup ─────────────────────────────────────────────────────────
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'admin_login'

@login_manager.user_loader
def load_user(user_id):
    return User.get(user_id)

# ── Static files ──────────────────────────────────────────────────────────────
@app.route('/static/<path:filename>')
def serve_static(filename):
    return send_from_directory('static', filename)

# ── Public routes ─────────────────────────────────────────────────────────────
@app.route('/')
def home():
    events = Event.get_recent(3)
    sermons = Sermon.get_recent(3)
    return render_template('home.html', events=events, sermons=sermons)

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/services')
def services():
    return render_template('services.html')

@app.route('/events')
def events():
    all_events = Event.get_all()
    return render_template('events.html', events=all_events)

@app.route('/sermons')
def sermons():
    all_sermons = Sermon.get_all()
    return render_template('sermons.html', sermons=all_sermons)

@app.route('/contact')
def contact():
    return render_template('contact.html')

@app.route('/gallery')
def gallery():
    photos = [
        {'url': '/static/gallery/photo1.jpg'},
        {'url': '/static/gallery/photo2.jpg'},
        {'url': '/static/gallery/photo3.jpg'},
        {'url': '/static/gallery/photo4.jpg'},
        {'url': '/static/gallery/photo5.jpg'},
        {'url': '/static/gallery/photo6.jpg'},
        {'url': '/static/gallery/photo7.jpg'},
        {'url': '/static/gallery/photo8.jpg'},
        {'url': '/static/gallery/photo9.jpg'},
        {'url': '/static/gallery/photo10.jpg'},
        {'url': '/static/gallery/photo11.jpg'},
        {'url': '/static/gallery/photo12.jpg'},
        {'url': '/static/gallery/photo13.jpg'},
        {'url': '/static/gallery/photo14.jpg'},
        {'url': '/static/gallery/photo15.jpg'},
        {'url': '/static/gallery/photo16.jpg'},
        {'url': '/static/gallery/photo17.jpg'},
        {'url': '/static/gallery/photo18.jpg'},
    ]
    return render_template('gallery.html', photos=photos)

# ── Admin routes ──────────────────────────────────────────────────────────────
@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
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
    events = Event.get_all()
    sermons = Sermon.get_all()
    return render_template('admin_dashboard.html', events=events, sermons=sermons)

@app.route('/admin/logout')
@login_required
def admin_logout():
    logout_user()
    flash('Logged out successfully', 'success')
    return redirect(url_for('home'))

@app.route('/admin/add-event', methods=['POST'])
@login_required
def add_event():
    """Add new event — supports image or PDF upload, or a pasted URL."""
    title       = request.form.get('title')
    date        = request.form.get('date')
    description = request.form.get('description')
    image_url   = request.form.get('image_url', '').strip()

    # Uploaded file takes priority over a pasted URL
    uploaded = request.files.get('event_file')
    if uploaded and uploaded.filename and allowed_file(uploaded.filename):
        ext       = uploaded.filename.rsplit('.', 1)[1].lower()
        safe_name = str(uuid.uuid4()) + '.' + ext
        save_path = os.path.join(app.config['UPLOAD_FOLDER'], safe_name)
        uploaded.save(save_path)
        image_url = '/static/uploads/' + safe_name

    # Event.create expects exactly 4 args: title, date, description, image_url
    Event.create(title, date, description, image_url)
    flash('Event added successfully!', 'success')
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/delete-event/<int:event_id>', methods=['POST'])
@login_required
def delete_event(event_id):
    Event.delete(event_id)
    flash('Event deleted successfully!', 'success')
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/add-sermon', methods=['POST'])
@login_required
def add_sermon():
    title       = request.form.get('title')
    preacher    = request.form.get('preacher')
    date        = request.form.get('date')
    youtube_url = convert_youtube_url(request.form.get('youtube_url', '').strip())
    description = request.form.get('description')
    Sermon.create(title, preacher, date, youtube_url, description)
    flash('Sermon added successfully!', 'success')
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/delete-sermon/<int:sermon_id>', methods=['POST'])
@login_required
def delete_sermon(sermon_id):
    Sermon.delete(sermon_id)
    flash('Sermon deleted successfully!', 'success')
    return redirect(url_for('admin_dashboard'))

# ── Entry point ───────────────────────────────────────────────────────────────
if __name__ == '__main__':
    init_db()
    if os.environ.get('RENDER'):
        app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 10000)))
    else:
        print("\n" + "=" * 60)
        print("CLAYVILLE GARDENS SDA CHURCH WEBSITE")
        print("=" * 60)
        print("\nStarting server at http://localhost:5000")
        print("\nADMIN LOGIN:")
        print("  URL: http://localhost:5000/admin")
        print("  Username: admin")
        print("  Password: Clayville007")
        print("\nPress CTRL+C to stop the server")
        print("=" * 60 + "\n")
        app.run(debug=True, port=5000)
