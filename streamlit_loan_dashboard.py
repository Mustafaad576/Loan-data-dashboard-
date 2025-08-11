import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Microfinance Loan Analysis Dashboard", layout="wide")

st.title("📊 Microfinance Loan Analysis Dashboard")
st.markdown("Upload your loan dataset in Excel format to explore the dashboard.")

# File uploader
uploaded_file = st.file_uploader("Upload your Excel file", type=["xlsx"])

if uploaded_file:
    try:
        df = pd.read_excel(uploaded_file)

        # Ensure date columns are parsed
        if 'actual_date_of_loan' in df.columns:
            df['actual_date_of_loan'] = pd.to_datetime(df['actual_date_of_loan'], errors='coerce')
            df['Loan_Month_Year'] = df['actual_date_of_loan'].dt.to_period('M').astype(str)
        else:
            st.error("The dataset must contain a column named 'actual_date_of_loan'.")
            st.stop()

        # Tabs
        tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
            "Overview",
            "Trend Analysis",
            "Customer Segmentation",
            "Risk Analysis",
            "Repayment Rate",
            "DPD by Segment",
            "MoM % Change"
        ])

        # --- Tab 1: Overview ---
        with tab1:
            st.subheader("Overall Loan Summary")
            total_disbursed = df['Sum_Loan_Amount_Disbursed'].sum()
            total_recovered = df['Sum_Total_Recovered'].sum()
            total_outstanding = df['Outstanding_Principle'].sum()
            recovery_rate = (total_recovered / total_disbursed) * 100 if total_disbursed else 0

            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Total Disbursed", f"{total_disbursed:,.0f}")
            col2.metric("Total Recovered", f"{total_recovered:,.0f}")
            col3.metric("Outstanding", f"{total_outstanding:,.0f}")
            col4.metric("Recovery Rate (%)", f"{recovery_rate:.2f}%")

        # --- Tab 2: Trend Analysis ---
        with tab2:
            st.subheader("Monthly Loan and Recovery Trends")
            monthly = df.groupby('Loan_Month_Year')[['Sum_Loan_Amount_Disbursed', 'Sum_Total_Recovered']].sum().reset_index()
            fig_trend = px.line(monthly, x='Loan_Month_Year', y=['Sum_Loan_Amount_Disbursed', 'Sum_Total_Recovered'], markers=True)
            st.plotly_chart(fig_trend, use_container_width=True)

        # --- Tab 3: Customer Segmentation ---
        with tab3:
            st.subheader("Customer Segmentation")
            if 'Gender' in df.columns:
                gender_counts = df['Gender'].value_counts().reset_index()
                fig_gender = px.pie(gender_counts, names='index', values='Gender', title="Customer Distribution by Gender")
                st.plotly_chart(fig_gender, use_container_width=True)

            if 'Segment' in df.columns:
                segment_counts = df['Segment'].value_counts().reset_index()
                fig_segment = px.bar(segment_counts, x='index', y='Segment', title="Customer Distribution by Segment")
                st.plotly_chart(fig_segment, use_container_width=True)

        # --- Tab 4: Risk Analysis ---
        with tab4:
            st.subheader("Risk Analysis")
            if 'Days_Past_Due_Date' in df.columns:
                overdue = df[df['Days_Past_Due_Date'] > 0]
                avg_dpd = df['Days_Past_Due_Date'].mean()
                col1, col2 = st.columns(2)
                col1.metric("Total Overdue Loans", len(overdue))
                col2.metric("Average DPD", f"{avg_dpd:.2f} days")

                fig_dpd = px.histogram(df, x='Days_Past_Due_Date', nbins=20, title="DPD Distribution")
                st.plotly_chart(fig_dpd, use_container_width=True)

        # --- Tab 5: Repayment Rate ---
        with tab5:
            st.subheader("Month-to-Month Repayment/Recovery Rate")
            if 'Sum_Total_Recovered' in df.columns and 'Sum_Loan_Amount_Disbursed' in df.columns:
                monthly_rates = df.groupby('Loan_Month_Year')[['Sum_Total_Recovered', 'Sum_Loan_Amount_Disbursed']].sum()
                monthly_rates['Recovery_Rate_%'] = (monthly_rates['Sum_Total_Recovered'] / monthly_rates['Sum_Loan_Amount_Disbursed']) * 100
                monthly_rates = monthly_rates.reset_index()
                fig_recovery_rate = px.line(monthly_rates, x='Loan_Month_Year', y='Recovery_Rate_%', markers=True, title="Monthly Recovery Rate (%)")
                st.plotly_chart(fig_recovery_rate, use_container_width=True)

        # --- Tab 6: DPD by Segment ---
        with tab6:
            st.subheader("DPD Distribution by Customer Segment")
            if 'Segment' in df.columns and 'Days_Past_Due_Date' in df.columns:
                fig_dpd_segment = px.strip(
                    df,
                    x='Segment',
                    y='Days_Past_Due_Date',
                    color='Days_Past_Due_Date',
                    color_continuous_scale='RdYlGn_r',
                    title="Days Past Due by Segment (Color = Severity)"
                )
                fig_dpd_segment.update_traces(jitter=True, marker=dict(size=6))
                st.plotly_chart(fig_dpd_segment, use_container_width=True)

        # --- Tab 7: MoM % Change ---
        with tab7:
            st.subheader("Month-to-Month Percentage Change")
            if 'Sum_Set_up_Fee' in df.columns and 'Sum_Total_Recovered' in df.columns:
                metrics = ['Sum_Set_up_Fee', 'Sum_Total_Recovered']
                mom_df = df.groupby('Loan_Month_Year')[metrics].sum().pct_change() * 100
                mom_df = mom_df.reset_index()

                # Line chart for Sum_Set_up_Fee
                fig_fee = px.line(
                    mom_df,
                    x='Loan_Month_Year',
                    y='Sum_Set_up_Fee',
                    markers=True,
                    title="MoM % Change: Sum_Set_up_Fee"
                )
                st.plotly_chart(fig_fee, use_container_width=True)

                # Bar chart for Sum_Total_Recovered
                fig_recovered = px.bar(
                    mom_df,
                    x='Loan_Month_Year',
                    y='Sum_Total_Recovered',
                    title="MoM % Change: Sum_Total_Recovered"
                )
                st.plotly_chart(fig_recovered, use_container_width=True)

    except Exception as e:
        st.error(f"Error loading file: {e}")
else:
    st.info("Please upload an Excel file to proceed.")
