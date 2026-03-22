
import streamlit as st
import pandas as pd

st.set_page_config(page_title="TPS Engine ", layout="wide")

TEMPERATURE_LEVELS = [0.2, 0.5, 0.8]

st.title("Nano Mech Labs - TPS Engine ")
st.markdown("### Kanyakumari SDG Problem Generator")

if "generated_results" not in st.session_state:
    st.session_state.generated_results = None

if "selected_problem" not in st.session_state:
    st.session_state.selected_problem = None

st.sidebar.header("Upload Kanyakumari Excel File")
file = st.sidebar.file_uploader("Upload Excel File", type=["xlsx"])

def find_column(df, possible_names):
    for col in df.columns:
        clean = str(col).strip().lower()
        if clean in [name.strip().lower() for name in possible_names]:
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
            f"Sustainable Development Goal '{sdg_goal}'."
        )
    elif temperature == 0.5:
        return (
            f"Apply the Grade {grade} {subject} topic '{topic}' to analyze the sustainability "
            f"related to the Sustainable Development Goal '{sdg_goal}'."
        )
    else:
        return (
            f"Using the Grade {grade} {subject} concept '{topic}', design an innovative solution "
            f"and contribute toward achieving the Sustainable Development Goal '{sdg_goal}'."
        )

if file:
    try:
        df = pd.read_excel(file)

        grade_col = find_column(df, ["Grade"])
        subject_col = find_column(df, ["Subject"])
        topic_col = find_column(df, ["Topic"])
        sdg_number_col = find_column(df, ["SDG_Number", "SDG_Number"])
        sdg_goal_col = find_column(df, ["SDG_Goal", "SDG Goal", "Goal"])
        context_col = find_column(df, ["Context", "Localized SDG Goals", "Problem Context"])

        required = {
            "Grade": grade_col,
            "Subject": subject_col,
            "Topic": topic_col,
            "SDG_Number": sdg_number_col,
            "SDG_Goal": sdg_goal_col,
            "Context": context_col,
        }

        missing = [k for k, v in required.items() if v is None]
        if missing:
            st.error(f"Missing required columns in Excel file: {', '.join(missing)}")
            st.stop()

        st.success("Kanyakumari Excel file loaded successfully")

        grades = sorted(df[grade_col].dropna().unique().tolist())
        sdg_values = df[[sdg_number_col, sdg_goal_col]].dropna().drop_duplicates().sort_values(by=sdg_number_col)

        sdg_options = [
            f"{int(row[sdg_number_col])} - {row[sdg_goal_col]}"
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
                (pd.to_numeric(df[sdg_number_col], errors="coerce") == selected_sdg_id)
            ]

            if filtered.empty:
                st.error("No data found for selected Grade and SDG")
            else:
                row = filtered.sample(1).iloc[0]
                st.session_state.generated_results = [
                    generate_problem(
                        row, temp, grade_col, subject_col, topic_col, sdg_goal_col, context_col
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

    except Exception as e:
        st.error(f"Error reading Excel file: {e}")

else:
    st.warning("Please upload only the Kanyakumari Excel file.")
