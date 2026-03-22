import os
import json
import re
import streamlit as st
import pandas as pd

try:
    from openai import OpenAI
except ImportError:
    OpenAI = None

st.set_page_config(page_title="TPS Engine", layout="wide")

st.title("Nano Mech Labs - TPS Engine")
st.markdown("### Kanyakumari SDG Problem Generator")

if "generated_problem" not in st.session_state:
    st.session_state.generated_problem = None


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


def tokenize(text):
    text = clean_text(text).lower()
    return set(re.findall(r"[a-zA-Z]+", text))


def one_line(text):
    return " ".join(str(text).split())


def get_sdg_keywords(sdg_goal_text, sdg_number):
    base_keywords = tokenize(sdg_goal_text)

    sdg_map = {
        1: {"poverty", "income", "livelihood", "employment", "work", "fishermen", "season", "earning"},
        2: {"food", "nutrition", "hunger", "fish", "farming", "agriculture"},
        3: {"health", "disease", "sanitation", "wellbeing", "clean"},
        4: {"education", "learning", "school", "literacy"},
        5: {"women", "girls", "gender", "equality", "safety"},
        6: {"water", "sanitation", "drinking", "wastewater", "clean"},
        7: {"energy", "electricity", "solar", "power", "circuit"},
        8: {"jobs", "income", "industry", "economic", "livelihood", "business"},
        9: {"innovation", "technology", "infrastructure", "machine", "design"},
        10: {"inclusion", "equity", "access"},
        11: {"city", "community", "housing", "transport", "waste"},
        12: {"waste", "recycling", "plastic", "consumption", "production"},
        13: {"climate", "rain", "weather", "disaster", "environment"},
        14: {"sea", "ocean", "fish", "coast", "marine", "fishermen"},
        15: {"forest", "land", "soil", "biodiversity", "plants"},
        16: {"justice", "peace", "rights", "safety"},
        17: {"partnership", "collaboration", "community"},
    }

    return base_keywords.union(sdg_map.get(int(sdg_number), set()))


def score_topic(row, subject_col, topic_col, context_col, sdg_keywords):
    subject_words = tokenize(row[subject_col])
    topic_words = tokenize(row[topic_col])
    context_words = tokenize(row[context_col])

    score = 0
    score += len(topic_words.intersection(sdg_keywords)) * 3
    score += len(subject_words.intersection(sdg_keywords)) * 2
    score += len(context_words.intersection(sdg_keywords)) * 4

    topic_text = clean_text(row[topic_col]).lower()
    subject_text = clean_text(row[subject_col]).lower()

    if "food" in topic_text and ("hunger" in sdg_keywords or "nutrition" in sdg_keywords or "fish" in sdg_keywords):
        score += 5
    if "rain" in topic_text and ("rain" in sdg_keywords or "climate" in sdg_keywords or "season" in sdg_keywords):
        score += 5
    if ("electric" in topic_text or "circuit" in topic_text or "energy" in subject_text) and (
        "solar" in sdg_keywords or "energy" in sdg_keywords or "power" in sdg_keywords
    ):
        score += 5
    if "waste" in topic_text and ("waste" in sdg_keywords or "plastic" in sdg_keywords):
        score += 5
    if "fish" in context_words and ("fish" in sdg_keywords or "marine" in sdg_keywords or "fishermen" in sdg_keywords):
        score += 5

    return score


def build_problem_statement(location, grade, sdg_goal, local_context, top_topics):
    topic_names = [clean_text(row["topic"]) for row in top_topics if clean_text(row["topic"])]
    subject_names = [clean_text(row["subject"]) for row in top_topics if clean_text(row["subject"])]

    topic_phrase = ", ".join(topic_names[:3]) if topic_names else "relevant classroom concepts"
    subject_phrase = ", ".join(sorted(set(subject_names))) if subject_names else "relevant subjects"

    statement = (
        f"For Grade {grade} students in {location}, how can {local_context} be solved through the SDG goal '{sdg_goal}' using concepts from {subject_phrase} such as {topic_phrase}?"
    )
    return one_line(statement)


def generate_with_rules(filtered, selected_location, selected_grade, selected_sdg_id, selected_sdg_goal,
                        subject_col, topic_col, context_col):
    sdg_keywords = get_sdg_keywords(selected_sdg_goal, selected_sdg_id)

    scored_rows = []
    for _, row in filtered.iterrows():
        score = score_topic(row, subject_col, topic_col, context_col, sdg_keywords)
        scored_rows.append({"row": row, "score": score})

    scored_rows = sorted(scored_rows, key=lambda x: x["score"], reverse=True)
    top_scored = scored_rows[:3]

    top_topics = []
    for item in top_scored:
        row = item["row"]
        top_topics.append({
            "subject": clean_text(row[subject_col]),
            "topic": clean_text(row[topic_col]),
            "context": clean_text(row[context_col]),
        })

    local_context = top_topics[0]["context"] if top_topics else f"a local issue in {selected_location}"
    problem_statement = build_problem_statement(
        selected_location,
        selected_grade,
        selected_sdg_goal,
        local_context,
        top_topics
    )
    return one_line(problem_statement)

def generate_with_openai(filtered, selected_location, selected_grade, selected_sdg_id, selected_sdg_goal,
                         subject_col, topic_col, context_col):

    api_key = os.getenv("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")
    if not api_key or OpenAI is None:
        raise ValueError("OpenAI unavailable")

    client = OpenAI(api_key=api_key)

    topic_candidates = []
    for _, row in filtered.iterrows():
        topic_candidates.append({
            "subject": clean_text(row[subject_col]),
            "topic": clean_text(row[topic_col]),
            "context": clean_text(row[context_col]),
        })

    topic_candidates = topic_candidates[:30]

    prompt = f"""
You are an expert school curriculum designer.

Student input:
- Location: {selected_location}
- Class: {selected_grade}
- SDG Goal: {selected_sdg_goal}

Available topics:
{json.dumps(topic_candidates, ensure_ascii=False)}

Your task:
1. Understand the real local problem in {selected_location}.
2. Select the most relevant school topics that can help solve it.
3. Create ONE real-life problem statement.

STRICT RULES:
- Use very simple language (student-friendly).
- Must sound like a real-life situation.
- Must be practical and local (fishermen, rain, food, waste, etc.).
- Must NOT sound like textbook or exam language.
- MUST be ONE line only.
- Start with real context (not "design", not "analyze").
- Prefer "How can..." or "In {selected_location} how can..."

GOOD EXAMPLE:
Using the fish produced in Kanyakumari how can fishermen create value-added products and earn income during rainy season using solar dryers?

BAD EXAMPLE:
Design a sustainable solution for poverty using interdisciplinary concepts.

Return ONLY JSON:
{{
  "problem_statement": "your sentence"
}}
"""

    response = client.responses.create(
        model="gpt-4.1-mini",
        input=prompt
    )

    raw_text = response.output_text.strip()
    data = json.loads(raw_text)

    return one_line(data["problem_statement"])


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

if st.button("Generate Problem Statement"):
    filtered = df[
        (df[grade_col] == selected_grade) &
        (pd.to_numeric(df[sdg_id_col], errors="coerce") == selected_sdg_id)
    ].copy()

    if location_col:
        filtered = filtered[
            filtered[location_col].astype(str).str.strip().str.lower() == selected_location.strip().lower()
        ]

    if filtered.empty:
        st.error("No data found for selected location, class, and SDG.")
    else:
        try:
            problem_statement = generate_with_openai(
                filtered,
                selected_location,
                selected_grade,
                selected_sdg_id,
                selected_sdg_goal,
                subject_col,
                topic_col,
                context_col
            )
        except Exception:
            problem_statement = generate_with_rules(
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

if st.session_state.generated_problem:
    st.subheader("Generated Problem Statement")
    st.info(st.session_state.generated_problem)
