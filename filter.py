import pandas as pd

df = pd.read_csv("budget.csv")
df.columns = (
    df.columns.str.strip()
    .str.replace(" ", "_")
    .str.replace("[^a-zA-Z0-9_]", "", regex=True)
)

if "Record_Date" in df.columns:
    df['Record_Date'] = pd.to_datetime(df['Record_Date'], errors='coerce')

# Negyedév oszlop létrehozása
df['Quarter'] = (
    df['Record_Date'].dt.year.astype(str) + " Q" +
    (((df['Record_Date'].dt.month - 1) // 3) + 1).astype(str)
)

# Csak az első negyedév (pl. 2023 Q1)
target_quarter = "2023 Q1"
filtered = df[df['Quarter'] == target_quarter].copy()

# Csak az első 100 sor
filtered = filtered.head(100)

filtered.to_csv("filtered_budget.csv", index=False)
print(f"Szűrt CSV mentve: filtered_budget.csv ({len(filtered)} sor, csak {target_quarter})")