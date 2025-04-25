#!/usr/bin/env python
# coding: utf-8

# In[19]:
# -----------------------
# OPPORTUNITY ANALYSIS (Updated with Tabs + Styling)
# -----------------------
st.markdown("### 📦 Opportunity Analysis")

# Capitalize for consistency
df['matched_product'] = df['matched_product'].str.title()

# Recompute metrics (unfiltered)
median_stock = df['stock_level'].median()
median_trend = df['trend_score'].median()

opportunity_df = (
    df.groupby('matched_product')
    .agg(avg_stock=('stock_level', 'mean'), trend_score=('trend_score', 'sum'))
    .reset_index()
)

high_opp = opportunity_df[(opportunity_df['avg_stock'] < median_stock) & (opportunity_df['trend_score'] > median_trend)]

# Declining Trends Logic
weekly_trends = (
    df.groupby(['matched_product', 'week'])['trend_score']
    .sum()
    .reset_index()
    .sort_values(['matched_product', 'week'])
)
weekly_trends['pct_change'] = weekly_trends.groupby('matched_product')['trend_score'].pct_change()
recent_drop = (
    weekly_trends.groupby('matched_product').tail(1)
    .query('pct_change < -0.2')
    .sort_values('pct_change')
)

# Tab Layout
tab1, tab2 = st.tabs(["🟢 High Opportunity Products", "📉 Declining Trends"])

# Style helpers
def center_bold_header():
    return [
        {'selector': 'th', 'props': [('text-align', 'center'), ('font-weight', 'bold')]},
        {'selector': 'td', 'props': [('text-align', 'center')]}
    ]

def highlight_decline(val):
    color = 'red' if val < 0 else 'green'
    return f'color: {color}'

with tab1:
    st.caption("These products are trending but have relatively low stock.")
    if not high_opp.empty:
        display_df = high_opp.rename(columns={
            'matched_product': 'Product Subcategory',
            'avg_stock': 'Avg Stock',
            'trend_score': 'Trend Score'
        })
        st.dataframe(
            display_df.style.set_table_styles(center_bold_header()).format({'Avg Stock': '{:,.0f}', 'Trend Score': '{:,.0f}'}),
            use_container_width=True
        )
    else:
        st.info("No high opportunity products found.")

with tab2:
    st.caption("Products with a significant drop in trend score over the last week.")
    if not recent_drop.empty:
        display_df = recent_drop.rename(columns={
            'matched_product': 'Product Subcategory',
            'trend_score': 'Latest Trend Score',
            'pct_change': '% Change'
        })[['Product Subcategory', 'Latest Trend Score', '% Change']]
        st.dataframe(
            display_df.style
                .set_table_styles(center_bold_header())
                .applymap(highlight_decline, subset=['% Change'])
                .format({'Latest Trend Score': '{:,.0f}', '% Change': '{:.0%}'}),
            use_container_width=True
        )
    else:
        st.info("No declining trends detected this week.")
