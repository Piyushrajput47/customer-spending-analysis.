"""Core functions for the sales data analysis project.

Typical use (from the project root, e.g. inside the notebook):

    from src.analysis import load_data, clean_data, spend, summary

    df = clean_data(load_data())
    spend(df, "Gender")
    summary(df)

Run it as a script to print the summary table:

    python src/analysis.py
"""

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

# Default dataset location (works no matter where the code is run from)
DATA_PATH = Path(__file__).resolve().parent.parent / "data" / "sales_data.csv"

# Columns used to compare spending groups
SUMMARY_COLUMNS = [
    "Gender",
    "State",
    "Occupation",
    "Age Group",
    "Marital_Status",
    "Product_Category",
]

# Angle of the x-axis labels in the count plot
LABEL_ROTATION = 123


# --------------------------------------------------------------------------
# 1. Loading and cleaning
# --------------------------------------------------------------------------
def load_data(path=DATA_PATH):
    """Read the sales CSV (the file uses the cp1252 encoding)."""
    return pd.read_csv(path, encoding="cp1252")


def clean_data(df):
    """Return a cleaned copy of the raw sales data.

    Steps:
      1. remove duplicate rows
      2. drop the completely empty columns (Status, unnamed1)
      3. remove rows with missing values (only Amount has any)
      4. make Gender (F/M) and Marital_Status (0/1) readable
    """
    df = df.drop_duplicates()
    df = df.drop(columns=["Status", "unnamed1"], errors="ignore")
    df = df.dropna()
    df = df.reset_index(drop=True)

    df["Gender"] = df["Gender"].map({"F": "Female", "M": "Male"})
    df["Marital_Status"] = df["Marital_Status"].map({0: "Single", 1: "Married"})
    return df


# --------------------------------------------------------------------------
# 2. Grouping helpers
# --------------------------------------------------------------------------
def group_by(df, column):
    """Total Amount per group of `column`, highest first."""
    return (
        df.groupby(column)["Amount"]
        .sum()
        .sort_values(ascending=False)
        .reset_index()
    )


def _label_center(ax):
    """Put the value inside every bar of a plot."""
    for container in ax.containers:
        ax.bar_label(container, label_type="center")


def _label_edge(ax):
    """Put the rupee value at the end of every bar of a plot."""
    for container in ax.containers:
        ax.bar_label(container, label_type="edge", fmt="₹ %.0f")


# --------------------------------------------------------------------------
# 3. Visualization
# --------------------------------------------------------------------------
def spend(df, column, chart="auto", save_path=None):
    """Print and plot how much each group of `column` spends.

    Draws a 2x2 figure: order count, spend share (pie for 5 groups or fewer,
    bar otherwise), amount distribution (box plot) and highest vs lowest group.

    Parameters
    ----------
    df : DataFrame        cleaned data from `clean_data`
    column : str          column to group by, e.g. "Gender" or "State"
    chart : str           "auto" (default) or "piechart" to force a pie chart
    save_path : str/Path  optional file name to save the figure to
    """
    g = group_by(df, column)
    total = g["Amount"].sum()
    top_row = g.iloc[0]
    low_row = g.iloc[-1]

    print(
        f"Top {column} by spend: {top_row[column]}  "
        f"(₹ {top_row['Amount']:,.0f}, {top_row['Amount'] / total * 100:.1f}% of total)"
    )
    print(
        f"Lowest {column} by spend: {low_row[column]}  "
        f"(₹ {low_row['Amount']:,.0f}, {low_row['Amount'] / total * 100:.1f}% of total)"
    )

    fig, axes = plt.subplots(nrows=2, ncols=2, figsize=(20, 16))

    # Order count
    count_ax = sns.countplot(
        x=column, data=df, hue=column, palette="pastel", legend=False, ax=axes[0, 0]
    )
    _label_center(count_ax)
    axes[0, 0].tick_params(axis="x", labelrotation=LABEL_ROTATION)
    axes[0, 0].set_title(f"Order count by {column}")

    # Spend share: pie for few groups, sorted bar for many
    use_pie = (chart == "piechart") or (chart == "auto" and g[column].nunique() <= 5)
    if use_pie:
        axes[0, 1].pie(g["Amount"], labels=g[column], autopct="%0.1f%%", shadow=True)
        axes[0, 1].set_title(f"Spend share by {column}")
    else:
        bar_ax = sns.barplot(
            x="Amount", y=column, data=g, hue=column, palette="viridis", ax=axes[0, 1]
        )
        axes[0, 1].set_title(f"Total spend by {column} (sorted, highest first)")
        axes[0, 1].set_xlabel("Total Amount")
        _label_edge(bar_ax)

    # Distribution of order amounts
    sns.boxplot(
        x="Amount", y=column, data=df, hue=column, showmeans=True,
        palette="magma", legend=False, ax=axes[1, 0],
    )
    axes[1, 0].set_title(f"Distribution of order Amount by {column}")

    # Highest vs lowest group
    bars = axes[1, 1].bar(
        [str(top_row[column]), str(low_row[column])],
        [top_row["Amount"], low_row["Amount"]],
        color=["#2ca02c", "#d62728"],
    )
    axes[1, 1].bar_label(bars, fmt="₹ %.0f")
    axes[1, 1].set_title(f"Highest vs lowest spending {column}")
    axes[1, 1].set_ylabel("Total Amount")

    plt.tight_layout()
    if save_path is not None:
        fig.savefig(save_path, bbox_inches="tight")
    plt.show()


# --------------------------------------------------------------------------
# 4. Summary table
# --------------------------------------------------------------------------
def summary(df, columns=SUMMARY_COLUMNS):
    """Highest and lowest spending group for every column in `columns`."""
    rows = []
    for column in columns:
        g = group_by(df, column)
        top_row = g.iloc[0]
        low_row = g.iloc[-1]
        rows.append(
            [
                column,
                top_row[column],
                f"₹ {top_row['Amount']:,.0f}",
                low_row[column],
                f"₹ {low_row['Amount']:,.0f}",
            ]
        )
    return pd.DataFrame(
        rows,
        columns=[
            "Category",
            "max spend category",
            "max spend amount",
            "min spend category",
            "min spend amount",
        ],
    )


if __name__ == "__main__":
    data = clean_data(load_data())
    print(f"Clean data: {data.shape[0]} rows x {data.shape[1]} columns\n")
    print(summary(data).to_string())
