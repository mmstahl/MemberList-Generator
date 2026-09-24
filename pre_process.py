import pandas as pd
import numpy as np


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
        user_cols    = ["user_email", "first_name", "last_name", "cellphone1"]
        partner_cols = ["partneremail", "partnerfirst", "partnerlast", "partnerphone"]
        user_values    = row[user_cols].copy()
        partner_values = row[partner_cols].copy()
        row[user_cols]    = partner_values.values
        row[partner_cols] = user_values.values
        row["yourgender"], row["partnergender"] = p_gen, u_gen
    return row


def pre_process(input_path, output_path, exclude_unapproved=False):
    """Clean, transform, and sort raw member CSV. Returns output row count.

    exclude_unapproved: keep only users whose New User Approve status
    (user_status column) is 'approved' \u2014 drops denied and pending users.
    """
    df = pd.read_csv(input_path, encoding='utf-8-sig')

    # --- HEADER CLEANING ---
    df.columns = df.columns.str.strip().str.replace('\ufeff', '')

    # --- APPROVAL FILTER ---
    if exclude_unapproved:
        status = (df["user_status"].fillna("").astype(str).str.strip()
                  if "user_status" in df.columns else pd.Series(dtype=str))
        # Column missing or empty for everyone = site plugin is out of date
        if len(df) and (status == "").all():
            raise ValueError(
                "The member data has no approval status. Upload the latest "
                "Yedidya Admin Portal plugin to the website and run again."
            )
        df = df[status == "approved"]

    # --- PRIVACY FILTER ---
    df = df.query("contact_list_privacy_setting == 'Yes' and privacy_approval == 'approve'").copy()

    # 1. Global Cleanup
    df = df.replace({np.nan: ""})
    for col in df.columns:
        df[col] = df[col].astype(str).str.strip()
        df.loc[df[col] == "0", col] = ""

    # --- PARTNER FIELDS CLEANUP ---
    partner_fields = ["partnerfirst", "partnerlast", "partneremail", "partnerphone", "partnergender"]
    no_partner_mask = df["havepartner"].str.upper() == "NO"
    df.loc[no_partner_mask, partner_fields] = ""

    # --- Lowercase Email Addresses ---
    df["user_email"]   = df["user_email"].str.lower()
    df["partneremail"] = df["partneremail"].str.lower()

    # 2. Apply gender-based swap logic
    df = df.apply(maybe_swap, axis=1)

    # --- 3. CROSS-REFERENCE LOGIC ---
    new_rows = []
    for _, row in df.iterrows():
        if has_partner_data(row):
            if row["last_name"].lower() != row["partnerlast"].lower() and row["partnerlast"] != "":
                ref_row = row.copy()
                ref_row["first_name"]   = row["partnerfirst"]
                ref_row["last_name"]    = row["partnerlast"]
                ref_row["user_email"]   = f" ראה: {row['last_name']}"
                ref_row["cellphone1"]   = ""
                ref_row["partnerfirst"] = ""
                ref_row["partnerlast"]  = ""
                ref_row["partneremail"] = ""
                ref_row["partnerphone"] = ""
                ref_row["home_address"] = "skip"
                new_rows.append(ref_row)

    if new_rows:
        df = pd.concat([df, pd.DataFrame(new_rows)], ignore_index=True)

    # 4. Sort
    df = df.sort_values(by=["last_name", "first_name"], ascending=True).reset_index(drop=True)

    # 5. Add "order" column
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

    df.to_csv(output_path, index=False, encoding="utf-8-sig")
    return len(df)


if __name__ == "__main__":
    import defaults_manager as dm

    input_path  = dm.get('members_list', 'raw_csv_path')
    output_path = dm.get('members_list', 'processed_csv_path')
    count = pre_process(input_path, output_path)
    print(f"Success: Processed {count} entries. Emails are now lowercase.")
