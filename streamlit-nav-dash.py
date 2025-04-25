#!/usr/bin/env python
# coding: utf-8

# In[19]:
import streamlit as st
import pandas as pd
import altair as alt

# -----------------------
# PAGE CONFIG — MUST BE FIRST
# -----------------------
st.set_page_config(page_title="TrendNav AI", layout="wide", page_icon="📊")

# -----------------------
# COLOR THEME
# -----------------------
BG_COLOR = "#f5fefd"
CARD_COLOR = "#d6f5f2"
TEXT_COLOR = "#0b6da4"

# -----------------------
# LOAD DATA
# -----------------------
@st.cache_data
def load_data():
    df = pd.read_csv("matched_df_final_filt.csv", parse_dates=['timestamp'])
    df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')
    df['sentiment_score'] = pd.to_numeric(df['sentiment_score'], errors='coerce')
    df['phrase_freq'] = pd.to_numeric(df['phrase_freq'], errors='coerce')
    df['trend_score'] = df['sentiment_score'].fillna(0) + df['phrase_freq'].fillna(0)
    df['sentiment_label'] = df['sentiment_score'].apply(
        lambda x: 'Positive' if x == 1 else 'Negative' if x == -1 else 'Neutral'
    )
    df['Date'] = df['timestamp'].dt.date
    df['Week'] = df['timestamp'].dt.strftime('%Y-%U')
    df['Month'] = df['timestamp'].dt.to_period('M').astype(str)
    return df

df = load_data()

# -----------------------
# HEADER
# -----------------------
st.markdown(
    f"""
    <h1 style='text-align: center; color: {TEXT_COLOR};'>📊 TrendNav AI: E-commerce Opportunity Scanner</h1>
    <p style='text-align: center; color: #333;'>Identifying <strong>trending product demands</strong> using Reddit & Amazon QA, and mapping them against <strong>inventory signals</strong> to find high-opportunity areas for sellers.</p>
    """,
    unsafe_allow_html=True,
)

# -----------------------
# SENTIMENT FILTER (Global)
# -----------------------
sentiment_choice = st.radio(
    "🧠 Select Sentiment View:",
    options=['All', 'Positive', 'Neutral', 'Negative'],
    index=0,
    horizontal=True
)

if sentiment_choice != 'All':
    df_filtered = df[df['sentiment_label'] == sentiment_choice]
else:
    df_filtered = df.copy()

# -----------------------
# SMART SUMMARY
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

# -----------------------
# SECTION 1: KPI METRICS
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

with st.container():
    col1, col2 = st.columns([1, 3])

    with col1:
        st.markdown(f"""
            <div style="background-color:{CARD_COLOR}; padding: 18px 20px; border-radius: 20px; margin-bottom: 20px;">
                <h5 style="color:{TEXT_COLOR}; margin: 0;">🔑 Top Trending Keyword</h5>
                <h3 style="margin: 5px 0;">{top_row['clean_phrase'] if not top_phrase.empty else 'N/A'}</h3>
                <p><b>Subcategory:</b> {top_row['matched_product'] if not top_phrase.empty else 'N/A'}</p>
            </div>
            <div style="background-color:{CARD_COLOR}; padding: 18px 20px; border-radius: 20px; margin-bottom: 20px;">
                <h5 style="color:{TEXT_COLOR}; margin: 0;">📈 Total Mentions</h5>
                <h3 style="margin: 5px 0;">{int(top_row['total_mentions']) if not top_phrase.empty else '0'}</h3>
            </div>
            <div style="background-color:{CARD_COLOR}; padding: 18px 20px; border-radius: 20px;">
                <h5 style="color:{TEXT_COLOR}; margin: 0;">💬 Avg Sentiment</h5>
                <h3 style="margin: 5px 0;">{round(top_row['avg_sentiment'], 2) if not top_phrase.empty else '0.0'}</h3>
            </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown("")

# -----------------------
# SECTION 2: 🔥 Top Trending Products (Drilldown Capable)
# -----------------------
st.subheader("🔥 Top Trending Subcategories")

top_subcats = (
    df_filtered.groupby('matched_product')
    .agg(total_mentions=('phrase_freq', 'sum'),
         avg_sentiment=('sentiment_score', 'mean'),
         trend_score=('trend_score', 'sum'))
    .reset_index()
    .sort_values('trend_score', ascending=False)
)

selected_subcat = st.selectbox("📦 Select Subcategory to Drill Down:", top_subcats['matched_product'])

keywords = (
    df_filtered[df_filtered['matched_product'] == selected_subcat]
    .groupby('clean_phrase')
    .agg(mentions=('phrase_freq', 'sum'),
         avg_sentiment=('sentiment_score', 'mean'),
         trend_score=('trend_score', 'sum'))
    .reset_index()
    .sort_values('trend_score', ascending=False)
    .head(10)
)

st.markdown(f"**Top Product Keywords in _{selected_subcat}_**")
st.dataframe(keywords)

# -----------------------
# SECTION 3: 📈 Trend Over Time
# -----------------------
st.subheader("📈 Trend Score Over Time")

time_view = st.radio("Select Time View:", ['Daily', 'Weekly', 'Monthly'], horizontal=True)

if time_view == 'Daily':
    time_col = 'Date'
elif time_view == 'Weekly':
    time_col = 'Week'
else:
    time_col = 'Month'

trend_time = (
    df_filtered.groupby([time_col, 'matched_product'])
    .agg(trend_score=('trend_score', 'sum'))
    .reset_index()
)

chart = alt.Chart(trend_time).mark_line().encode(
    x=alt.X(f'{time_col}:T' if time_view == 'Daily' else f'{time_col}:O', title=time_col),
    y='trend_score:Q',
    color='matched_product:N',
    tooltip=[time_col, 'matched_product', 'trend_score']
).properties(
    width=900,
    height=400
)

st.altair_chart(chart, use_container_width=True)
