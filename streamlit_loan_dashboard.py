# --- Tab 7: MoM % Change ---
with tab7:
    st.subheader("Month-to-Month Percentage Change")

    metrics = ['Sum_Set_up_Fee', 'Sum_Total_Recovered']  # FIXED COLUMN NAME
    mom_df = filtered_df.groupby('Loan_Month_Year')[metrics].sum().pct_change() * 100
    mom_df = mom_df.reset_index()

    for metric in metrics:
        fig_metric = px.bar(mom_df, x='Loan_Month_Year', y=metric, title=f"MoM % Change: {metric}")
        st.plotly_chart(fig_metric, use_container_width=True)
