from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import sqlite3, os, json
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from functools import wraps

app = Flask(__name__)
app.secret_key = 'gaurav_portfolio_secret_2026'

# /tmp is the only writable directory on Vercel serverless
import tempfile
DB_PATH = os.path.join(tempfile.gettempdir(), 'portfolio.db')
UPLOAD_FOLDER = os.path.join(tempfile.gettempdir(), 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

def allowed_file(f):
    return '.' in f and f.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    c = conn.cursor()

    c.execute('''CREATE TABLE IF NOT EXISTS admin (id INTEGER PRIMARY KEY, username TEXT, password TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS profile (
        id INTEGER PRIMARY KEY,
        name TEXT, headline TEXT, bio TEXT, tagline TEXT,
        location TEXT, email TEXT, phone TEXT,
        linkedin TEXT, github TEXT, kaggle TEXT, resume_link TEXT,
        photo TEXT, years_exp TEXT, projects_count TEXT, certs_count TEXT, domain TEXT
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS projects (
        id INTEGER PRIMARY KEY, title TEXT, description TEXT,
        details TEXT, tools TEXT, github_link TEXT, kaggle_link TEXT,
        demo_link TEXT, status TEXT, emoji TEXT, sort_order INTEGER
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS skills (
        id INTEGER PRIMARY KEY, category TEXT, name TEXT, level INTEGER, badge_color TEXT, sort_order INTEGER
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS certifications (
        id INTEGER PRIMARY KEY, name TEXT, issuer TEXT, year TEXT, credential_id TEXT, link TEXT, sort_order INTEGER
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS education (
        id INTEGER PRIMARY KEY, degree TEXT, institution TEXT, year TEXT, description TEXT, sort_order INTEGER
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS timeline (
        id INTEGER PRIMARY KEY, year TEXT, title TEXT, description TEXT, sort_order INTEGER
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT)''')

    # Seed admin
    if not c.execute('SELECT * FROM admin').fetchone():
        c.execute('INSERT INTO admin VALUES (1,?,?)', ('gaurav', generate_password_hash('admin123')))

    # Seed profile
    if not c.execute('SELECT * FROM profile').fetchone():
        c.execute('''INSERT INTO profile VALUES (1,
            "Gaurav Govind Nikam",
            "Aspiring Data Analyst · E-commerce Analytics",
            "I turn raw e-commerce data into decisions that actually move business metrics. From SQL queries to Power BI dashboards — I build the full picture.",
            "Building in public. Every day. No shortcuts.",
            "Pune, Maharashtra 🇮🇳",
            "gauravnikam072@gmail.com",
            "+918669212675",
            "https://www.linkedin.com/in/gaurav-nikam-44842a345",
            "https://github.com/gauravnikam777-vision",
            "https://www.kaggle.com/gnikam9211",
            "",
            "",
            "1+", "5+", "14+", "E-commerce"
        )''')

    # Seed projects
    if not c.execute('SELECT * FROM projects').fetchone():
        projects = [
            ("SuperStore Power BI Sales Forecast", "Power BI dashboard with 20-day sales forecasting using the SuperStore dataset", "Built interactive dashboard with sales trends, regional breakdown, category performance. Implemented 20-day forecast using Power BI built-in forecasting.", "Power BI, DAX", "https://github.com/gauravnikam777-vision/SuperStore-PowerBI-Sales-Forecast", "", "", "Completed", "⚡", 1),
            ("Diabetes Prediction App", "Streamlit web app for diabetes prediction using XGBoost", "End-to-end ML project: data cleaning → model training → deployed web app accessible to anyone.", "Python, XGBoost, Streamlit, pandas", "https://github.com/gauravnikam777-vision/diabetes-prediction-app", "", "", "Completed", "🩺", 2),
            ("Customer Churn Prediction", "Predicting customer churn using classification models", "Analyzed customer behavior data, engineered features, trained and evaluated multiple ML models to identify at-risk customers.", "Python, pandas, scikit-learn", "https://github.com/gauravnikam777-vision/customer-churn-prediction", "", "", "Completed", "📉", 3),
            ("Trader Behavior Insights", "Analysis of trader behavior patterns from financial market data", "Deep EDA on trader activity — identified patterns, peak trading windows, and behavioral clusters.", "Python, pandas, Matplotlib", "https://github.com/gauravnikam777-vision/Trader-Behavior-Insights", "https://www.kaggle.com/gnikam9211", "", "Completed", "📊", 4),
        ]
        c.executemany('INSERT INTO projects (title,description,details,tools,github_link,kaggle_link,demo_link,status,emoji,sort_order) VALUES (?,?,?,?,?,?,?,?,?,?)', projects)

    # Seed skills
    if not c.execute('SELECT * FROM skills').fetchone():
        skills = [
            ("Languages", "Python", 75, "#00d4ff", 1),
            ("Languages", "SQL", 60, "#00d4ff", 2),
            ("Libraries", "Pandas", 75, "#7c3aed", 3),
            ("Libraries", "NumPy", 70, "#7c3aed", 4),
            ("Visualization", "Power BI", 70, "#00ffcc", 5),
            ("Visualization", "Tableau", 45, "#00ffcc", 6),
            ("Visualization", "Matplotlib", 65, "#00ffcc", 7),
            ("Tools", "Excel", 75, "#f59e0b", 8),
            ("Tools", "Git / GitHub", 65, "#f59e0b", 9),
        ]
        c.executemany('INSERT INTO skills (category,name,level,badge_color,sort_order) VALUES (?,?,?,?,?)', skills)

    # Seed certs
    if not c.execute('SELECT * FROM certifications').fetchone():
        certs = [
            ("Artificial Intelligence: Concepts & Techniques", "NPTEL", "Oct 2025", "NPTEL25CS159S1166901114", "", 1),
            ("Machine Learning with Python", "Anaconda", "Nov 2025", "", "", 2),
            ("Machine Learning Statistical Foundations", "Wolfram Research", "Nov 2025", "", "", 3),
            ("Microsoft Azure AI Essentials", "Microsoft", "Nov 2025", "", "", 4),
            ("Azure Data Engineer Associate (DP-203) Prep", "LinkedIn / Microsoft Press", "Nov 2025", "", "", 5),
            ("Introduction to Large Language Models", "Google", "Jul 2025", "16967960", "", 6),
            ("Introduction to Generative AI", "Google", "Jul 2025", "16967919", "", 7),
            ("British Airways Data Science Simulation", "Forage", "Jun 2025", "ayhErmMB4ZoGw5cfw", "", 8),
            ("Deloitte Australia Data Analytics Simulation", "Forage", "Jun 2025", "o6DpBJWwJJ9Ck2jFS", "", 9),
            ("Python 101 for Data Science", "IBM", "Jun 2025", "0706eed25698439f91b15f0ff6225c55", "", 10),
            ("Data Science Tools", "IBM", "Jun 2025", "0f383339f5584305a3029d3e448ff9a9", "", 11),
            ("Data Science 101", "IBM", "Jun 2025", "56b724315fae4df2b26ddbbc55afd628", "", 12),
            ("Python Programming and SQL", "ExcelR", "Oct 2022", "", "", 13),
            ("Advanced Excel, PowerPoint & Word", "ExcelR", "Nov 2022", "", "", 14),
        ]
        c.executemany('INSERT INTO certifications (name,issuer,year,credential_id,link,sort_order) VALUES (?,?,?,?,?,?)', certs)

    # Seed education
    if not c.execute('SELECT * FROM education').fetchone():
        edu = [
            ("MCA — Master of Computer Applications", "Pursuing · Pune, Maharashtra", "2024 – Present", "Specializing in data systems, analytics, and software engineering.", 1),
            ("BBA-CA — Bachelor of Business Administration (Computer Applications)", "Completed · Pune, Maharashtra", "2021 – 2024", "Foundation in business analytics, database management, and computing.", 2),
        ]
        c.executemany('INSERT INTO education (degree,institution,year,description,sort_order) VALUES (?,?,?,?,?)', edu)

    conn.commit()
    conn.close()

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'admin' not in session:
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return decorated

# ── PUBLIC ──────────────────────────────────────────────
@app.route('/')
def index():
    db = get_db()
    profile = db.execute('SELECT * FROM profile').fetchone()
    projects = db.execute('SELECT * FROM projects ORDER BY sort_order').fetchall()
    skills = db.execute('SELECT * FROM skills ORDER BY sort_order').fetchall()
    certs = db.execute('SELECT * FROM certifications ORDER BY sort_order').fetchall()
    education = db.execute('SELECT * FROM education ORDER BY sort_order').fetchall()
    db.close()

    skill_cats = {}
    for s in skills:
        skill_cats.setdefault(s['category'], []).append(s)

    return render_template('index.html', profile=profile, projects=projects,
                           skill_cats=skill_cats, certs=certs, education=education)

# ── ADMIN LOGIN ──────────────────────────────────────────
@app.route('/admin/login', methods=['GET','POST'])
def admin_login():
    error = None
    if request.method == 'POST':
        db = get_db()
        admin = db.execute('SELECT * FROM admin WHERE username=?', (request.form['username'],)).fetchone()
        db.close()
        if admin and check_password_hash(admin['password'], request.form['password']):
            session['admin'] = True
            return redirect(url_for('admin_dashboard'))
        error = 'Invalid credentials'
    return render_template('admin_login.html', error=error)

@app.route('/admin/logout')
def admin_logout():
    session.pop('admin', None)
    return redirect(url_for('index'))

# ── ADMIN DASHBOARD ──────────────────────────────────────
@app.route('/admin')
@login_required
def admin_dashboard():
    db = get_db()
    profile = db.execute('SELECT * FROM profile').fetchone()
    projects = db.execute('SELECT * FROM projects ORDER BY sort_order').fetchall()
    skills = db.execute('SELECT * FROM skills ORDER BY sort_order').fetchall()
    certs = db.execute('SELECT * FROM certifications ORDER BY sort_order').fetchall()
    education = db.execute('SELECT * FROM education ORDER BY sort_order').fetchall()
    db.close()
    return render_template('admin.html', profile=profile, projects=projects,
                           skills=skills, certs=certs, education=education)

# ── ADMIN: PROFILE ───────────────────────────────────────
@app.route('/admin/profile', methods=['POST'])
@login_required
def update_profile():
    f = request.form
    db = get_db()
    photo = db.execute('SELECT photo FROM profile').fetchone()['photo']
    if 'photo' in request.files:
        file = request.files['photo']
        if file and allowed_file(file.filename):
            fname = secure_filename(file.filename)
            save_path = os.path.join(app.config['UPLOAD_FOLDER'], fname)
            file.save(save_path)
            photo = '/static/uploads/' + fname
    db.execute('''UPDATE profile SET name=?,headline=?,bio=?,tagline=?,location=?,email=?,phone=?,
                  linkedin=?,github=?,kaggle=?,resume_link=?,photo=?,
                  years_exp=?,projects_count=?,certs_count=?,domain=? WHERE id=1''',
               (f['name'],f['headline'],f['bio'],f['tagline'],f['location'],f['email'],f['phone'],
                f['linkedin'],f['github'],f['kaggle'],f.get('resume_link',''),photo,
                f['years_exp'],f['projects_count'],f['certs_count'],f['domain']))
    db.commit(); db.close()
    return redirect(url_for('admin_dashboard') + '#profile')

# ── ADMIN: PROJECTS ──────────────────────────────────────
@app.route('/admin/project/add', methods=['POST'])
@login_required
def add_project():
    f = request.form
    db = get_db()
    db.execute('INSERT INTO projects (title,description,details,tools,github_link,kaggle_link,demo_link,status,emoji,sort_order) VALUES (?,?,?,?,?,?,?,?,?,?)',
               (f['title'],f['description'],f['details'],f['tools'],f.get('github_link',''),f.get('kaggle_link',''),f.get('demo_link',''),f['status'],f.get('emoji','📊'),
                int(db.execute('SELECT COUNT(*) FROM projects').fetchone()[0])+1))
    db.commit(); db.close()
    return redirect(url_for('admin_dashboard') + '#projects')

@app.route('/admin/project/edit/<int:pid>', methods=['POST'])
@login_required
def edit_project(pid):
    f = request.form
    db = get_db()
    db.execute('UPDATE projects SET title=?,description=?,details=?,tools=?,github_link=?,kaggle_link=?,demo_link=?,status=?,emoji=? WHERE id=?',
               (f['title'],f['description'],f['details'],f['tools'],f.get('github_link',''),f.get('kaggle_link',''),f.get('demo_link',''),f['status'],f.get('emoji','📊'),pid))
    db.commit(); db.close()
    return redirect(url_for('admin_dashboard') + '#projects')

@app.route('/admin/project/delete/<int:pid>')
@login_required
def delete_project(pid):
    db = get_db()
    db.execute('DELETE FROM projects WHERE id=?', (pid,))
    db.commit(); db.close()
    return redirect(url_for('admin_dashboard') + '#projects')

# ── ADMIN: SKILLS ────────────────────────────────────────
@app.route('/admin/skill/add', methods=['POST'])
@login_required
def add_skill():
    f = request.form
    db = get_db()
    db.execute('INSERT INTO skills (category,name,level,badge_color,sort_order) VALUES (?,?,?,?,?)',
               (f['category'],f['name'],int(f['level']),f.get('badge_color','#00d4ff'),
                int(db.execute('SELECT COUNT(*) FROM skills').fetchone()[0])+1))
    db.commit(); db.close()
    return redirect(url_for('admin_dashboard') + '#skills')

@app.route('/admin/skill/delete/<int:sid>')
@login_required
def delete_skill(sid):
    db = get_db()
    db.execute('DELETE FROM skills WHERE id=?', (sid,))
    db.commit(); db.close()
    return redirect(url_for('admin_dashboard') + '#skills')

# ── ADMIN: CERTS ─────────────────────────────────────────
@app.route('/admin/cert/add', methods=['POST'])
@login_required
def add_cert():
    f = request.form
    db = get_db()
    db.execute('INSERT INTO certifications (name,issuer,year,credential_id,link,sort_order) VALUES (?,?,?,?,?,?)',
               (f['name'],f['issuer'],f['year'],f.get('credential_id',''),f.get('link',''),
                int(db.execute('SELECT COUNT(*) FROM certifications').fetchone()[0])+1))
    db.commit(); db.close()
    return redirect(url_for('admin_dashboard') + '#certs')

@app.route('/admin/cert/delete/<int:cid>')
@login_required
def delete_cert(cid):
    db = get_db()
    db.execute('DELETE FROM certifications WHERE id=?', (cid,))
    db.commit(); db.close()
    return redirect(url_for('admin_dashboard') + '#certs')

# ── ADMIN: EDUCATION ─────────────────────────────────────
@app.route('/admin/edu/add', methods=['POST'])
@login_required
def add_edu():
    f = request.form
    db = get_db()
    db.execute('INSERT INTO education (degree,institution,year,description,sort_order) VALUES (?,?,?,?,?)',
               (f['degree'],f['institution'],f['year'],f.get('description',''),
                int(db.execute('SELECT COUNT(*) FROM education').fetchone()[0])+1))
    db.commit(); db.close()
    return redirect(url_for('admin_dashboard') + '#education')

@app.route('/admin/edu/delete/<int:eid>')
@login_required
def delete_edu(eid):
    db = get_db()
    db.execute('DELETE FROM education WHERE id=?', (eid,))
    db.commit(); db.close()
    return redirect(url_for('admin_dashboard') + '#education')

# ── ADMIN: CHANGE PASSWORD ───────────────────────────────
@app.route('/admin/password', methods=['POST'])
@login_required
def change_password():
    f = request.form
    db = get_db()
    admin = db.execute('SELECT * FROM admin WHERE id=1').fetchone()
    if check_password_hash(admin['password'], f['current']):
        db.execute('UPDATE admin SET password=? WHERE id=1', (generate_password_hash(f['new']),))
        db.commit()
    db.close()
    return redirect(url_for('admin_dashboard'))

# This runs on every cold start in Vercel serverless
try:
    init_db()
except Exception as e:
    print(f"init_db error: {e}")

if __name__ == '__main__':
    init_db()
    app.run(debug=True)
