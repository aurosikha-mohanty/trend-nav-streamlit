#!/usr/bin/env python
# coding: utf-8

# In[19]:
import streamlit as st
import pandas as pd
import altair as alt

# -----------------------
# THEME COLORS
# -----------------------
BG_COLOR = "#f5fefd"
CARD_COLOR = "#d6f5f2"
TEXT_COLOR = "#0b6da4"

# -----------------------
# LOAD DATA
# -----------------------
@st.cache_data
def load_data():
    df = pd.read_csv("matched_df_v2.csv", parse_dates=['timestamp'])
    df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')
    df['sentiment_score'] = pd.to_numeric(df['sentiment_score'], errors='coerce')
    df['phrase_freq'] = pd.to_numeric(df['phrase_freq'], errors='coerce')
    df['trend_score'] = df['sentiment_score'].fillna(0) + df['phrase_freq'].fillna(0)
    df['sentiment_label'] = df['sentiment_score'].apply(
        lambda x: 'Positive' if x == 1 else 'Negative' if x == -1 else 'Neutral'
    )
    return df

df = load_data()

# -----------------------
# PAGE CONFIG + HEADER
# -----------------------
st.set_page_config(page_title="TrendNav AI", layout="wide", page_icon="📊")

st.markdown(
    f"""
    <h1 style='text-align: center; color: {TEXT_COLOR};'>📊 TrendNav AI: E-commerce Opportunity Scanner</h1>
    <p style='text-align: center; color: #444;'>Identifying <strong>trending product demands</strong> using Reddit & Amazon QA, and mapping them against <strong>inventory signals</strong> to find high-opportunity areas for sellers.</p>
    """,
    unsafe_allow_html=True,
)

# -----------------------
# SENTIMENT SELECTOR
# -----------------------
st.markdown("<br>", unsafe_allow_html=True)
sentiment_choice = st.radio(
    "🧠 Select Sentiment View:",
    options=['All', 'Positive', 'Neutral', 'Negative'],
    horizontal=True,
    index=0
)

if sentiment_choice != 'All':
    df_filtered = df[df['sentiment_label'] == sentiment_choice]
else:
    df_filtered = df.copy()

# -----------------------
# AGGREGATE + TOP PHRASE
# -----------------------
top_phrase = (
    df_filtered.groupby(['clean_phrase', 'matched_product'])
    .agg(total_mentions=('phrase_freq', 'sum'),
         avg_sentiment=('sentiment_score', 'mean'),
         trend_score=('trend_score', 'sum'))
    .reset_index()
    .sort_values('trend_score', ascending=False)
)

top_row = top_phrase.iloc[0] if not top_phrase.empty else {}

# -----------------------
# KPI CARDS (VERTICAL LEFT)
# -----------------------
with st.container():
    col1, col2 = st.columns([1, 3])

    with col1:
        st.markdown(f"""
            <div style="background-color:{CARD_COLOR}; padding: 20px; border-radius: 20px; margin-bottom: 20px;">
                <h4 style="color:{TEXT_COLOR};">🔑 Top Trending Keyword</h4>
                <h2>{top_row['clean_phrase'] if not top_phrase.empty else 'N/A'}</h2>
                <p><b>Subcategory:</b> {top_row['matched_product'] if not top_phrase.empty else 'N/A'}</p>
            </div>
            <div style="background-color:{CARD_COLOR}; padding: 20px; border-radius: 20px; margin-bottom: 20px;">
                <h4 style="color:{TEXT_COLOR};">📈 Mentions</h4>
                <h2>{int(top_row['total_mentions']) if not top_phrase.empty else '0'}</h2>
            </div>
            <div style="background-color:{CARD_COLOR}; padding: 20px; border-radius: 20px;">
                <h4 style="color:{TEXT_COLOR};">💬 Avg Sentiment</h4>
                <h2>{round(top_row['avg_sentiment'], 2) if not top_phrase.empty else '0.0'}</h2>
            </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown("")

# -----------------------
# DYNAMIC SMART SUMMARY
# -----------------------
summary_map = {
    'Positive': "🌿 Sentiment is strongly positive — these products are resonating well!",
    'Negative': "⚠️ Negative feedback signals product improvement potential.",
    'Neutral': "🟡 Moderate opinions — could go either way!",
    'All': "📊 Viewing combined sentiment — ideal for overall trend monitoring."
}
st.markdown(
    f"<p style='text-align:center; color:#333; font-size: 18px;'>{summary_map.get(sentiment_choice)}</p>",
    unsafe_allow_html=True
)
