import streamlit as st
import requests
import matplotlib.pyplot as plt

st.title("Loan Office Assistant")

income = st.number_input("Income", min_value=0.0)
debt = st.number_input("Debt", min_value=0.0)
loan_amount = st.number_input("Loan Amount", min_value=0.0)
property_value = st.number_input("Property Value", min_value=0.0)
interest_rate = st.number_input("Interest Rate (%)", min_value=0.0) / 100
tenure = st.number_input("Tenure (months)", min_value=1)

if st.button("Calculate"):
    dti = debt / income if income else 0
    ltv = loan_amount / property_value if property_value else 0
    emi = (loan_amount * (interest_rate/12) * (1 + interest_rate/12)**tenure) / ((1 + interest_rate/12)**tenure - 1)

    st.write(f"DTI: {dti:.2f}")
    st.write(f"LTV: {ltv:.2f}")
    st.write(f"EMI: {emi:.2f}")

    # Pie chart for EMI breakdown
    principal = loan_amount
    total_payment = emi * tenure
    interest = total_payment - principal

    fig, ax = plt.subplots()
    ax.pie([principal, interest], labels=['Principal', 'Interest'], autopct='%1.1f%%')
    st.pyplot(fig)
