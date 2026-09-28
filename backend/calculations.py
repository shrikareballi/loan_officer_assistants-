def calculate_dti(monthly_debt, monthly_income):
    if monthly_income <= 0:
        return 0

    return (monthly_debt / monthly_income) * 100


def calculate_ltv(loan_amount, property_value):
    if property_value <= 0:
        return 0

    return (loan_amount / property_value) * 100


def calculate_emi(principal, annual_rate, years):
    monthly_rate = annual_rate / (12 * 100)
    months = years * 12

    if monthly_rate == 0:
        return principal / months

    emi = (
        principal
        * monthly_rate
        * (1 + monthly_rate) ** months
        / ((1 + monthly_rate) ** months - 1)
    )

    return emi