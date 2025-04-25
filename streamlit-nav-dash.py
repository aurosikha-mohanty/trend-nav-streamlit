#!/usr/bin/env python
# coding: utf-8

# In[19]:
import streamlit as st
import pandas as pd
import altair as alt

st.set_page_config(page_title="TrendNav AI", layout="wide", page_icon="📊")

# ---------- Theme ----------
CARD_COLOR = "#183642"  # darker teal-blue
TEXT_COLOR = "#ffffff"

# ---------- Load Data ----------
@st.cache_data

def load_data():
    df = pd.read_csv("matched_df_final_filt.csv", parse_dates=['timestamp'])
    df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')
    df['sentiment_score'] = pd.to_numeric(df['sentiment_score'], errors='coerce')
    df['phrase_freq'] = pd.to_numeric(df['phrase_freq'], errors='coerce')
    df['trend_score'] = df['sentiment_score'].fillna(0) + df['phrase_freq'].fillna(0)
    df['sentiment_label'] = df['sentiment_score'].apply(lambda x: 'Positive' if x == 1 else 'Negative' if x == -1 else 'Neutral')
    df['date'] = df['timestamp'].dt.date
    return df

df = load_data()

# ---------- Sentiment Filter ----------
sentiment_choice = st.radio("Select Sentiment:", ['All', 'Positive', 'Neutral', 'Negative'], horizontal=True, index=0)

if sentiment_choice != 'All':
    df_filtered = df[df['sentiment_label'] == sentiment_choice]
else:
    df_filtered = df.copy()

# ---------- Section Layout ----------
left_col, mid_col, right_col = st.columns([1.2, 2.2, 2.6])

# ---------- Section 1: KPI CARDS ----------
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

# ---------- Section 2: Trending Products Table ----------
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

# ---------- Section 3: Trend Over Time ----------
with right_col:
    st.markdown("#### 📈 Trend Score Over Time")
    df_trend = df_filtered[df_filtered['timestamp'].dt.year < 2025]
    trend_time = (
        df_trend.groupby(["date", "matched_product"])
        .agg(trend_score=('trend_score', 'sum'))
        .reset_index()
    )
    chart = alt.Chart(trend_time).mark_line().encode(
        x=alt.X('date:T', title="Date"),
        y=alt.Y('trend_score:Q', title="Trend Score"),
        color='matched_product:N',
        tooltip=['date:T', 'matched_product:N', 'trend_score:Q']
    ).properties(width=520, height=390)
    st.altair_chart(chart, use_container_width=True)

# ---------- Section 4: High Opportunity Products ----------
st.markdown("#### 📦 High Opportunity Products (Low Stock + High Trend)")
high_opp = (
    df_filtered.groupby(['matched_product'])
    .agg(trend_score=('trend_score', 'sum'), avg_stock=('stock_level', 'mean'))
    .reset_index()
)
high_opp = high_opp[(high_opp['avg_stock'] < 3000) & (high_opp['trend_score'] > 10)].sort_values("trend_score", ascending=False)
st.dataframe(high_opp.rename(columns={
    'matched_product': 'Product Subcategory',
    'trend_score': 'Trend Score',
    'avg_stock': 'Avg Stock'
}))

# ---------- Section 5: Low Opportunity Products ----------
st.markdown("#### 📉 Low Opportunity Products (High Stock + Low Trend)")
low_opp = (
    df_filtered.groupby(['matched_product'])
    .agg(trend_score=('trend_score', 'sum'), avg_stock=('stock_level', 'mean'))
    .reset_index()
)
low_opp = low_opp[(low_opp['avg_stock'] > 5000) & (low_opp['trend_score'] < 5)].sort_values("trend_score")
st.dataframe(low_opp.rename(columns={
    'matched_product': 'Product Subcategory',
    'trend_score': 'Trend Score',
    'avg_stock': 'Avg Stock'
}))
