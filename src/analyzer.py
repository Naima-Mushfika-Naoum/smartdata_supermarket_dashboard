
import pandas as pd


def load_data(file_path):
    """Read and validate the transaction CSV used by the dashboard."""
    try:
        df = pd.read_csv(file_path, dtype={"Invoice ID": "string"})
    except pd.errors.EmptyDataError as exc:
        raise ValueError("The transaction CSV is empty.") from exc

    text_columns = ("Invoice ID", "Branch", "Product line")
    numeric_columns = ("Sales", "Quantity", "Rating")
    required_columns = (*text_columns, "Date", *numeric_columns)

    missing = [column for column in required_columns if column not in df]
    if missing:
        raise ValueError("Missing required columns: " + ", ".join(missing))
    if df.empty:
        raise ValueError("The transaction CSV contains no rows.")

    def reject_rows(mask, message):
        if mask.any():
            rows = ", ".join(str(index + 1) for index in df.index[mask][:5])
            raise ValueError(f"{message} Data row(s): {rows}.")

    for column in text_columns:
        values = df[column].astype("string").str.strip()
        reject_rows(values.isna() | values.eq(""), f"{column} cannot be blank.")
        if column == "Invoice ID":
            reject_rows(values.duplicated(keep=False), "Duplicate invoice ID.")

    dates = pd.to_datetime(df["Date"], format="%m/%d/%Y", errors="coerce")
    reject_rows(dates.isna(), "Date must be a valid purchase date in MM/DD/YYYY format.")
    df["Date"] = dates

    for column in numeric_columns:
        values = pd.to_numeric(df[column], errors="coerce")
        invalid = values.isna() | values.isin([float("inf"), float("-inf")])
        reject_rows(invalid, f"{column} must contain a valid number.")
        df[column] = values

    return df


def calculate_metrics(df):
    """Calculate dashboard metrics for the supplied transactions."""
    return {
        "Total sales (including tax)": df["Sales"].sum(),
        "Transactions": len(df),
        "Units sold": df["Quantity"].sum(),
        "Average transaction value": df["Sales"].mean(),
        "Average rating": df["Rating"].mean()
    }

