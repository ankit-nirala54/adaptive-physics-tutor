import streamlit as st
import json
import plotly.express as px
import networkx as nx
from google import genai

st.set_page_config(page_title="Adaptive AI Tutor", page_icon="🧠", layout="wide")

# Initialize Google GenAI client safely using Streamlit secrets
try:
    client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])
except:
    client = None

# --- 2. EXPANDED CONCEPT GRAPH (DAG WITH PREREQUISITES) ---
if "concept_graph" not in st.session_state:
    st.session_state.concept_graph = {
        "Reflection Laws": {"prereqs": [], "mastery": 0.2},
        "Curved Mirrors": {"prereqs": ["Reflection Laws"], "mastery": 0.2},
        "Mirror Formula": {"prereqs": ["Curved Mirrors"], "mastery": 0.2},
        "Refraction (Snell's Law)": {"prereqs": ["Reflection Laws"], "mastery": 0.2},
        "Lens Formula": {"prereqs": ["Refraction (Snell's Law)"], "mastery": 0.2}
    }

if "misconception_logs" not in st.session_state:
    st.session_state.misconception_logs = []

# --- SIDEBAR NAVIGATION ---
st.sidebar.title("Navigation")
app_mode = st.sidebar.selectbox("Choose Mode", ["Student Mode (Adaptive Practice)", "Teacher Dashboard"])

# --- 1. & 2. STUDENT MODE (Adaptive Selection & Misconception Detection) ---
if app_mode == "Student Mode (Adaptive Practice)":
    st.title("💡 Class 10 Physics: Adaptive Optics Tutor")
    st.write("Our agent analyzes your step-by-step reasoning, catches specific conceptual mistakes, and adapts your learning path.")

    graph = st.session_state.concept_graph

    # Find unlocked concepts whose prerequisites are satisfied (mastery >= 0.5) or root nodes
    available_concepts = {}
    for node, data in graph.items():
        prereqs_met = all(graph[p]["mastery"] >= 0.5 for p in data["prereqs"])
        if prereqs_met or not data["prereqs"]:
            available_concepts[node] = data["mastery"]

    if not available_concepts:
        available_concepts = {"Reflection Laws": graph["Reflection Laws"]["mastery"]}

    # Target the concept with the lowest mastery among available nodes
    weakest_concept = min(available_concepts, key=available_concepts.get)
    current_score = graph[weakest_concept]["mastery"]

    st.info(f"🎯 **Active Target Concept:** {weakest_concept} (Current Mastery: {current_score:.2f})")

    # Questions bank mapped to concepts
    question_bank = {
        "Reflection Laws": "A light ray strikes a plane mirror at a 30° angle to the mirror surface. What is the angle of reflection, and why?",
        "Curved Mirrors": "Explain why concave mirrors are preferred over convex mirrors for shaving or makeup mirrors.",
        "Mirror Formula": "An object is placed 30 cm in front of a concave mirror with a focal length of 15 cm. Calculate image distance and explain sign conventions.",
        "Refraction (Snell's Law)": "Why does a pool of water look shallower than it actually is? Explain using refraction principles.",
        "Lens Formula": "A convex lens has a focal length of 20 cm. Where should an object be placed to get a real image of the same size?"
    }

    st.subheader("Practice Problem:")
    st.write(question_bank.get(weakest_concept, "Explain the core mechanics of this topic."))

    student_reasoning = st.text_area("Type your final answer AND explain your step-by-step reasoning:")

    if st.button("Submit Answer & Analyze"):
        if student_reasoning.strip():
            with st.spinner("AI Agent analyzing your reasoning & diagnosing errors..."):
                
                # Fallback check if API key isn't provided yet
                if client is None:
                    st.error("GEMINI_API_KEY missing in Streamlit Secrets! Please add it to test live LLM grading.")
                else:
                    # --- GOOGLE GENAI MISCONCEPTION DETECTION PROMPT ---
                    prompt = f"""
                    You are an expert physics teacher and diagnostic AI. 
                    Concept: {weakest_concept}
                    Question: {question_bank.get(weakest_concept)}
                    Student Answer & Reasoning: {student_reasoning}

                    Analyze the student's reasoning carefully. Look for deep conceptual flaws, not just math slips.
                    Return a valid JSON object ONLY, with EXACTLY these keys:
                    - "is_correct": boolean (true/false)
                    - "misconception_tag": string (short label of the misconception if wrong, e.g., "Sign Convention Error", "Refractive Index Inversion", or "None")
                    - "feedback": string (constructive explanation pointing out why their logic works or failed)
                    """

                    try:
                        response = client.models.generate_content(
    model="gemini-2.5-flash",
    contents=prompt,
)
                        
                        # Clean potential markdown code block formatting from response text
                        raw_text = response.text.strip()
                        if raw_text.startswith("```json"):
                            raw_text = raw_text[7:]
                        if raw_text.endswith("```"):
                            raw_text = raw_text[:-3]
                            
                        result = json.loads(raw_text.strip())
                        
                        is_correct = result.get("is_correct", False)
                        tag = result.get("misconception_tag", "General Error")
                        feedback = result.get("feedback", "Review the concept notes.")

                        if is_correct:
                            st.success(f"✅ **Correct!** {feedback}")
                            # Bayesian mastery boost
                            graph[weakest_concept]["mastery"] = min(1.0, current_score + 0.35 * (1.0 - current_score))
                        else:
                            st.error(f"❌ **Incorrect.** **Misconception Flagged:** `{tag}`\n\n{feedback}")
                            # Penalty reduction
                            graph[weakest_concept]["mastery"] = max(0.0, current_score - 0.25 * current_score)
                            # Log misconception for teacher dashboard
                            st.session_state.misconception_logs.append({"concept": weakest_concept, "tag": tag})

                        st.rerun()

                    except Exception as e:
                        st.error(f"Error communicating with Google GenAI: {e}")
        else:
            st.warning("Please type your explanation first.")

# --- 3. POLISHED TEACHER DASHBOARD ---
elif app_mode == "Teacher Dashboard":
    st.title("📊 Class-Wide Analytics & Gaps Dashboard")
    st.write("Real-time telemetry showing student mastery bottlenecks and prevalent conceptual misconceptions.")

    graph = st.session_state.concept_graph

    # Prepare data for Plotly bar chart
    concepts_list = list(graph.keys())
    mastery_scores = [graph[c]["mastery"] for c in concepts_list]

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("🌐 Concept Mastery Heatmap")
        fig = px.bar(
            x=mastery_scores,
            y=concepts_list,
            orientation='h',
            labels={"x": "Average Class Mastery Score", "y": "Syllabus Concept"},
            title="Syllabus Bottleneck Analysis",
            color=mastery_scores,
            color_continuous_scale="Reds"
        )
        fig.update_layout(xaxis=dict(range=[0, 1]))
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.subheader("🚨 Most Frequent Misconceptions")
        if st.session_state.misconception_logs:
            # Count tags
            tag_counts = {}
            for log in st.session_state.misconception_logs:
                t = log["tag"]
                tag_counts[t] = tag_counts.get(t, 0) + 1
            
            fig_pie = px.pie(
                names=list(tag_counts.keys()),
                values=list(tag_counts.values()),
                title="Error Distribution Breakdown"
            )
            st.plotly_chart(fig_pie, use_container_width=True)
        else:
            st.info("No student misconception logs recorded yet. Switch to Student Mode and submit a wrong answer to populate this chart!")

    st.markdown("---")
    st.subheader("📋 Detailed Concept Graph Prerequisite Tree")
    for concept, data in graph.items():
        status = "🟢 Unlocked" if (all(graph[p]["mastery"] >= 0.5 for p in data["prereqs"]) or not data["prereqs"]) else "🔒 Locked (Prerequisite needed)"
        st.write(f"- **{concept}** | Prereqs: *{', '.join(data['prereqs']) if data['prereqs'] else 'None'}* | Status: {status} | Mastery: `{data['mastery']:.2f}`")
