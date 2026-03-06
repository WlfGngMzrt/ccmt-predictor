import os
import pandas as pd
from flask import Flask, render_template, request

app = Flask(__name__)
DATA_DIR = 'data'

# --- GRANULAR SPECIALIZATION MAPPING ---
# Categories are now broken down into distinct "Pure" vs "Hybrid" types
def get_precision_info(program_name):
    p = program_name.lower()
    
    # --- ECE / VLSI / EMBEDDED POOL ---
    if 'vlsi' in p and 'embedded' in p:
        return "VLSI & Embedded Systems", "EC, EE, IN", "#E0E7FF", "#4338CA"
    elif 'vlsi' in p:
        return "VLSI Design", "EC, EE", "#E0F2FE", "#0369A1"
    elif 'embedded' in p:
        return "Embedded Systems", "EC, IN", "#F0F9FF", "#075985"
    elif 'microelectron' in p:
        return "Microelectronics", "EC, EE", "#DBEAFE", "#1E40AF"
    
    # --- ECE / COMM POOL ---
    elif 'microwave' in p or 'rf' in p:
        return "RF & Microwave Engineering", "EC", "#D1FAE5", "#065F46"
    elif ('signal processing' in p) and ('communication' in p):
        return "Signal Processing & Comm", "EC", "#ECFDF5", "#047857"
    elif 'communication' in p:
        return "Communication Engineering", "EC", "#F0FDF4", "#166534"
    elif 'signal processing' in p:
        return "Signal Processing", "EC", "#F7FEE7", "#4D7C0F"
    
    # --- CSE / AI / DATA SCIENCE POOL ---
    elif ('artificial intelligence' in p or ' ai ' in p) and ('data science' in p or 'data analytics' in p):
        return "AI & Data Science", "CS", "#F3E8FF", "#6B21A8"
    elif 'artificial intelligence' in p or ' ai ' in p:
        return "Artificial Intelligence", "CS", "#FAF5FF", "#7E22CE"
    elif 'data science' in p or 'data analytics' in p:
        return "Data Science / Analytics", "CS", "#F5F3FF", "#5B21B6"
    elif 'cyber' in p or 'security' in p:
        return "Cyber Security", "CS", "#FDF2F8", "#9D174D"
    elif 'computer science' in p or 'computer engineering' in p:
        return "Computer Science", "CS", "#EFF6FF", "#1D4ED8"
    
    # --- EE / POWER / CONTROL POOL ---
    elif 'electric vehicle' in p:
        return "Electric Vehicle Tech", "EE, ME", "#FEF3C7", "#92400E"
    elif 'power electronics' in p:
        return "Power Electronics & Drives", "EE", "#FFF7ED", "#9A3412"
    elif 'power system' in p:
        return "Power Systems", "EE", "#FFFBEB", "#B45309"
    elif 'control' in p:
        return "Control & Automation", "EE, IN", "#F0FDFA", "#0F766E"
    
    # --- IN / SENSORS ---
    elif 'instrumentation' in p:
        return "Instrumentation", "IN, EC", "#FFF1F2", "#BE123C"

    return "Other Specialization", "GEN", "#F9FAFB", "#374151"

# Mapping: Which "Precision Category" is relevant to which Branch
BRANCH_MAP = {
    'ECE': ["VLSI & Embedded Systems", "VLSI Design", "Embedded Systems", "Microelectronics", 
            "RF & Microwave Engineering", "Signal Processing & Comm", "Communication Engineering", 
            "Signal Processing", "Instrumentation"],
    'CSE': ["AI & Data Science", "Artificial Intelligence", "Data Science / Analytics", "Cyber Security", "Computer Science"],
    'EE':  ["Power Electronics & Drives", "Power Systems", "Electric Vehicle Tech", "Control & Automation", "VLSI Design"],
    'IN':  ["Instrumentation", "Control & Automation", "Embedded Systems", "VLSI Design"],
    'ALL': []
}

def get_available_years():
    if not os.path.exists(DATA_DIR): os.makedirs(DATA_DIR)
    return sorted([f.replace('.csv', '') for f in os.listdir(DATA_DIR) if f.endswith('.csv')], reverse=True)

def calculate_chance(user_score, min_score):
    diff = user_score - min_score
    if diff >= 50: return "Level 4: Very High", "#10b981"
    if diff >= 20: return "Level 3: High", "#34d399"
    if diff >= 5:  return "Level 2: Moderate", "#fbbf24"
    return "Level 1: Borderline", "#f87171"

@app.route('/', methods=['GET', 'POST'])
def index():
    years = get_available_years()
    results, user_score = None, None
    selected_year, selected_cat, selected_branch, selected_spec = None, "OPEN", "ECE", "ALL"

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

            mask = (df['Category'] == selected_cat) & (df['Min GATE Score'] <= user_score)
            filtered_df = df[mask].copy()

            res_list = []
            for _, row in filtered_df.iterrows():
                spec_name, codes, bg, text_clr = get_precision_info(row['PG Program'])
                
                # Filter by Branch Relevance
                if (spec_name in BRANCH_MAP.get(selected_branch, [])) or selected_branch == "ALL":
                    # Filter by Specific Specialization chosen by user
                    if selected_spec == "ALL" or spec_name == selected_spec:
                        chance_text, chance_color = calculate_chance(user_score, row['Min GATE Score'])
                        item = row.to_dict()
                        item.update({'spec': spec_name, 'codes': codes, 'bg': bg, 'text_clr': text_clr,
                                    'chance': chance_text, 'chance_color': chance_color})
                        res_list.append(item)
            results = res_list
        except Exception as e: print(f"Error: {e}")

    return render_template('index.html', years=years, results=results, user_score=user_score, 
                           category=selected_cat, selected_year=selected_year, 
                           selected_branch=selected_branch, selected_spec=selected_spec, 
                           branch_map=BRANCH_MAP)

if __name__ == '__main__':
    app.run(debug=True, port=5001)