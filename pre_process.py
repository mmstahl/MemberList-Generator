import pandas as pd
import numpy as np

# Load your CSV
df = pd.read_csv("members data raw.csv")

# --- HEADER CLEANING ---
df.columns = df.columns.str.strip().str.replace('\ufeff', '')

# --- PRIVACY FILTER ---
df = df.query("contact_list_privacy_setting == 'Yes' and privacy_approval == 'approve'").copy()

# 1. Global Cleanup
df = df.replace({np.nan: ""})
for col in df.columns:
    df[col] = df[col].astype(str).str.strip()
    df.loc[df[col] == "0", col] = ""

# --- NEW: Lowercase Email Addresses ---
# We do this before creating reference rows so we don't lowercase the Hebrew "ראה"
df["user_email"] = df["user_email"].str.lower()
df["partneremail"] = df["partneremail"].str.lower()

# Columns to swap
user_cols = ["user_email", "first_name", "last_name", "cellphone1"]
partner_cols = ["partneremail", "partnerfirst", "partnerlast", "partnerphone"]

def has_partner_data(row):
    return any([
        row["partnerfirst"] != "",
        row["partnerlast"] != "",
        row["partneremail"] != "",
        row["partnerphone"] != ""
    ])

def maybe_swap(row):
    u_gen = str(row["yourgender"]).strip().upper()
    p_gen = str(row["partnergender"]).strip().upper()
    if not has_partner_data(row):
        return row
    if u_gen == "M" and p_gen == "F":
        user_values = row[user_cols].copy()
        partner_values = row[partner_cols].copy()
        row[user_cols] = partner_values.values
        row[partner_cols] = user_values.values
        row["yourgender"], row["partnergender"] = p_gen, u_gen
    return row

# 2. Apply swap logic
df = df.apply(maybe_swap, axis=1)

# --- 3. CROSS-REFERENCE LOGIC (NEW) ---
new_rows = []
for _, row in df.iterrows():
    if has_partner_data(row):
        # Compare last names (case-insensitive check)
        if row["last_name"].lower() != row["partnerlast"].lower() and row["partnerlast"] != "":
            # Create a "See" reference row
            ref_row = row.copy()
            # The name in the list is the Partner's name
            ref_row["first_name"] = row["partnerfirst"]
            ref_row["last_name"] = row["partnerlast"]
            # Clear contact info for the reference row to avoid duplicates
            # Note: We use the user_email column for the Hebrew pointer
            ref_row["user_email"] = f" ראה: {row['last_name']}"
            ref_row["cellphone1"] = ""
            ref_row["partnerfirst"] = ""
            ref_row["partnerlast"] = ""
            ref_row["partneremail"] = ""
            ref_row["partnerphone"] = ""
            # Set the "See" message in the address column
            ref_row["home_address"] = "skip"
            new_rows.append(ref_row)

# Add the new reference rows to the main dataframe
if new_rows:
    df = pd.concat([df, pd.DataFrame(new_rows)], ignore_index=True)

# 4. Sort by last_name (Now includes the new reference rows)
df = df.sort_values(by=["last_name", "first_name"], ascending=True).reset_index(drop=True)

# 5. Add "order" column (Hebrew letters)
order_col = []
previous_letter = None

for _, row in df.iterrows():
    last = row["last_name"]
    current_letter = last[0] if last else ""
    if current_letter != previous_letter:
        order_col.append(current_letter)
        previous_letter = current_letter
    else:
        order_col.append("")

df["order"] = order_col

# Save output
df.to_csv("pre-processing output.csv", index=False, encoding="utf-8-sig")

print(f"Success: Processed {len(df)} entries. Emails are now lowercase.")