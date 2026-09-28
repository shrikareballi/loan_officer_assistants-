from backend.calculations import calculate_dti, calculate_ltv, calculate_emi

def test_dti():
    # Debt = 1000, Income = 5000 → DTI = 20%
    assert calculate_dti(1000, 5000) == 20.0

def test_ltv():
    # Loan = 200000, Property = 250000 → LTV = 80%
    assert calculate_ltv(200000, 250000) == 80.0

def test_emi():
    # Loan = 100000, Interest = 8%, Tenure = 10 years → EMI ≈ 1213.28
    emi = calculate_emi(100000, 8, 10)
    assert round(emi, 2) == 1213.28

