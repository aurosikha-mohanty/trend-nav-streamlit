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
    <p style='text-align: center; color: {SUMMARY_COLOR}; font-size:20px;'>
        Identifying <strong>trending product demands</strong> using Reddit & Amazon QA,
        and mapping them against <strong>inventory signals</strong> to find high-opportunity areas for sellers.
    </p>
    """, unsafe_allow_html=True
)

# -----------------------
# KPI CARDS (HORIZONTAL)
# -----------------------
# KPIs should use unfiltered data
top_phrase_unfiltered = (
    df.groupby(['clean_phrase', 'matched_product'])
    .agg(total_mentions=('phrase_freq', 'sum'), avg_sentiment=('sentiment_score', 'mean'), trend_score=('trend_score', 'sum'))
    .reset_index()
    .sort_values('trend_score', ascending=False)
)
top_row_unfiltered = top_phrase_unfiltered.iloc[0] if not top_phrase_unfiltered.empty else {}

kpi1, kpi2, kpi3 = st.columns(3)

with kpi1:
    keyword = top_row_unfiltered['clean_phrase'] if not top_phrase_unfiltered.empty else 'N/A'
    subcat = top_row_unfiltered['matched_product'] if not top_phrase_unfiltered.empty else ''
    st.markdown(f"""
    <div style="background-color:{CARD_COLOR}; padding:15px; height:140px; border-radius:12px;">
        <h5 style="color:{TEXT_COLOR};">Top Keyword</h5>
        <h3>{keyword} <span style='font-size: 16px; color: #777;'>({subcat})</span></h3>
    </div>
    """, unsafe_allow_html=True)

with kpi2:
    total_mentions = int(top_row_unfiltered['total_mentions']) if not top_phrase_unfiltered.empty else 0
    st.markdown(f"""
    <div style="background-color:{CARD_COLOR}; padding:15px; height:140px; border-radius:12px;">
        <h5 style="color:{TEXT_COLOR};">Total Mentions</h5>
        <h3>{total_mentions}</h3>
    </div>
    """, unsafe_allow_html=True)

with kpi3:
    avg_sentiment = round(top_row_unfiltered['avg_sentiment'], 2) if not top_phrase_unfiltered.empty else 0.0
    st.markdown(f"""
    <div style="background-color:{CARD_COLOR}; padding:15px; height:140px; border-radius:12px;">
        <h5 style="color:{TEXT_COLOR};">Avg Sentiment</h5>
        <h3>{avg_sentiment}</h3>
    </div>
    """, unsafe_allow_html=True)



# -----------------------
# FILTERS
# -----------------------
# one space row to make the space 
st.markdown("<br>", unsafe_allow_html=True)
st.markdown("<br>", unsafe_allow_html=True)
st.markdown("<br>", unsafe_allow_html=True)
st.markdown(
    """
    <p style='text-align:center; font-size:20px; color:#333;'>
    💡 Want to see what people <strong>love</strong> or <strong>complain</strong> about?  
    Use the filters to explore trending products by sentiment.
    </p>
    """,
    unsafe_allow_html=True
)
# 3 filters in a row
col1, col2, col3 = st.columns(3)

with col1:
    sentiment_choice = st.radio("🧠 Sentiment:", ['All', 'Positive', 'Neutral', 'Negative'], horizontal=True, index=0)

with col2:
    time_choice = st.radio("⏱️ Time View:", ['Daily', 'Weekly', 'Monthly'], horizontal=True)

with col3:
    all_subcats = sorted(df['matched_product'].dropna().unique())
    selected_subcat = st.selectbox("🧵 Subcategory:", options=["All"] + all_subcats, index=0)
    
# -----------------------
# APPLY FILTERS to create df_filtered
# -----------------------
df_filtered = df.copy()

if sentiment_choice != 'All':
    df_filtered = df_filtered[df_filtered['sentiment_label'] == sentiment_choice]

if selected_subcat != "All":
    df_filtered = df_filtered[df_filtered['matched_product'] == selected_subcat]

# Apply time view
if time_choice == 'Weekly':
    df_filtered['time_unit'] = df_filtered['week']
elif time_choice == 'Monthly':
    df_filtered['time_unit'] = df_filtered['month']
else:
    df_filtered['time_unit'] = df_filtered['date']

# -----------------------
# TIME FILTER
# -----------------------
# time_choice = st.radio("⏱️ Time View:", ['Daily', 'Weekly', 'Monthly'], horizontal=True)
if time_choice == 'Weekly':
    df_filtered['time_unit'] = df_filtered['week']
elif time_choice == 'Monthly':
    df_filtered['time_unit'] = df_filtered['month']
else:
    df_filtered['time_unit'] = df_filtered['date']

# -----------------------
# SUMMARY LINE
# -----------------------
st.markdown("<br>", unsafe_allow_html=True)

summary_map = {
    'Positive': "🌿 Sentiment is strongly positive — these products are resonating well!",
    'Negative': "⚠️ Negative feedback signals product improvement potential.",
    'Neutral': "🟡 Moderate opinions — could go either way!",
    'All': "📊 Viewing combined sentiment — ideal for overall trend monitoring."
}
st.markdown(f"<p style='text-align:center; color:#333; font-size:20px;'>{summary_map.get(sentiment_choice)}</p>", unsafe_allow_html=True)


# -----------------------
# TRENDING TABLE + CHART
# -----------------------
st.markdown("<br>", unsafe_allow_html=True)

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

# -----------------------# -----------------------
# OPPORTUNITY ANALYSIS (Tabs + Monthly Decline Trends)
# -----------------------
st.markdown("### 📦 Opportunity Analysis")

# Capitalize for consistent display
df['matched_product'] = df['matched_product'].str.title()

# Calculate stock and trend stats (unfiltered)
median_stock = df['stock_level'].median()
median_trend = df['trend_score'].median()

opportunity_df = (
    df.groupby('matched_product')
    .agg(avg_stock=('stock_level', 'mean'), trend_score=('trend_score', 'sum'))
    .reset_index()
)

# Filter high opportunity: low stock, high trend
high_opp = opportunity_df[
    (opportunity_df['avg_stock'] < median_stock) & 
    (opportunity_df['trend_score'] > median_trend)
]

# Prepare Declining Trends — Month-over-Month
df['month'] = df['timestamp'].dt.to_period('M').astype(str)
monthly_trends = (
    df.groupby(['matched_product', 'month'])['trend_score']
    .sum()
    .reset_index()
    .sort_values(['matched_product', 'month'])
)
monthly_trends['pct_change'] = monthly_trends.groupby('matched_product')['trend_score'].pct_change()

# Most recent month's change
recent_month_drop = (
    monthly_trends.groupby('matched_product').tail(1)
    .query('pct_change < -0.2')  # Drop > 20%
    .sort_values('pct_change')
)

# Reusable style helpers
def center_bold_header():
    return [
        {'selector': 'th', 'props': [('text-align', 'center'), ('font-weight', 'bold')]},
        {'selector': 'td', 'props': [('text-align', 'center')]}
    ]

def highlight_decline(val):
    color = 'red' if val < 0 else 'green'
    return f'color: {color}'

# Layout with tabs
tab1, tab2 = st.tabs(["🟢 High Opportunity Products", "📉 Declining Trends"])

with tab1:
    st.caption("These products are trending but have relatively low stock.")
    if not high_opp.empty:
        display_df = high_opp.rename(columns={
            'matched_product': 'Product Subcategory',
            'avg_stock': 'Avg Stock',
            'trend_score': 'Trend Score'
        })
        st.dataframe(
            display_df
            .style
            .set_table_styles(center_bold_header())
            .format({'Avg Stock': '{:,.0f}', 'Trend Score': '{:,.0f}'}),
            use_container_width=True
        )
    else:
        st.info("No high opportunity products found.")

with tab2:
    st.caption("Products with a significant drop in trend score over the last month.")
    if not recent_month_drop.empty:
        display_df = recent_month_drop.rename(columns={
            'matched_product': 'Product Subcategory',
            'trend_score': 'Latest Trend Score',
            'pct_change': '% Change'
        })[['Product Subcategory', 'Latest Trend Score', '% Change']]

        st.dataframe(
            display_df
            .style
            .set_table_styles(center_bold_header())
            .applymap(highlight_decline, subset=['% Change'])
            .format({'Latest Trend Score': '{:,.0f}', '% Change': '{:.0%}'}),
            use_container_width=True
        )
    else:
        st.info("No declining trends detected this month.")
