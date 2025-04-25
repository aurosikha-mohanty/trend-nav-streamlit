#!/usr/bin/env python
# coding: utf-8

# In[19]:
import streamlit as st
import pandas as pd
import altair as alt

# -----------------------
# PAGE CONFIG
# -----------------------
st.set_page_config(page_title="TrendNav AI", layout="wide", page_icon="📊")

# -----------------------
# THEME COLORS
# -----------------------
CARD_COLOR = "#d6f5f2"
TEXT_COLOR = "#0b6da4"
SUMMARY_COLOR = "#444"

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
    df['sentiment_label'] = df['sentiment_score'].apply(lambda x: 'Positive' if x == 1 else 'Negative' if x == -1 else 'Neutral')
    df['date'] = df['timestamp'].dt.date
    df['month'] = df['timestamp'].dt.to_period('M').astype(str)
    df['week'] = df['timestamp'].dt.strftime('%Y-%U')
    return df

df = load_data()

# -----------------------
# HEADER
# -----------------------
st.markdown(
    f"""
    <h1 style='text-align: center; color: {TEXT_COLOR};'>📊 TrendNav AI: E-commerce Opportunity Scanner</h1>
    <p style='text-align: center; color: {SUMMARY_COLOR};'>
        Identifying <strong>trending product demands</strong> using Reddit & Amazon QA,
        and mapping them against <strong>inventory signals</strong> to find high-opportunity areas for sellers.
    </p>
    """, unsafe_allow_html=True
)

# -----------------------
# FILTERS
# -----------------------
left_filter, right_filter = st.columns([1.5, 2])
with left_filter:
    sentiment_choice = st.radio("🧠 Sentiment Filter:", ['All', 'Positive', 'Neutral', 'Negative'], horizontal=True, index=0)
with right_filter:
    selected_subcats = st.multiselect("🧵 Product Subcategories:", sorted(df['matched_product'].dropna().unique()),
                                      default=sorted(df['matched_product'].dropna().unique())[:10])

df_filtered = df.copy()
if sentiment_choice != 'All':
    df_filtered = df_filtered[df_filtered['sentiment_label'] == sentiment_choice]
df_filtered = df_filtered[df_filtered['matched_product'].isin(selected_subcats)]

# -----------------------
# TIME FILTER
# -----------------------
time_choice = st.radio("⏱️ Time View:", ['Daily', 'Weekly', 'Monthly'], horizontal=True)
if time_choice == 'Weekly':
    df_filtered['time_unit'] = df_filtered['week']
elif time_choice == 'Monthly':
    df_filtered['time_unit'] = df_filtered['month']
else:
    df_filtered['time_unit'] = df_filtered['date']

# -----------------------
# SUMMARY LINE
# -----------------------
summary_map = {
    'Positive': "🌿 Sentiment is strongly positive — these products are resonating well!",
    'Negative': "⚠️ Negative feedback signals product improvement potential.",
    'Neutral': "🟡 Moderate opinions — could go either way!",
    'All': "📊 Viewing combined sentiment — ideal for overall trend monitoring."
}
st.markdown(f"<p style='text-align:center; color:#333;'>{summary_map.get(sentiment_choice)}</p>", unsafe_allow_html=True)

# -----------------------
# KPI CARDS (HORIZONTAL)
# -----------------------
top_phrase = (
    df_filtered.groupby(['clean_phrase', 'matched_product'])
    .agg(total_mentions=('phrase_freq', 'sum'), avg_sentiment=('sentiment_score', 'mean'), trend_score=('trend_score', 'sum'))
    .reset_index()
    .sort_values('trend_score', ascending=False)
)
top_row = top_phrase.iloc[0] if not top_phrase.empty else {}

kpi1, kpi2, kpi3 = st.columns(3)
with kpi1:
    st.markdown(f"""
    <div style="background-color:{CARD_COLOR}; padding:15px; border-radius:12px;">
        <h5 style="color:{TEXT_COLOR};">Top Keyword</h5>
        <h3>{top_row['clean_phrase'] if not top_phrase.empty else 'N/A'}</h3>
        <p><b>Subcategory:</b> {top_row['matched_product'] if not top_phrase.empty else 'N/A'}</p>
    </div>
    """, unsafe_allow_html=True)

with kpi2:
    st.markdown(f"""
    <div style="background-color:{CARD_COLOR}; padding:15px; border-radius:12px;">
        <h5 style="color:{TEXT_COLOR};">Total Mentions</h5>
        <h3>{int(top_row['total_mentions']) if not top_phrase.empty else 0}</h3>
    </div>
    """, unsafe_allow_html=True)

with kpi3:
    st.markdown(f"""
    <div style="background-color:{CARD_COLOR}; padding:15px; border-radius:12px;">
        <h5 style="color:{TEXT_COLOR};">Avg Sentiment</h5>
        <h3>{round(top_row['avg_sentiment'], 2) if not top_phrase.empty else 0.0}</h3>
    </div>
    """, unsafe_allow_html=True)

# -----------------------
# TRENDING TABLE + CHART
# -----------------------
left_col, right_col = st.columns([2, 2.2])

with left_col:
    st.markdown("### 🔥 Top Trending Products")
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

with right_col:
    st.markdown("### 📈 Trend Score Over Time")
    df_trend = df_filtered[df_filtered['timestamp'].dt.year < 2025].copy()
    trend_data = (
        df_trend.groupby(['time_unit', 'matched_product'])
        .agg(trend_score=('trend_score', 'sum'))
        .reset_index()
    )
    chart = alt.Chart(trend_data).mark_line().encode(
        x=alt.X('time_unit:T', title='Date'),
        y=alt.Y('trend_score:Q', title='Trend Score'),
        color='matched_product:N',
        tooltip=['time_unit:T', 'matched_product:N', 'trend_score:Q']
    ).properties(width=520, height=390)
    st.altair_chart(chart, use_container_width=True)

# -----------------------
# OPPORTUNITY ANALYSIS
# -----------------------
st.markdown("### 📦 Opportunity Analysis")

# Use unfiltered for stock-opportunity logic
median_stock = df['stock_level'].median()
median_trend = df['trend_score'].median()

opportunity_df = (
    df.groupby('matched_product')
    .agg(avg_stock=('stock_level', 'mean'), trend_score=('trend_score', 'sum'))
    .reset_index()
)

high_opp = opportunity_df[(opportunity_df['avg_stock'] < median_stock) & (opportunity_df['trend_score'] > median_trend)]
low_opp = opportunity_df[(opportunity_df['avg_stock'] > median_stock) & (opportunity_df['trend_score'] < median_trend)]

col_high, col_low = st.columns(2)
with col_high:
    st.markdown("#### 🟢 High Opportunity Products")
    st.caption("These products are trending but have relatively low stock.")
    if not high_opp.empty:
        st.dataframe(high_opp.rename(columns={'matched_product': 'Product Subcategory', 'avg_stock': 'Avg Stock', 'trend_score': 'Trend Score'}))
    else:
        st.info("No high opportunity products found.")

with col_low:
    st.markdown("#### 🔴 Low Opportunity Products")
    st.caption("These products have high stock but are not trending.")
    if not low_opp.empty:
        st.dataframe(low_opp.rename(columns={'matched_product': 'Product Subcategory', 'avg_stock': 'Avg Stock', 'trend_score': 'Trend Score'}))
    else:
        st.info("No low opportunity products found.")
