"""SpendSense — Synthetic Customer Enrichment Pipeline

Provides synthetic enrichment attributes to support the business analytics pillars:
1. Customer ID (for RFM segmentation)
2. Transaction Date (across 12-24 months for Cohort Analysis)
3. Merchant Category (Travel, Dining, Retail, Grocery, etc.)
4. Geographic location (City, State)

TRANSPARENCY NOTICE:
This module generates SYNTHETIC attributes required for customer segmentation,
cohort analysis, and merchant mix. The transaction PCA features and fraud labels
originate from the primary credit card dataset; customer demographics and merchant
categories are synthetically joined and explicitly flagged with `is_synthetic = True`.
"""

import logging
from datetime import datetime, timedelta
import numpy as np
import pandas as pd
from sqlalchemy import text

from src.config import Config
from src.database import get_engine, execute_sql

logger = logging.getLogger(__name__)

CITIES_STATES = [
    ("New York", "NY"), ("San Francisco", "CA"), ("Chicago", "IL"),
    ("Austin", "TX"), ("Seattle", "WA"), ("Atlanta", "GA"),
    ("Miami", "FL"), ("Boston", "MA"), ("Denver", "CO"), ("Los Angeles", "CA"),
    ("Dallas", "TX"), ("Phoenix", "AZ"), ("Philadelphia", "PA"),
]


def generate_customer_enrichment(
    n_transactions: int,
    n_customers: int = 5000,
    start_date: str = "2023-01-01",
    random_state: int = 42
) -> pd.DataFrame:
    """Generate synthetic customer profiles and assign transactions to them."""
    logger.info("Generating synthetic enrichment for %d transactions across %d customers...",
                n_transactions, n_customers)
    rng = np.random.default_rng(random_state)

    # Customer IDs: CUST-0001 to CUST-5000
    customer_ids = [f"CUST-{i:04d}" for i in range(1, n_customers + 1)]
    
    # Assign customers with Pareto distribution (some heavy spenders, many casual)
    alpha = 1.3
    weights = rng.pareto(alpha, n_customers)
    weights /= weights.sum()

    assigned_customers = rng.choice(customer_ids, size=n_transactions, p=weights)

    # Assign transaction dates spanning 18 months from start_date
    base_date = datetime.strptime(start_date, "%Y-%m-%d")
    max_days = 540  # ~18 months
    
    # Assign dates with growth trend over time
    day_offsets = (rng.beta(2, 2, size=n_transactions) * max_days).astype(int)
    assigned_dates = [(base_date + timedelta(days=int(d))).strftime("%Y-%m-%d") for d in day_offsets]

    # Assign merchant categories
    categories = Config.MERCHANT_CATEGORIES
    cat_weights = [0.18, 0.12, 0.20, 0.15, 0.08, 0.07, 0.06, 0.05, 0.05, 0.04]
    cat_weights = np.array(cat_weights) / sum(cat_weights)
    assigned_categories = rng.choice(categories, size=n_transactions, p=cat_weights)

    # Assign locations
    city_indices = rng.choice(len(CITIES_STATES), size=n_transactions)
    assigned_cities = [CITIES_STATES[i][0] for i in city_indices]
    assigned_states = [CITIES_STATES[i][1] for i in city_indices]

    df_enrichment = pd.DataFrame({
        "transaction_id": np.arange(1, n_transactions + 1),
        "customer_id": assigned_customers,
        "transaction_date": assigned_dates,
        "merchant_category": assigned_categories,
        "city": assigned_cities,
        "state": assigned_states,
        "is_synthetic": True,
    })

    return df_enrichment


def load_enrichment_to_db(df_enrichment: pd.DataFrame, batch_size: int = 10000) -> int:
    """Load synthetic enrichment records into PostgreSQL/SQLite."""
    engine = get_engine()
    logger.info("Loading %d enrichment records into customer_enrichment table...", len(df_enrichment))
    
    with engine.begin() as conn:
        conn.execute(text("DELETE FROM customer_enrichment"))

    df_enrichment.to_sql(
        "customer_enrichment",
        con=engine,
        if_exists="append",
        index=False,
        chunksize=batch_size
    )
    logger.info("Successfully loaded customer enrichment data.")
    return len(df_enrichment)
