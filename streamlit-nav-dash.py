#!/usr/bin/env python
# coding: utf-8

# In[19]:
import streamlit as st
import pandas as pd
import altair as alt

# --------------------
# Page Config
# --------------------
st.set_page_config(page_title="TrendNav AI", layout="wide", page_icon="📊")

# --------------------
# Theme Colors
# --------------------
CARD_COLOR = "#183642"
TEXT_COLOR = "#ffffff"

# --------------------
# Load Data
# --------------------
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
    df['date'] = df['timestamp'].dt.date
    df['month'] = df['timestamp'].dt.to_period('M').astype(str)
    df['week'] = df['timestamp'].dt.strftime('%Y-%U')
    return df

df = load_data()

# --------------------
# Title
# --------------------
st.markdown(
    f"""
    <h1 style='text-align: center; color: {TEXT_COLOR}; background-color: {CARD_COLOR}; padding: 20px 0;'>📊 TrendNav AI: E-commerce Opportunity Scanner</h1>
    <p style='text-align: center; color: #ccc;'>Identifying <strong>trending product demands</strong> using Reddit & Amazon QA, and mapping them against <strong>inventory signals</strong> to find high-opportunity areas for sellers.</p>
    """,
    unsafe_allow_html=True,
)

# --------------------
# Top Filters Section
# --------------------
filter_col1, filter_col2 = st.columns([2, 2])

with filter_col1:
    sentiment_choice = st.radio("🧠 Sentiment Filter", ['All', 'Positive', 'Neutral', 'Negative'], horizontal=True)
with filter_col2:
    subcats = df['matched_product'].dropna().unique()
    subcat_choice = st.selectbox("📦 Filter by Product Subcategory", options=["All"] + sorted(subcats.tolist()))

df_filtered = df.copy()
if sentiment_choice != 'All':
    df_filtered = df_filtered[df_filtered['sentiment_label'] == sentiment_choice]
if subcat_choice != "All":
    df_filtered = df_filtered[df_filtered['matched_product'] == subcat_choice]

# --------------------
# KPI Cards (Top Horizontal)
# --------------------
top_phrase = (
    df_filtered.groupby(['clean_phrase', 'matched_product'])
    .agg(total_mentions=('phrase_freq', 'sum'),
         avg_sentiment=('sentiment_score', 'mean'),
         trend_score=('trend_score', 'sum'))
    .reset_index()
    .sort_values('trend_score', ascending=False)
)
top_row = top_phrase.iloc[0] if not top_phrase.empty else {}

kpi1, kpi2, kpi3 = st.columns(3)

with kpi1:
    st.markdown(f"""
    <div style="background-color:{CARD_COLOR}; padding: 18px; border-radius: 12px;">
        <h4 style="color:{TEXT_COLOR};">🔑 Top Product Keyword</h4>
        <h2 style="color:white;">{top_row['clean_phrase'] if not top_phrase.empty else 'N/A'}</h2>
        <p style="color:white;"><b>Subcategory:</b> {top_row['matched_product'] if not top_phrase.empty else 'N/A'}</p>
    </div>
    """, unsafe_allow_html=True)

with kpi2:
    st.markdown(f"""
    <div style="background-color:{CARD_COLOR}; padding: 18px; border-radius: 12px;">
        <h4 style="color:{TEXT_COLOR};">📈 Total Mentions</h4>
        <h2 style="color:white;">{int(top_row['total_mentions']) if not top_phrase.empty else '0'}</h2>
    </div>
    """, unsafe_allow_html=True)

with kpi3:
    st.markdown(f"""
    <div style="background-color:{CARD_COLOR}; padding: 18px; border-radius: 12px;">
        <h4 style="color:{TEXT_COLOR};">💬 Avg Sentiment</h4>
        <h2 style="color:white;">{round(top_row['avg_sentiment'], 2) if not top_phrase.empty else '0.0'}</h2>
    </div>
    """, unsafe_allow_html=True)

# --------------------
# Summary Line
# --------------------
summary_map = {
    'Positive': "🌿 Sentiment is strongly positive — these products are resonating well!",
    'Negative': "⚠️ Negative feedback signals product improvement potential.",
    'Neutral': "🟡 Moderate opinions — could go either way!",
    'All': "📊 Viewing combined sentiment — ideal for overall trend monitoring."
}
st.markdown(
    f"<p style='text-align:center; color:#333; font-size: 16px;'>{summary_map.get(sentiment_choice)}</p>",
    unsafe_allow_html=True
)

# --------------------
# Top Trending Products
# --------------------
st.subheader("🔥 Top Trending Products")

top_keywords = (
    df_filtered.groupby(['matched_product', 'clean_phrase'])
    .agg(total_mentions=('phrase_freq', 'sum'),
         avg_sentiment=('sentiment_score', 'mean'),
         trend_score=('trend_score', 'sum'))
    .reset_index()
    .rename(columns={
        'matched_product': 'Product Subcategory',
        'clean_phrase': 'Product Keywords',
        'total_mentions': 'Total Mentions',
        'avg_sentiment': 'Avg Sentiment',
        'trend_score': 'Trend Score'
    })
    .sort_values('Trend Score', ascending=False)
    .head(15)
)
st.dataframe(top_keywords, use_container_width=True)

# --------------------
# Trend Over Time
# --------------------
st.subheader("📈 Trend Score Over Time")
time_view = st.radio("⏱️ Select Time Granularity:", ['Daily', 'Weekly', 'Monthly'], horizontal=True)
if time_view == 'Weekly':
    df_filtered['time_unit'] = df_filtered['week']
elif time_view == 'Monthly':
    df_filtered['time_unit'] = df_filtered['month']
else:
    df_filtered['time_unit'] = df_filtered['date']

df_trend = df_filtered[df_filtered['timestamp'].dt.year < 2025].copy()
trend_time = (
    df_trend.groupby(['time_unit', 'matched_product'])
    .agg(trend_score=('trend_score', 'sum'))
    .reset_index()
)

chart = alt.Chart(trend_time).mark_line().encode(
    x=alt.X('time_unit:T', title="Date"),
    y=alt.Y('trend_score:Q', title="Trend Score"),
    color='matched_product:N',
    tooltip=['time_unit:T', 'matched_product:N', 'trend_score:Q']
).properties(width=1000, height=400)

st.altair_chart(chart, use_container_width=True)

# --------------------
# Opportunity Analysis
# --------------------
col_hi, col_lo = st.columns(2)

with col_hi:
    st.subheader("📦 High Opportunity Products")
    high_opp = (
        df_filtered.groupby(['matched_product'])
        .agg(trend_score=('trend_score', 'sum'), avg_stock=('stock_level', 'mean'))
        .reset_index()
    )
    median_stock = high_opp['avg_stock'].median()
    median_trend = high_opp['trend_score'].median()
    high_opp = high_opp[
        (high_opp['avg_stock'] < median_stock) & (high_opp['trend_score'] > median_trend)
    ]
    st.dataframe(high_opp.rename(columns={
        'matched_product': 'Product Subcategory',
        'trend_score': 'Trend Score',
        'avg_stock': 'Avg Stock'
    }))

with col_lo:
    st.subheader("📉 Low Opportunity Products")
    low_opp = (
        df_filtered.groupby(['matched_product'])
        .agg(trend_score=('trend_score', 'sum'), avg_stock=('stock_level', 'mean'))
        .reset_index()
    )
    low_opp = low_opp[
        (low_opp['avg_stock'] > median_stock) & (low_opp['trend_score'] < median_trend)
    ]
    st.dataframe(low_opp.rename(columns={
        'matched_product': 'Product Subcategory',
        'trend_score': 'Trend Score',
        'avg_stock': 'Avg Stock'
    }))
