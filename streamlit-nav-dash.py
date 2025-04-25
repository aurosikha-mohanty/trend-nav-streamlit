#!/usr/bin/env python
# coding: utf-8

# In[19]:
import streamlit as st
import pandas as pd
import altair as alt

# ----------------------
# Page Config
# ----------------------
st.set_page_config(page_title="TrendNav AI", layout="wide", page_icon="📊")

# ----------------------
# Theme Colors
# ----------------------
CARD_COLOR = "#183642"  # dark blue-teal
TEXT_COLOR = "#ffffff"

# ----------------------
# Load Data
# ----------------------
@st.cache_data
def load_data():
    df = pd.read_csv("matched_df_final_filt.csv", parse_dates=['timestamp'])
    df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')
    df['sentiment_score'] = pd.to_numeric(df['sentiment_score'], errors='coerce')
    df['phrase_freq'] = pd.to_numeric(df['phrase_freq'], errors='coerce')
    df['trend_score'] = df['sentiment_score'].fillna(0) + df['phrase_freq'].fillna(0)
    df['sentiment_label'] = df['sentiment_score'].apply(lambda x: 'Positive' if x == 1 else 'Negative' if x == -1 else 'Neutral')
    df['date'] = df['timestamp'].dt.date
    df['month'] = df['timestamp'].dt.to_period('M').astype(str)
    df['week'] = df['timestamp'].dt.strftime('%Y-%U')
    return df

df = load_data()

# ----------------------
# Header
# ----------------------
st.markdown(
    f"""
    <h1 style='text-align: center; color: {TEXT_COLOR};'>📊 TrendNav AI: E-commerce Opportunity Scanner</h1>
    <p style='text-align: center; color: #ccc;'>Identifying <strong>trending product demands</strong> using Reddit & Amazon QA, and mapping them against <strong>inventory signals</strong> to find high-opportunity areas for sellers.</p>
    """,
    unsafe_allow_html=True,
)

# ----------------------
# Global Filters
# ----------------------
sentiment_choice = st.radio("🧠 Select Sentiment View:", ['All', 'Positive', 'Neutral', 'Negative'], horizontal=True, index=0)

df_filtered = df.copy()
if sentiment_choice != 'All':
    df_filtered = df_filtered[df_filtered['sentiment_label'] == sentiment_choice]

time_view = st.radio("⏱️ Select Time Granularity:", ['Daily', 'Weekly', 'Monthly'], horizontal=True, index=0)
if time_view == 'Weekly':
    df_filtered['time_unit'] = df_filtered['week']
elif time_view == 'Monthly':
    df_filtered['time_unit'] = df_filtered['month']
else:
    df_filtered['time_unit'] = df_filtered['date']

# ----------------------
# Summary Message
# ----------------------
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

# ----------------------
# Layout Columns
# ----------------------
left_col, mid_col, right_col = st.columns([1.2, 2.2, 2.6])

# ----------------------
# Section 1: KPI Cards
# ----------------------
top_phrase = (
    df_filtered.groupby(['clean_phrase', 'matched_product'])
    .agg(total_mentions=('phrase_freq', 'sum'), avg_sentiment=('sentiment_score', 'mean'), trend_score=('trend_score', 'sum'))
    .reset_index()
    .sort_values('trend_score', ascending=False)
)
top_row = top_phrase.iloc[0] if not top_phrase.empty else {}

with left_col:
    st.markdown(f"""
    <div style="background-color:{CARD_COLOR}; padding: 15px 20px; border-radius: 16px; margin-bottom: 10px;">
        <h4 style="color:{TEXT_COLOR};">Top Product Keyword</h4>
        <h2 style="color:white;">{top_row['clean_phrase'] if not top_phrase.empty else 'N/A'}</h2>
        <p style="color:white;"><b>Subcategory:</b> {top_row['matched_product'] if not top_phrase.empty else 'N/A'}</p>
    </div>
    <div style="background-color:{CARD_COLOR}; padding: 15px 20px; border-radius: 16px; margin-bottom: 10px;">
        <h4 style="color:{TEXT_COLOR};">Total Mentions</h4>
        <h2 style="color:white;">{int(top_row['total_mentions']) if not top_phrase.empty else '0'}</h2>
    </div>
    <div style="background-color:{CARD_COLOR}; padding: 15px 20px; border-radius: 16px;">
        <h4 style="color:{TEXT_COLOR};">Avg Sentiment</h4>
        <h2 style="color:white;">{round(top_row['avg_sentiment'], 2) if not top_phrase.empty else '0.0'}</h2>
    </div>
    """, unsafe_allow_html=True)

# ----------------------
# Section 2: Top Trending Products Table
# ----------------------
with mid_col:
    st.markdown("#### 🔥 Top Trending Products")
    top_keywords = (
        df_filtered.groupby(['matched_product', 'clean_phrase'])
        .agg(total_mentions=('phrase_freq', 'sum'), avg_sentiment=('sentiment_score', 'mean'), trend_score=('trend_score', 'sum'))
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

# ----------------------
# Section 3: Trend Score Over Time
# ----------------------
with right_col:
    st.markdown("#### 📈 Trend Score Over Time")
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
    ).properties(width=530, height=390)
    st.altair_chart(chart, use_container_width=True)

# ----------------------
# Threshold Controls
# ----------------------
st.markdown("### 🧪 Inventory Opportunity Thresholds")

col_thresh1, col_thresh2 = st.columns(2)
with col_thresh1:
    low_stock_cutoff = st.slider("Low Stock Threshold (for High Opportunity)", 100, 5000, 3000, step=100)
    high_trend_cutoff = st.slider("Min Trend Score (for High Opportunity)", 5, 50, 10, step=1)
with col_thresh2:
    high_stock_cutoff = st.slider("High Stock Threshold (for Low Opportunity)", 1000, 10000, 5000, step=100)
    low_trend_cutoff = st.slider("Max Trend Score (for Low Opportunity)", 0, 30, 5, step=1)

# ----------------------
# Section 4: High Opportunity Products
# ----------------------
st.markdown("#### 📦 High Opportunity Products (Low Stock + High Trend)")

high_opp = (
    df_filtered.groupby(['matched_product'])
    .agg(trend_score=('trend_score', 'sum'), avg_stock=('stock_level', 'mean'))
    .reset_index()
)
high_opp = high_opp[
    (high_opp['avg_stock'] < low_stock_cutoff) & (high_opp['trend_score'] > high_trend_cutoff)
].sort_values("trend_score", ascending=False)

if not high_opp.empty:
    st.dataframe(high_opp.rename(columns={
        'matched_product': 'Product Subcategory',
        'trend_score': 'Trend Score',
        'avg_stock': 'Avg Stock'
    }))
else:
    st.info("No high opportunity products matching current filters.")

# ----------------------
# Section 5: Low Opportunity Products
# ----------------------
st.markdown("#### 📉 Low Opportunity Products (High Stock + Low Trend)")

low_opp = (
    df_filtered.groupby(['matched_product'])
    .agg(trend_score=('trend_score', 'sum'), avg_stock=('stock_level', 'mean'))
    .reset_index()
)
low_opp = low_opp[
    (low_opp['avg_stock'] > high_stock_cutoff) & (low_opp['trend_score'] < low_trend_cutoff)
].sort_values("trend_score")

if not low_opp.empty:
    st.dataframe(low_opp.rename(columns={
        'matched_product': 'Product Subcategory',
        'trend_score': 'Trend Score',
        'avg_stock': 'Avg Stock'
    }))
else:
    st.info("No low opportunity products matching current filters.")
