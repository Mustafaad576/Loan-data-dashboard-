import streamlit as st
import pandas as pd
import plotly.express as px
import re

st.set_page_config(page_title="Microfinance Loan Dashboard (Fixed)", layout="wide")
st.title("📊 Microfinance Loan Analysis Dashboard — Fixed & Robust")
st.markdown("Upload your loan dataset (.xlsx). The app will try to automatically detect column names and avoid errors.")

def normalize(col_name: str) -> str:
    """Normalize column names: lowercase, remove non-alphanumeric characters."""
    return re.sub(r'[^a-z0-9]', '', str(col_name).lower())

def find_column(df, candidates):
    """Find first matching column in df whose normalized name matches any of the candidates (normalized)."""
    norm_to_col = {normalize(c): c for c in df.columns}
    for cand in candidates:
        nc = normalize(cand)
        if nc in norm_to_col:
            return norm_to_col[nc]
    # if none matched exactly, try partial substring match
    for nc, col in norm_to_col.items():
        for cand in candidates:
            if normalize(cand) in nc or nc in normalize(cand):
                return col
    return None

# Upload file
uploaded_file = st.file_uploader("Upload your Excel file (xlsx)", type=["xlsx"])
if not uploaded_file:
    st.info("Please upload an Excel file to begin analysis.")
    st.stop()

# Read file
try:
    df = pd.read_excel(uploaded_file, engine="openpyxl")
except Exception as e:
    st.error(f"Error reading Excel file: {e}")
    st.stop()

st.write("Detected columns:", list(df.columns))

# Column detection (list common variants)
col_candidates = {
    'loan_date': ['actual_date_of_loan', 'actual date of loan', 'disbursal_date', 'loan_date', 'date'],
    'sum_disbursed': ['sum_loan_amount_disbursed', 'sumloanamountdisbursed', 'sum_loan_amount', 'loan_amount', 'sumdisbursed'],
    'sum_setup_fee': ['sum_set_up_fee', 'sum_set_up_fees', 'sumsetupfee', 'setup_fee', 'sum set up fee'],
    'sum_recovered': ['sum_total_recovered', 'sum_total_recovered', 'sumtotalrecovered', 'total_recovered', 'sum_recovered'],
    'outstanding': ['outstanding_principle', 'outstanding_principal', 'outstandingprinciple'],
    'days_past_due': ['days_past_due_date', 'dayspastduedate', 'days_past_due', 'dpd_days', 'dayspastdue'],
    'dpd_cat': ['dpd', 'dpd_status'],
    'segment': ['segment', 'customer_segment'],
    'gender': ['gender', 'sex'],
    'loan_status': ['loan_status', 'status'],
    'account_state': ['account_state_name', 'account_state']
}

found = {}
for key, candidates in col_candidates.items():
    col = find_column(df, candidates)
    if col:
        found[key] = col

# Rename found columns to canonical short names for easier use below
rename_map = {}
for k, col in found.items():
    rename_map[col] = k
df = df.rename(columns=rename_map)

# Check required date column
if 'loan_date' not in df.columns:
    st.error("Could not detect a date column. Please ensure your file has a column like 'actual_date_of_loan'. Found columns: " + ", ".join(df.columns))
    st.stop()

# create Loan_Month_Year
df['loan_date'] = pd.to_datetime(df['loan_date'], errors='coerce')
df['Loan_Month_Year'] = df['loan_date'].dt.to_period('M').astype(str)

# Sidebar filters (only show if available)
st.sidebar.header("Filters")
filters = {}
if 'loan_status' in df.columns:
    choices = sorted(df['loan_status'].dropna().astype(str).unique().tolist())
    filters['loan_status'] = st.sidebar.multiselect("Loan Status", choices, default=choices)
if 'segment' in df.columns:
    choices = sorted(df['segment'].dropna().astype(str).unique().tolist())
    filters['segment'] = st.sidebar.multiselect("Segment", choices, default=choices)
if 'gender' in df.columns:
    choices = sorted(df['gender'].dropna().astype(str).unique().tolist())
    filters['gender'] = st.sidebar.multiselect("Gender", choices, default=choices)
if 'account_state' in df.columns:
    choices = sorted(df['account_state'].dropna().astype(str).unique().tolist())
    filters['account_state'] = st.sidebar.multiselect("Account State", choices, default=choices)

# Apply filters
filtered = df.copy()
for k, vals in filters.items():
    if len(vals) > 0:
        filtered = filtered[filtered[k].astype(str).isin(vals)]

st.write(f"Filtered rows: {len(filtered)} (from {len(df)})")

# Helper: chronological sort for monthly data
def sort_month_df(month_df, month_col='Loan_Month_Year'):
    tmp = month_df.copy()
    tmp['_dt'] = pd.to_datetime(tmp[month_col].astype(str) + '-01', errors='coerce')
    tmp = tmp.sort_values('_dt').drop(columns=['_dt'])
    return tmp

# --- Tabs ---
tab_overview, tab_trend, tab_seg, tab_risk, tab_recovery, tab_dpdseg, tab_mom = st.tabs([
    "Overview", "Trend Analysis", "Customer Segmentation", "Risk Analysis", "Repayment Rate (MoM)",
    "DPD by Segment", "MoM % Change"
])

# --- Overview ---
with tab_overview:
    st.subheader("Portfolio Overview")
    total_disbursed = filtered.get('sum_disbursed', pd.Series(dtype=float)).sum()
    total_recovered = filtered.get('sum_recovered', pd.Series(dtype=float)).sum()
    outstanding = filtered.get('outstanding', pd.Series(dtype=float)).sum()
    recovery_pct = (total_recovered / total_disbursed * 100) if total_disbursed else 0

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Disbursed", f"PKR {total_disbursed:,.0f}")
    c2.metric("Total Recovered", f"PKR {total_recovered:,.0f}")
    c3.metric("Outstanding", f"PKR {outstanding:,.0f}")
    c4.metric("Recovery Rate", f"{recovery_pct:.2f}%")

    st.markdown("**Top 5 rows (preview)**")
    st.dataframe(filtered.head())

# --- Trend Analysis ---
with tab_trend:
    st.subheader("Monthly Loan & Recovery Trends")
    if 'sum_disbursed' in filtered.columns and 'sum_recovered' in filtered.columns:
        monthly = filtered.groupby('Loan_Month_Year')[['sum_disbursed', 'sum_recovered']].sum().reset_index()
        monthly = sort_month_df(monthly, 'Loan_Month_Year')
        fig = px.line(monthly, x='Loan_Month_Year', y=['sum_disbursed', 'sum_recovered'], markers=True,
                      labels={'value': 'PKR', 'variable': 'Metric'}, title="Monthly Disbursed vs Recovered")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Missing columns for trend analysis ('sum_disbursed' and/or 'sum_recovered'). Detected mapping: " + str(found))

# --- Customer Segmentation ---
with tab_seg:
    st.subheader("Customer Segmentation")
    if 'gender' in filtered.columns:
        gcounts = filtered['gender'].fillna('Unknown').value_counts().reset_index()
        gcounts.columns = ['Gender', 'Count']
        fig = px.pie(gcounts, names='Gender', values='Count', title="Gender distribution")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Gender column not detected. Detected mapping: " + str(found))

    if 'segment' in filtered.columns:
        scounts = filtered['segment'].fillna('Unknown').value_counts().reset_index()
        scounts.columns = ['Segment', 'Count']
        fig2 = px.bar(scounts, x='Segment', y='Count', title="Customers by Segment")
        st.plotly_chart(fig2, use_container_width=True)

# --- Risk Analysis ---
with tab_risk:
    st.subheader("Risk Analysis & DPD distribution")
    if 'days_past_due' in filtered.columns:
        filtered['days_past_due'] = pd.to_numeric(filtered['days_past_due'], errors='coerce')
        st.markdown("Overall DPD histogram (including negative values = not yet due)")
        fig_all = px.histogram(filtered, x='days_past_due', nbins=40, title="DPD Distribution (all)")
        st.plotly_chart(fig_all, use_container_width=True)

        st.markdown("DPD histogram (only overdue loans: days_past_due > 0)")
        overdue = filtered[filtered['days_past_due'] > 0].copy()
        fig_overdue = px.histogram(overdue, x='days_past_due', nbins=40, title="Overdue DPD Distribution (days > 0)")
        st.plotly_chart(fig_overdue, use_container_width=True)

        st.markdown("DPD summary statistics")
        stats = filtered['days_past_due'].describe().to_frame().transpose()
        st.dataframe(stats)
    else:
        st.info("No DPD column detected. Detected mapping: " + str(found))

# --- Repayment Rate (MoM) ---
with tab_recovery:
    st.subheader("Month-to-Month Recovery Rate")
    if {'sum_recovered', 'sum_disbursed'}.issubset(filtered.columns):
        mr = filtered.groupby('Loan_Month_Year')[['sum_recovered', 'sum_disbursed']].sum().reset_index()
        mr = sort_month_df(mr, 'Loan_Month_Year')
        mr['recovery_pct'] = (mr['sum_recovered'] / mr['sum_disbursed'] * 100).replace([float('inf'), -float('inf')], 0)
        fig_r = px.line(mr, x='Loan_Month_Year', y='recovery_pct', markers=True, title="Monthly Recovery Rate (%)")
        st.plotly_chart(fig_r, use_container_width=True)
    else:
        st.info("Missing sum_recovered and/or sum_disbursed for recovery rate calculation. Detected mapping: " + str(found))

# --- DPD by Segment (improved visuals) ---
with tab_dpdseg:
    st.subheader("DPD by Segment (violin + buckets)")
    if {'segment', 'days_past_due'}.issubset(filtered.columns):
        filtered['days_past_due'] = pd.to_numeric(filtered['days_past_due'], errors='coerce')

        # create buckets for discrete coloring (works on older plotly versions)
        def dpd_bucket(x):
            try:
                x = float(x)
            except:
                return 'Unknown'
            if x <= 0:
                return 'Current/Not due'
            if x <= 30:
                return '1-30'
            if x <= 60:
                return '31-60'
            if x <= 90:
                return '61-90'
            return '90+'

        filtered['dpd_bucket'] = filtered['days_past_due'].apply(dpd_bucket)

        # Violin (shows distribution per segment, focuses on density)
        overdue = filtered[filtered['days_past_due'] > 0]
        if overdue.empty:
            st.info("No overdue loans (days_past_due > 0) to show violin for.")
        else:
            violin = px.violin(overdue, x='segment', y='days_past_due', box=True, points='all',
                               title="Overdue DPD distribution by Segment (violin + points)")
            st.plotly_chart(violin, use_container_width=True)

        # Strip plot colored by bucket (discrete colors)
        strip = px.strip(filtered, x='segment', y='days_past_due', color='dpd_bucket',
                         title="All DPD points by Segment (colored by bucket)")
        strip.update_traces(jitter=0.3, marker=dict(size=6, opacity=0.7))
        st.plotly_chart(strip, use_container_width=True)

        # Aggregated segment stats
        seg_stats = filtered.groupby('segment')['days_past_due'].agg(['count', 'mean', 'median', 'max']).reset_index()
        seg_stats.columns = ['Segment', 'Count', 'Mean_DPD', 'Median_DPD', 'Max_DPD']
        # percent overdue
        pct_overdue = filtered.groupby('segment').apply(lambda x: (x['days_past_due'] > 0).sum() / max(1, len(x)) * 100).reset_index(name='Pct_Overdue')
        seg_stats = seg_stats.merge(pct_overdue, left_on='Segment', right_on='segment').drop(columns=['segment'])
        seg_stats['Pct_Overdue'] = seg_stats['Pct_Overdue'].round(2)
        st.subheader("DPD summary by Segment")
        st.dataframe(seg_stats)
    else:
        st.info("Segment and/or DPD columns not detected. Detected mapping: " + str(found))

# --- MoM % Change (Sum_Set_up_Fee as line) ---
with tab_mom:
    st.subheader("Month-to-Month % Change (select metric)")
    available_metrics = []
    if 'sum_setup_fee' in filtered.columns:
        available_metrics.append('sum_setup_fee')
    if 'sum_recovered' in filtered.columns:
        available_metrics.append('sum_recovered')
    if 'sum_disbursed' in filtered.columns:
        available_metrics.append('sum_disbursed')

    if not available_metrics:
        st.info("No candidate metrics found for MoM % change. Detected mapping: " + str(found))
    else:
        metric = st.selectbox("Choose metric for MoM % change (line chart preferred for setup fee)", options=available_metrics, index=0)
        mom = filtered.groupby('Loan_Month_Year')[[metric]].sum().reset_index()
        mom = sort_month_df(mom, 'Loan_Month_Year')
        mom[metric + '_mom_pct'] = mom[metric].pct_change() * 100
        # plot line for setup fee, bar otherwise (but user can choose)
        fig_mom = px.line(mom, x='Loan_Month_Year', y=metric + '_mom_pct', markers=True, title=f"MoM % Change: {metric}")
        st.plotly_chart(fig_mom, use_container_width=True)

st.markdown("---")
st.markdown("If you still see 'column missing' errors, please reply with the exact error message and I will update the detection logic to include that column variant.")
