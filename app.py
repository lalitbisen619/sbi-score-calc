import streamlit as st
import pdfplumber
import pandas as pd

# --- MINATO BRANDING ---
st.set_page_config(page_title="Minato SBI Scorer", layout="wide")
st.markdown("<h1 style='text-align: center; color: #1E3A8A;'>🎯 Minato's SBI Clerk Scorecard</h1>", unsafe_allow_html=True)

def extract_sbi_smart_grid(pdf_file):
    extracted = []
    with pdfplumber.open(pdf_file) as pdf:
        for page in pdf.pages:
            table = page.extract_table()
            if table:
                for row in table:
                    # 1. Extract all text from the row and split into isolated words
                    raw_tokens = []
                    for cell in row:
                        if cell is None: continue
                        parts = str(cell).replace('\n', ' ').split()
                        for p in parts:
                            if p.strip(): raw_tokens.append(p.strip().upper())
                    
                    # 2. Filter out garbage (like watermarks) to only keep valid answers
                    clean_tokens = []
                    for t in raw_tokens:
                        # Sometimes OCR reads '$' as 'S'
                        if t in ['$', 'S']: 
                            clean_tokens.append('$')
                        # Keep only numbers between 1 and 190
                        elif t.isdigit() and 1 <= int(t) <= 190:
                            clean_tokens.append(t)
                            
                    # 3. Sliding window to perfectly capture (Q_No, Chosen, Correct)
                    i = 0
                    while i < len(clean_tokens) - 2:
                        q_val = clean_tokens[i]
                        c_val = clean_tokens[i+1]
                        k_val = clean_tokens[i+2]
                        
                        # Check if it perfectly matches the pattern of a question block
                        if q_val.isdigit() and 1 <= int(q_val) <= 190:
                            if c_val in ['1','2','3','4','5','$'] and k_val in ['1','2','3','4','5']:
                                extracted.append({
                                    "Q": int(q_val),
                                    "Chosen": c_val,
                                    "Correct": k_val
                                })
                                i += 3 # Skip ahead since we found a valid question
                                continue
                        i += 1 # Move by 1 to re-sync if the pattern was broken
                        
    df = pd.DataFrame(extracted)
    if not df.empty:
        # Sort and remove any duplicates
        df = df.drop_duplicates('Q', keep='last').sort_values('Q')
    return df

# --- CALCULATION AND DISPLAY ---
file = st.file_uploader("Upload Response Sheet PDF", type="pdf")
if file:
    with st.spinner("Minato's engine is scanning the grid..."):
        df = extract_sbi_smart_grid(file)
    
    if not df.empty and len(df) > 100:
        def calculate(row):
            q, ch, co = row['Q'], row['Chosen'], row['Correct']
            # Treat $ as unattempted
            if ch == "$": return 0.0, 0, 0
            
            # Reasoning 1.2 weightage (Q141-190)
            weight = 1.2 if 141 <= q <= 190 else 1.0
            if ch == co: return weight, 1, 0
            else: return -0.25, 0, 1

        # Apply calculations
        df[['Marks', 'Is_Pos', 'Is_Neg']] = df.apply(calculate, axis=1, result_type='expand')
        
        # Sectional Mapping
        sections = {"General Awareness (1-50)": (1, 50), "English (51-90)": (51, 90), 
                    "Quant (91-140)": (91, 140), "Reasoning (141-190)": (141, 190)}
        
        st.success(f"## Total Score: {round(df['Marks'].sum(), 2)} / 200")
        
        summary = []
        for name, (s, e) in sections.items():                       
            sec_df = df[(df['Q'] >= s) & (df['Q'] <= e)]
            summary.append({
                "Section": name, 
                "Attempted": len(sec_df[sec_df['Chosen'] != '$']),
                "Correct": sec_df['Is_Pos'].sum(), 
                "Wrong": sec_df['Is_Neg'].sum(),
                "Score": round(sec_df['Marks'].sum(), 2)
            })
        st.table(pd.DataFrame(summary))
        
        with st.expander("Detailed Analysis (See what you got wrong)"):
            wrong_df = df[df['Is_Neg'] > 0]
            st.write("### Incorrect Answers")
            st.dataframe(wrong_df[['Q', 'Chosen', 'Correct']], hide_index=True)
    else:
        st.error("Minato could not read the full table. Please try again.")

st.markdown("<p style='text-align: right; font-size: 14px; color: gray;'>Powered by Minato</p>", unsafe_allow_html=True)
