import os
import json
import streamlit as st
import pandas as pd

import google.generativeai as genai

st.set_page_config(page_title="TPS Engine", layout="wide")

st.title("Nano Mech Labs - TPS Engine")
st.markdown("### Kanyakumari SDG Problem Generator")

if "generated_problem" not in st.session_state:
    st.session_state.generated_problem = None
if "last_cache_key" not in st.session_state:
    st.session_state.last_cache_key = None


def find_column(df, possible_names):
    possible_names_clean = [name.strip().lower() for name in possible_names]
    for col in df.columns:
        if str(col).strip().lower() in possible_names_clean:
            return col
    return None


def clean_text(text):
    if pd.isna(text):
        return ""
    return str(text).strip()


def one_line(text):
    return " ".join(str(text).split())


def generate_with_gemini(
    filtered,
    selected_location,
    selected_grade,
    selected_sdg_id,
    selected_sdg_goal,
    subject_col,
    topic_col,
    context_col
):
    api_key = st.secrets["GEMINI_API_KEY"]
    if not api_key:
        raise ValueError("GEMINI_API_KEY not found.")

    genai.configure(api_key=api_key)

    topic_candidates = []
    for _, row in filtered.iterrows():
        topic_candidates.append({
            "subject": clean_text(row[subject_col]),
            "topic": clean_text(row[topic_col]),
            "context": clean_text(row[context_col]),
        })

    topic_candidates = topic_candidates[:30]

    prompt = f"""
You are an expert school curriculum designer for Nano Mech Labs.

Student input:
- Location: {selected_location}
- Class: {selected_grade}
- SDG Goal: {selected_sdg_id} - {selected_sdg_goal}

Available curriculum topics:
{json.dumps(topic_candidates, ensure_ascii=False)}

Generate exactly ONE problem statement.

Rules:
- Use simple student-friendly language.
- Make it realistic and locally relevant.
- Make it one line only.
- Make it precise and easy to understand.
- Prefer styles like:
  "How can..."
  "In {selected_location} how can..."
  "Using ... how can..."
"""

    model = genai.GenerativeModel("gemini-1.5-flash")
    response = model.generate_content(prompt)

   
    return one_line(response.text.strip().replace('"', ''))

try:
    df = pd.read_excel("Kanyakumari.xlsx")
except Exception as e:
    st.error(f"Could not read Kanyakumari.xlsx: {e}")
    st.stop()

grade_col = find_column(df, ["Grade", "Class"])
subject_col = find_column(df, ["Subject"])
topic_col = find_column(df, ["Topic", "Chapter", "Lesson"])
sdg_id_col = find_column(df, ["SDG_ID", "SDG ID", "SDG_Number", "SDG Number"])
sdg_goal_col = find_column(df, ["SDG_Goal", "SDG Goal", "Goal"])
context_col = find_column(df, ["Context", "Localized SDG Goals", "Problem Context"])
location_col = find_column(df, ["Location", "District", "Place"])

required = {
    "Grade": grade_col,
    "Subject": subject_col,
    "Topic": topic_col,
    "SDG_ID": sdg_id_col,
    "SDG_Goal": sdg_goal_col,
    "Context": context_col,
}

missing = [k for k, v in required.items() if v is None]
if missing:
    st.error(f"Missing required columns in Excel file: {', '.join(missing)}")
    st.stop()

st.success("Kanyakumari dataset loaded successfully")

grades = sorted(df[grade_col].dropna().unique().tolist())
sdg_values = (
    df[[sdg_id_col, sdg_goal_col]]
    .dropna()
    .drop_duplicates()
    .sort_values(by=sdg_id_col)
)

sdg_options = [
    f"{int(row[sdg_id_col])} - {row[sdg_goal_col]}"
    for _, row in sdg_values.iterrows()
]

if location_col:
    locations = sorted(df[location_col].dropna().astype(str).unique().tolist())
else:
    locations = ["Kanyakumari"]

col1, col2, col3 = st.columns(3)

with col1:
    selected_location = st.selectbox("Select Location", locations)

with col2:
    selected_grade = st.selectbox("Select Class", grades)

with col3:
    selected_sdg_option = st.selectbox("Select SDG Goal", sdg_options)

selected_sdg_id = int(selected_sdg_option.split(" - ")[0])
selected_sdg_goal = selected_sdg_option.split(" - ", 1)[1]


cache_key = f"{selected_location}|{selected_grade}|{selected_sdg_id}"

if st.button("Generate Problem Statement"):

   
    if (
        st.session_state.last_cache_key == cache_key and
        st.session_state.generated_problem
    ):
        pass  # reuse old result

    else:
        filtered = df[
            (df[grade_col] == selected_grade) &
            (pd.to_numeric(df[sdg_id_col], errors="coerce") == selected_sdg_id)
        ].copy()

        if location_col:
            filtered = filtered[
                filtered[location_col].astype(str).str.strip().str.lower()
                == selected_location.strip().lower()
            ]

        if filtered.empty:
            st.error("No data found for selected location, class, and SDG.")
        else:
            try:
                with st.spinner("Generating problem statement..."):
                    problem_statement = generate_with_gemini(
                        filtered,
                        selected_location,
                        selected_grade,
                        selected_sdg_id,
                        selected_sdg_goal,
                        subject_col,
                        topic_col,
                        context_col
                    )

                st.session_state.generated_problem = one_line(problem_statement)
                st.session_state.last_cache_key = cache_key

            except Exception as e:
                st.session_state.generated_problem = None
                st.error(f"Error: {str(e)}")

if st.session_state.generated_problem:
    st.subheader("Generated Problem Statement")
    st.info(st.session_state.generated_problem)
