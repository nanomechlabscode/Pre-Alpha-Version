import streamlit as st
import pandas as pd

st.set_page_config(page_title="TPS Engine", layout="wide")

TEMPERATURE_LEVELS = [0.2, 0.5, 0.8]

st.title("Nano Mech Labs - TPS Engine")
st.markdown("### Kanyakumari SDG Problem Generator")

if "generated_results" not in st.session_state:
    st.session_state.generated_results = None

if "selected_problem" not in st.session_state:
    st.session_state.selected_problem = None


def find_column(df, possible_names):
    possible_names_clean = [name.strip().lower() for name in possible_names]
    for col in df.columns:
        if str(col).strip().lower() in possible_names_clean:
            return col
    return None


def generate_problem(row, temperature, grade_col, subject_col, topic_col, sdg_goal_col, context_col):
    grade = row[grade_col]
    subject = row[subject_col]
    topic = row[topic_col]
    sdg_goal = row[sdg_goal_col]
    context = row[context_col]

    if temperature == 0.2:
        return (
            f"Using the Grade {grade} {subject} concept '{topic}', explain how the issue "
            f"'{context}' can be understood and relate it to the Sustainable Development Goal "
            f"'{sdg_goal}'."
        )
    elif temperature == 0.5:
        return (
            f"Apply the Grade {grade} {subject} topic '{topic}' to analyze the sustainability "
            f"challenge '{context}' and examine causes and impacts related to the Sustainable "
            f"Development Goal '{sdg_goal}'."
        )
    else:
        return (
            f"Using the Grade {grade} {subject} concept '{topic}', design an innovative solution "
            f"to address the issue '{context}' and contribute toward achieving the Sustainable "
            f"Development Goal '{sdg_goal}'."
        )


try:
    df = pd.read_excel("Kanyakumari.xlsx")
except Exception as e:
    st.error(f"Could not read Kanyakumari.xlsx: {e}")
    st.stop()

grade_col = find_column(df, ["Grade"])
subject_col = find_column(df, ["Subject"])
topic_col = find_column(df, ["Topic"])
sdg_id_col = find_column(df, ["SDG_ID", "SDG ID", "SDG_Number", "SDG Number"])
sdg_goal_col = find_column(df, ["SDG_Goal", "SDG Goal", "Goal"])
context_col = find_column(df, ["Context", "Localized SDG Goals", "Problem Context"])

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

col1, col2 = st.columns(2)

with col1:
    selected_grade = st.selectbox("Select Grade", grades)

with col2:
    selected_sdg_option = st.selectbox("Select SDG Goal", sdg_options)

selected_sdg_id = int(selected_sdg_option.split(" - ")[0])

if st.button("Generate Problem Statements"):
    filtered = df[
        (df[grade_col] == selected_grade) &
        (pd.to_numeric(df[sdg_id_col], errors="coerce") == selected_sdg_id)
    ]

    if filtered.empty:
        st.error("No data found for selected Grade and SDG")
    else:
        row = filtered.sample(1).iloc[0]
        st.session_state.generated_results = [
            generate_problem(
                row,
                temp,
                grade_col,
                subject_col,
                topic_col,
                sdg_goal_col,
                context_col
            )
            for temp in TEMPERATURE_LEVELS
        ]
        st.session_state.selected_problem = None

if st.session_state.generated_results:
    st.subheader("Generated Problem Statements")

    labels = []
    for i, statement in enumerate(st.session_state.generated_results, start=1):
        label = f"Problem Statement {i}"
        labels.append(label)
        st.info(statement)
        st.markdown("---")

    selected_label = st.radio("Select one problem statement:", labels)

    if st.button("Proceed"):
        idx = labels.index(selected_label)
        st.session_state.selected_problem = st.session_state.generated_results[idx]

if st.session_state.selected_problem:
    st.subheader("Selected Problem Statement")
    st.success(st.session_state.selected_problem)
