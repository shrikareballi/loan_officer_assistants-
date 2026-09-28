import streamlit as st
import requests

st.title("Loan Officer Assistant")

income = st.number_input("Monthly Income", min_value=0.0)
debt = st.number_input("Monthly Debt", min_value=0.0)
loan = st.number_input("Loan Amount", min_value=0.0)
property_value = st.number_input("Property Value", min_value=0.0)
interest = st.number_input("Interest Rate (%)", min_value=0.0)
tenure = st.number_input("Tenure (years)", min_value=1)

if st.button("Analyze Loan"):
    payload = {
        "monthly_income": income,
        "monthly_debt": debt,
        "loan_amount": loan,
        "property_value": property_value,
        "interest_rate": interest,
        "tenure": tenure
    }
    response = requests.post("http://127.0.0.1:5000/analyze", json=payload)
    st.json(response.json())
