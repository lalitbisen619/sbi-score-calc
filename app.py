import streamlit as st
import pdfplumber
import pandas as pd

# --- BRANDING ---
st.set_page_config(page_title="Minato SBI Scorer", layout="wide")
st.markdown("<h1 style='text-align: center;'>🎯 Minato's SBI Clerk Scorecard</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center;'>Created by <b>Minato</b></p>", unsafe_allow_html=True)

def extract_sbi_grid_data(pdf_file):
    extracted = []
    with pdfplumber.open(pdf_file) as pdf:
        for page in pdf.pages:
            table = page.extract_table()
            if table:
                for row in table:
                    # Your PDF has 4 sets of (Q, Response, Key) in one row
                    # Set 1: indices 0,1,2 | Set 2: 4,5,6 | Set 3: 7,8,9 | Set 4: 10,11,12
                    indices = [(0, 1, 2), (4, 1, 2), (6, 7, 8), (9, 10, 11)] # Adjusting for your grid
                    for q_idx, res_idx, key_idx in indices:
                        try:
                            q_val = str(row[q_idx]).strip()
                            # Ensure we only pick numeric Question Numbers
                            if q_val.isdigit():
                                extracted.append({
                                    "Q": int(q_val),
                                    "Chosen": str(row[res_idx]).strip(),
                                    "Correct": str(row[key_idx]).strip()
                                })
                        except: continue
    return pd.DataFrame(extracted).drop_duplicates('Q').sort_values('Q')

# --- APP INTERFACE ---
file = st.file_uploader("Upload your Response Sheet PDF", type="pdf")

if file:
    df = extract_sbi_grid_data(file)
    
    if not df.empty:
        def calculate(row):
            q, ch, co = row['Q'], row['Chosen'], row['Correct']
            if ch == "$" or ch == "None": return 0, 0, 0
            
            # Reasoning 1.2 Weightage (Q 141-190)
            weight = 1.2 if 141 <= q <= 190 else 1.0
            if ch == co: return weight, weight, 0
            else: return -0.25, 0, 0.25

        df[['Marks', 'Pos', 'Neg']] = df.apply(calculate, axis=1, result_type='expand')
        
        # Sectional Mapping
        sections = {"General Awareness (1-50)": (1, 50), "English (51-90)": (51, 90), 
                    "Quant (91-140)": (91, 140), "Reasoning (141-190)": (141, 190)}
        
        st.success(f"## Total Score: {round(df['Marks'].sum(), 2)} / 200")
        
        summary = []
        for name, (s, e) in sections.items():
            sec_df = df[(df['Q'] >= s) & (df['Q'] <= e)]
            summary.append({"Section": name, "Correct": len(sec_df[sec_df['Marks'] > 0]), 
                            "Wrong": len(sec_df[sec_df['Marks'] < 0]), "Score": round(sec_df['Marks'].sum(), 2)})
        st.table(pd.DataFrame(summary))
    else:
        st.error("Could not read the table. Please ensure the PDF is a direct download from the portal.")
