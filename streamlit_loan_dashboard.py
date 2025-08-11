import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Microfinance Loan Analysis Dashboard", layout="wide")
st.title("📊 Microfinance Loan Analysis Dashboard")
st.markdown("Upload your loan dataset in Excel format to explore the dashboard.")

# File uploader
uploaded_file = st.file_uploader("Upload your Excel file", type=["xlsx"])

def sort_months_chronologically(df, month_col='Loan_Month_Year'):
    # convert "YYYY-MM" (or similar) to a datetime so plots are ordered correctly
    tmp = df.copy()
    tmp['_month_dt'] = pd.to_datetime(tmp[month_col].astype(str) + '-01', errors='coerce')
    tmp = tmp.sort_values('_month_dt').drop(columns=['_month_dt'])
    return tmp

if uploaded_file:
    try:
        # Read excel
        df = pd.read_excel(uploaded_file, engine="openpyxl")

        # Check date column
        if 'actual_date_of_loan' not in df.columns:
            st.error("The dataset must contain a column named 'actual_date_of_loan'.")
            st.stop()

        df['actual_date_of_loan'] = pd.to_datetime(df['actual_date_of_loan'], errors='coerce')
        df['Loan_Month_Year'] = df['actual_date_of_loan'].dt.to_period('M').astype(str)

        # Tabs
        tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
            "Overview", "Trend Analysis", "Customer Segmentation", "Risk Analysis",
            "Repayment Rate", "DPD by Segment", "MoM % Change"
        ])

        # --- Tab 1: Overview ---
        with tab1:
            st.subheader("Overall Loan Summary")
            total_disbursed = df.get('Sum_Loan_Amount_Disbursed', pd.Series()).sum()
            total_recovered = df.get('Sum_Total_Recovered', pd.Series()).sum()
            total_outstanding = df.get('Outstanding_Principle', pd.Series()).sum()
            recovery_rate = (total_recovered / total_disbursed) * 100 if total_disbursed else 0

            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Total Disbursed", f"{total_disbursed:,.0f}")
            c2.metric("Total Recovered", f"{total_recovered:,.0f}")
            c3.metric("Outstanding", f"{total_outstanding:,.0f}")
            c4.metric("Recovery Rate (%)", f"{recovery_rate:.2f}%")

        # --- Tab 2: Trend Analysis ---
        with tab2:
            st.subheader("Monthly Loan and Recovery Trends")
            if 'Sum_Loan_Amount_Disbursed' in df.columns and 'Sum_Total_Recovered' in df.columns:
                monthly = df.groupby('Loan_Month_Year')[['Sum_Loan_Amount_Disbursed', 'Sum_Total_Recovered']].sum().reset_index()
                monthly = sort_months_chronologically(monthly, 'Loan_Month_Year')
                fig_trend = px.line(monthly, x='Loan_Month_Year', y=['Sum_Loan_Amount_Disbursed', 'Sum_Total_Recovered'],
                                    markers=True, title="Loan Disbursal & Recovery (monthly)")
                st.plotly_chart(fig_trend, use_container_width=True)
            else:
                st.info("Columns 'Sum_Loan_Amount_Disbursed' and/or 'Sum_Total_Recovered' missing for trend analysis.")

        # --- Tab 3: Customer Segmentation ---
        with tab3:
            st.subheader("Customer Segmentation")
            if 'Gender' in df.columns:
                gender_counts = df['Gender'].value_counts().reset_index()
                # Explicitly rename columns to avoid ambiguity
                gender_counts.columns = ['Gender', 'Count']
                fig_gender = px.pie(gender_counts, names='Gender', values='Count', title="Customer Distribution by Gender")
                st.plotly_chart(fig_gender, use_container_width=True)
            else:
                st.info("Column 'Gender' not found.")

            if 'Segment' in df.columns:
                segment_counts = df['Segment'].value_counts().reset_index()
                segment_counts.columns = ['Segment', 'Count']
                fig_segment = px.bar(segment_counts, x='Segment', y='Count', title="Customer Distribution by Segment")
                st.plotly_chart(fig_segment, use_container_width=True)
            else:
                st.info("Column 'Segment' not found.")

            if 'Customer_Account_Type' in df.columns:
                acct_counts = df['Customer_Account_Type'].value_counts().reset_index()
                acct_counts.columns = ['Account_Type', 'Count']
                fig_acct = px.bar(acct_counts, x='Account_Type', y='Count', title="Customer Account Types")
                st.plotly_chart(fig_acct, use_container_width=True)

        # --- Tab 4: Risk Analysis ---
        with tab4:
            st.subheader("Risk Analysis")
            if 'Days_Past_Due_Date' in df.columns:
                overdue = df[df['Days_Past_Due_Date'] > 0]
                avg_dpd = df['Days_Past_Due_Date'].mean()
                rc1, rc2 = st.columns(2)
                rc1.metric("Total Overdue Loans", len(overdue))
                rc2.metric("Average DPD", f"{avg_dpd:.2f} days")
                fig_dpd = px.histogram(df, x='Days_Past_Due_Date', nbins=30, title="DPD Distribution")
                st.plotly_chart(fig_dpd, use_container_width=True)
            else:
                st.info("Column 'Days_Past_Due_Date' not found.")

        # --- Tab 5: Repayment Rate (MoM) ---
        with tab5:
            st.subheader("Month-to-Month Recovery Rate")
            if {'Sum_Total_Recovered', 'Sum_Loan_Amount_Disbursed'}.issubset(df.columns):
                monthly_rates = df.groupby('Loan_Month_Year')[['Sum_Total_Recovered', 'Sum_Loan_Amount_Disbursed']].sum().reset_index()
                monthly_rates = sort_months_chronologically(monthly_rates, 'Loan_Month_Year')
                monthly_rates['Recovery_Rate_%'] = (monthly_rates['Sum_Total_Recovered'] / monthly_rates['Sum_Loan_Amount_Disbursed']) * 100
                fig_recovery_rate = px.line(monthly_rates, x='Loan_Month_Year', y='Recovery_Rate_%', markers=True,
                                            title="Monthly Recovery Rate (%)")
                st.plotly_chart(fig_recovery_rate, use_container_width=True)
            else:
                st.info("Required columns for recovery rate not found: 'Sum_Total_Recovered' and/or 'Sum_Loan_Amount_Disbursed'.")

        # --- Tab 6: DPD by Segment (improved) ---
        with tab6:
            st.subheader("DPD Distribution by Customer Segment (color = severity)")
            if {'Segment', 'Days_Past_Due_Date'}.issubset(df.columns):
                # Strip/violin + color scale approach
                fig_strip = px.strip(df, x='Segment', y='Days_Past_Due_Date',
                                     color='Days_Past_Due_Date', color_continuous_scale='RdYlGn_r',
                                     title="DPD by Segment (strip plot with severity coloring)")
                fig_strip.update_traces(jitter=0.3, marker=dict(size=6, opacity=0.7))
                st.plotly_chart(fig_strip, use_container_width=True)

                # Optionally also show aggregated statistics per segment
                seg_stats = df.groupby('Segment')['Days_Past_Due_Date'].agg(['count', 'mean', 'median', 'max']).reset_index()
                seg_stats.columns = ['Segment', 'Count', 'Mean_DPD', 'Median_DPD', 'Max_DPD']
                st.subheader("DPD summary by Segment")
                st.dataframe(seg_stats)
            else:
                st.info("Columns 'Segment' and/or 'Days_Past_Due_Date' missing for DPD by segment analysis.")

        # --- Tab 7: MoM % Change (Sum_Set_up_Fee as line) ---
        with tab7:
            st.subheader("Month-to-Month Percentage Change")
            required = {'Sum_Set_up_Fee', 'Sum_Total_Recovered'}
            if required.issubset(df.columns):
                mom_df = df.groupby('Loan_Month_Year')[['Sum_Set_up_Fee', 'Sum_Total_Recovered']].sum().reset_index()
                mom_df = sort_months_chronologically(mom_df, 'Loan_Month_Year')
                mom_df[['Sum_Set_up_Fee', 'Sum_Total_Recovered']] = mom_df[['Sum_Set_up_Fee', 'Sum_Total_Recovered']].pct_change() * 100

                # Line chart for Sum_Set_up_Fee (shows rise/fall better)
                fig_fee = px.line(mom_df, x='Loan_Month_Year', y='Sum_Set_up_Fee', markers=True,
                                  title="MoM % Change: Sum_Set_up_Fee", labels={'Sum_Set_up_Fee': 'MoM % (Setup Fee)'})
                st.plotly_chart(fig_fee, use_container_width=True)

                # Bar chart for Sum_Total_Recovered (keep as bar for quick comparisons)
                fig_rec = px.bar(mom_df, x='Loan_Month_Year', y='Sum_Total_Recovered',
                                 title="MoM % Change: Sum_Total_Recovered", labels={'Sum_Total_Recovered': 'MoM % (Recovered)'})
                st.plotly_chart(fig_rec, use_container_width=True)
            else:
                st.info("Required columns for MoM % change not found: 'Sum_Set_up_Fee' and/or 'Sum_Total_Recovered'.")

    except Exception as e:
        st.error(f"Error loading file: {e}")
else:
    st.info("Please upload an Excel file to proceed.")
