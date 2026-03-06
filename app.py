import os
import pandas as pd
from flask import Flask, render_template, request

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET", "any_random_string")

# Google OAuth Setup
oauth = OAuth(app)
google = oauth.register(
    name='google',
    client_id=os.environ.get("GOOGLE_CLIENT_ID"),
    client_secret=os.environ.get("GOOGLE_CLIENT_SECRET"),
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
    client_kwargs={'scope': 'openid email profile'}
)

@app.route('/')
def home():

    if 'user' not in session:
        return redirect(url_for('login'))


    user = session.get('user')
    if not user:
        return render_template('login.html') # Minimal login page with "Sign in with Google" button
    return render_template('index.html', user=user)

@app.route('/login')
def login():
    return google.authorize_redirect(url_for('auth', _external=True))

@app.route('/auth')
def auth():
    token = google.authorize_access_token()
    session['user'] = token['userinfo']
    return redirect('/')

app = Flask(__name__)
DATA_DIR = 'data'

# --- EXHAUSTIVE PRECISION MAPPING FOR ALL BRANCHES ---
def get_precision_info(program_name):
    p = program_name.lower()
    
    # ECE / VLSI / EMBEDDED
    if 'vlsi' in p and 'embedded' in p: return "VLSI & Embedded Systems", "EC, EE, IN", "#E0E7FF", "#4338CA"
    elif 'vlsi' in p: return "VLSI Design", "EC, EE", "#E0F2FE", "#0369A1"
    elif 'embedded' in p: return "Embedded Systems", "EC, IN", "#F0F9FF", "#075985"
    elif 'microelectron' in p: return "Microelectronics", "EC, EE", "#DBEAFE", "#1E40AF"
    
    # ECE / COMMUNICATIONS
    elif 'microwave' in p or 'rf' in p: return "RF & Microwave Engineering", "EC", "#D1FAE5", "#065F46"
    elif 'communication' in p and 'signal' in p: return "Signal Processing & Comm", "EC", "#ECFDF5", "#047857"
    elif 'communication' in p: return "Communication Systems", "EC", "#F0FDF4", "#166534"
    elif 'signal processing' in p: return "Signal Processing", "EC", "#F7FEE7", "#4D7C0F"
    
    # CSE / AI / DATA SCIENCE
    elif ('artificial' in p or ' ai ' in p) and ('data science' in p or 'analytics' in p): return "AI & Data Science", "CS", "#F3E8FF", "#6B21A8"
    elif 'artificial' in p or ' ai ' in p: return "Artificial Intelligence", "CS", "#FAF5FF", "#7E22CE"
    elif 'data science' in p or 'analytics' in p: return "Data Science", "CS", "#F5F3FF", "#5B21B6"
    elif 'cyber' in p or 'security' in p: return "Cyber Security", "CS", "#FDF2F8", "#9D174D"
    elif 'computer science' in p or ' it ' in p or 'software' in p: return "Computer Science / IT", "CS", "#EFF6FF", "#1D4ED8"
    
    # ELECTRICAL / POWER / CONTROL
    elif 'electric vehicle' in p: return "Electric Vehicle Tech", "EE, ME", "#FEF3C7", "#92400E"
    elif 'power electronics' in p: return "Power Electronics & Drives", "EE", "#FFF7ED", "#9A3412"
    elif 'power system' in p: return "Power Systems", "EE", "#FFFBEB", "#B45309"
    elif 'control' in p and 'instrumentation' in p: return "Control & Instrumentation", "IN, EE", "#FFF1F2", "#BE123C"
    elif 'control' in p: return "Control & Automation", "EE, IN", "#F0FDFA", "#0F766E"
    elif 'instrumentation' in p: return "Instrumentation Engineering", "IN, EC", "#FFF1F2", "#BE123C"

    # MECHANICAL / DESIGN / THERMAL
    elif 'thermal' in p or 'heat' in p or 'fluids' in p: return "Thermal & Fluids", "ME", "#FFF5F5", "#C53030"
    elif 'machine design' in p or 'mechanical design' in p: return "Machine Design", "ME", "#FFF5F5", "#C53030"
    elif 'manufacturing' in p or 'production' in p: return "Manufacturing & Production", "ME", "#F7FAFC", "#2D3748"
    elif 'robotics' in p or 'mechatronics' in p or 'automation' in p: return "Robotics & Automation", "ME, EE, EC", "#EBF8FF", "#2B6CB0"
    elif 'industrial' in p: return "Industrial Engineering", "ME", "#F0FFF4", "#276749"
    
    # CIVIL / STRUCTURAL / GEOTECH
    elif 'structural' in p: return "Structural Engineering", "CE", "#F3F0FF", "#553C9A"
    elif 'geotechnical' in p: return "Geotechnical Engineering", "CE", "#FFFAF0", "#7B341E"
    elif 'transportation' in p: return "Transportation Engg", "CE", "#EBF4FF", "#2A4365"
    elif 'environmental' in p: return "Environmental Engg", "CE", "#F0FFF4", "#22543D"
    elif 'water resource' in p: return "Water Resources", "CE", "#E6FFFA", "#234E52"

    # CHEMICAL / BIOTECH / MATERIALS
    elif 'chemical' in p: return "Chemical Engineering", "CH", "#FFF5F7", "#9B2C2C"
    elif 'biotech' in p: return "Biotechnology", "BT", "#F0FFF4", "#2F855A"
    elif 'material' in p or 'metallurg' in p: return "Materials & Metallurgy", "MT", "#EDF2F7", "#2D3748"

    return "Specialized Branch", "GEN", "#F9FAFB", "#374151"

BRANCH_MAP = {
    'ECE': ["VLSI & Embedded Systems", "VLSI Design", "Embedded Systems", "Microelectronics", "RF & Microwave Engineering", "Signal Processing & Comm", "Communication Systems", "Signal Processing", "Instrumentation Engineering", "Robotics & Automation"],
    'CSE': ["AI & Data Science", "Artificial Intelligence", "Data Science", "Cyber Security", "Computer Science / IT"],
    'EE':  ["Power Electronics & Drives", "Power Systems", "Electric Vehicle Tech", "Control & Automation", "Control & Instrumentation", "VLSI Design", "Robotics & Automation"],
    'IN':  ["Control & Instrumentation", "Control & Automation", "Embedded Systems", "Instrumentation Engineering"],
    'ME':  ["Thermal & Fluids", "Machine Design", "Manufacturing & Production", "Robotics & Automation", "Industrial Engineering", "Electric Vehicle Tech"],
    'CE':  ["Structural Engineering", "Geotechnical Engineering", "Transportation Engg", "Environmental Engg", "Water Resources"],
    'Other': ["Chemical Engineering", "Biotechnology", "Materials & Metallurgy", "Specialized Branch"]
}

def calculate_chance(user_score, min_score):
    diff = user_score - min_score
    if diff >= 50: return "Level 4: Very High", "#10b981"
    if diff >= 20: return "Level 3: High", "#34d399"
    if diff >= 5:  return "Level 2: Moderate", "#fbbf24"
    return "Level 1: Borderline", "#f87171"

@app.route('/', methods=['GET', 'POST'])
def index():
    years = sorted([f.replace('.csv', '') for f in os.listdir(DATA_DIR) if f.endswith('.csv')], reverse=True)
    results, user_score, selected_year = None, None, None
    selected_cat, selected_branch, selected_spec = "OPEN", "ECE", "ALL"

    if request.method == 'POST':
        try:
            user_score = int(request.form.get('gate_score'))
            selected_year = request.form.get('year')
            selected_cat = request.form.get('category')
            selected_branch = request.form.get('qualifying_branch')
            selected_spec = request.form.get('specialization')

            df = pd.read_csv(os.path.join(DATA_DIR, f"{selected_year}.csv"))
            df.columns = [c.strip() for c in df.columns]
            df['Min GATE Score'] = pd.to_numeric(df['Min GATE Score'], errors='coerce')
            df = df.dropna(subset=['Min GATE Score'])

            # FILTER: Matches Category and Score (User >= Cutoff)
            mask = (df['Category'] == selected_cat) & (df['Min GATE Score'] <= user_score)
            filtered_df = df[mask].copy()

            res_list = []
            for _, row in filtered_df.iterrows():
                spec_name, codes, bg, text_clr = get_precision_info(row['PG Program'])
                
                # BRANCH RELEVANCE CHECK
                if (spec_name in BRANCH_MAP.get(selected_branch, [])) or selected_branch == "ALL":
                    if selected_spec == "ALL" or spec_name == selected_spec:
                        chance_text, chance_color = calculate_chance(user_score, row['Min GATE Score'])
                        item = row.to_dict()
                        item.update({'spec': spec_name, 'codes': codes, 'bg': bg, 'text_clr': text_clr, 'chance': chance_text, 'chance_color': chance_color})
                        res_list.append(item)
            
            # SORTING: Highest Cutoff first (Most "Ambitious" and "Near" user score)
            results = sorted(res_list, key=lambda x: x['Min GATE Score'], reverse=True)
            
        except Exception as e: print(f"Error: {e}")

    return render_template('index.html', years=years, results=results, user_score=user_score, category=selected_cat, selected_year=selected_year, selected_branch=selected_branch, selected_spec=selected_spec, branch_map=BRANCH_MAP)

if __name__ == '__main__':
    app.run(debug=True, port=5001)