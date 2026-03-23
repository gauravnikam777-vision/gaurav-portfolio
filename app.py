from flask import Flask, render_template, jsonify, request
import sqlite3, os
from functools import wraps

from github_sync import fetch_github_profile, merge_projects, invalidate_cache

app = Flask(__name__)
app.secret_key = 'gaurav_portfolio_secret_2026'

import tempfile
DB_PATH = os.path.join(tempfile.gettempdir(), 'portfolio.db')

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    c = conn.cursor()

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

    if not c.execute('SELECT * FROM projects').fetchone():
        projects = [
            ("SuperStore Power BI Sales Forecast", "Power BI dashboard with 20-day sales forecasting using the SuperStore dataset", "Built interactive dashboard with sales trends, regional breakdown, category performance.", "Power BI, DAX", "https://github.com/gauravnikam777-vision/SuperStore-PowerBI-Sales-Forecast", "", "", "Completed", "⚡", 1),
            ("Diabetes Prediction App", "Streamlit web app for diabetes prediction using XGBoost", "End-to-end ML project: data cleaning → model training → deployed web app.", "Python, XGBoost, Streamlit, pandas", "https://github.com/gauravnikam777-vision/diabetes-prediction-app", "", "https://diabetes-prediction-app-pro.streamlit.app/", "Completed", "🩺", 2),
            ("Customer Churn Prediction", "Predicting customer churn using classification models", "Analyzed customer behavior data, engineered features, trained ML models to identify at-risk customers.", "Python, pandas, scikit-learn", "https://github.com/gauravnikam777-vision/customer-churn-prediction", "", "https://customer-churn-prediction-7dmchid9v9vkkyigyn3ivc.streamlit.app/", "Completed", "📉", 3),
            ("Trader Behavior Insights", "Analysis of trader behavior patterns from financial market data", "Deep EDA on trader activity — identified patterns, peak trading windows, and behavioral clusters.", "Python, pandas, Matplotlib", "https://github.com/gauravnikam777-vision/Trader-Behavior-Insights", "https://www.kaggle.com/gnikam9211", "", "Completed", "📊", 4),
        ]
        c.executemany('INSERT INTO projects (title,description,details,tools,github_link,kaggle_link,demo_link,status,emoji,sort_order) VALUES (?,?,?,?,?,?,?,?,?,?)', projects)

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

    if not c.execute('SELECT * FROM education').fetchone():
        edu = [
            ("MCA — Master of Computer Applications", "Pursuing · Pune, Maharashtra", "2024 – Present", "Specializing in data systems, analytics, and software engineering.", 1),
            ("BBA-CA — Bachelor of Business Administration (Computer Applications)", "Completed · Pune, Maharashtra", "2021 – 2024", "Foundation in business analytics, database management, and computing.", 2),
        ]
        c.executemany('INSERT INTO education (degree,institution,year,description,sort_order) VALUES (?,?,?,?,?)', edu)

    conn.commit()
    conn.close()


# ── PUBLIC PORTFOLIO ──────────────────────────────────────────────
@app.route('/')
def index():
    db = get_db()
    profile_row = db.execute('SELECT * FROM profile').fetchone()
    db_projects = db.execute('SELECT * FROM projects ORDER BY sort_order').fetchall()
    skills      = db.execute('SELECT * FROM skills ORDER BY sort_order').fetchall()
    certs       = db.execute('SELECT * FROM certifications ORDER BY sort_order').fetchall()
    education   = db.execute('SELECT * FROM education ORDER BY sort_order').fetchall()
    db.close()

    # GitHub sync — merge repos + get live avatar
    projects = merge_projects(db_projects)
    gh       = fetch_github_profile()

    profile = dict(profile_row)
    if not profile.get("photo") and gh.get("avatar_url"):
        profile["photo"] = gh["avatar_url"]
    profile["gh_followers"] = gh.get("followers", 0)
    profile["gh_repos"]     = gh.get("repo_count", 0)

    skill_cats = {}
    for s in skills:
        skill_cats.setdefault(s['category'], []).append(s)

    return render_template('index.html',
        profile=profile,
        projects=projects,
        skill_cats=skill_cats,
        certs=certs,
        education=education
    )


# ── GITHUB WEBHOOK — instant cache refresh on push ───────────────
@app.route('/webhook/github', methods=['POST'])
def github_webhook():
    invalidate_cache()
    return jsonify({"status": "ok"}), 200


# ── MANUAL REFRESH ────────────────────────────────────────────────
@app.route('/refresh')
def manual_refresh():
    invalidate_cache()
    return jsonify({"status": "refreshed"})


# ── DEBUG — see live data ─────────────────────────────────────────
@app.route('/api/projects')
def api_projects():
    db = get_db()
    db_projects = db.execute('SELECT * FROM projects ORDER BY sort_order').fetchall()
    db.close()
    return jsonify(merge_projects(db_projects))


try:
    init_db()
except Exception as e:
    print(f"init_db error: {e}")

if __name__ == '__main__':
    init_db()
    app.run(debug=True)
