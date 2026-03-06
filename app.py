import os
import pandas as pd
from flask import Flask, render_template, request

app = Flask(__name__)
DATA_DIR = 'data'

# --- ENHANCED DOMAIN CONFIGURATION ---
# Format: 'Category Name': {'regex': r'...', 'codes': 'CODE1, CODE2'}
DOMAIN_CONFIG = {
    'VLSI & Embedded': {
        'regex': r'VLSI|Embedded|Microelectron|Microsystem|Integrated Circuit',
        'codes': 'EC, EE, IN'
    },
    'Communications & RF': {
        'regex': r'Communication|RF|Microwave|Wireless|Signal Processing|Photonics|Optic|Antenna',
        'codes': 'EC'
    },
    'Computer Science & AI': {
        'regex': r'Computer Science|Information Technology|Artificial Intelligence|Machine Learning|Data Science|Data Analytics|Computing|Security|Software|Cloud|Distributed',
        'codes': 'CS'
    },
    'Instrumentation & Control': {
        'regex': r'Instrumentation|Process Control|Control and Instrumentation|Sensors|Measurement',
        'codes': 'IN, EC, EE'
    },
    'Electrical & Power': {
        'regex': r'Power|Control|Electrical|Electric Vehicle|High Voltage|Energy Systems|Drives|Renewable',
        'codes': 'EE'
    },
    'Mechanical & Design': {
        'regex': r'Thermal|Design|Manufacturing|Robotics|Mechatronics|CAD|CAM|Automobile|Mechanical|Industrial|Fluid|Aerospace|Production',
        'codes': 'ME'
    },
    'Civil & Infrastructure': {
        'regex': r'Structural|Geotechnical|Environmental|Transportation|Water Resources|Construction|Surveying|Hydraulics|Civil|Infrastructure|Geomatics',
        'codes': 'CE'
    }
}

# Mapping: Qualifying Branch -> Which categories they see
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
    if diff >= 50: return "Very High", "#059669"
    if diff >= 20: return "High", "#10b981"
    if diff >= 5:  return "Moderate", "#f59e0b"
    return "Borderline", "#ef4444"

def get_program_info(program_name):
    # Exclusion for Microwave (matches EC, not VLSI)
    if "Microwave" in program_name:
        category = "Communications & RF"
        return f"{category} | {DOMAIN_CONFIG[category]['codes']}", category

    for category, info in DOMAIN_CONFIG.items():
        if pd.Series(program_name).str.contains(info['regex'], case=False, na=False).any():
            return f"{category} | {info['codes']}", category
            
    return "Other Specialization", "Other"

@app.route('/', methods=['GET', 'POST'])
def index():
    years = get_available_years()
    results = None
    user_score = None
    selected_year = None
    selected_cat = "OPEN"
    selected_branch = "ALL"

    if request.method == 'POST':
        try:
            user_score = int(request.form.get('gate_score'))
            selected_year = request.form.get('year')
            selected_cat = request.form.get('category')
            selected_branch = request.form.get('qualifying_branch')

            file_path = os.path.join(DATA_DIR, f"{selected_year}.csv")
            df = pd.read_csv(file_path)
            df.columns = [c.strip() for c in df.columns]
            df['Min GATE Score'] = pd.to_numeric(df['Min GATE Score'], errors='coerce')
            df = df.dropna(subset=['Min GATE Score'])

            mask = (df['Category'] == selected_cat) & (df['Min GATE Score'] <= user_score)
            filtered_df = df[mask].copy()

            # Process tags and filter by branch relevance
            relevant_categories = BRANCH_RELEVANCE.get(selected_branch, BRANCH_RELEVANCE['ALL'])
            
            res_list = []
            for _, row in filtered_df.iterrows():
                tag_string, category_name = get_program_info(row['PG Program'])
                
                # Check if this program belongs to the user's branch pool
                if category_name in relevant_categories or selected_branch == "ALL":
                    chance_text, chance_color = calculate_chance(user_score, row['Min GATE Score'])
                    item = row.to_dict()
                    item['tag'] = tag_string
                    item['is_core'] = (category_name in ['VLSI & Embedded', 'Instrumentation & Control'])
                    item['chance'] = chance_text
                    item['chance_color'] = chance_color
                    res_list.append(item)

            results = sorted(res_list, key=lambda x: x['Min GATE Score'], reverse=True)

        except Exception as e:
            print(f"Error: {e}")

    return render_template('index.html', years=years, results=results, 
                           user_score=user_score, category=selected_cat, 
                           selected_year=selected_year, selected_branch=selected_branch)

if __name__ == '__main__':
    app.run(debug=True, port=5001)