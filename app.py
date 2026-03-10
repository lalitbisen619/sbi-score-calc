import streamlit as st
import pdfplumber
import pandas as pd
import re

# --- WEBSITE CONFIGURATION ---
st.set_page_config(page_title="Minato SBI PDF Scorer", page_icon="📄")

st.markdown("<h1 style='text-align: center;'>SBI Clerk Mains PDF Scorecard</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center;'>Created by <b>Minato</b></p>", unsafe_allow_html=True)
st.divider()

def extract_data_from_pdf(pdf_file):
    extracted_data = []
    with pdfplumber.open(pdf_file) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            # Logic to find Question No, Correct ID, and Chosen Option
            # This regex looks for common patterns in SBI/IBPS response sheets
            pattern = re.compile(r"Question No\.\s*(\d+).*?Correct Answer\s*:\s*([A-E]).*?Chosen Option\s*:\s*([A-E]|\d|\$|None)", re.DOTALL)
            matches = pattern.findall(text)
            
            for m in matches:
                extracted_data.append({
                    "Question No": int(m[0]),
                    "Correct Answer": m[1],
                    "Candidate Response": m[2] if m[2] != "None" else "$"
                })
    return pd.DataFrame(extracted_data)

# --- UPLOAD SECTION ---
uploaded_pdf = st.file_uploader("Upload your Official SBI Response PDF", type="pdf")

if uploaded_pdf:
    with st.spinner("Minato's bot is reading your PDF..."):
        df = extract_data_from_pdf(uploaded_pdf)
        
    if not df.empty:
        # --- CALCULATION LOGIC (Same as before) ---
        def calculate(row):
            q = row['Question No']
            corr = row['Correct Answer']
            ans = row['Candidate Response']
            
            if ans == "$": return 0, 0, 0, 1
            
            val = 1.2 if 141 <= q <= 190 else 1.0
            if ans == corr: return val, val, 0, 0
            else: return -0.25, 0, 0.25, 0

        res = df.apply(calculate, axis=1, result_type='expand')
        df[['Score', 'Pos', 'Neg', 'Un']] = res
        
        # Sectional Summary
        sections = {"GA": (1,50), "English": (51,90), "Quant": (91,140), "Reasoning": (141,190)}
        summary = []
        for name, (s, e) in sections.items():
            sec_df = df[(df['Question No'] >= s) & (df['Question No'] <= e)]
            summary.append({
                "Section": name,
                "Correct": len(sec_df[sec_df['Score'] > 0]),
                "Wrong": len(sec_df[sec_df['Score'] < 0]),
                "Final Marks": round(sec_df['Score'].sum(), 2)
            })
            
        st.table(pd.DataFrame(summary))
        st.success(f"### Total Score: {round(df['Score'].sum(), 2)}")
    else:
        st.error("Could not find data. Ensure this is the official SBI Response PDF.")

st.markdown("<div style='position: fixed; bottom: 10px; right: 10px; color: grey;'>Created by Minato</div>", unsafe_allow_html=True)
