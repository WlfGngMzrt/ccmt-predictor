import os
import pandas as pd
from flask import Flask, render_template, request

app = Flask(__name__)
DATA_DIR = 'data'

def get_available_years():
    # Looks for .csv files instead of .html
    return sorted([f.replace('.csv', '') for f in os.listdir(DATA_DIR) if f.endswith('.csv')], reverse=True)

@app.route('/', methods=['GET', 'POST'])
def index():
    years = get_available_years()
    results = None
    user_score = None

    if request.method == 'POST':
        user_score = int(request.form.get('gate_score'))
        selected_year = request.form.get('year')
        category = request.form.get('category')
        
        try:
            # 1. Load the specific year's CSV
            file_path = os.path.join(DATA_DIR, f"{selected_year}.csv")
            df = pd.read_csv(file_path)

            # 2. Clean column names (removes extra spaces if any)
            df.columns = [c.strip() for c in df.columns]

            # 3. Filter by Category and qualifying score
            # We check if your score is >= the minimum required for that college
            mask = (df['Category'] == category) & (df['Min GATE Score'] <= user_score)
            filtered_df = df[mask].copy()

            # 4. Sorting: 
            # Primary: Put VLSI and Embedded branches at the top
            # Secondary: Sort by Min Score descending (toughest to get into on top)
            filtered_df['is_core'] = filtered_df['PG Program'].str.contains('VLSI|Embedded', case=False, na=False)
            
            results_df = filtered_df.sort_values(
                by=['is_core', 'Min GATE Score'], 
                ascending=[False, False]
            )
            
            results = results_df.to_dict(orient='records')
            
        except Exception as e:
            print(f"Error processing CSV: {e}")

    return render_template('index.html', years=years, results=results, user_score=user_score)

if __name__ == '__main__':
    app.run(debug=True)