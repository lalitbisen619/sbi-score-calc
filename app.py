import streamlit as st
import pandas as pd

# --- WEBSITE CONFIGURATION ---
st.set_page_config(page_title="SBI Clerk Mains Scorecard", page_icon="🎯", layout="centered")

# Custom CSS for Branding
st.markdown("""
    <style>
    .footer { position: fixed; bottom: 10px; right: 10px; font-size: 14px; color: #888; }
    .main-header { text-align: center; color: #1E3A8A; }
    </style>
    """, unsafe_allow_html=True)

st.markdown("<h1 class='main-header'>SBI Clerk Mains Scorecard Generator</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center;'>Created by <b>Minato</b></p>", unsafe_allow_html=True)
st.divider()

# --- CALCULATION LOGIC ---
def process_scorecard(df):
    # Mapping Sections
    sections = {
        "General Awareness": (1, 50, 1.0),
        "English Language": (51, 90, 1.0),
        "Quantitative Aptitude": (91, 140, 1.0),
        "Reasoning Ability": (141, 190, 1.2)
    }
    
    summary = []
    t_pos, t_neg = 0, 0

    for sec, (start, end, pos_val) in sections.items():
        # Filtering questions by number
        sec_df = df[(df['Question No'] >= start) & (df['Question No'] <= end)]
        
        correct = len(sec_df[sec_df['Candidate Response'] == sec_df['Correct Answer']])
        unattempted = len(sec_df[sec_df['Candidate Response'] == "$"])
        wrong = len(sec_df) - correct - unattempted
        
        sec_pos = correct * pos_val
        sec_neg = wrong * 0.25 # As per your instruction: always -0.25
        sec_final = sec_pos - sec_neg
        
        t_pos += sec_pos
        t_neg += sec_neg
        
        summary.append({
            "Subject": sec,
            "Correct": correct,
            "Wrong": wrong,
            "Unattempted": unattempted,
            "Pos Marks": round(sec_pos, 2),
            "Neg Marks": round(sec_neg, 2),
            "Final Score": round(sec_final, 2)
        })

    return pd.DataFrame(summary), round(t_pos, 2), round(t_neg, 2)

# --- UPLOAD SECTION ---
uploaded_file = st.file_uploader("Upload your Response CSV (Columns: Question No, Correct Answer, Candidate Response)", type="csv")

if uploaded_file:
    try:
        data = pd.read_csv(uploaded_file)
        results, total_pos, total_neg = process_scorecard(data)
        
        # Display Results
        st.subheader("📊 Your Section-Wise Performance")
        st.dataframe(results, use_container_width=True, hide_index=True)
        
        st.divider()
        
        # Overall Score
        final_total = round(total_pos - total_neg, 2)
        c1, c2, c3 = st.columns(3)
        c1.metric("Total Positive", f"+{total_pos}")
        c2.metric("Total Negative", f"-{total_neg}")
        c3.metric("FINAL TOTAL SCORE", f"{final_total} / 200")

        # Detailed Analysis
        strongest = results.loc[results['Final Score'].idxmax()]['Subject']
        weakest = results.loc[results['Neg Marks'].idxmax()]['Subject']
        
        st.info(f"💡 Analysis: Your strongest section is {strongest}. You lost the most marks due to accuracy in {weakest}.")

    except Exception as e:
        st.error(f"Error reading file. Please ensure columns are exactly: 'Question No', 'Correct Answer', 'Candidate Response'.")

# Footer Branding
st.markdown("<div class='footer'>Created by Minato | 2026</div>", unsafe_allow_html=True)
