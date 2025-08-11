import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Loan Data Dashboard", layout="wide")

st.title("📊 Microfinance Loan Data Dashboard")

# File uploader
uploaded_file = st.file_uploader("Upload your loan dataset (.xlsx)", type=["xlsx"])

if uploaded_file:
    df = pd.read_excel(uploaded_file)

    # Ensure date column is datetime
    if 'Loan_Month_Year' in df.columns:
        df['Loan_Month_Year'] = pd.to_datetime(df['Loan_Month_Year'], errors='coerce')

    # Sidebar filters
    st.sidebar.header("Filters")
    segment_filter = st.sidebar.multiselect(
        "Select Segment(s)",
        options=df['Segment'].unique() if 'Segment' in df.columns else [],
        default=df['Segment'].unique() if 'Segment' in df.columns else []
    )

    filtered_df = df[df['Segment'].isin(segment_filter)] if 'Segment' in df.columns else df

    # Create tabs
    tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
        "Overview", "Loan Amounts", "Repayment/Recovery Rate", 
        "DPD Distribution", "Customer Segments", 
        "DPD by Segment", "MoM % Change"
    ])

    # --- Tab 1: Overview ---
    with tab1:
        st.subheader("Dataset Overview")
        st.dataframe(filtered_df)
        st.write("Shape:", filtered_df.shape)

    # --- Tab 2: Loan Amounts ---
    with tab2:
        if 'Loan_Month_Year' in filtered_df.columns and 'Loan_Amount' in filtered_df.columns:
            loan_monthly = filtered_df.groupby('Loan_Month_Year')['Loan_Amount'].sum().reset_index()
            fig_loan = px.bar(loan_monthly, x='Loan_Month_Year', y='Loan_Amount',
                              title="Total Loan Amount by Month")
            st.plotly_chart(fig_loan, use_container_width=True)
        else:
            st.info("Required columns missing: 'Loan_Month_Year', 'Loan_Amount'.")

    # --- Tab 3: Repayment/Recovery Rate ---
    with tab3:
        if {'Loan_Month_Year', 'Total_Repaid', 'Loan_Amount'}.issubset(filtered_df.columns):
            repayment_df = filtered_df.groupby('Loan_Month_Year')[['Total_Repaid', 'Loan_Amount']].sum().reset_index()
            repayment_df['Recovery_Rate'] = (repayment_df['Total_Repaid'] / repayment_df['Loan_Amount']) * 100
            fig_recovery = px.line(repayment_df, x='Loan_Month_Year', y='Recovery_Rate', markers=True,
                                   title="Month-to-Month Recovery Rate (%)")
            st.plotly_chart(fig_recovery, use_container_width=True)
        else:
            st.info("Required columns missing for Recovery Rate calculation.")

    # --- Tab 4: DPD Distribution ---
    with tab4:
        if 'Days_Past_Due_Date' in filtered_df.columns:
            fig_dpd = px.histogram(filtered_df, x='Days_Past_Due_Date', nbins=20,
                                   title="DPD (Days Past Due) Distribution")
            st.plotly_chart(fig_dpd, use_container_width=True)
        else:
            st.info("Column 'Days_Past_Due_Date' missing.")

    # --- Tab 5: Customer Segments ---
    with tab5:
        if 'Segment' in filtered_df.columns:
            seg_count = filtered_df['Segment'].value_counts().reset_index()
            seg_count.columns = ['Segment', 'count']
            fig_seg = px.pie(seg_count, names='Segment', values='count', title="Customer Segment Distribution")
            st.plotly_chart(fig_seg, use_container_width=True)
        else:
            st.info("Column 'Segment' missing.")

    # --- Tab 6: DPD by Segment (compatible version) ---
    with tab6:
        st.subheader("DPD Distribution by Customer Segment (color = severity)")
        if {'Segment', 'Days_Past_Due_Date'}.issubset(filtered_df.columns):
            fig_strip = px.strip(
                filtered_df,
                x='Segment',
                y='Days_Past_Due_Date',
                color='Days_Past_Due_Date',  # Color points by severity
                title="DPD by Segment"
            )
            fig_strip.update_traces(jitter=0.3, marker=dict(size=6, opacity=0.7))
            fig_strip.update_layout(coloraxis_colorscale='RdYlGn_r')
            st.plotly_chart(fig_strip, use_container_width=True)

            seg_stats = filtered_df.groupby('Segment')['Days_Past_Due_Date'].agg(
                ['count', 'mean', 'median', 'max']).reset_index()
            seg_stats.columns = ['Segment', 'Count', 'Mean_DPD', 'Median_DPD', 'Max_DPD']
            st.subheader("DPD summary by Segment")
            st.dataframe(seg_stats)
        else:
            st.info("Columns 'Segment' and/or 'Days_Past_Due_Date' missing.")

    # --- Tab 7: MoM % Change ---
    with tab7:
        st.subheader("Month-to-Month Percentage Change")
        metrics = ['Sum_Set_up_Fee', 'Sum_Total_Recovered']
        if {'Loan_Month_Year'}.issubset(filtered_df.columns) and set(metrics).issubset(filtered_df.columns):
            mom_df = filtered_df.groupby('Loan_Month_Year')[metrics].sum().pct_change() * 100
            mom_df = mom_df.reset_index()

            # Line chart for Sum_Set_up_Fee
            fig_fee = px.line(mom_df, x='Loan_Month_Year', y='Sum_Set_up_Fee',
                              markers=True, title="MoM % Change: Sum_Set_up_Fee")
            st.plotly_chart(fig_fee, use_container_width=True)

            # Bar chart for Sum_Total_Recovered
            fig_recovered = px.bar(mom_df, x='Loan_Month_Year', y='Sum_Total_Recovered',
                                   title="MoM % Change: Sum_Total_Recovered")
            st.plotly_chart(fig_recovered, use_container_width=True)
        else:
            st.info(f"Required columns missing for MoM % Change: {metrics}")

else:
    st.info("Please upload an Excel file to begin analysis.")
