from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Literal

import pandas as pd


@dataclass(frozen=True)
class SalesOrdersSummary:
    date_min: pd.Timestamp
    date_max: pd.Timestamp
    total_revenue_usd: float
    total_profit_usd: float
    top_category: str | None
    row_count: int


def _coerce_numeric(series: pd.Series) -> pd.Series:
    if pd.api.types.is_numeric_dtype(series.dtype):
        return series
    return pd.to_numeric(series, errors="coerce")


def load_sales_orders(path: str | Path, *, sheet_name: str = "Sales Orders") -> pd.DataFrame:
    """
    Load Sales Orders data from either:
    - Excel: `Global Bike Sales Data (1).xlsx` (sheet: "Sales Orders")
    - CSV export of that sheet
    """
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(str(p))

    if p.suffix.lower() in {".xlsx", ".xls"}:
        df = pd.read_excel(p, sheet_name=sheet_name)
    elif p.suffix.lower() == ".csv":
        df = pd.read_csv(p)
    else:
        raise ValueError(f"Unsupported file type: {p.suffix}")

    df.columns = [str(c).strip() for c in df.columns]
    return df


def clean_sales_orders(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()

    if "Date" in out.columns:
        out["Date"] = pd.to_datetime(out["Date"], errors="coerce")

    for col in ("Revenue USD", "Costs in USD"):
        if col in out.columns:
            out[col] = _coerce_numeric(out[col])

    if "Revenue USD" in out.columns and "Costs in USD" in out.columns:
        out["Profit"] = out["Revenue USD"] - out["Costs in USD"]
        revenue = out["Revenue USD"]
        out["Profit Margin"] = out["Profit"].where(revenue != 0) / revenue.where(revenue != 0)

    # Missing value handling (conservative):
    # - Drop rows missing key fields needed for KPIs
    must_have = [c for c in ["Date", "Revenue USD", "Costs in USD"] if c in out.columns]
    if must_have:
        out = out.dropna(subset=must_have)

    # - Fill non-critical text fields to avoid grouping issues
    for col in ("CatDescr", "ProdCat", "ProdDescr", "Country", "City", "Customer"):
        if col in out.columns:
            out[col] = out[col].astype("string").fillna("Unknown")

    return out


def summarize_sales_orders(
    df: pd.DataFrame,
    *,
    category_col_preference: tuple[str, ...] = ("CatDescr", "ProdCat"),
    top_by: Literal["revenue", "count"] = "revenue",
) -> SalesOrdersSummary:
    if df.empty:
        raise ValueError("No rows after cleaning.")

    date_min = pd.to_datetime(df["Date"]).min()
    date_max = pd.to_datetime(df["Date"]).max()

    total_revenue_usd = float(df["Revenue USD"].sum()) if "Revenue USD" in df.columns else float("nan")
    total_profit_usd = float(df["Profit"].sum()) if "Profit" in df.columns else float("nan")

    category_col = next((c for c in category_col_preference if c in df.columns), None)
    top_category: str | None = None
    if category_col is not None:
        if top_by == "revenue" and "Revenue USD" in df.columns:
            top_series = df.groupby(category_col, dropna=False)["Revenue USD"].sum()
        else:
            top_series = df[category_col].value_counts(dropna=False)

        if len(top_series) > 0:
            top_category = str(top_series.sort_values(ascending=False).index[0])

    return SalesOrdersSummary(
        date_min=date_min,
        date_max=date_max,
        total_revenue_usd=total_revenue_usd,
        total_profit_usd=total_profit_usd,
        top_category=top_category,
        row_count=int(len(df)),
    )

