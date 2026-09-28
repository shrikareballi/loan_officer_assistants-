import math

def calculate_dti(income, debt):
    return debt / income

def calculate_ltv(loan_amount, property_value):
    return loan_amount / property_value

def calculate_emi(principal, annual_rate, tenure_months):
    monthly_rate = annual_rate / 12
    emi = (principal * monthly_rate * (1 + monthly_rate)**tenure_months) / ((1 + monthly_rate)**tenure_months - 1)
    return emi
