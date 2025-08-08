import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Microfinance Loan Dashboard", layout="wide")
st.title("📊 Microfinance Loan Analysis Dashboard")

# File upload
uploaded_file = st.file_uploader("📤 Upload your Excel file", type=["xlsx"])

if uploaded_file is not None:
    try:
        # Load Excel
        df = pd.read_excel(uploaded_file, engine="openpyxl")
        df['actual_date_of_loan'] = pd.to_datetime(df['actual_date_of_loan'], errors='coerce')
        df['Loan_Month_Year'] = df['actual_date_of_loan'].dt.to_period('M').astype(str)

        # Sidebar filters
        st.sidebar.header("🔍 Filter Options")
        loan_status_filter = st.sidebar.multiselect(
            "Loan Status",
            options=df['Loan_Status'].dropna().unique(),
            default=list(df['Loan_Status'].dropna().unique())
        )
        segment_filter = st.sidebar.multiselect(
            "Segment",
            options=df['Segment'].dropna().unique(),
            default=list(df['Segment'].dropna().unique())
        )
        gender_filter = st.sidebar.multiselect(
            "Gender",
            options=df['Gender'].dropna().unique(),
            default=list(df['Gender'].dropna().unique())
        )

        filtered_df = df[
            (df['Loan_Status'].isin(loan_status_filter)) &
            (df['Segment'].isin(segment_filter)) &
            (df['Gender'].isin(gender_filter))
        ]

        # Tabs
        tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
            "📈 Overview",
            "📅 Trend Analysis",
            "👥 Customer Segments",
            "⚠️ Risk Analysis",
            "💰 Recovery Rate (MoM)",
            "📊 DPD by Segment",
            "📉 MoM % Change"
        ])

        # --- Tab 1: Overview ---
        with tab1:
            st.subheader("Loan Portfolio Overview")

            total_disbursed = filtered_df['Sum_Loan_Amount_Disbursed'].sum()
            total_recovered = filtered_df['Sum_Total_Recovered'].sum()
            total_outstanding = filtered_df['Outstanding_Principle'].sum()
            recovery_rate = (total_recovered / total_disbursed) * 100 if total_disbursed != 0 else 0

            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Total Disbursed", f"PKR {total_disbursed:,.0f}")
            col2.metric("Total Recovered", f"PKR {total_recovered:,.0f}")
            col3.metric("Outstanding", f"PKR {total_outstanding:,.0f}")
            col4.metric("Recovery Rate", f"{recovery_rate:.2f}%")

            st.plotly_chart(
                px.pie(filtered_df, names='Account_State_Name', title='Account State Distribution'),
                use_container_width=True
            )

        # --- Tab 2: Trend Analysis ---
        with tab2:
            st.subheader("Monthly Trends")

            monthly = filtered_df.groupby('Loan_Month_Year').agg({
                'Sum_Loan_Amount_Disbursed': 'sum',
                'Sum_Total_Recovered': 'sum',
                'Outstanding_Principle': 'sum'
            }).reset_index()

            fig1 = px.line(monthly, x='Loan_Month_Year', y='Sum_Loan_Amount_Disbursed', title="Monthly Loan Disbursal")
            fig2 = px.line(monthly, x='Loan_Month_Year', y='Sum_Total_Recovered', title="Monthly Recovery")
            fig3 = px.line(monthly, x='Loan_Month_Year', y='Outstanding_Principle', title="Outstanding Principal Over Time")

            st.plotly_chart(fig1, use_container_width=True)
            st.plotly_chart(fig2, use_container_width=True)
            st.plotly_chart(fig3, use_container_width=True)

        # --- Tab 3: Customer Segmentation ---
        with tab3:
            st.subheader("Customer Segmentation")

            seg_count = filtered_df['Segment'].value_counts().reset_index()
            seg_count.columns = ['Segment', 'Count']
            fig_seg = px.bar(seg_count, x='Segment', y='Count', title="Customers by Segment")

            gender_count = filtered_df['Gender'].value_counts().reset_index()
            gender_count.columns = ['Gender', 'Count']
            fig_gender = px.pie(gender_count, names='Gender', values='Count', title='Gender Distribution')

            acct_type = filtered_df['Customer_Account_Type'].value_counts().reset_index()
            acct_type.columns = ['Account Type', 'Count']
            fig_acct = px.bar(acct_type, x='Account Type', y='Count', title="Customer Account Types")

            st.plotly_chart(fig_seg, use_container_width=True)
            st.plotly_chart(fig_gender, use_container_width=True)
            st.plotly_chart(fig_acct, use_container_width=True)

        # --- Tab 4: Risk Analysis ---
        with tab4:
            st.subheader("Loan Risk and Default Analysis")

            overdue = filtered_df[filtered_df['Days_Past_Due_Date'] > 0]
            overdue_count = len(overdue)
            avg_dpd = overdue['Days_Past_Due_Date'].mean() if overdue_count > 0 else 0

            col5, col6 = st.columns(2)
            col5.metric("Overdue Loans", f"{overdue_count}")
            col6.metric("Avg Days Past Due", f"{avg_dpd:.1f} days")

            fig_dpd = px.histogram(filtered_df, x='Days_Past_Due_Date', nbins=30, title="DPD Distribution")
            st.plotly_chart(fig_dpd, use_container_width=True)

        # --- Tab 5: Recovery Rate MoM ---
        with tab5:
            st.subheader("Month-to-Month Recovery Rate")

            recovery_df = filtered_df.groupby('Loan_Month_Year').agg({
                'Sum_Loan_Amount_Disbursed': 'sum',
                'Sum_Total_Recovered': 'sum'
            }).reset_index()
            recovery_df['Recovery_Rate_%'] = (recovery_df['Sum_Total_Recovered'] / recovery_df['Sum_Loan_Amount_Disbursed']) * 100

            fig_recovery = px.line(recovery_df, x='Loan_Month_Year', y='Recovery_Rate_%', title="Recovery Rate Over Time (%)")
            st.plotly_chart(fig_recovery, use_container_width=True)

        # --- Tab 6: DPD by Segment ---
        with tab6:
            st.subheader("DPD Distribution by Customer Segment")
            fig_dpd_segment = px.box(
                filtered_df, x='Segment', y='Days_Past_Due_Date', points="all",
                title="Days Past Due by Segment"
            )
            st.plotly_chart(fig_dpd_segment, use_container_width=True)

        # --- Tab 7: MoM % Change ---
        with tab7:
            st.subheader("Month-to-Month Percentage Change")

            metrics = ['Sum_Set_up_Fee', 'Sum_Total_Recovered']  # FIXED COLUMN NAME
            mom_df = filtered_df.groupby('Loan_Month_Year')[metrics].sum().pct_change() * 100
            mom_df = mom_df.reset_index()

            for metric in metrics:
                fig_metric = px.bar(mom_df, x='Loan_Month_Year', y=metric, title=f"MoM % Change: {metric}")
                st.plotly_chart(fig_metric, use_container_width=True)

    except Exception as e:
        st.error(f"Error loading file: {e}")
else:
    st.info("Please upload an Excel file to begin.")
