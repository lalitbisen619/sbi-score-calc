import streamlit as st
import pdfplumber
import re
import pandas as pd

# --- MINATO BRANDING ---
st.set_page_config(page_title="Minato SBI Clerk Scorer", layout="centered")
st.markdown("<h1 style='text-align: center; color: #1E3A8A;'>🎯 SBI Clerk Mains Scorecard</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center;'>Created by <b>Minato</b></p>", unsafe_allow_html=True)
st.info("Simply download your response sheet as a PDF and upload it below. No special settings required.")

def extract_sbi_marks(pdf_file):
    data = []
    with pdfplumber.open(pdf_file) as pdf:
        # Extract text from every page and join it
        full_text = "\n".join([page.extract_text() for page in pdf.pages if page.extract_text()])
    
    # Logic: Look for Question blocks. SBI sheets usually have "Question ID : 123456"
    # This pattern catches the Question No, the Correct ID, and the Chosen ID
    blocks = re.split(r"Question No\.", full_text)
    
    for block in blocks[1:]:
        try:
            q_no = int(re.search(r"(\d+)", block).group(1))
            
            # Find the Correct Option ID (e.g., 'Correct Answer : 54321' or 'A')
            correct = re.search(r"(?:Correct Answer|Correct Option)\s*[:\-]\s*(\w+)", block, re.I)
            
            # Find the Student's Chosen Option ID
            chosen = re.search(r"(?:Chosen Option|Marked Option)\s*[:\-]\s*(\w+|-|None)", block, re.I)
            
            if correct and chosen:
                c_val = correct.group(1).strip()
                s_val = chosen.group(1).strip()
                
                # Treat '-', 'None', or 'Null' as Unattempted
                if s_val.lower() in ['-', 'none', 'null', 'not']:
                    s_val = "$"
                
                data.append({"Q": q_no, "Correct": c_val, "Chosen": s_val})
        except:
            continue
    return pd.DataFrame(data)

# --- UPLOAD SECTION ---
uploaded_file = st.file_uploader("Upload your PDF here", type="pdf")

if uploaded_file:
    with st.spinner("Minato's bot is calculating your marks..."):
        df = extract_sbi_marks(uploaded_file)
        
    if not df.empty:
        # Marking Rules
        def score_row(row):
            q, corr, chosen = row['Q'], row['Correct'], row['Chosen']
            if chosen == "$": return 0
            # Reasoning 1.2 weightage
            weight = 1.2 if 141 <= q <= 190 else 1.0
            return weight if chosen == corr else -0.25

        df['Marks'] = df.apply(score_row, axis=1)
        
        # Display Final Summary
        total = round(df['Marks'].sum(), 2)
        st.success(f"## Your Total Score: {total} / 200")
        
        # Sectional Breakdown
        sections = {"GA": (1,50), "English": (51,90), "Quant": (91,140), "Reasoning": (141,190)}
        summary = []
        for name, (s, e) in sections.items():
            sec_df = df[(df['Q'] >= s) & (df['Q'] <= e)]
            summary.append({"Section": name, "Attempted": len(sec_df[sec_df['Chosen'] != "$"]), "Score": round(sec_df['Marks'].sum(), 2)})
        
        st.table(pd.DataFrame(summary))
    else:
        st.error("Error: Could not find question data. Please ensure this is an official SBI Response PDF.")

st.markdown("<p style='text-align: right; font-size: 12px; color: gray;'>Powered by Minato</p>", unsafe_allow_html=True)
