import os
import pandas as pd
from flask import Flask, render_template, request

app = Flask(__name__)
DATA_DIR = 'data'

# --- ENHANCED CONFIGURATION ---
DOMAIN_CONFIG = {
    'VLSI & Embedded': {'regex': r'VLSI|Embedded|Microelectron|Microsystem|Integrated Circuit', 'codes': 'EC, EE, IN', 'bg': '#E0E7FF', 'text': '#4338CA'},
    'Communications & RF': {'regex': r'Communication|RF|Microwave|Wireless|Signal Processing|Photonics|Optic|Antenna', 'codes': 'EC', 'bg': '#D1FAE5', 'text': '#065F46'},
    'Computer Science & AI': {'regex': r'Computer Science|Information Technology|Artificial Intelligence|Machine Learning|Data Science|Data Analytics|Computing|Security|Software|Cloud|Distributed', 'codes': 'CS', 'bg': '#F3E8FF', 'text': '#6B21A8'},
    'Instrumentation & Control': {'regex': r'Instrumentation|Process Control|Control and Instrumentation|Sensors|Measurement', 'codes': 'IN, EC, EE', 'bg': '#FEF3C7', 'text': '#92400E'},
    'Electrical & Power': {'regex': r'Power|Control|Electrical|Electric Vehicle|High Voltage|Energy Systems|Drives|Renewable', 'codes': 'EE', 'bg': '#FFEDD5', 'text': '#9A3412'},
    'Mechanical & Design': {'regex': r'Thermal|Design|Manufacturing|Robotics|Mechatronics|CAD|CAM|Automobile|Mechanical|Industrial|Fluid|Aerospace|Production', 'codes': 'ME', 'bg': '#FCE7F3', 'text': '#9D174D'},
    'Civil & Infrastructure': {'regex': r'Structural|Geotechnical|Environmental|Transportation|Water Resources|Construction|Surveying|Hydraulics|Civil|Infrastructure|Geomatics', 'codes': 'CE', 'bg': '#F1F5F9', 'text': '#475569'}
}

BRANCH_RELEVANCE = {
    'ECE': ['VLSI & Embedded', 'Communications & RF', 'Instrumentation & Control'],
    'CSE': ['Computer Science & AI'],
    'EE': ['Electrical & Power', 'VLSI & Embedded', 'Instrumentation & Control'],
    'IN': ['Instrumentation & Control', 'VLSI & Embedded'],
    'ME': ['Mechanical & Design'],
    'CE': ['Civil & Infrastructure'],
    'ALL': list(DOMAIN_CONFIG.keys())
}

def get_available_years():
    if not os.path.exists(DATA_DIR): os.makedirs(DATA_DIR)
    return sorted([f.replace('.csv', '') for f in os.listdir(DATA_DIR) if f.endswith('.csv')], reverse=True)

def calculate_chance(user_score, min_score):
    diff = user_score - min_score
    if diff >= 50: return "Very High", "#10b981"
    if diff >= 20: return "High", "#34d399"
    if diff >= 5:  return "Moderate", "#fbbf24"
    return "Borderline", "#f87171"

def get_program_info(program_name):
    if "Microwave" in program_name:
        cat = "Communications & RF"
        return DOMAIN_CONFIG[cat], cat
    for category, info in DOMAIN_CONFIG.items():
        if pd.Series(program_name).str.contains(info['regex'], case=False, na=False).any():
            return info, category
    return {'bg': '#f3f4f6', 'text': '#374151', 'codes': 'GEN'}, "Other"

@app.route('/', methods=['GET', 'POST'])
def index():
    years = get_available_years()
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
            df['Max GATE Score'] = pd.to_numeric(df['Max GATE Score'], errors='coerce')
            df = df.dropna(subset=['Min GATE Score'])

            mask = (df['Category'] == selected_cat) & (df['Min GATE Score'] <= user_score)
            filtered_df = df[mask].copy()

            res_list = []
            for _, row in filtered_df.iterrows():
                info, cat_name = get_program_info(row['PG Program'])
                if (cat_name in BRANCH_RELEVANCE.get(selected_branch, [])) or selected_branch == "ALL":
                    if selected_spec == "ALL" or cat_name == selected_spec:
                        chance_text, chance_color = calculate_chance(user_score, row['Min GATE Score'])
                        item = row.to_dict()
                        item.update({'tag': f"{cat_name} | {info['codes']}", 'tag_bg': info['bg'], 'tag_text': info['text'],
                                    'chance': chance_text, 'chance_color': chance_color})
                        res_list.append(item)
            results = res_list # Sorting removed as requested
        except Exception as e: print(f"Error: {e}")

    return render_template('index.html', years=years, results=results, user_score=user_score, 
                           category=selected_cat, selected_year=selected_year, 
                           selected_branch=selected_branch, selected_spec=selected_spec, 
                           branch_relevance=BRANCH_RELEVANCE)

if __name__ == '__main__':
    import sys, subprocess
    venv_python = os.path.join(os.getcwd(), 'venv', 'bin', 'python3')
    if sys.executable != venv_python and os.path.exists(venv_python):
        subprocess.check_call([venv_python, *sys.argv])
    else:
        app.run(debug=True, port=5001)