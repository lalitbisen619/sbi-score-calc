import streamlit as st
import pdfplumber
import pandas as pd
import re

# --- BRANDING ---
st.set_page_config(page_title="Minato SBI Scorer", page_icon="🎯")
st.markdown("<h1 style='text-align: center;'>🎯 SBI Clerk Mains PDF Scorer</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center;'>Created by <b>Minato</b></p>", unsafe_allow_html=True)

def extract_sbi_data(pdf_file):
    all_text = ""
    with pdfplumber.open(pdf_file) as pdf:
        for page in pdf.pages:
            all_text += page.extract_text() + "\n"
    
    # NEW SMART REGEX: This finds Question IDs and Choices more flexibly
    # It looks for "Question No" followed by digits, and "Chosen Option" / "Correct"
    extracted = []
    
    # We split the text by "Question No" to analyze each question block
    blocks = re.split(r"Question No\.", all_text)
    
    for block in blocks[1:]: # Skip the first empty split
        try:
            q_no = int(re.search(r"(\d+)", block).group(1))
            
            # Find Correct Answer (Usually looks like 'Correct Answer : A' or 'Option 1')
            correct_match = re.search(r"Correct Answer\s*[:\-]\s*([A-E1-4])", block, re.I)
            # Find Student Choice (Usually looks like 'Chosen Option : 2' or 'Chosen Option : --')
            chosen_match = re.search(r"Chosen Option\s*[:\-]\s*([A-E1-4]|-|\$|None)", block, re.I)
            
            if correct_match and chosen_match:
                correct = correct_match.group(1).upper()
                chosen = chosen_match.group(1).upper()
                
                # Handle unattempted cases
                if chosen in ["-", "NONE", "$"]:
                    chosen = "$"
                
                extracted.append([q_no, correct, chosen])
        except:
            continue
            
    return pd.DataFrame(extracted, columns=['Question No', 'Correct Answer', 'Candidate Response'])

# --- APP INTERFACE ---
uploaded_pdf = st.file_uploader("Upload your Response PDF", type="pdf")

if uploaded_pdf:
    df = extract_sbi_data(uploaded_pdf)
    
    if not df.empty:
        # Rules logic (Same as requested)
        def scoring(row):
            q, corr, ans = row['Question No'], row['Correct Answer'], row['Candidate Response']
            if ans == "$": return 0, 0, 0, 1
            weight = 1.2 if 141 <= q <= 190 else 1.0
            if ans == corr: return weight, weight, 0, 0
            else: return -0.25, 0, 0.25, 0

        df[['Score', 'Pos', 'Neg', 'Un']] = df.apply(scoring, axis=1, result_type='expand')
        
        # Display Summary Table
        sections = {"GA": (1,50), "English": (51,90), "Quant": (91,140), "Reasoning": (141,190)}
        summary = []
        for name, (s, e) in sections.items():
            sec_df = df[(df['Question No'] >= s) & (df['Question No'] <= e)]
            summary.append({
                "Section": name, 
                "Correct": len(sec_df[sec_df['Score'] > 0]),
                "Wrong": len(sec_df[sec_df['Score'] < 0]),
                "Marks": round(sec_df['Score'].sum(), 2)
            })
        
        st.table(pd.DataFrame(summary))
        st.success(f"### FINAL SCORE: {round(df['Score'].sum(), 2)} / 200")
        st.info(f"Analyzed {len(df)} questions found in PDF.")
    else:
        st.error("Minato's bot couldn't find the answers. Please make sure you saved the 'Full Response Sheet' as a PDF.")
