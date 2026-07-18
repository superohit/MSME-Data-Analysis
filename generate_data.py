"""
generate_data.py
----------------
Generates a realistic synthetic MSME Exporter Financing & Loan Disbursement dataset
inspired by RBI DBIE, DGFT export performance data, and SIDBI MSME Pulse reports.

Output: data/msme_loan_disbursements.csv
"""

import os
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import random

random.seed(42)
np.random.seed(42)

os.makedirs("data", exist_ok=True)

# ── Reference Data ────────────────────────────────────────────────────────────

STATES = {
    "Maharashtra":    {"weight": 0.14, "tier": 1},
    "Gujarat":        {"weight": 0.12, "tier": 1},
    "Tamil Nadu":     {"weight": 0.11, "tier": 1},
    "Karnataka":      {"weight": 0.09, "tier": 1},
    "Uttar Pradesh":  {"weight": 0.07, "tier": 2},
    "Rajasthan":      {"weight": 0.06, "tier": 2},
    "Punjab":         {"weight": 0.06, "tier": 2},
    "West Bengal":    {"weight": 0.05, "tier": 2},
    "Andhra Pradesh": {"weight": 0.05, "tier": 2},
    "Telangana":      {"weight": 0.05, "tier": 2},
    "Madhya Pradesh": {"weight": 0.04, "tier": 2},
    "Haryana":        {"weight": 0.04, "tier": 2},
    "Odisha":         {"weight": 0.03, "tier": 3},
    "Jharkhand":      {"weight": 0.03, "tier": 3},
    "Chhattisgarh":   {"weight": 0.02, "tier": 3},
    "Bihar":          {"weight": 0.02, "tier": 3},
    "Assam":          {"weight": 0.01, "tier": 3},
    "Uttarakhand":    {"weight": 0.01, "tier": 3},
}

SECTORS = {
    "Engineering Goods":           {"itchs": "84-85", "avg_loan": 4200000,  "npa_rate": 0.06},
    "Textiles & Apparel":          {"itchs": "50-63", "avg_loan": 1800000,  "npa_rate": 0.09},
    "Chemicals & Pharma":          {"itchs": "28-30", "avg_loan": 3500000,  "npa_rate": 0.05},
    "Leather & Footwear":          {"itchs": "41-64", "avg_loan": 1200000,  "npa_rate": 0.10},
    "Gems & Jewellery":            {"itchs": "71",    "avg_loan": 6500000,  "npa_rate": 0.07},
    "Agriculture & Food Products": {"itchs": "01-24", "avg_loan": 900000,   "npa_rate": 0.12},
    "Plastics & Rubber":           {"itchs": "39-40", "avg_loan": 1500000,  "npa_rate": 0.08},
    "Marine Products":             {"itchs": "03",    "avg_loan": 750000,   "npa_rate": 0.11},
    "Handicrafts":                 {"itchs": "97",    "avg_loan": 450000,   "npa_rate": 0.13},
    "Electronic Components":       {"itchs": "85-90", "avg_loan": 5200000,  "npa_rate": 0.04},
}

DESTINATION_COUNTRIES = {
    "USA":          {"risk": "Low",    "weight": 0.20},
    "UAE":          {"risk": "Low",    "weight": 0.12},
    "UK":           {"risk": "Low",    "weight": 0.08},
    "Germany":      {"risk": "Low",    "weight": 0.07},
    "Singapore":    {"risk": "Low",    "weight": 0.06},
    "Bangladesh":   {"risk": "Medium", "weight": 0.06},
    "China":        {"risk": "Medium", "weight": 0.05},
    "South Africa": {"risk": "Medium", "weight": 0.05},
    "Brazil":       {"risk": "Medium", "weight": 0.04},
    "Nigeria":      {"risk": "High",   "weight": 0.04},
    "Sri Lanka":    {"risk": "Medium", "weight": 0.04},
    "Vietnam":      {"risk": "Low",    "weight": 0.04},
    "Egypt":        {"risk": "High",   "weight": 0.03},
    "Turkey":       {"risk": "Medium", "weight": 0.03},
    "Iran":         {"risk": "High",   "weight": 0.02},
    "Russia":       {"risk": "High",   "weight": 0.02},
    "Others":       {"risk": "Medium", "weight": 0.05},
}

BANKS = [
    "State Bank of India", "Bank of Baroda", "Canara Bank",
    "Union Bank of India", "Punjab National Bank", "EXIM Bank of India",
    "SIDBI", "HDFC Bank", "ICICI Bank", "Axis Bank",
    "Indian Bank", "Bank of India"
]

LOAN_TYPES    = ["Pre-Shipment Credit", "Post-Shipment Credit", "Export Bill Discounting",
                 "Packing Credit", "Export Factoring", "ECGC-backed Term Loan"]
ENTERPRISE_SZ = ["Micro", "Small", "Medium"]

# ── COVID & Macro Shock Factors by FY ─────────────────────────────────────────
FISCAL_YEAR_FACTORS = {
    "FY2015-16": 1.00, "FY2016-17": 1.04, "FY2017-18": 1.09,
    "FY2018-19": 1.15, "FY2019-20": 1.10, "FY2020-21": 0.74,   # COVID dip
    "FY2021-22": 0.91, "FY2022-23": 1.08, "FY2023-24": 1.18,
}

# ── Helper Functions ──────────────────────────────────────────────────────────

def get_fy(date):
    return f"FY{date.year}-{str(date.year+1)[-2:]}" if date.month >= 4 \
        else f"FY{date.year-1}-{str(date.year)[-2:]}"

def random_date(fy_label):
    year = int(fy_label[2:6])
    start = datetime(year, 4, 1)
    end   = datetime(year + 1, 3, 31)
    return start + timedelta(days=random.randint(0, (end - start).days))

def compute_risk_score(row):
    score = 0
    # NPA history
    if row["NPA_History"] == "Yes":          score += 35
    # Export turnover volatility
    if row["Turnover_Volatility_Pct"] > 30:  score += 20
    elif row["Turnover_Volatility_Pct"] > 15: score += 10
    # Destination country risk
    if row["Destination_Risk"] == "High":    score += 25
    elif row["Destination_Risk"] == "Medium": score += 10
    # Sector NPA rate
    npa_rate = SECTORS[row["Sector"]]["npa_rate"]
    if npa_rate > 0.10:   score += 15
    elif npa_rate > 0.07: score += 8
    # Enterprise size (Micro = higher risk)
    if row["Enterprise_Size"] == "Micro":    score += 10
    elif row["Enterprise_Size"] == "Small":  score += 5
    # Loan amount relative to sector average
    avg = SECTORS[row["Sector"]]["avg_loan"]
    if row["Loan_Amount_INR"] > avg * 2:     score += 10
    return min(score, 100)

def risk_tier(score):
    if score >= 60:  return "High"
    if score >= 30:  return "Medium"
    return "Low"

def ies_eligible(sector, loan_type, fy):
    # IES eligibility: most sectors eligible pre-FY2024; some excluded post policy changes
    ineligible_sectors = ["Gems & Jewellery"]   # historically excluded
    if sector in ineligible_sectors:    return "No"
    if loan_type == "ECGC-backed Term Loan": return "No"
    return "Yes"

def ies_claimed(eligible, npa, risk):
    if eligible == "No" or npa == "Yes": return "No"
    # Tier-3 states claim less due to awareness gaps
    claim_prob = 0.85 if risk == "Low" else 0.60 if risk == "Medium" else 0.30
    return "Yes" if random.random() < claim_prob else "No"

# ── Main Generation ───────────────────────────────────────────────────────────

records = []
n_records = 8000

state_names   = list(STATES.keys())
state_weights = [STATES[s]["weight"] for s in state_names]
dest_names    = list(DESTINATION_COUNTRIES.keys())
dest_weights  = [DESTINATION_COUNTRIES[d]["weight"] for d in dest_names]

for i in range(n_records):
    fy_label  = random.choice(list(FISCAL_YEAR_FACTORS.keys()))
    fy_factor = FISCAL_YEAR_FACTORS[fy_label]
    date      = random_date(fy_label)

    state     = random.choices(state_names, weights=state_weights)[0]
    sector    = random.choice(list(SECTORS.keys()))
    dest      = random.choices(dest_names,  weights=dest_weights)[0]
    bank      = random.choice(BANKS)
    loan_type = random.choice(LOAN_TYPES)
    ent_size  = random.choices(ENTERPRISE_SZ, weights=[0.45, 0.35, 0.20])[0]

    base_loan = SECTORS[sector]["avg_loan"]
    size_mult = {"Micro": 0.5, "Small": 1.0, "Medium": 2.2}[ent_size]
    loan_amt  = int(base_loan * size_mult * fy_factor * np.random.lognormal(0, 0.35))
    loan_amt  = max(100000, min(loan_amt, 50000000))  # cap between 1L–5Cr

    export_turnover = int(loan_amt * np.random.uniform(1.5, 4.5))
    volatility      = round(np.random.uniform(5, 55), 1)
    npa_hist        = "Yes" if random.random() < SECTORS[sector]["npa_rate"] else "No"
    dest_risk       = DESTINATION_COUNTRIES[dest]["risk"]
    state_tier      = STATES[state]["tier"]
    itchs           = SECTORS[sector]["itchs"]
    ies_elig        = ies_eligible(sector, loan_type, fy_label)

    row = {
        "Loan_ID":                  f"IES{str(i+1).zfill(6)}",
        "Disbursement_Date":        date.strftime("%Y-%m-%d"),
        "Fiscal_Year":              fy_label,
        "State":                    state,
        "State_Tier":               state_tier,
        "Sector":                   sector,
        "ITC_HS_Chapter":           itchs,
        "Enterprise_Size":          ent_size,
        "Lending_Bank":             bank,
        "Loan_Type":                loan_type,
        "Loan_Amount_INR":          loan_amt,
        "Export_Turnover_INR":      export_turnover,
        "Turnover_Volatility_Pct":  volatility,
        "Destination_Country":      dest,
        "Destination_Risk":         dest_risk,
        "NPA_History":              npa_hist,
        "IES_Eligible":             ies_elig,
    }

    row["Risk_Score"]   = compute_risk_score(row)
    row["Risk_Tier"]    = risk_tier(row["Risk_Score"])
    row["IES_Claimed"]  = ies_claimed(ies_elig, npa_hist, row["Risk_Tier"])

    records.append(row)

df = pd.DataFrame(records)
df.to_csv("data/msme_loan_disbursements.csv", index=False)
print(f"Dataset generated: {len(df)} records → data/msme_loan_disbursements.csv")
print(df.head(3).to_string())
print(f"\nFiscal Year distribution:\n{df['Fiscal_Year'].value_counts().sort_index()}")
