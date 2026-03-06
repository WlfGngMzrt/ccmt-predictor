import os
import logging
import pandas as pd
from flask import Flask, render_template, request, redirect, url_for, session
from authlib.integrations.flask_client import OAuth

app = Flask(__name__)

# --- CONFIGURATION ---
app.secret_key = os.environ.get("FLASK_SECRET", "syandan_mvp_2026")
# Use absolute path for Data Directory to avoid Render pathing issues
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DATA_DIR = os.path.join(BASE_DIR, 'data')

# Ensure the data directory exists so the app doesn't crash on startup
if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)
    logging.warning(f"Data directory not found. Created: {DATA_DIR}")

# --- LOGGING SETUP ---
logging.basicConfig(level=logging.INFO)

# --- GOOGLE AUTH SETUP ---
oauth = OAuth(app)
google = oauth.register(
    name='google',
    client_id=os.environ.get("GOOGLE_CLIENT_ID"),
    client_secret=os.environ.get("GOOGLE_CLIENT_SECRET"),
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
    client_kwargs={'scope': 'openid email profile'}
)

# --- SPECIALIZATION MAPPING LOGIC ---
def get_precision_info(program_name):
    p = str(program_name).lower()
    if 'vlsi' in p and 'embedded' in p: return "VLSI & Embedded Systems", "EC, EE, IN", "#E0E7FF", "#4338CA"
    elif 'vlsi' in p: return "VLSI Design", "EC, EE", "#E0F2FE", "#0369A1"
    elif 'embedded' in p: return "Embedded Systems", "EC, IN", "#F0F9FF", "#075985"
    elif 'microelectron' in p: return "Microelectronics", "EC, EE", "#DBEAFE", "#1E40AF"
    elif 'microwave' in p or 'rf' in p: return "RF & Microwave Engineering", "EC", "#D1FAE5", "#065F46"
    elif 'communication' in p and 'signal' in p: return "Signal Processing & Comm", "EC", "#ECFDF5", "#047857"
    elif 'communication' in p: return "Communication Systems", "EC", "#F0FDF4", "#166534"
    elif ('artificial' in p or ' ai ' in p) and ('data science' in p or 'analytics' in p): return "AI & Data Science", "CS", "#F3E8FF", "#6B21A8"
    elif 'artificial' in p or ' ai ' in p: return "Artificial Intelligence", "CS", "#FAF5FF", "#7E22CE"
    elif 'data science' in p or 'analytics' in p: return "Data Science", "CS", "#F5F3FF", "#5B21B6"
    elif 'cyber' in p or 'security' in p: return "Cyber Security", "CS", "#FDF2F8", "#9D174D"
    elif 'electric vehicle' in p: return "Electric Vehicle Tech", "EE, ME", "#FEF3C7", "#92400E"
    elif 'power electronics' in p: return "Power Electronics & Drives", "EE", "#FFF7ED", "#9A3412"
    elif 'control' in p: return "Control & Automation", "EE, IN", "#F0FDFA", "#0F766E"
    return "Specialized Branch", "GEN", "#F9FAFB", "#374151"

BRANCH_MAP = {
    'ECE': ["VLSI & Embedded Systems", "VLSI Design", "Embedded Systems", "Microelectronics", "RF & Microwave Engineering", "Signal Processing & Comm", "Communication Systems"],
    'CSE': ["AI & Data Science", "Artificial Intelligence", "Data Science", "Cyber Security"],
    'EE':  ["Power Electronics & Drives", "Power Systems", "Electric Vehicle Tech", "Control & Automation", "VLSI Design"],
    'IN':  ["Control & Automation", "Embedded Systems", "Instrumentation Engineering"],
    'ALL': []
}

# --- AUTH ROUTES ---
@app.route('/login')
def login():
    redirect_uri = url_for('auth', _external=True)
    return google.authorize_redirect(redirect_uri)

@app.route('/auth')
def auth():
    token = google.authorize_access_token()
    session['user'] = token['userinfo']
    logging.info(f"LOGIN_SUCCESS: {session['user'].get('email')}")
    return redirect(url_for('index'))

@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('index'))

# --- MAIN PREDICTOR ROUTE ---
@app.route('/', methods=['GET', 'POST'])
def index():
    if 'user' not in session:
        return render_template('login.html')

    # Fail-safe year retrieval
    try:
        years = sorted([f.replace('.csv', '') for f in os.listdir(DATA_DIR) if f.endswith('.csv')], reverse=True)
    except Exception:
        years = []

    results, user_score = None, None
    selected_year = request.form.get('year') if request.form.get('year') else (years[0] if years else None)
    selected_cat, selected_branch, selected_spec = "OPEN", "ECE", "ALL"

    if request.method == 'POST' and selected_year:
        try:
            user_score = int(request.form.get('gate_score', 0))
            selected_cat = request.form.get('category', 'OPEN')
            selected_branch = request.form.get('qualifying_branch', 'ECE')
            selected_spec = request.form.get('specialization', 'ALL')

            csv_path = os.path.join(DATA_DIR, f"{selected_year}.csv")
            if os.path.exists(csv_path):
                df = pd.read_csv(csv_path)
                df.columns = [c.strip() for c in df.columns]
                df['Min GATE Score'] = pd.to_numeric(df['Min GATE Score'], errors='coerce')
                df = df.dropna(subset=['Min GATE Score'])

                mask = (df['Category'] == selected_cat) & (df['Min GATE Score'] <= user_score)
                filtered_df = df[mask].copy()

                res_list = []
                for _, row in filtered_df.iterrows():
                    spec_name, codes, bg, text_clr = get_precision_info(row['PG Program'])
                    if (spec_name in BRANCH_MAP.get(selected_branch, [])) or selected_branch == "ALL":
                        if selected_spec == "ALL" or spec_name == selected_spec:
                            diff = user_score - row['Min GATE Score']
                            chance = "Level 4: Very High" if diff >= 50 else "Level 3: High" if diff >= 20 else "Level 2: Moderate" if diff >= 5 else "Level 1: Borderline"
                            color = "#10b981" if diff >= 50 else "#34d399" if diff >= 20 else "#fbbf24" if diff >= 5 else "#f87171"
                            
                            item = row.to_dict()
                            item.update({'spec': spec_name, 'codes': codes, 'bg': bg, 'text_clr': text_clr, 'chance': chance, 'chance_color': color})
                            res_list.append(item)
                
                results = sorted(res_list, key=lambda x: x['Min GATE Score'], reverse=True)
        except Exception as e:
            logging.error(f"RUNTIME_ERROR: {e}")

    return render_template('index.html', years=years, results=results, user_score=user_score, 
                           category=selected_cat, selected_year=selected_year, 
                           selected_branch=selected_branch, selected_spec=selected_spec, 
                           branch_map=BRANCH_MAP, user=session.get('user'))

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5001))
    app.run(host='0.0.0.0', port=port)