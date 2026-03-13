from flask import Flask, render_template, request, redirect, url_for, flash, send_from_directory
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from database import init_db
from models import User, Event, Sermon
import os
import re
import uuid
from datetime import datetime, timedelta
from werkzeug.utils import secure_filename

try:
    import requests as http_requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False

app = Flask(__name__)
app.secret_key = 'clayville-sda-secret-key-change-this-in-production'

# ── Upload configuration ──────────────────────────────────────────────────────
UPLOAD_FOLDER = os.path.join('static', 'uploads')
GALLERY_FOLDER = os.path.join('static', 'gallery')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp', 'pdf'}
ALLOWED_IMAGE_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50 MB max

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(GALLERY_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def allowed_image(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_IMAGE_EXTENSIONS

def convert_youtube_url(url):
    """Convert any YouTube URL to embed format."""
    if not url:
        return ''
    if 'youtube.com/embed/' in url:
        return url
    match = re.search(r'youtu\.be/([a-zA-Z0-9_-]{11})', url)
    if match:
        return 'https://www.youtube.com/embed/' + match.group(1)
    match = re.search(r'youtube\.com/watch\?.*v=([a-zA-Z0-9_-]{11})', url)
    if match:
        return 'https://www.youtube.com/embed/' + match.group(1)
    return url

# ── Sabbath School Lesson — Adventech public API ──────────────────────────────
_lesson_cache = {'data': None, 'fetched': None}

def get_quarter_code(dt):
    """Return quarter string e.g. 2026-01, 2026-02, 2026-03, 2026-04."""
    q = (dt.month - 1) // 3 + 1
    return f"{dt.year}-{q:02d}"

def get_this_weeks_lesson():
    """Fetch and cache this week's Sabbath School lesson from Adventech API.
    Returns None silently if the API is unreachable — never breaks the page."""
    if not REQUESTS_AVAILABLE:
        return None

    now = datetime.now()

    # Return cached data if less than 12 hours old
    if _lesson_cache['data'] and _lesson_cache['fetched']:
        if now - _lesson_cache['fetched'] < timedelta(hours=12):
            return _lesson_cache['data']

    try:
        quarter = get_quarter_code(now)
        base    = 'https://sabbath-school.adventech.io/api/v1/en'

        # 1. Get all lessons for the quarter
        r = http_requests.get(f'{base}/quarterlies/{quarter}/lessons/index.json', timeout=6)
        r.raise_for_status()
        data = r.json()
        lessons = data if isinstance(data, list) else data.get('lessons', [])
        if not lessons:
            return None

        # 2. Find the lesson whose week contains today
        today   = now.date()
        current = None
        for lesson in lessons:
            try:
                start = datetime.strptime(lesson['start_date'], '%Y-%m-%d').date()
                end   = datetime.strptime(lesson['end_date'],   '%Y-%m-%d').date()
                if start <= today <= end:
                    current = lesson
                    break
            except Exception:
                continue
        if not current:
            current = lessons[-1]  # fallback: most recent lesson

        # 3. Enrich with quarterly cover + title
        qr = http_requests.get(f'{base}/quarterlies/{quarter}/index.json', timeout=6)
        if qr.status_code == 200:
            qdata = qr.json()
            current['quarterly_title'] = qdata.get('title', '')
            current['quarterly_cover'] = qdata.get('splash', qdata.get('cover', ''))
        else:
            current['quarterly_title'] = ''
            current['quarterly_cover'] = ''
        current['quarterly_id'] = quarter

        # 4. Build lesson URL — use sabbath.school which always works
        # lesson id from API is like "2026-01-01", "2026-01-02" etc.
        lesson_id = current.get('id', '')
        # Extract just the lesson number portion (last segment)
        lesson_num = lesson_id.split('-')[-1] if lesson_id else ''
        if lesson_num:
            current['adventech_url'] = 'https://www.sabbath.school/Lesson'
        else:
            current['adventech_url'] = 'https://www.sabbath.school/Lesson'

        # 5. Build day pills (Sun → Sat)
        day_names = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sab']
        current['day_pills'] = [
            {'short': day_names[i] if i < len(day_names) else f'Day {i+1}',
             'title': d.get('title', '')}
            for i, d in enumerate(current.get('days', [])[:7])
        ]

        _lesson_cache['data']    = current
        _lesson_cache['fetched'] = now
        return current

    except Exception as e:
        print(f'[Sabbath Lesson] API error: {e}')
        return _lesson_cache.get('data')  # return stale cache if available

# ── Template globals ──────────────────────────────────────────────────────────
@app.context_processor
def inject_globals():
    return {'now': datetime.now(), 'current_year': datetime.now().year}

# ── Flask-Login setup ─────────────────────────────────────────────────────────
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'admin_login'

@login_manager.user_loader
def load_user(user_id):
    return User.get(user_id)

# ── Static files (handles subdirectories like uploads/) ──────────────────────
@app.route('/static/<path:filename>')
def serve_static(filename):
    return send_from_directory('static', filename)

# ── Service worker MUST be served from root scope ─────────────────────────────
@app.route('/sw.js')
def service_worker():
    response = send_from_directory('static', 'sw.js')
    response.headers['Service-Worker-Allowed'] = '/'
    response.headers['Cache-Control'] = 'no-cache'
    return response

# ── PWA offline fallback ──────────────────────────────────────────────────────
@app.route('/offline')
def offline():
    return render_template('offline.html')

# ── Public routes ─────────────────────────────────────────────────────────────
@app.route('/')
def home():
    events  = Event.get_recent(3)
    sermons = Sermon.get_recent(3)
    lesson  = get_this_weeks_lesson()          # ← NEW: fetch this week's lesson
    return render_template('home.html', events=events, sermons=sermons, lesson=lesson)

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
    """Live gallery — reads all images from static/gallery/ folder automatically."""
    image_exts = {'.jpg', '.jpeg', '.png', '.gif', '.webp'}
    photos = []
    if os.path.exists(GALLERY_FOLDER):
        files = sorted(os.listdir(GALLERY_FOLDER))
        for filename in files:
            ext = os.path.splitext(filename)[1].lower()
            if ext in image_exts:
                photos.append({'url': '/static/gallery/' + filename})
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
    # Count gallery photos for dashboard info
    gallery_count = 0
    if os.path.exists(GALLERY_FOLDER):
        image_exts = {'.jpg', '.jpeg', '.png', '.gif', '.webp'}
        gallery_count = sum(
            1 for f in os.listdir(GALLERY_FOLDER)
            if os.path.splitext(f)[1].lower() in image_exts
        )
    # Build file list for gallery preview
    gallery_files = []
    if os.path.exists(GALLERY_FOLDER):
        image_exts = {'.jpg', '.jpeg', '.png', '.gif', '.webp'}
        gallery_files = sorted([f for f in os.listdir(GALLERY_FOLDER) if os.path.splitext(f)[1].lower() in image_exts])
        gallery_count = len(gallery_files)
    return render_template('admin_dashboard.html', events=events, sermons=sermons, gallery_count=gallery_count, gallery_files=gallery_files)

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

    uploaded = request.files.get('event_file')
    if uploaded and uploaded.filename and allowed_file(uploaded.filename):
        ext       = uploaded.filename.rsplit('.', 1)[1].lower()
        safe_name = str(uuid.uuid4()) + '.' + ext
        save_path = os.path.join(app.config['UPLOAD_FOLDER'], safe_name)
        uploaded.save(save_path)
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

@app.route('/admin/upload-gallery', methods=['POST'])
@login_required
def upload_gallery():
    """Upload one or more photos directly to the gallery folder."""
    files = request.files.getlist('gallery_photos')
    uploaded_count = 0
    for file in files:
        if file and file.filename and allowed_image(file.filename):
            ext       = file.filename.rsplit('.', 1)[1].lower()
            safe_name = str(uuid.uuid4()) + '.' + ext
            file.save(os.path.join(GALLERY_FOLDER, safe_name))
            uploaded_count += 1

    if uploaded_count:
        flash(f'{uploaded_count} photo(s) added to the gallery!', 'success')
    else:
        flash('No valid images were uploaded.', 'error')
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/delete-gallery/<filename>', methods=['POST'])
@login_required
def delete_gallery(filename):
    """Delete a photo from the gallery."""
    safe = secure_filename(filename)
    path = os.path.join(GALLERY_FOLDER, safe)
    if os.path.exists(path):
        os.remove(path)
        flash('Photo deleted from gallery.', 'success')
    else:
        flash('Photo not found.', 'error')
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
