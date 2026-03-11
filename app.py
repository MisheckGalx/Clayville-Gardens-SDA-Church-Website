from flask import Flask, render_template, request, redirect, url_for, flash, send_from_directory, Response
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from database import init_db
from models import User, Event, Sermon
import os
import re
import uuid
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = 'clayville-sda-secret-key-change-this-in-production'

# ── Upload config ─────────────────────────────────────────────────────────────
UPLOAD_FOLDER = os.path.join('static', 'uploads')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp', 'pdf'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16 MB

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def convert_youtube_url(url):
    """Convert any YouTube URL format to embed URL."""
    if not url:
        return ''
    if 'youtube.com/embed/' in url:
        return url
    m = re.search(r'youtu\.be/([a-zA-Z0-9_-]{11})', url)
    if m:
        return 'https://www.youtube.com/embed/' + m.group(1)
    m = re.search(r'youtube\.com/watch\?.*v=([a-zA-Z0-9_-]{11})', url)
    if m:
        return 'https://www.youtube.com/embed/' + m.group(1)
    return url

# ── Flask-Login ───────────────────────────────────────────────────────────────
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'admin_login'

@login_manager.user_loader
def load_user(user_id):
    return User.get(user_id)

# ── PWA files served from ROOT (required for full-site scope) ─────────────────
@app.route('/sw.js')
def service_worker():
    """Service worker MUST be at root to control the entire site."""
    response = send_from_directory('static', 'sw.js')
    response.headers['Content-Type'] = 'application/javascript'
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Service-Worker-Allowed'] = '/'
    return response

@app.route('/manifest.json')
def manifest():
    """Web app manifest served from root."""
    response = send_from_directory('static', 'manifest.json')
    response.headers['Content-Type'] = 'application/manifest+json'
    return response

# ── Static files (handles subdirs like /static/uploads/) ─────────────────────
@app.route('/static/<path:filename>')
def serve_static(filename):
    return send_from_directory('static', filename)

# ── PWA offline fallback page ─────────────────────────────────────────────────
@app.route('/offline')
def offline():
    return render_template('offline.html')

# ── Public routes ─────────────────────────────────────────────────────────────
@app.route('/')
def home():
    events  = Event.get_recent(3)
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
    return render_template('events.html', events=Event.get_all())

@app.route('/sermons')
def sermons():
    return render_template('sermons.html', sermons=Sermon.get_all())

@app.route('/contact')
def contact():
    return render_template('contact.html')

@app.route('/gallery')
def gallery():
    photos = [{'url': f'/static/gallery/photo{i}.jpg'} for i in range(1, 19)]
    return render_template('gallery.html', photos=photos)

# ── Admin routes ──────────────────────────────────────────────────────────────
@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if current_user.is_authenticated:
        return redirect(url_for('admin_dashboard'))
    if request.method == 'POST':
        user = User.authenticate(request.form.get('username'), request.form.get('password'))
        if user:
            login_user(user)
            flash('Login successful!', 'success')
            return redirect(url_for('admin_dashboard'))
        flash('Invalid username or password', 'error')
    return render_template('admin_login.html')

@app.route('/admin')
@login_required
def admin_dashboard():
    return render_template('admin_dashboard.html', events=Event.get_all(), sermons=Sermon.get_all())

@app.route('/admin/logout')
@login_required
def admin_logout():
    logout_user()
    flash('Logged out successfully', 'success')
    return redirect(url_for('home'))

@app.route('/admin/add-event', methods=['POST'])
@login_required
def add_event():
    title       = request.form.get('title')
    date        = request.form.get('date')
    description = request.form.get('description')
    image_url   = request.form.get('image_url', '').strip()

    uploaded = request.files.get('event_file')
    if uploaded and uploaded.filename and allowed_file(uploaded.filename):
        ext       = uploaded.filename.rsplit('.', 1)[1].lower()
        safe_name = str(uuid.uuid4()) + '.' + ext
        uploaded.save(os.path.join(app.config['UPLOAD_FOLDER'], safe_name))
        image_url = '/static/uploads/' + safe_name

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
    Sermon.create(
        request.form.get('title'),
        request.form.get('preacher'),
        request.form.get('date'),
        convert_youtube_url(request.form.get('youtube_url', '').strip()),
        request.form.get('description')
    )
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
        print("\n  Local:  http://localhost:5000")
        print("  Admin:  http://localhost:5000/admin")
        print("  User:   admin  |  Pass: Clayville007")
        print("\n  PWA:    Visit the site in Chrome, then look")
        print("          for the Install banner at the bottom!")
        print("=" * 60 + "\n")
        app.run(debug=True, port=5000)
