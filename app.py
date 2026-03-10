import streamlit as st
import pdfplumber
import pandas as pd
import re

st.set_page_config(page_title="Minato SBI Scorer", page_icon="🎯")
st.markdown("<h1 style='text-align: center;'>🎯 Minato's SBI Clerk PDF Scorer</h1>", unsafe_allow_html=True)

def extract_flexible_data(pdf_file):
    extracted = []
    with pdfplumber.open(pdf_file) as pdf:
        # We join all text to handle cases where a question is split across pages
        full_text = "\n".join([page.extract_text() for page in pdf.pages if page.extract_text()])
    
    # This splits the document by "Question No" or "Q." to isolate each question
    blocks = re.split(r"(?:Question No\.|Q\.)\s*", full_text)
    
    for block in blocks[1:]:
        try:
            # 1. Find Question Number
            q_match = re.search(r"(\d+)", block)
            if not q_match: continue
            q_no = int(q_match.group(1))
            
            # 2. Find Correct Answer (looks for 'Correct Answer', 'Answer Key', or 'Ans:')
            # It captures A-E or 1-4
            corr_match = re.search(r"(?:Correct Answer|Correct Option|Answer)\s*[:\-]\s*([A-E1-5])", block, re.I)
            
            # 3. Find Candidate Choice (looks for 'Chosen Option', 'Your Answer')
            chosen_match = re.search(r"(?:Chosen Option|Status|Marked)\s*[:\-]\s*([A-E1-5]|-|None|Not Attempted)", block, re.I)
            
            if corr_match and chosen_match:
                corr = corr_match.group(1).strip().upper()
                chosen = chosen_match.group(1).strip().upper()
                
                # Normalize unattempted markers
                if chosen in ["-", "NONE", "NOT ATTEMPTED", ""]:
                    chosen = "$"
                
                extracted.append({"Question No": q_no, "Correct": corr, "Chosen": chosen})
        except:
            continue
            
    return pd.DataFrame(extracted)

# --- UPLOAD ---
file = st.file_uploader("Upload Official SBI Response PDF", type="pdf")

if file:
    with st.spinner("Minato is analyzing the paper..."):
        df = extract_flexible_data(file)
    
    if not df.empty:
        # Scoring Logic
        def get_marks(row):
            q, corr, ans = row['Question No'], row['Correct'], row['Chosen']
            if ans == "$": return 0
            # Reasoning 1.2 marks rule (Q141-190)
            weight = 1.2 if 141 <= q <= 190 else 1.0
            return weight if ans == corr else -0.25

        df['Marks'] = df.apply(get_marks, axis=1)
        
        # Sectional Grouping
        sections = {"GA (1-50)": (1,50), "English (51-90)": (51,90), "Quant (91-140)": (141,140), "Reasoning (141-190)": (141,190)}
        
        st.subheader("Your Results")
        total_score = df['Marks'].sum()
        st.metric("FINAL SCORE", f"{round(total_score, 2)} / 200")
        
        # Show breakdown
        st.write("Section-wise Summary:")
        summary = []
        for name, (s, e) in sections.items():
            sec_df = df[(df['Question No'] >= s) & (df['Question No'] <= e)]
            summary.append({"Section": name, "Attempted": len(sec_df[sec_df['Chosen'] != "$"]), "Score": round(sec_df['Marks'].sum(), 2)})
        st.table(pd.DataFrame(summary))
    else:
        st.error("Minato could not find the question data. Try saving the PDF again with 'Background Graphics' enabled.")

st.markdown("<p style='text-align: right; color: gray;'>Created by Minato</p>", unsafe_allow_html=True)
