import pandas as pd

df = pd.read_csv("budget.csv")

# Csak a szükséges oszlopok maradnak
needed_cols = [
    "Record_Date", "Department", "Division", "Cost_Center", "Fund_Name",
    "Budgeted_Amount", "Actual_Amount", "Variance",
    "Obj_Class_Name", "Expenditure_Category", "Expenditure_Line_Item"
]
df = df[[col for col in needed_cols if col in df.columns]]

df.to_csv("budget_reduced.csv", index=False)