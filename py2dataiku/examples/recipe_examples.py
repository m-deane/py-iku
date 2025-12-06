"""
Comprehensive examples for every Dataiku DSS recipe type.

This module provides Python code examples that map to each Dataiku recipe type,
demonstrating how py2dataiku detects and converts various pandas operations
into their corresponding Dataiku DSS recipe configurations.
"""

from typing import Dict, Any

# =============================================================================
# VISUAL RECIPES
# =============================================================================

# -----------------------------------------------------------------------------
# PREPARE Recipe - Data transformation with processors
# -----------------------------------------------------------------------------
PREPARE_EXAMPLE = """
import pandas as pd
import numpy as np

# Load input data
df = pd.read_csv('raw_data.csv')

# String transformations
df['name'] = df['name'].str.strip().str.title()
df['email'] = df['email'].str.lower()

# Type conversions
df['age'] = df['age'].astype(int)
df['created_date'] = pd.to_datetime(df['created_date'])

# Fill missing values
df['category'] = df['category'].fillna('Unknown')
df['score'] = df['score'].fillna(df['score'].mean())

# Numeric transformations
df['score_normalized'] = (df['score'] - df['score'].min()) / (df['score'].max() - df['score'].min())
df['amount_rounded'] = df['amount'].round(2)

# Filter bad data
df = df[df['age'] > 0]
df = df.dropna(subset=['customer_id'])

# Save output
df.to_csv('cleaned_data.csv', index=False)
"""

# -----------------------------------------------------------------------------
# SYNC Recipe - Copy data between datasets
# -----------------------------------------------------------------------------
SYNC_EXAMPLE = """
import pandas as pd

# Load source data
source_df = pd.read_csv('source_data.csv')

# Simple copy/sync operation
target_df = source_df.copy()

# Save to target
target_df.to_csv('target_data.csv', index=False)
"""

# -----------------------------------------------------------------------------
# GROUPING Recipe - Aggregate data by groups
# -----------------------------------------------------------------------------
GROUPING_EXAMPLE = """
import pandas as pd

# Load data
df = pd.read_csv('transactions.csv')

# Group by single column
category_summary = df.groupby('category').agg({
    'amount': 'sum',
    'quantity': 'mean',
    'transaction_id': 'count'
}).reset_index()
category_summary.columns = ['category', 'total_amount', 'avg_quantity', 'transaction_count']

# Save output
category_summary.to_csv('category_summary.csv', index=False)
"""

GROUPING_MULTI_COLUMN_EXAMPLE = """
import pandas as pd

# Load data
df = pd.read_csv('sales.csv')

# Group by multiple columns with multiple aggregations
regional_product_summary = df.groupby(['region', 'product_category']).agg({
    'revenue': ['sum', 'mean', 'max', 'min'],
    'units_sold': 'sum',
    'customer_id': 'nunique',
    'discount': 'std'
}).reset_index()

# Flatten column names
regional_product_summary.columns = [
    'region', 'product_category',
    'total_revenue', 'avg_revenue', 'max_revenue', 'min_revenue',
    'total_units', 'unique_customers', 'discount_std'
]

# Save output
regional_product_summary.to_csv('regional_product_summary.csv', index=False)
"""

# -----------------------------------------------------------------------------
# WINDOW Recipe - Window/analytic functions
# -----------------------------------------------------------------------------
WINDOW_EXAMPLE = """
import pandas as pd

# Load time series data
df = pd.read_csv('daily_metrics.csv')
df['date'] = pd.to_datetime(df['date'])
df = df.sort_values('date')

# Rolling window calculations
df['rolling_7d_avg'] = df['value'].rolling(window=7).mean()
df['rolling_30d_sum'] = df['value'].rolling(window=30).sum()
df['rolling_7d_std'] = df['value'].rolling(window=7).std()

# Cumulative calculations
df['cumulative_sum'] = df['value'].cumsum()
df['cumulative_max'] = df['value'].cummax()
df['cumulative_min'] = df['value'].cummin()

# Save output
df.to_csv('metrics_with_windows.csv', index=False)
"""

WINDOW_GROUPED_EXAMPLE = """
import pandas as pd

# Load data
df = pd.read_csv('user_activity.csv')
df['date'] = pd.to_datetime(df['date'])
df = df.sort_values(['user_id', 'date'])

# Window functions per group
df['user_running_total'] = df.groupby('user_id')['activity_count'].cumsum()
df['user_7d_avg'] = df.groupby('user_id')['activity_count'].transform(
    lambda x: x.rolling(window=7, min_periods=1).mean()
)

# Expanding window
df['user_expanding_avg'] = df.groupby('user_id')['activity_count'].transform(
    lambda x: x.expanding().mean()
)

# Lag and lead
df['prev_activity'] = df.groupby('user_id')['activity_count'].shift(1)
df['next_activity'] = df.groupby('user_id')['activity_count'].shift(-1)

# Save output
df.to_csv('user_activity_windowed.csv', index=False)
"""

# -----------------------------------------------------------------------------
# JOIN Recipe - Combine datasets
# -----------------------------------------------------------------------------
JOIN_INNER_EXAMPLE = """
import pandas as pd

# Load datasets
customers = pd.read_csv('customers.csv')
orders = pd.read_csv('orders.csv')

# Inner join
customer_orders = pd.merge(
    customers,
    orders,
    on='customer_id',
    how='inner'
)

# Save output
customer_orders.to_csv('customer_orders.csv', index=False)
"""

JOIN_LEFT_EXAMPLE = """
import pandas as pd

# Load datasets
customers = pd.read_csv('customers.csv')
orders = pd.read_csv('orders.csv')

# Left join - keep all customers
customer_orders = pd.merge(
    customers,
    orders,
    on='customer_id',
    how='left'
)

# Save output
customer_orders.to_csv('customer_orders_left.csv', index=False)
"""

JOIN_RIGHT_EXAMPLE = """
import pandas as pd

# Load datasets
customers = pd.read_csv('customers.csv')
orders = pd.read_csv('orders.csv')

# Right join - keep all orders
customer_orders = pd.merge(
    customers,
    orders,
    on='customer_id',
    how='right'
)

# Save output
customer_orders.to_csv('customer_orders_right.csv', index=False)
"""

JOIN_OUTER_EXAMPLE = """
import pandas as pd

# Load datasets
customers = pd.read_csv('customers.csv')
orders = pd.read_csv('orders.csv')

# Outer join - keep all records
customer_orders = pd.merge(
    customers,
    orders,
    on='customer_id',
    how='outer'
)

# Save output
customer_orders.to_csv('customer_orders_outer.csv', index=False)
"""

JOIN_CROSS_EXAMPLE = """
import pandas as pd

# Load datasets
products = pd.read_csv('products.csv')
regions = pd.read_csv('regions.csv')

# Cross join - all combinations
product_regions = pd.merge(
    products,
    regions,
    how='cross'
)

# Save output
product_regions.to_csv('product_regions_cross.csv', index=False)
"""

JOIN_MULTI_KEY_EXAMPLE = """
import pandas as pd

# Load datasets
sales = pd.read_csv('sales.csv')
targets = pd.read_csv('targets.csv')

# Join on multiple keys
sales_vs_targets = pd.merge(
    sales,
    targets,
    left_on=['region', 'product_id', 'quarter'],
    right_on=['region_code', 'sku', 'fiscal_quarter'],
    how='left'
)

# Save output
sales_vs_targets.to_csv('sales_vs_targets.csv', index=False)
"""

# -----------------------------------------------------------------------------
# FUZZY_JOIN Recipe - Approximate matching joins
# -----------------------------------------------------------------------------
FUZZY_JOIN_EXAMPLE = """
import pandas as pd
from fuzzywuzzy import fuzz

# Load datasets
internal_companies = pd.read_csv('internal_companies.csv')
external_companies = pd.read_csv('external_companies.csv')

# Fuzzy matching function
def fuzzy_match(row, df_to_match, col_name, threshold=80):
    best_match = None
    best_score = 0
    for _, match_row in df_to_match.iterrows():
        score = fuzz.ratio(str(row[col_name]).lower(), str(match_row[col_name]).lower())
        if score > best_score and score >= threshold:
            best_score = score
            best_match = match_row
    return best_match

# Apply fuzzy matching
matches = []
for _, row in internal_companies.iterrows():
    match = fuzzy_match(row, external_companies, 'company_name')
    if match is not None:
        matches.append({
            'internal_id': row['id'],
            'internal_name': row['company_name'],
            'external_id': match['id'],
            'external_name': match['company_name']
        })

fuzzy_joined = pd.DataFrame(matches)
fuzzy_joined.to_csv('fuzzy_matched_companies.csv', index=False)
"""

# -----------------------------------------------------------------------------
# GEO_JOIN Recipe - Geographic spatial joins
# -----------------------------------------------------------------------------
GEO_JOIN_EXAMPLE = """
import pandas as pd
import numpy as np

# Load datasets
stores = pd.read_csv('stores.csv')  # Has latitude, longitude
regions = pd.read_csv('regions.csv')  # Has polygon boundaries

# Calculate distance between points (Haversine formula)
def haversine_distance(lat1, lon1, lat2, lon2):
    R = 6371  # Earth's radius in kilometers
    lat1, lon1, lat2, lon2 = map(np.radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = np.sin(dlat/2)**2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon/2)**2
    c = 2 * np.arcsin(np.sqrt(a))
    return R * c

# Join stores to nearest city center
cities = pd.read_csv('city_centers.csv')
stores_with_city = stores.copy()
stores_with_city['nearest_city'] = stores.apply(
    lambda row: cities.loc[
        cities.apply(
            lambda city: haversine_distance(
                row['latitude'], row['longitude'],
                city['lat'], city['lon']
            ), axis=1
        ).idxmin()
    ]['city_name'], axis=1
)

stores_with_city.to_csv('stores_with_city.csv', index=False)
"""

# -----------------------------------------------------------------------------
# STACK Recipe - Vertically combine datasets
# -----------------------------------------------------------------------------
STACK_EXAMPLE = """
import pandas as pd

# Load multiple datasets
q1_sales = pd.read_csv('sales_q1.csv')
q2_sales = pd.read_csv('sales_q2.csv')
q3_sales = pd.read_csv('sales_q3.csv')
q4_sales = pd.read_csv('sales_q4.csv')

# Add quarter identifier
q1_sales['quarter'] = 'Q1'
q2_sales['quarter'] = 'Q2'
q3_sales['quarter'] = 'Q3'
q4_sales['quarter'] = 'Q4'

# Stack all quarters
all_sales = pd.concat([q1_sales, q2_sales, q3_sales, q4_sales], ignore_index=True)

# Save output
all_sales.to_csv('all_sales.csv', index=False)
"""

STACK_MULTIPLE_SOURCES_EXAMPLE = """
import pandas as pd

# Load data from multiple sources
web_orders = pd.read_csv('web_orders.csv')
mobile_orders = pd.read_csv('mobile_orders.csv')
store_orders = pd.read_csv('store_orders.csv')

# Add source identifier
web_orders['source'] = 'web'
mobile_orders['source'] = 'mobile'
store_orders['source'] = 'store'

# Stack with different column alignment
all_orders = pd.concat(
    [web_orders, mobile_orders, store_orders],
    ignore_index=True,
    sort=False
)

# Save output
all_orders.to_csv('all_orders.csv', index=False)
"""

# -----------------------------------------------------------------------------
# SPLIT Recipe - Filter/partition data
# -----------------------------------------------------------------------------
SPLIT_EXAMPLE = """
import pandas as pd

# Load data
df = pd.read_csv('all_data.csv')

# Split by condition - filter
active_customers = df[df['status'] == 'active']
inactive_customers = df[df['status'] == 'inactive']

# Save outputs
active_customers.to_csv('active_customers.csv', index=False)
inactive_customers.to_csv('inactive_customers.csv', index=False)
"""

SPLIT_MULTIPLE_CONDITIONS_EXAMPLE = """
import pandas as pd

# Load data
df = pd.read_csv('transactions.csv')

# Split into multiple groups
high_value = df[df['amount'] >= 1000]
medium_value = df[(df['amount'] >= 100) & (df['amount'] < 1000)]
low_value = df[df['amount'] < 100]

# Save outputs
high_value.to_csv('high_value_transactions.csv', index=False)
medium_value.to_csv('medium_value_transactions.csv', index=False)
low_value.to_csv('low_value_transactions.csv', index=False)
"""

# -----------------------------------------------------------------------------
# SORT Recipe - Order rows
# -----------------------------------------------------------------------------
SORT_EXAMPLE = """
import pandas as pd

# Load data
df = pd.read_csv('products.csv')

# Sort by single column
sorted_by_price = df.sort_values('price', ascending=True)

# Save output
sorted_by_price.to_csv('products_sorted.csv', index=False)
"""

SORT_MULTI_COLUMN_EXAMPLE = """
import pandas as pd

# Load data
df = pd.read_csv('employees.csv')

# Sort by multiple columns
sorted_employees = df.sort_values(
    by=['department', 'salary', 'hire_date'],
    ascending=[True, False, True]
)

# Save output
sorted_employees.to_csv('employees_sorted.csv', index=False)
"""

# -----------------------------------------------------------------------------
# DISTINCT Recipe - Remove duplicates
# -----------------------------------------------------------------------------
DISTINCT_EXAMPLE = """
import pandas as pd

# Load data
df = pd.read_csv('raw_data.csv')

# Remove complete duplicates
unique_df = df.drop_duplicates()

# Save output
unique_df.to_csv('unique_data.csv', index=False)
"""

DISTINCT_SUBSET_EXAMPLE = """
import pandas as pd

# Load data
df = pd.read_csv('customer_interactions.csv')

# Remove duplicates based on specific columns (keep first)
unique_customers = df.drop_duplicates(subset=['customer_id', 'email'], keep='first')

# Remove duplicates keeping last
latest_interactions = df.drop_duplicates(subset=['customer_id'], keep='last')

# Save outputs
unique_customers.to_csv('unique_customers.csv', index=False)
latest_interactions.to_csv('latest_interactions.csv', index=False)
"""

# -----------------------------------------------------------------------------
# TOP_N Recipe - Select top/bottom N rows
# -----------------------------------------------------------------------------
TOP_N_EXAMPLE = """
import pandas as pd

# Load data
df = pd.read_csv('sales.csv')

# Get top 10 by sales amount
top_10_sales = df.nlargest(10, 'sales_amount')

# Save output
top_10_sales.to_csv('top_10_sales.csv', index=False)
"""

TOP_N_GROUPED_EXAMPLE = """
import pandas as pd

# Load data
df = pd.read_csv('products.csv')

# Top N per group
top_3_per_category = df.groupby('category').apply(
    lambda x: x.nlargest(3, 'revenue')
).reset_index(drop=True)

# Bottom N per group
bottom_5_per_region = df.groupby('region').apply(
    lambda x: x.nsmallest(5, 'price')
).reset_index(drop=True)

# Simple head/tail
first_100 = df.head(100)
last_50 = df.tail(50)

# Save outputs
top_3_per_category.to_csv('top_3_per_category.csv', index=False)
bottom_5_per_region.to_csv('bottom_5_per_region.csv', index=False)
"""

# -----------------------------------------------------------------------------
# PIVOT Recipe - Reshape data
# -----------------------------------------------------------------------------
PIVOT_EXAMPLE = """
import pandas as pd

# Load data
df = pd.read_csv('sales.csv')

# Pivot table
pivot_table = df.pivot_table(
    values='amount',
    index='product_category',
    columns='month',
    aggfunc='sum',
    fill_value=0
)

# Reset index for export
pivot_table = pivot_table.reset_index()

# Save output
pivot_table.to_csv('sales_pivot.csv', index=False)
"""

PIVOT_MELT_EXAMPLE = """
import pandas as pd

# Load wide data
wide_df = pd.read_csv('monthly_metrics.csv')

# Melt (unpivot) from wide to long format
long_df = pd.melt(
    wide_df,
    id_vars=['product_id', 'product_name'],
    value_vars=['jan', 'feb', 'mar', 'apr', 'may', 'jun'],
    var_name='month',
    value_name='sales'
)

# Save output
long_df.to_csv('monthly_metrics_long.csv', index=False)
"""

# -----------------------------------------------------------------------------
# SAMPLING Recipe - Random sampling
# -----------------------------------------------------------------------------
SAMPLING_EXAMPLE = """
import pandas as pd

# Load data
df = pd.read_csv('large_dataset.csv')

# Random sample - percentage
sample_10pct = df.sample(frac=0.1, random_state=42)

# Random sample - fixed size
sample_1000 = df.sample(n=1000, random_state=42)

# Save outputs
sample_10pct.to_csv('sample_10pct.csv', index=False)
sample_1000.to_csv('sample_1000.csv', index=False)
"""

SAMPLING_STRATIFIED_EXAMPLE = """
import pandas as pd
from sklearn.model_selection import train_test_split

# Load data
df = pd.read_csv('customers.csv')

# Stratified sampling
train, test = train_test_split(
    df,
    test_size=0.2,
    stratify=df['segment'],
    random_state=42
)

# Save outputs
train.to_csv('train_set.csv', index=False)
test.to_csv('test_set.csv', index=False)
"""

# -----------------------------------------------------------------------------
# DOWNLOAD Recipe - Download from external source
# -----------------------------------------------------------------------------
DOWNLOAD_EXAMPLE = """
import pandas as pd
import requests

# Download from URL
url = 'https://api.example.com/data.csv'
response = requests.get(url)

# Parse CSV from response
from io import StringIO
df = pd.read_csv(StringIO(response.text))

# Save locally
df.to_csv('downloaded_data.csv', index=False)
"""

# =============================================================================
# CODE RECIPES
# =============================================================================

# -----------------------------------------------------------------------------
# PYTHON Recipe - Custom Python code
# -----------------------------------------------------------------------------
PYTHON_RECIPE_EXAMPLE = """
import pandas as pd
import numpy as np

# Load input data
df = pd.read_csv('input_data.csv')

# Complex custom transformation that can't be done with visual recipes
def custom_scoring_algorithm(row):
    base_score = row['revenue'] * 0.4
    engagement_bonus = np.log1p(row['interactions']) * 10
    recency_factor = 1 / (1 + row['days_since_last_purchase'] / 30)

    score = base_score * engagement_bonus * recency_factor
    return round(score, 2)

df['customer_score'] = df.apply(custom_scoring_algorithm, axis=1)

# Custom aggregation logic
df['segment'] = pd.cut(
    df['customer_score'],
    bins=[-np.inf, 50, 150, 300, np.inf],
    labels=['Bronze', 'Silver', 'Gold', 'Platinum']
)

# Save output
df.to_csv('scored_customers.csv', index=False)
"""

# -----------------------------------------------------------------------------
# SQL Recipe - SQL queries
# -----------------------------------------------------------------------------
SQL_RECIPE_EXAMPLE = """
import pandas as pd
import sqlite3

# Create in-memory database
conn = sqlite3.connect(':memory:')

# Load data into database
customers = pd.read_csv('customers.csv')
orders = pd.read_csv('orders.csv')

customers.to_sql('customers', conn, index=False)
orders.to_sql('orders', conn, index=False)

# Execute SQL query
query = '''
SELECT
    c.customer_id,
    c.name,
    COUNT(o.order_id) as order_count,
    SUM(o.amount) as total_spend,
    AVG(o.amount) as avg_order_value
FROM customers c
LEFT JOIN orders o ON c.customer_id = o.customer_id
GROUP BY c.customer_id, c.name
HAVING COUNT(o.order_id) > 0
ORDER BY total_spend DESC
'''

result = pd.read_sql(query, conn)
conn.close()

# Save output
result.to_csv('customer_order_summary.csv', index=False)
"""

# -----------------------------------------------------------------------------
# R Recipe - R code (represented as Python equivalent)
# -----------------------------------------------------------------------------
R_RECIPE_EXAMPLE = """
import pandas as pd
import numpy as np
from scipy import stats

# Load data (equivalent to R's read.csv)
df = pd.read_csv('data.csv')

# Statistical analysis (R-style)
# Linear regression
slope, intercept, r_value, p_value, std_err = stats.linregress(df['x'], df['y'])

# Add regression results
df['predicted'] = intercept + slope * df['x']
df['residual'] = df['y'] - df['predicted']

# Save output
df.to_csv('regression_results.csv', index=False)
"""

# =============================================================================
# ML RECIPES
# =============================================================================

# -----------------------------------------------------------------------------
# PREDICTION_SCORING Recipe - Apply trained model
# -----------------------------------------------------------------------------
PREDICTION_SCORING_EXAMPLE = """
import pandas as pd
import pickle

# Load test data
test_data = pd.read_csv('test_data.csv')

# Load trained model
with open('trained_model.pkl', 'rb') as f:
    model = pickle.load(f)

# Prepare features
features = test_data[['feature1', 'feature2', 'feature3', 'feature4']]

# Make predictions
test_data['prediction'] = model.predict(features)
test_data['probability'] = model.predict_proba(features)[:, 1]

# Save output
test_data.to_csv('predictions.csv', index=False)
"""

# -----------------------------------------------------------------------------
# CLUSTERING_SCORING Recipe - Apply clustering model
# -----------------------------------------------------------------------------
CLUSTERING_SCORING_EXAMPLE = """
import pandas as pd
import pickle

# Load data
df = pd.read_csv('customer_data.csv')

# Load trained clustering model
with open('kmeans_model.pkl', 'rb') as f:
    kmeans = pickle.load(f)

# Prepare features
features = df[['recency', 'frequency', 'monetary']]

# Assign cluster labels
df['cluster'] = kmeans.predict(features)

# Calculate distance to cluster centers
df['distance_to_center'] = kmeans.transform(features).min(axis=1)

# Save output
df.to_csv('clustered_customers.csv', index=False)
"""

# -----------------------------------------------------------------------------
# EVALUATION Recipe - Model evaluation
# -----------------------------------------------------------------------------
EVALUATION_EXAMPLE = """
import pandas as pd
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
from sklearn.metrics import classification_report, confusion_matrix

# Load predictions and actuals
df = pd.read_csv('predictions.csv')

# Extract predictions and actuals
y_true = df['actual']
y_pred = df['prediction']

# Calculate metrics
metrics = {
    'accuracy': accuracy_score(y_true, y_pred),
    'precision': precision_score(y_true, y_pred, average='weighted'),
    'recall': recall_score(y_true, y_pred, average='weighted'),
    'f1': f1_score(y_true, y_pred, average='weighted')
}

# Create evaluation report
eval_df = pd.DataFrame([metrics])
eval_df.to_csv('model_evaluation.csv', index=False)

# Confusion matrix
cm = confusion_matrix(y_true, y_pred)
cm_df = pd.DataFrame(cm)
cm_df.to_csv('confusion_matrix.csv', index=False)
"""

# =============================================================================
# ADDITIONAL RECIPES (DSS 14)
# =============================================================================

# -----------------------------------------------------------------------------
# UPSERT Recipe - Update or insert records
# -----------------------------------------------------------------------------
UPSERT_EXAMPLE = """
import pandas as pd

# Load existing and new data
existing = pd.read_csv('existing_records.csv')
updates = pd.read_csv('new_records.csv')

# Upsert logic: update existing records or insert new ones
key_column = 'record_id'

# Get records to update (exist in both)
to_update = updates[updates[key_column].isin(existing[key_column])]

# Get records to insert (only in updates)
to_insert = updates[~updates[key_column].isin(existing[key_column])]

# Get unchanged records
unchanged = existing[~existing[key_column].isin(updates[key_column])]

# Combine: unchanged + updated + new
result = pd.concat([unchanged, to_update, to_insert], ignore_index=True)

# Save output
result.to_csv('upserted_records.csv', index=False)
"""

# -----------------------------------------------------------------------------
# GENERATE_FEATURES Recipe - Automatic feature generation
# -----------------------------------------------------------------------------
GENERATE_FEATURES_EXAMPLE = """
import pandas as pd
import numpy as np

# Load data
df = pd.read_csv('raw_features.csv')

# Generate date features
df['date'] = pd.to_datetime(df['date'])
df['year'] = df['date'].dt.year
df['month'] = df['date'].dt.month
df['day'] = df['date'].dt.day
df['day_of_week'] = df['date'].dt.dayofweek
df['is_weekend'] = df['day_of_week'].isin([5, 6]).astype(int)
df['quarter'] = df['date'].dt.quarter

# Generate numeric features
df['amount_log'] = np.log1p(df['amount'])
df['amount_squared'] = df['amount'] ** 2
df['amount_sqrt'] = np.sqrt(df['amount'].clip(lower=0))

# Generate interaction features
df['amount_x_quantity'] = df['amount'] * df['quantity']
df['price_per_unit'] = df['amount'] / df['quantity'].replace(0, 1)

# Save output
df.to_csv('generated_features.csv', index=False)
"""

# -----------------------------------------------------------------------------
# PYSPARK Recipe - Spark processing
# -----------------------------------------------------------------------------
PYSPARK_EXAMPLE = """
import pandas as pd

# Note: In Dataiku, this would run as a PySpark recipe
# Here we show the pandas equivalent

# Load large dataset
df = pd.read_csv('large_data.csv')

# Transformations that would benefit from Spark
df['processed'] = df['text'].str.lower()
grouped = df.groupby(['category', 'region']).agg({
    'amount': 'sum',
    'count': 'sum'
}).reset_index()

# Save output
grouped.to_csv('spark_processed.csv', index=False)
"""

# -----------------------------------------------------------------------------
# HIVE/SQL Recipe - Hive SQL queries
# -----------------------------------------------------------------------------
HIVE_EXAMPLE = """
import pandas as pd

# Load data (simulating Hive table read)
fact_sales = pd.read_csv('fact_sales.csv')
dim_product = pd.read_csv('dim_product.csv')
dim_date = pd.read_csv('dim_date.csv')

# Join facts with dimensions (star schema query)
result = fact_sales.merge(
    dim_product, on='product_id'
).merge(
    dim_date, on='date_id'
)

# Aggregate
summary = result.groupby(['year', 'month', 'category']).agg({
    'amount': 'sum',
    'quantity': 'sum'
}).reset_index()

# Save output
summary.to_csv('hive_result.csv', index=False)
"""

# =============================================================================
# RECIPE EXAMPLES REGISTRY
# =============================================================================

RECIPE_EXAMPLES: Dict[str, str] = {
    # Visual Recipes
    "prepare": PREPARE_EXAMPLE,
    "sync": SYNC_EXAMPLE,
    "grouping": GROUPING_EXAMPLE,
    "grouping_multi": GROUPING_MULTI_COLUMN_EXAMPLE,
    "window": WINDOW_EXAMPLE,
    "window_grouped": WINDOW_GROUPED_EXAMPLE,
    "join_inner": JOIN_INNER_EXAMPLE,
    "join_left": JOIN_LEFT_EXAMPLE,
    "join_right": JOIN_RIGHT_EXAMPLE,
    "join_outer": JOIN_OUTER_EXAMPLE,
    "join_cross": JOIN_CROSS_EXAMPLE,
    "join_multi_key": JOIN_MULTI_KEY_EXAMPLE,
    "fuzzy_join": FUZZY_JOIN_EXAMPLE,
    "geo_join": GEO_JOIN_EXAMPLE,
    "stack": STACK_EXAMPLE,
    "stack_multi": STACK_MULTIPLE_SOURCES_EXAMPLE,
    "split": SPLIT_EXAMPLE,
    "split_multi": SPLIT_MULTIPLE_CONDITIONS_EXAMPLE,
    "sort": SORT_EXAMPLE,
    "sort_multi": SORT_MULTI_COLUMN_EXAMPLE,
    "distinct": DISTINCT_EXAMPLE,
    "distinct_subset": DISTINCT_SUBSET_EXAMPLE,
    "top_n": TOP_N_EXAMPLE,
    "top_n_grouped": TOP_N_GROUPED_EXAMPLE,
    "pivot": PIVOT_EXAMPLE,
    "pivot_melt": PIVOT_MELT_EXAMPLE,
    "sampling": SAMPLING_EXAMPLE,
    "sampling_stratified": SAMPLING_STRATIFIED_EXAMPLE,
    "download": DOWNLOAD_EXAMPLE,
    # Code Recipes
    "python": PYTHON_RECIPE_EXAMPLE,
    "sql": SQL_RECIPE_EXAMPLE,
    "r": R_RECIPE_EXAMPLE,
    # ML Recipes
    "prediction_scoring": PREDICTION_SCORING_EXAMPLE,
    "clustering_scoring": CLUSTERING_SCORING_EXAMPLE,
    "evaluation": EVALUATION_EXAMPLE,
    # Additional Recipes
    "upsert": UPSERT_EXAMPLE,
    "generate_features": GENERATE_FEATURES_EXAMPLE,
    "pyspark": PYSPARK_EXAMPLE,
    "hive": HIVE_EXAMPLE,
}

# Metadata for each example
RECIPE_METADATA: Dict[str, Dict[str, Any]] = {
    "prepare": {
        "name": "prepare",
        "description": "Data transformation with multiple processors",
        "recipe_type": "PREPARE",
        "pandas_operations": ["str.strip", "str.title", "astype", "to_datetime", "fillna", "round", "dropna"],
        "complexity": "intermediate",
        "use_case": "Data cleaning and normalization"
    },
    "sync": {
        "name": "sync",
        "description": "Copy data between datasets",
        "recipe_type": "SYNC",
        "pandas_operations": ["copy"],
        "complexity": "basic",
        "use_case": "Dataset replication"
    },
    "grouping": {
        "name": "grouping",
        "description": "Aggregate data by groups",
        "recipe_type": "GROUPING",
        "pandas_operations": ["groupby", "agg", "reset_index"],
        "complexity": "basic",
        "use_case": "Summary statistics by category"
    },
    "window": {
        "name": "window",
        "description": "Window and rolling calculations",
        "recipe_type": "WINDOW",
        "pandas_operations": ["rolling", "cumsum", "cummax", "cummin"],
        "complexity": "intermediate",
        "use_case": "Time series analysis"
    },
    "join_inner": {
        "name": "join_inner",
        "description": "Inner join two datasets",
        "recipe_type": "JOIN",
        "join_type": "INNER",
        "pandas_operations": ["merge"],
        "complexity": "basic",
        "use_case": "Combine related datasets"
    },
    "stack": {
        "name": "stack",
        "description": "Vertically combine multiple datasets",
        "recipe_type": "STACK",
        "pandas_operations": ["concat"],
        "complexity": "basic",
        "use_case": "Combine data from multiple periods"
    },
    "split": {
        "name": "split",
        "description": "Filter and partition data",
        "recipe_type": "SPLIT",
        "pandas_operations": ["boolean indexing"],
        "complexity": "basic",
        "use_case": "Segment data by conditions"
    },
    "sort": {
        "name": "sort",
        "description": "Order rows by columns",
        "recipe_type": "SORT",
        "pandas_operations": ["sort_values"],
        "complexity": "basic",
        "use_case": "Data ordering"
    },
    "distinct": {
        "name": "distinct",
        "description": "Remove duplicate rows",
        "recipe_type": "DISTINCT",
        "pandas_operations": ["drop_duplicates"],
        "complexity": "basic",
        "use_case": "Data deduplication"
    },
    "top_n": {
        "name": "top_n",
        "description": "Select top/bottom N rows",
        "recipe_type": "TOP_N",
        "pandas_operations": ["nlargest", "nsmallest", "head", "tail"],
        "complexity": "basic",
        "use_case": "Top performers analysis"
    },
    "pivot": {
        "name": "pivot",
        "description": "Reshape data with pivot tables",
        "recipe_type": "PIVOT",
        "pandas_operations": ["pivot_table", "melt"],
        "complexity": "intermediate",
        "use_case": "Data reshaping for reporting"
    },
    "sampling": {
        "name": "sampling",
        "description": "Random data sampling",
        "recipe_type": "SAMPLING",
        "pandas_operations": ["sample"],
        "complexity": "basic",
        "use_case": "Create representative samples"
    },
}


def get_recipe_example(name: str) -> str:
    """Get a recipe example by name."""
    return RECIPE_EXAMPLES.get(name, "")


def get_recipe_metadata(name: str) -> Dict[str, Any]:
    """Get metadata for a recipe example."""
    return RECIPE_METADATA.get(name, {})


def list_recipe_examples() -> list:
    """List all available recipe examples."""
    return list(RECIPE_EXAMPLES.keys())
