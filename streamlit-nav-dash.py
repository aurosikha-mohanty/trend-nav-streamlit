#!/usr/bin/env python
# coding: utf-8

# In[19]:

import streamlit as st
import pandas as pd
import altair as alt

# --------------------
# Load Data
# --------------------
@st.cache_data
def load_data():
    df = pd.read_csv("matched_df_v2.csv", parse_dates=['timestamp'])
    df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')
    df['sentiment_score'] = pd.to_numeric(df['sentiment_score'], errors='coerce')
    df['phrase_freq'] = pd.to_numeric(df['phrase_freq'], errors='coerce')
    df['trend_score'] = df['sentiment_score'].fillna(0) + df['phrase_freq'].fillna(0)
    df['Date'] = df['timestamp'].dt.date
    df['Week'] = df['timestamp'].dt.strftime('%Y-%U')
    df['Month'] = df['timestamp'].dt.to_period('M').astype(str)
    df['sentiment_label'] = df['sentiment_score'].apply(lambda x: 'Positive' if x == 1 else 'Negative' if x == -1 else 'Neutral')
    return df

df = load_data()

# --------------------
# Sidebar Filters
# --------------------
st.sidebar.header("🔍 Filters")

sentiment_filter = st.sidebar.multiselect(
    "Sentiment Filter:",
    options=['Positive', 'Neutral', 'Negative', 'All'],
    default=['All']
)

category_filter = st.sidebar.multiselect(
    "Product Categories:",
    options=sorted(df['listing_category'].dropna().unique()),
    default=sorted(df['listing_category'].dropna().unique())
)

time_view = st.sidebar.radio(
    "View Trends By:",
    ['Daily', 'Weekly', 'Monthly']
)

# Filter Logic
filtered_df = df[df['listing_category'].isin(category_filter)]
if 'All' not in sentiment_filter:
    filtered_df = filtered_df[filtered_df['sentiment_label'].isin(sentiment_filter)]

# --------------------
# Dashboard Header
# --------------------
st.title("📊 TrendNav AI: E-commerce Opportunity Scanner")
st.markdown(
    "Identifying **trending product demands** using Reddit & Amazon QA, and mapping them against **inventory signals** to find high-opportunity areas for sellers."
)

# --------------------
# Top Trending Products
# --------------------
col1, col2 = st.columns([1.2, 1.8])

with col1:
    st.subheader("🔥 Top Trending Products")

    top_products = (
        filtered_df.groupby(['matched_product', 'listing_category'])
        .agg(
            total_mentions=('phrase_freq', 'sum'),
            avg_sentiment=('sentiment_score', 'mean'),
            trend_score=('trend_score', 'sum'),
            avg_stock=('stock_level', 'mean')
        )
        .reset_index()
        .sort_values('trend_score', ascending=False)
        .head(20)
    )
    st.dataframe(top_products)

with col2:
    st.subheader("📅 Trend Score Over Time")
    time_col = 'Date' if time_view == 'Daily' else 'Week' if time_view == 'Weekly' else 'Month'

    trend_time = (
        filtered_df.groupby([time_col, 'listing_category'])
        .agg(trend_score=('trend_score', 'sum'))
        .reset_index()
    )

    chart = alt.Chart(trend_time).mark_line().encode(
        x=alt.X(f'{time_col}:T' if time_view == 'Daily' else f'{time_col}:O', title=time_col),
        y='trend_score:Q',
        color='listing_category:N',
        tooltip=[time_col, 'listing_category', 'trend_score']
    ).properties(
        width=800,
        height=400
    )

    st.altair_chart(chart, use_container_width=True)

# --------------------
# 📚 Top Keywords for Each Product
# --------------------
st.subheader("🔍 Top Clean Phrases (Keywords) by Product")

for product in top_products['matched_product'].unique():
    st.markdown(f"**{product}**")
    keywords = (
        filtered_df[filtered_df['matched_product'] == product]
        .groupby('clean_phrase')
        .agg(freq=('phrase_freq', 'sum'))
        .reset_index()
        .sort_values('freq', ascending=False)
        .head(5)
    )
    st.write(keywords)

# --------------------
# 💡 Inventory Opportunity Analysis
# --------------------
st.subheader("📦 High Opportunity Products (Low Stock, High Trend)")

opportunity_df = top_products.copy()
opportunity_df = opportunity_df[opportunity_df['avg_stock'] < opportunity_df['avg_stock'].quantile(0.25)]
opportunity_df = opportunity_df.sort_values('trend_score', ascending=False)

if opportunity_df.empty:
    st.info("No high-opportunity products found in current filter. Try adjusting the filters.")
else:
    st.dataframe(opportunity_df[['matched_product', 'listing_category', 'trend_score', 'avg_stock']])

# --------------------
# 🔁 Export Option
# --------------------
st.download_button("📥 Download Full Filtered Data", data=filtered_df.to_csv(index=False), file_name="trendnav_filtered.csv")

# In[20]:


df

