import traceback
import streamlit as st
from url_fetcher import fetch_text_from_url
from study_engine import generate_flashcards, generate_quiz, call_gemini

st.set_page_config(page_title="AI Study Assistant", page_icon="📚", layout="wide")

st.title("📚 AI Study Assistant")
st.subheader("Generate Syllabus-Aligned Flashcards, Quizzes & AI Explanations")

# Sidebar for Exam Board & Level configuration
with st.sidebar:
    st.header("⚙️ Exam Settings")
    exam_board = st.selectbox("Exam Board", ["AQA", "OCR", "Edexcel", "CIE", "General / Other"])
    level = st.selectbox("Education Level", ["A-Level", "GCSE", "University / Undergraduate", "General"])
    
    st.markdown("---")
    st.markdown("### 📥 Source Material")
    input_type = st.radio("Choose input method:", ["Paste Notes", "Web URL (e.g. Physics / Thermal Physics)", "Upload File (.txt, .md)"])

study_text = ""

if input_type == "Paste Notes":
    study_text = st.text_area(
        "Paste your study notes or syllabus content here:",
        height=200,
        placeholder="e.g. Specific heat capacity is defined as the amount of energy required to raise the temperature of 1kg of a substance by 1K..."
    )
elif input_type == "Web URL (e.g. Physics / Thermal Physics)":
    url_input = st.text_input(
        "Enter Web URL:",
        placeholder="[suspicious link removed]"
    )
    if url_input:
        with st.spinner("Fetching content from web page..."):
            study_text = fetch_text_from_url(url_input)
            if study_text.startswith("Error") or study_text.startswith("Could not"):
                st.error(study_text)
                study_text = ""
            else:
                st.success(f"Successfully extracted article content ({len(study_text)} characters)")
                with st.expander("Preview Extracted Text"):
                    st.write(study_text[:1000] + "...")
elif input_type == "Upload File (.txt, .md)":
    uploaded_file = st.file_uploader("Upload a text or markdown file", type=["txt", "md"])
    if uploaded_file is not None:
        study_text = uploaded_file.read().decode("utf-8")
        st.success("File uploaded successfully!")

st.markdown("---")

# Navigation Tabs
tab1, tab2, tab3 = st.tabs(["🎴 Flashcards", "❓ Interactive Quiz", "🤖 AI Tutor Explainer"])

# ----------------------------
# TAB 1: FLASHCARDS
# ----------------------------
with tab1:
    st.header("Interactive Flashcards")
    card_count = st.slider("Number of flashcards", 3, 10, 5, key="fc_count")
    
    if st.button("Generate Flashcards", type="primary", key="btn_fc"):
        if not study_text.strip():
            st.warning("Please provide study notes or a valid Web URL first!")
        else:
            try:
                with st.spinner("AI thinking... (retrying automatically if busy)"):
                    cards = generate_flashcards(study_text, exam_board, level, card_count)
                st.session_state["flashcards"] = cards
            except Exception as e:
                st.session_state.pop("flashcards", None)
                st.error(f"Error generating flashcards: {e}")
                st.code(traceback.format_exc())

    # Render outside button block so state persists across reruns
    for idx, card in enumerate(st.session_state.get("flashcards", []), 1):
        with st.expander(f"Card {idx}: {card['question']}"):
            st.markdown(f"**Answer:** {card['answer']}")

# ----------------------------
# TAB 2: INTERACTIVE QUIZ
# ----------------------------
with tab2:
    st.header("Multiple Choice Quiz")
    quiz_count = st.slider("Number of questions", 3, 10, 5, key="q_count")
    
    if st.button("Generate Quiz", type="primary", key="btn_q"):
        if not study_text.strip():
            st.warning("Please provide study notes or a valid Web URL first!")
        else:
            try:
                with st.spinner("AI thinking... (creating exam-style quiz)"):
                    quiz_data = generate_quiz(study_text, exam_board, level, quiz_count)
                st.session_state["quiz"] = quiz_data
            except Exception as e:
                st.session_state.pop("quiz", None)
                st.error(f"Error generating quiz: {e}")
                st.code(traceback.format_exc())

    # Render quiz from session state outside button block
    quiz_list = st.session_state.get("quiz", [])
    if quiz_list:
        with st.form("quiz_form"):
            user_answers = {}
            for idx, q in enumerate(quiz_list, 1):
                st.markdown(f"### Q{idx}. {q['question']}")
                user_answers[idx] = st.radio(
                    "Select an answer:",
                    q["options"],
                    key=f"q_{idx}",
                    index=None
                )
                st.markdown("---")
            
            submit_quiz = st.form_submit_button("Submit Quiz Answers")
            if submit_quiz:
                score = 0
                total = len(quiz_list)
                st.header("📊 Results")
                for idx, q in enumerate(quiz_list, 1):
                    selected = user_answers.get(idx)
                    correct = q["correct"]
                    
                    is_correct = False
                    if selected:
                        if selected == correct or selected.startswith(correct) or correct in selected:
                            is_correct = True

                    if is_correct:
                        score += 1
                        st.success(f"**Q{idx}: Correct!** ✅")
                    else:
                        st.error(f"**Q{idx}: Incorrect** ❌ (Your answer: {selected if selected else 'None'} | Correct: {correct})")
                    
                    st.info(f"💡 **Mark Scheme / Working:** {q['explanation']}")
                    st.markdown("---")
                
                st.metric("Final Score", f"{score} / {total}", f"{(score/total)*100:.1f}%")

# ----------------------------
# TAB 3: AI TUTOR EXPLAINER
# ----------------------------
with tab3:
    st.header("Ask AI Tutor")
    st.write("Have a question about a tricky topic in your study material?")
    question_input = st.text_input("Ask a question (e.g. 'Explain ideal gas law assumptions for A-Level AQA'):")
    
    if st.button("Ask AI Tutor", key="btn_tutor"):
        if not question_input.strip():
            st.warning("Please enter a question!")
        elif not study_text.strip():
            st.warning("Please provide study notes or a valid Web URL first!")
        else:
            try:
                prompt = (
                    f"You are an expert {level} tutor for the {exam_board} board.\n"
                    f"Based on the study material below, answer this question clearly with syllabus rigor:\n\n"
                    f"Question: {question_input}\n\nStudy Material:\n{study_text[:4000]}"
                )
                with st.spinner("AI Tutor is thinking..."):
                    answer = call_gemini(prompt)
                st.session_state["ai_tutor_answer"] = answer
            except Exception as e:
                st.session_state.pop("ai_tutor_answer", None)
                st.error(f"Error asking AI Tutor: {e}")
                st.code(traceback.format_exc())

    # Render AI Tutor response outside button block
    if "ai_tutor_answer" in st.session_state:
        st.markdown("### Answer")
        st.markdown(st.session_state["ai_tutor_answer"])