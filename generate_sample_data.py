"""
generate_sample_data.py
────────────────────────
Generates four sample CSV datasets for testing the EDA benchmarking system.
Run this script once: python generate_sample_data.py
"""

import random
import string
import numpy as np
import pandas as pd
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent / "data"
DATA_DIR.mkdir(exist_ok=True)

RNG = np.random.default_rng(seed=42)


def titanic_style(n: int = 1000) -> pd.DataFrame:
    """Synthetic Titanic-like dataset — clean, balanced, mixed types."""
    ages = RNG.normal(35, 15, n).clip(1, 80)
    fares = RNG.exponential(scale=30, size=n).clip(5, 500)
    pclasses = RNG.choice([1, 2, 3], size=n, p=[0.25, 0.40, 0.35])
    sexes = RNG.choice(["male", "female"], size=n, p=[0.55, 0.45])
    siblings = RNG.choice([0, 1, 2, 3, 4], size=n, p=[0.60, 0.25, 0.10, 0.03, 0.02])
    parents = RNG.choice([0, 1, 2, 3], size=n, p=[0.68, 0.20, 0.09, 0.03])
    embark = RNG.choice(["S", "C", "Q"], size=n, p=[0.72, 0.19, 0.09])

    # Target: survival probability loosely based on features
    logit = (
        -0.02 * ages
        + 0.012 * fares
        - 0.5 * (pclasses == 3).astype(float)
        + 1.2 * (sexes == "female").astype(float)
    )
    prob = 1 / (1 + np.exp(-logit))
    survived = (RNG.random(n) < prob).astype(int)

    return pd.DataFrame({
        "PassengerId": range(1, n + 1),
        "Pclass": pclasses,
        "Sex": sexes,
        "Age": ages.round(1),
        "SibSp": siblings,
        "Parch": parents,
        "Fare": fares.round(2),
        "Embarked": embark,
        "Survived": survived,
    })


def add_noise(df: pd.DataFrame, std_multiplier: float = 0.5) -> pd.DataFrame:
    """Inject Gaussian noise into numeric columns + random missing values."""
    df = df.copy()
    for col in df.select_dtypes(include=[np.number]).columns:
        if col in ("PassengerId", "Survived"):
            continue
        std = df[col].std() or 1.0
        df[col] = df[col] + RNG.normal(0, std * std_multiplier, len(df))
    # 20% missing overall
    total = df.size
    n_miss = int(total * 0.20)
    flat = random.sample(range(total), n_miss)
    for idx in flat:
        r, c = divmod(idx, len(df.columns))
        df.iat[r, c] = np.nan
    return df


def make_imbalanced(df: pd.DataFrame) -> pd.DataFrame:
    """Create a 95/5 class imbalance in Survived column."""
    df = df.copy()
    minority = df[df["Survived"] == 1].sample(frac=0.10, random_state=42)
    majority = df[df["Survived"] == 0]
    return pd.concat([majority, minority]).sample(frac=1, random_state=42).reset_index(drop=True)


def add_high_cardinality(df: pd.DataFrame) -> pd.DataFrame:
    """Add a column with 500+ unique string values."""
    df = df.copy()
    df["UserToken"] = [
        "".join(random.choices(string.ascii_lowercase + string.digits, k=12))
        for _ in range(len(df))
    ]
    df["ProductCode"] = RNG.choice(
        [f"PROD-{i:04d}" for i in range(600)], size=len(df)
    )
    return df


if __name__ == "__main__":
    print("Generating sample datasets …")

    base = titanic_style(n=1000)
    base.to_csv(DATA_DIR / "sample_clean.csv", index=False)
    print(f"  ✓ sample_clean.csv       — {base.shape}")

    noisy = add_noise(base)
    noisy.to_csv(DATA_DIR / "sample_noisy.csv", index=False)
    print(f"  ✓ sample_noisy.csv       — {noisy.shape}")

    imbalanced = make_imbalanced(base)
    imbalanced.to_csv(DATA_DIR / "sample_imbalanced.csv", index=False)
    surv_dist = imbalanced["Survived"].value_counts().to_dict()
    print(f"  ✓ sample_imbalanced.csv  — {imbalanced.shape}  dist={surv_dist}")

    hc = add_high_cardinality(base)
    hc.to_csv(DATA_DIR / "sample_high_cardinality.csv", index=False)
    print(f"  ✓ sample_high_cardinality.csv — {hc.shape}")

    print("\nAll sample datasets saved to data/")
