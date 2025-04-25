#!/usr/bin/env python
# coding: utf-8

# In[19]:

import streamlit as st
import pandas as pd
import numpy as np
import altair as alt

# ----------------------------
# 🎨 Custom Page Config
# ----------------------------
st.set_page_config(
    page_title="TrendNav AI Dashboard",
    layout="wide",
    page_icon="📊"
)

# ----------------------------
# 🌈 Custom CSS for center-align + pastel theme
# ----------------------------
st.markdown("""
<style>
    body {
        background-color: #e9f7f6;
    }
    .main {
        background-color: #e9f7f6;
    }
    .block-container {
        padding-top: 1rem;
        padding-bottom: 0rem;
    }
    .metric-card {
        background-color: #d5f4f2;
        border-radius: 15px;
        padding: 1.5rem;
        margin: 1rem;
        box-shadow: 2px 2px 10px rgba(0,0,0,0.05);
        text-align: center;
    }
    .centered {
        display: flex;
        justify-content: center;
        align-items: center;
    }
    .sentiment-radio > div {
        display: flex;
        justify-content: center;
    }
</style>
""", unsafe_allow_html=True)

# ----------------------------
# 🧪 Mock Data Placeholder
# ----------------------------
data = pd.DataFrame({
    'timestamp': pd.date_range(start='2024-01-01', periods=30),
    'phrase_freq': np.random.randint(5, 100, 30),
    'sentiment_score': np.random.choice([-1, 0, 1], size=30),
    'clean_phrase': np.random.choice(['wireless earbuds', 'robot vacuum', 'adjustable desk'], size=30),
    'matched_product': np.random.choice(['Audio Devices', 'Home Appliances', 'Office Furniture'], size=30)
})

# Add computed trend_score
data['trend_score'] = data['sentiment_score'] + data['phrase_freq']
data['sentiment_label'] = data['sentiment_score'].map({1: "Positive", 0: "Neutral", -1: "Negative"})

# ----------------------------
# 🏷️ Header
# ----------------------------
st.markdown("<h1 style='text-align: center;'>📊 TrendNav AI: E-commerce Opportunity Scanner</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center;'>Identifying <b>trending product demands</b> using Reddit & Amazon QA, and mapping them against <b>inventory signals</b> to find high-opportunity areas for sellers.</p>", unsafe_allow_html=True)

# ----------------------------
# 🎛️ Sentiment Selector (Horizontal)
# ----------------------------
sentiment_map = {
    "🟢 Positive": 1,
    "🟡 Neutral": 0,
    "🔴 Negative": -1,
    "All": "All"
}
st.markdown("<div class='sentiment-radio'>", unsafe_allow_html=True)
sentiment_choice = st.radio(
    "Select Sentiment", list(sentiment_map.keys()), index=3, horizontal=True, label_visibility="collapsed"
)
st.markdown("</div>", unsafe_allow_html=True)

sentiment_val = sentiment_map[sentiment_choice]
if sentiment_val != "All":
    filtered_data = data[data['sentiment_score'] == sentiment_val]
else:
    filtered_data = data.copy()

# ----------------------------
# 🔢 KPI Metric Cards
# ----------------------------
total_mentions = int(filtered_data['phrase_freq'].sum())
top_keyword = filtered_data['clean_phrase'].value_counts().idxmax()
top_subcategory = filtered_data['matched_product'].value_counts().idxmax()

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("<div class='metric-card'>", unsafe_allow_html=True)
    st.metric("🔁 Total Mentions", f"{total_mentions}")
    st.altair_chart(
        alt.Chart(filtered_data).mark_line(point=True).encode(
            x='timestamp:T', y='phrase_freq:Q'
        ).properties(width=200, height=60), use_container_width=False
    )
    st.markdown("</div>", unsafe_allow_html=True)

with col2:
    st.markdown("<div class='metric-card'>", unsafe_allow_html=True)
    st.metric("💬 Top Product Keyword", f"{top_keyword}")
    st.markdown("</div>", unsafe_allow_html=True)

with col3:
    st.markdown("<div class='metric-card'>", unsafe_allow_html=True)
    st.metric("📦 Top Subcategory", f"{top_subcategory}")
    st.markdown("</div>", unsafe_allow_html=True)

# ----------------------------
# 🧠 Summary Insight
# ----------------------------
summary_text = {
    1: f"💚 Positive sentiment is growing around **{top_keyword}**, especially in **{top_subcategory}**.",
    0: f"🟡 Mixed or uncertain feedback around **{top_keyword}**, with variable attention in **{top_subcategory}**.",
    -1: f"🔴 Negative sentiment dominates for **{top_keyword}**, suggesting possible product gaps in **{top_subcategory}**.",
    "All": f"📊 Overall, **{top_keyword}** is a consistent trend keyword across **{top_subcategory}**."
}
st.markdown(f"<p style='text-align: center; font-size:18px;'>{summary_text[sentiment_val]}</p>", unsafe_allow_html=True)

