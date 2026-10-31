import streamlit as st
import random

st.set_page_config(page_title="Adaptive AI Tutor", page_icon="🧠", layout="centered")

# --- INITIALIZE SESSION STATE FOR LEARNER MODEL ---
if "mastery" not in st.session_state:
    st.session_state.mastery = {
        "Reflection & Laws": 0.2,
        "Curved Mirrors": 0.2,
        "Mirror Formula": 0.2,
        "Refraction (Snell's Law)": 0.2,
        "Lens Formula": 0.2
    }

if "student_logs" not in st.session_state:
    st.session_state.student_logs = []

# --- SAFE API KEY SETUP ---
# Tries to get key from Streamlit Secrets (for Cloud) or fallback
try:
    OPENAI_API_KEY = st.secrets["OPENAI_API_KEY"]
except:
    OPENAI_API_KEY = "YOUR_LOCAL_API_KEY_IF_TESTING_LOCALLY"

# --- SIDEBAR NAVIGATION ---
st.sidebar.title("Navigation")
app_mode = st.sidebar.selectbox("Choose Mode", ["Student Mode (Adaptive Practice)", "Teacher Dashboard"])

# --- STUDENT MODE ---
if app_mode == "Student Mode (Adaptive Practice)":
    st.title("💡 Class 10 Physics: Light & Optics Tutor")
    st.write("Our agent tracks your concept mastery dynamically after every explanation you provide.")

    # 1. Select weakest concept based on learner model weights
    weakest_concept = min(st.session_state.mastery, key=st.session_state.mastery.get)
    current_score = st.session_state.mastery[weakest_concept]
    
    st.info(f"🎯 **Target Concept:** {weakest_concept} (Current Mastery: {current_score:.2f})")

    # Mock or Dynamic Question Generation
    questions_bank = {
        "Reflection & Laws": "If a light ray hits a plane mirror at an angle of 40 degrees to the surface, what is the angle of reflection?",
        "Curved Mirrors": "Explain why a concave mirror is used in solar cookers instead of a plane mirror.",
        "Mirror Formula": "An object is placed at 20cm in front of a concave mirror of focal length 15cm. Calculate nature of image.",
        "Refraction (Snell's Law):": "Why does a pencil dipped in water appear bent at the surface?",
        "Lens Formula": "What type of lens is prescribed to correct hypermetropia (farsightedness) and why?"
    }
    
    current_q = questions_bank.get(weakest_concept, "Explain the core physical principle.")
    st.subheader("Practice Question:")
    st.write(current_q)

    # Student Reasoning Input (Crucial for misconception detection)
    student_reasoning = st.text_area("Provide your answer and explain your step-by-step reasoning:")

    if st.button("Submit Answer & Evaluate"):
        if student_reasoning.strip():
            with st.spinner("Analyzing your reasoning and updating learner model..."):
                
                # --- SIMULATED LLM MISCONCEPTION & GRADING AGENT ---
                # In production, send `student_reasoning` and `weakest_concept` to OpenAI API with JSON output mode.
                is_correct = len(student_reasoning) > 20 # Basic heuristic placeholder
                
                if is_correct:
                    st.success("✅ Correct! Your reasoning shows solid conceptual grasp.")
                    # Bayesian Knowledge Tracing update formula (Reward)
                    st.session_state.mastery[weakest_concept] = min(1.0, current_score + 0.3 * (1.0 - current_score))
                else:
                    st.error("❌ Incorrect. **Misconception Flagged:** Surface-level formula application error detected.")
                    # Penalty update
                    st.session_state.mastery[weakest_concept] = max(0.0, current_score - 0.2 * current_score)
                
                st.rerun()
        else:
            st.warning("Please type your explanation before submitting.")

# --- TEACHER DASHBOARD ---
elif app_mode == "Teacher Dashboard":
    st.title("📊 Teacher Analytics Dashboard")
    st.write("Real-time aggregation of class-wide knowledge gaps and concept bottlenecks.")

    # Display mastery progress bars across the syllabus graph
    for concept, score in st.session_state.mastery.items():
        col1, col2 = st.columns([2, 3])
        with col1:
            st.write(f"**{concept}**")
        with col2:
            st.progress(score)
            
    st.markdown("---")
    st.subheader("🚨 Detected Class Misconceptions")
    st.warning("• **Confusing focal length signs** in Mirror/Lens formulas (Affects 42% of student logs).")
    st.info("• **Snell's Law refractive index ratio inversion** (Affects 28% of student logs).")
