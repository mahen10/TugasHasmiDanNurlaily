import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np
import os
from groq import Groq
from dotenv import load_dotenv

# ===============================
# LOAD API KEY
# ===============================
GROQ_API_KEY = st.secrets["GROQ_API_KEY"]

if not GROQ_API_KEY:
    st.error("🚨 API Key 'GROQ_API_KEY' tidak ditemukan! Cek file .env kamu.")
    st.stop()

client = Groq(api_key=GROQ_API_KEY)

# ===============================
# STREAMLIT UI CONFIG
# ===============================
st.set_page_config(page_title="Financial Copilot AI", layout="wide")
st.title("📊 Financial Copilot AI – Scenario Planning & Insights")

# ===============================
# MODEL SELECTOR (UPDATED)
# ===============================
selected_model = st.selectbox(
    "🤖 Select AI Model",
    [
        "llama-3.1-8b-instant",
        "llama-3.1-70b-versatile",
        "mixtral-8x7b-8k"
    ]
)

# ===============================
# FILE UPLOADER
# ===============================
uploaded_file = st.file_uploader("📂 Upload your dataset (CSV/Excel)", type=["csv", "xlsx"])

if uploaded_file:

    # Read file safely
    try:
        if uploaded_file.name.endswith(".csv"):
            df = pd.read_csv(uploaded_file)
        else:
            df = pd.read_excel(uploaded_file, engine="openpyxl")
    except Exception as e:
        st.error(f"❌ File gagal dibaca: {e}")
        st.stop()

    st.subheader("📄 Preview Data")
    st.write(df.head())

    numeric_cols = df.select_dtypes(include=['int64', 'float64']).columns.tolist()

    if len(numeric_cols) == 0:
        st.error("⚠️ Dataset tidak memiliki kolom numerik.")
        st.stop()

    selected_col = st.selectbox("📌 Pilih kolom numerik untuk simulasi skenario:", numeric_cols)
    scenario_prompt = st.text_area("📝 Enter a financial scenario (optional)")

    # ===============================
    # GENERATE SCENARIOS
    # ===============================
    if st.button("🚀 Generate Scenarios"):

        df["Optimistic"] = df[selected_col] * np.random.uniform(1.1, 1.3, len(df))
        df["Pessimistic"] = df[selected_col] * np.random.uniform(0.7, 0.9, len(df))
        df["Worst Case"] = df[selected_col] * np.random.uniform(0.5, 0.7, len(df))

        col1, col2 = st.columns([2, 1])

        # ===============================
        # LEFT SIDE — TABLE + CHART
        # ===============================
        with col1:
            st.subheader("📊 Scenario Projections")
            st.dataframe(df)

            fig = px.bar(
                df,
                x=df.index.astype(str),
                y=[selected_col, "Optimistic", "Pessimistic", "Worst Case"],
                title=f"📈 Scenario Planning for: {selected_col}",
                barmode="group"
            )
            st.plotly_chart(fig, use_container_width=True)

        # ===============================
        # RIGHT SIDE — AI INSIGHTS
        # ===============================
        with col2:
            st.subheader("🤖 AI Insight Generator")

            df_preview = df.head(20).to_string(index=False)

            try:
                response = client.chat.completions.create(
                    model=selected_model,
                    messages=[
                        {"role": "system", "content": "You are an AI Financial Copilot."},
                        {
                            "role": "user",
                            "content": f"Here is the data:\n{df_preview}\nScenario: {scenario_prompt}\nGive key insights."
                        }
                    ]
                )

                st.markdown("**AI Analysis:**")
                st.write(response.choices[0].message.content)

            except Exception as e:
                st.error(f"⚠️ AI failed: {e}")

# =====================================================
# CHAT SECTION — LETAKKAN DI LUAR BLOK SCENARIO
# =====================================================
st.subheader("💬 Financial Copilot Chat")

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

user_query = st.text_input("Ask anything…")

colA, colB = st.columns([4, 1])
send_btn = colA.button("Send")
reset_btn = colB.button("Clear Chat")

if reset_btn:
    st.session_state.chat_history = []
    st.success("Chat cleared!")

if send_btn and user_query:
    try:
        chat_resp = client.chat.completions.create(
            model=selected_model,
            messages=[
                {"role": "system", "content": "You are a financial copilot."},
                *st.session_state.chat_history,
                {"role": "user", "content": user_query}
            ]
        )

        ai_reply = chat_resp.choices[0].message.content

        st.session_state.chat_history.append({"role": "user", "content": user_query})
        st.session_state.chat_history.append({"role": "assistant", "content": ai_reply})

    except Exception as e:
        st.error(f"⚠️ Chat error: {e}")

# Show chat
for msg in st.session_state.chat_history:
    role = "👤 You" if msg["role"] == "user" else "🤖 Copilot"
    st.markdown(f"**{role}:** {msg['content']}")

        # Show chat
for msg in st.session_state.chat_history:
            role = "👤 You" if msg["role"] == "user" else "🤖 Copilot"
            st.markdown(f"**{role}:** {msg['content']}")
