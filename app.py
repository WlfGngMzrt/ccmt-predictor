import os
import logging
import pandas as pd
from flask import Flask, render_template, request, redirect, url_for, session

from authlib.integrations.flask_client import OAuth

app = Flask(__name__)

# --- CONFIGURATION ---
# Uses Render Environment Variables for security
app.secret_key = os.environ.get("FLASK_SECRET", "syandan_mvp_2026")
DATA_DIR = 'data'

# --- LOGGING SETUP (For your Mac Analytics) ---
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

# --- REFINED SPECIALIZATION MAPPING ---
def get_precision_info(program_name):
    p = program_name.lower()
    
    # ECE / VLSI / EMBEDDED POOL
    if 'vlsi' in p and 'embedded' in p: return "VLSI & Embedded Systems", "EC, EE, IN", "#E0E7FF", "#4338CA"
    elif 'vlsi' in p: return "VLSI Design", "EC, EE", "#E0F2FE", "#0369A1"
    elif 'embedded' in p: return "Embedded Systems", "EC, IN", "#F0F9FF", "#075985"
    elif 'microelectron' in p: return "Microelectronics", "EC, EE", "#DBEAFE", "#1E40AF"
    
    # ECE / COMMUNICATIONS
    elif 'microwave' in p or 'rf' in p: return "RF & Microwave Engineering", "EC", "#D1FAE5", "#065F46"
    elif 'communication' in p and 'signal' in p: return "Signal Processing & Comm", "EC", "#ECFDF5", "#047857"
    elif 'communication' in p: return "Communication Systems", "EC", "#F0FDF4", "#166534"
    
    # CSE / AI / DATA SCIENCE (The Splitting Logic)
    elif ('artificial' in p or ' ai ' in p) and ('data science' in p or 'analytics' in p): return "AI & Data Science", "CS", "#F3E8FF", "#6B21A8"
    elif 'artificial' in p or ' ai ' in p: return "Artificial Intelligence", "CS", "#FAF5FF", "#7E22CE"
    elif 'data science' in p or 'analytics' in p: return "Data Science", "CS", "#F5F3FF", "#5B21B6"
    elif 'cyber' in p or 'security' in p: return "Cyber Security", "CS", "#FDF2F8", "#9D174D"
    
    # EE / ME / IN
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
    logging.info(f"LOGIN_SUCCESS: {session['user']['email']}")
    return redirect(url_for('index'))

@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('index'))

# --- MAIN PREDICTOR ROUTE ---
@app.route('/', methods=['GET', 'POST'])
def index():
    # THE GATEKEEPER: Forces login
    if 'user' not in session:
        return render_template('login.html')

    years = sorted([f.replace('.csv', '') for f in os.listdir(DATA_DIR) if f.endswith('.csv')], reverse=True)
    results, user_score = None, None
    selected_year, selected_cat, selected_branch, selected_spec = None, "OPEN", "ECE", "ALL"

    if request.method == 'POST':
        try:
            user_score = int(request.form.get('gate_score'))
            selected_year = request.form.get('year')
            selected_cat = request.form.get('category')
            selected_branch = request.form.get('qualifying_branch')
            selected_spec = request.form.get('specialization')

            # ANALYTICS LOGGING: Track what scores people are checking
            logging.info(f"PREDICT_QUERY: User={session['user']['email']} | Score={user_score} | Branch={selected_branch}")

            df = pd.read_csv(os.path.join(DATA_DIR, f"{selected_year}.csv"))
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
                        # CHANCE LOGIC
                        diff = user_score - row['Min GATE Score']
                        chance = "Level 4: Very High" if diff >= 50 else "Level 3: High" if diff >= 20 else "Level 2: Moderate" if diff >= 5 else "Level 1: Borderline"
                        color = "#10b981" if diff >= 50 else "#34d399" if diff >= 20 else "#fbbf24" if diff >= 5 else "#f87171"
                        
                        item = row.to_dict()
                        item.update({'spec': spec_name, 'codes': codes, 'bg': bg, 'text_clr': text_clr, 'chance': chance, 'chance_color': color})
                        res_list.append(item)
            
            # SORTING: Ambitious (Highest Cutoff) First
            results = sorted(res_list, key=lambda x: x['Min GATE Score'], reverse=True)
            
        except Exception as e:
            logging.error(f"RUNTIME_ERROR: {e}")

    return render_template('index.html', years=years, results=results, user_score=user_score, 
                           category=selected_cat, selected_year=selected_year, 
                           selected_branch=selected_branch, selected_spec=selected_spec, 
                           branch_map=BRANCH_MAP, user=session['user'])

if __name__ == '__main__':
    # Flask app start logic
    port = int(os.environ.get("PORT", 5001))
    app.run(host='0.0.0.0', port=port)