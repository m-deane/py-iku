"""
Comprehensive combination examples for Dataiku DSS recipes and processors.

This module provides Python code examples that combine multiple recipes
and processors in realistic data processing pipelines, demonstrating
how py2dataiku handles complex multi-step transformations.
"""

from typing import Dict, Any

# =============================================================================
# RECIPE COMBINATIONS (20 combinations)
# =============================================================================

# 1. PREPARE -> GROUPING -> PREPARE (clean -> aggregate -> format)
PREPARE_GROUPING_PREPARE_EXAMPLE = """
import pandas as pd

# Load data
df = pd.read_csv('raw_transactions.csv')

# PREPARE: Clean data
df['customer_name'] = df['customer_name'].str.strip().str.title()
df['transaction_date'] = pd.to_datetime(df['transaction_date'])
df['amount'] = df['amount'].fillna(0)
df = df[df['amount'] > 0]

# GROUPING: Aggregate by customer
customer_summary = df.groupby('customer_id').agg({
    'amount': ['sum', 'mean', 'count'],
    'customer_name': 'first',
    'transaction_date': 'max'
}).reset_index()
customer_summary.columns = ['customer_id', 'total_amount', 'avg_amount',
                            'transaction_count', 'customer_name', 'last_transaction']

# PREPARE: Format output
customer_summary['total_amount'] = customer_summary['total_amount'].round(2)
customer_summary['avg_amount'] = customer_summary['avg_amount'].round(2)
customer_summary['customer_tier'] = pd.cut(
    customer_summary['total_amount'],
    bins=[0, 100, 500, 1000, float('inf')],
    labels=['Bronze', 'Silver', 'Gold', 'Platinum']
)

customer_summary.to_csv('customer_summary.csv', index=False)
"""

# 2. JOIN -> WINDOW -> SPLIT (combine -> calculate -> partition)
JOIN_WINDOW_SPLIT_EXAMPLE = """
import pandas as pd

# Load data
orders = pd.read_csv('orders.csv')
products = pd.read_csv('products.csv')

# JOIN: Combine orders with products
orders_enriched = pd.merge(orders, products, on='product_id', how='left')

# WINDOW: Calculate running totals and rankings
orders_enriched = orders_enriched.sort_values(['customer_id', 'order_date'])
orders_enriched['customer_running_total'] = orders_enriched.groupby('customer_id')['amount'].cumsum()
orders_enriched['customer_order_rank'] = orders_enriched.groupby('customer_id').cumcount() + 1

# SPLIT: Partition into first-time and repeat customers
first_time = orders_enriched[orders_enriched['customer_order_rank'] == 1]
repeat = orders_enriched[orders_enriched['customer_order_rank'] > 1]

first_time.to_csv('first_time_orders.csv', index=False)
repeat.to_csv('repeat_orders.csv', index=False)
"""

# 3. STACK -> DISTINCT -> SORT (combine -> dedupe -> order)
STACK_DISTINCT_SORT_EXAMPLE = """
import pandas as pd

# Load multiple data sources
source1 = pd.read_csv('customers_crm.csv')
source2 = pd.read_csv('customers_web.csv')
source3 = pd.read_csv('customers_mobile.csv')

# STACK: Combine all sources
source1['source'] = 'crm'
source2['source'] = 'web'
source3['source'] = 'mobile'
all_customers = pd.concat([source1, source2, source3], ignore_index=True)

# DISTINCT: Remove duplicates (keep first by source priority)
all_customers['source_priority'] = all_customers['source'].map({'crm': 1, 'web': 2, 'mobile': 3})
all_customers = all_customers.sort_values('source_priority')
unique_customers = all_customers.drop_duplicates(subset=['email'], keep='first')

# SORT: Order by registration date
unique_customers = unique_customers.sort_values('registration_date', ascending=False)

unique_customers.to_csv('unified_customers.csv', index=False)
"""

# 4. GROUPING -> PIVOT -> PREPARE (aggregate -> reshape -> clean)
GROUPING_PIVOT_PREPARE_EXAMPLE = """
import pandas as pd

# Load data
sales = pd.read_csv('sales_detail.csv')
sales['date'] = pd.to_datetime(sales['date'])
sales['month'] = sales['date'].dt.strftime('%Y-%m')

# GROUPING: Aggregate by product and month
monthly_sales = sales.groupby(['product_id', 'month']).agg({
    'amount': 'sum',
    'quantity': 'sum'
}).reset_index()

# PIVOT: Reshape to wide format
pivot_amount = monthly_sales.pivot(index='product_id', columns='month', values='amount')
pivot_amount = pivot_amount.reset_index()

# PREPARE: Clean and calculate totals
pivot_amount = pivot_amount.fillna(0)
numeric_cols = pivot_amount.select_dtypes(include='number').columns
pivot_amount['total'] = pivot_amount[numeric_cols].sum(axis=1)
pivot_amount['avg_monthly'] = pivot_amount[numeric_cols].mean(axis=1).round(2)

pivot_amount.to_csv('product_monthly_pivot.csv', index=False)
"""

# 5. SPLIT -> JOIN -> GROUPING (filter -> combine -> aggregate)
SPLIT_JOIN_GROUPING_EXAMPLE = """
import pandas as pd

# Load data
transactions = pd.read_csv('transactions.csv')
customers = pd.read_csv('customers.csv')

# SPLIT: Filter to high-value transactions
high_value = transactions[transactions['amount'] >= 100]

# JOIN: Enrich with customer data
high_value_enriched = pd.merge(
    high_value,
    customers[['customer_id', 'segment', 'region']],
    on='customer_id',
    how='left'
)

# GROUPING: Aggregate by segment and region
segment_summary = high_value_enriched.groupby(['segment', 'region']).agg({
    'amount': ['sum', 'mean', 'count'],
    'customer_id': 'nunique'
}).reset_index()
segment_summary.columns = ['segment', 'region', 'total_amount', 'avg_amount',
                           'transaction_count', 'unique_customers']

segment_summary.to_csv('high_value_segment_summary.csv', index=False)
"""

# 6. PREPARE -> TOP_N -> PREPARE (clean -> limit -> format)
PREPARE_TOPN_PREPARE_EXAMPLE = """
import pandas as pd

# Load data
products = pd.read_csv('products.csv')

# PREPARE: Clean product data
products['product_name'] = products['product_name'].str.strip().str.title()
products['revenue'] = products['revenue'].fillna(0)
products['margin'] = products['margin'].fillna(0)
products['composite_score'] = products['revenue'] * 0.7 + products['margin'] * 0.3

# TOP_N: Get top 100 products
top_products = products.nlargest(100, 'composite_score')

# PREPARE: Format for report
top_products['rank'] = range(1, len(top_products) + 1)
top_products['revenue_formatted'] = top_products['revenue'].apply(lambda x: f'${x:,.2f}')
top_products['performance'] = pd.cut(
    top_products['composite_score'],
    bins=[0, 50, 100, float('inf')],
    labels=['Underperformer', 'Average', 'Star']
)

top_products.to_csv('top_100_products.csv', index=False)
"""

# 7. SAMPLING -> PREPARE -> GROUPING (sample -> clean -> aggregate)
SAMPLING_PREPARE_GROUPING_EXAMPLE = """
import pandas as pd

# Load data
large_dataset = pd.read_csv('large_logs.csv')

# SAMPLING: Take 10% sample
sample = large_dataset.sample(frac=0.1, random_state=42)

# PREPARE: Clean and transform
sample['timestamp'] = pd.to_datetime(sample['timestamp'])
sample['hour'] = sample['timestamp'].dt.hour
sample['is_error'] = sample['status_code'] >= 400
sample['response_time_ms'] = sample['response_time'] * 1000

# GROUPING: Aggregate by hour
hourly_stats = sample.groupby('hour').agg({
    'request_id': 'count',
    'response_time_ms': ['mean', 'median', 'std'],
    'is_error': 'sum'
}).reset_index()
hourly_stats.columns = ['hour', 'request_count', 'avg_response_ms',
                        'median_response_ms', 'std_response_ms', 'error_count']
hourly_stats['error_rate'] = (hourly_stats['error_count'] / hourly_stats['request_count'] * 100).round(2)

hourly_stats.to_csv('hourly_stats_sample.csv', index=False)
"""

# 8. JOIN -> JOIN -> GROUPING (multi-join -> aggregate)
MULTI_JOIN_GROUPING_EXAMPLE = """
import pandas as pd

# Load data
orders = pd.read_csv('orders.csv')
customers = pd.read_csv('customers.csv')
products = pd.read_csv('products.csv')
categories = pd.read_csv('categories.csv')

# JOIN 1: Orders with customers
orders_customers = pd.merge(orders, customers[['customer_id', 'segment', 'region']],
                             on='customer_id', how='left')

# JOIN 2: With products and categories
orders_full = pd.merge(orders_customers, products[['product_id', 'category_id', 'product_name']],
                        on='product_id', how='left')
orders_full = pd.merge(orders_full, categories[['category_id', 'category_name']],
                        on='category_id', how='left')

# GROUPING: Multi-dimensional aggregation
summary = orders_full.groupby(['segment', 'region', 'category_name']).agg({
    'order_id': 'count',
    'amount': 'sum',
    'customer_id': 'nunique'
}).reset_index()
summary.columns = ['segment', 'region', 'category', 'order_count', 'total_revenue', 'unique_customers']

summary.to_csv('multi_dimensional_summary.csv', index=False)
"""

# 9. STACK -> STACK -> DISTINCT (multi-stack -> dedupe)
MULTI_STACK_DISTINCT_EXAMPLE = """
import pandas as pd

# Load data from multiple years and sources
sales_2022_web = pd.read_csv('sales_2022_web.csv')
sales_2022_store = pd.read_csv('sales_2022_store.csv')
sales_2023_web = pd.read_csv('sales_2023_web.csv')
sales_2023_store = pd.read_csv('sales_2023_store.csv')

# STACK 1: Combine 2022 sources
sales_2022_web['source'] = 'web'
sales_2022_store['source'] = 'store'
sales_2022 = pd.concat([sales_2022_web, sales_2022_store], ignore_index=True)
sales_2022['year'] = 2022

# STACK 2: Combine 2023 sources
sales_2023_web['source'] = 'web'
sales_2023_store['source'] = 'store'
sales_2023 = pd.concat([sales_2023_web, sales_2023_store], ignore_index=True)
sales_2023['year'] = 2023

# STACK 3: Combine all years
all_sales = pd.concat([sales_2022, sales_2023], ignore_index=True)

# DISTINCT: Remove duplicates
all_sales = all_sales.drop_duplicates(subset=['transaction_id'])

all_sales.to_csv('all_sales_combined.csv', index=False)
"""

# 10. WINDOW -> GROUPING -> SORT (window -> aggregate -> order)
WINDOW_GROUPING_SORT_EXAMPLE = """
import pandas as pd

# Load data
daily_metrics = pd.read_csv('daily_metrics.csv')
daily_metrics['date'] = pd.to_datetime(daily_metrics['date'])

# WINDOW: Calculate rolling metrics
daily_metrics = daily_metrics.sort_values(['product_id', 'date'])
daily_metrics['rolling_7d_avg'] = daily_metrics.groupby('product_id')['revenue'].transform(
    lambda x: x.rolling(7, min_periods=1).mean()
)
daily_metrics['rolling_7d_sum'] = daily_metrics.groupby('product_id')['revenue'].transform(
    lambda x: x.rolling(7, min_periods=1).sum()
)

# GROUPING: Aggregate by product
product_summary = daily_metrics.groupby('product_id').agg({
    'revenue': 'sum',
    'rolling_7d_avg': 'last',
    'rolling_7d_sum': 'last',
    'date': ['min', 'max']
}).reset_index()
product_summary.columns = ['product_id', 'total_revenue', 'latest_7d_avg',
                            'latest_7d_sum', 'first_date', 'last_date']

# SORT: Order by total revenue
product_summary = product_summary.sort_values('total_revenue', ascending=False)

product_summary.to_csv('product_summary_windowed.csv', index=False)
"""

# 11-20: Additional recipe combinations
FULL_ETL_PIPELINE_EXAMPLE = """
import pandas as pd
import numpy as np

# Load raw data sources
customers = pd.read_csv('raw_customers.csv')
orders = pd.read_csv('raw_orders.csv')
products = pd.read_csv('raw_products.csv')

# PREPARE 1: Clean customers
customers['email'] = customers['email'].str.lower().str.strip()
customers['name'] = customers['name'].str.strip().str.title()
customers = customers.dropna(subset=['customer_id', 'email'])
customers = customers.drop_duplicates(subset=['email'])

# JOIN 1: Orders with customers
orders_enriched = pd.merge(
    orders,
    customers[['customer_id', 'name', 'email', 'segment']],
    on='customer_id',
    how='inner'
)

# JOIN 2: With products
orders_full = pd.merge(
    orders_enriched,
    products[['product_id', 'product_name', 'category', 'unit_cost']],
    on='product_id',
    how='left'
)

# PREPARE 2: Calculate metrics
orders_full['order_date'] = pd.to_datetime(orders_full['order_date'])
orders_full['margin'] = orders_full['amount'] - orders_full['unit_cost'] * orders_full['quantity']
orders_full['margin_pct'] = (orders_full['margin'] / orders_full['amount'] * 100).round(2)

# GROUPING: Customer-level aggregation
customer_metrics = orders_full.groupby(['customer_id', 'name', 'segment']).agg({
    'order_id': 'count',
    'amount': 'sum',
    'margin': 'sum',
    'order_date': ['min', 'max']
}).reset_index()
customer_metrics.columns = ['customer_id', 'name', 'segment', 'order_count',
                             'total_revenue', 'total_margin', 'first_order', 'last_order']

# WINDOW: Add customer rankings
customer_metrics = customer_metrics.sort_values('total_revenue', ascending=False)
customer_metrics['revenue_rank'] = range(1, len(customer_metrics) + 1)
customer_metrics['revenue_percentile'] = (
    customer_metrics['revenue_rank'] / len(customer_metrics) * 100
).round(1)

# PREPARE 3: Final formatting
customer_metrics['clv_tier'] = pd.cut(
    customer_metrics['total_revenue'],
    bins=[0, 100, 500, 2000, float('inf')],
    labels=['Low', 'Medium', 'High', 'VIP']
)

customer_metrics.to_csv('customer_analytics.csv', index=False)
"""

# =============================================================================
# PROCESSOR COMBINATIONS (15 combinations)
# =============================================================================

# 1. STRING_TRANSFORMER -> FILL_EMPTY -> TYPE_SETTER (text pipeline)
TEXT_PIPELINE_EXAMPLE = """
import pandas as pd

df = pd.read_csv('raw_text_data.csv')

# STRING_TRANSFORMER: Clean text
df['name'] = df['name'].str.strip().str.title()
df['email'] = df['email'].str.lower().str.strip()
df['code'] = df['code'].str.upper()

# FILL_EMPTY: Handle missing values
df['name'] = df['name'].fillna('Unknown')
df['email'] = df['email'].fillna('')
df['code'] = df['code'].fillna('N/A')

# TYPE_SETTER: Ensure correct types
df['customer_id'] = df['customer_id'].astype(str)
df['is_active'] = df['is_active'].astype(bool)

df.to_csv('cleaned_text_data.csv', index=False)
"""

# 2. DATE_PARSER -> FORMULA -> FILTER_ON_DATE_RANGE (date pipeline)
DATE_PIPELINE_EXAMPLE = """
import pandas as pd
from datetime import datetime, timedelta

df = pd.read_csv('events.csv')

# DATE_PARSER: Parse date strings
df['event_date'] = pd.to_datetime(df['event_date_str'])
df['created_at'] = pd.to_datetime(df['created_at_str'])

# FORMULA: Calculate date-based metrics
df['days_since_event'] = (datetime.now() - df['event_date']).dt.days
df['processing_time'] = (df['event_date'] - df['created_at']).dt.total_seconds() / 3600
df['event_year'] = df['event_date'].dt.year
df['event_month'] = df['event_date'].dt.month
df['is_recent'] = (df['days_since_event'] <= 30).astype(int)

# FILTER_ON_DATE_RANGE: Keep only last 365 days
cutoff_date = datetime.now() - timedelta(days=365)
df = df[df['event_date'] >= cutoff_date]

df.to_csv('processed_events.csv', index=False)
"""

# 3. COLUMN_RENAMER -> COLUMN_DELETER -> COLUMNS_SELECTOR (column pipeline)
COLUMN_PIPELINE_EXAMPLE = """
import pandas as pd

df = pd.read_csv('raw_export.csv')

# COLUMN_RENAMER: Standardize column names
df = df.rename(columns={
    'cust_id': 'customer_id',
    'prod_nm': 'product_name',
    'qty': 'quantity',
    'amt': 'amount',
    'dt': 'date'
})

# COLUMN_DELETER: Remove unnecessary columns
columns_to_drop = ['temp_col', 'debug_info', 'internal_id', '_row_num']
df = df.drop(columns=[c for c in columns_to_drop if c in df.columns])

# COLUMNS_SELECTOR: Select final columns in order
final_columns = ['customer_id', 'product_name', 'quantity', 'amount', 'date']
df = df[[c for c in final_columns if c in df.columns]]

df.to_csv('cleaned_export.csv', index=False)
"""

# 4. NUMERICAL_TRANSFORMER -> ROUND -> CLIP -> BINNER (numeric pipeline)
NUMERIC_PIPELINE_EXAMPLE = """
import pandas as pd
import numpy as np

df = pd.read_csv('raw_metrics.csv')

# NUMERICAL_TRANSFORMER: Mathematical transformations
df['log_value'] = np.log1p(df['value'])
df['normalized'] = (df['value'] - df['value'].mean()) / df['value'].std()
df['pct_of_max'] = df['value'] / df['value'].max() * 100

# ROUND: Round to appropriate precision
df['value_rounded'] = df['value'].round(2)
df['pct_of_max'] = df['pct_of_max'].round(1)

# CLIP: Constrain to valid range
df['score'] = df['score'].clip(lower=0, upper=100)
df['normalized'] = df['normalized'].clip(lower=-3, upper=3)

# BINNER: Create categories
df['value_bucket'] = pd.cut(
    df['value_rounded'],
    bins=[0, 10, 50, 100, 500, float('inf')],
    labels=['XS', 'S', 'M', 'L', 'XL']
)
df['score_quartile'] = pd.qcut(df['score'], q=4, labels=['Q1', 'Q2', 'Q3', 'Q4'])

df.to_csv('processed_metrics.csv', index=False)
"""

# 5. REGEXP_EXTRACTOR -> SPLIT_COLUMN -> CONCAT_COLUMNS (text extraction)
TEXT_EXTRACTION_PIPELINE_EXAMPLE = """
import pandas as pd

df = pd.read_csv('raw_contacts.csv')

# REGEXP_EXTRACTOR: Extract patterns
df['area_code'] = df['phone'].str.extract(r'\\((\\d{3})\\)')
df['email_domain'] = df['email'].str.extract(r'@(.+)$')
df['zip_code'] = df['address'].str.extract(r'(\\d{5})(?:-\\d{4})?$')

# SPLIT_COLUMN: Split into parts
name_parts = df['full_name'].str.split(' ', n=1, expand=True)
df['first_name'] = name_parts[0]
df['last_name'] = name_parts[1]

address_parts = df['address'].str.split(',', expand=True)
df['street'] = address_parts[0]
df['city_state'] = address_parts[1]

# CONCAT_COLUMNS: Combine fields
df['display_name'] = df['first_name'] + ' ' + df['last_name'].str[0] + '.'
df['contact_info'] = df['email'] + ' | ' + df['phone']

df.to_csv('parsed_contacts.csv', index=False)
"""

# 6. FILL_EMPTY -> REMOVE_ROWS_ON_EMPTY -> REMOVE_DUPLICATES (cleaning pipeline)
CLEANING_PIPELINE_EXAMPLE = """
import pandas as pd

df = pd.read_csv('dirty_data.csv')

# FILL_EMPTY: Fill non-critical fields
df['category'] = df['category'].fillna('Other')
df['score'] = df['score'].fillna(df['score'].median())
df['notes'] = df['notes'].fillna('')

# REMOVE_ROWS_ON_EMPTY: Remove rows with critical missing values
df = df.dropna(subset=['customer_id', 'email', 'amount'])

# REMOVE_DUPLICATES: Deduplicate
df = df.drop_duplicates(subset=['customer_id', 'transaction_id'], keep='first')
df = df.drop_duplicates(subset=['email'], keep='last')

df.to_csv('clean_data.csv', index=False)
"""

# 7. FILTER_ON_VALUE -> FLAG_ON_VALUE -> CREATE_COLUMN_WITH_GREL (flagging pipeline)
FLAGGING_PIPELINE_EXAMPLE = """
import pandas as pd

df = pd.read_csv('transactions.csv')

# FILTER_ON_VALUE: Keep valid transactions
df = df[df['status'] != 'cancelled']
df = df[df['amount'] > 0]

# FLAG_ON_VALUE: Create flag columns
df['is_premium'] = (df['customer_tier'] == 'premium').astype(int)
df['is_high_value'] = (df['amount'] >= 1000).astype(int)
df['needs_review'] = (df['risk_score'] >= 0.8).astype(int)

# CREATE_COLUMN_WITH_GREL: Complex computed columns
df['priority'] = df.apply(
    lambda row: 'Critical' if row['is_high_value'] and row['needs_review']
    else 'High' if row['is_high_value'] or row['needs_review']
    else 'Normal',
    axis=1
)

df['display_label'] = df.apply(
    lambda row: f"{row['transaction_id']} - {row['customer_name']} (${row['amount']:,.2f})",
    axis=1
)

df.to_csv('flagged_transactions.csv', index=False)
"""

# 8. TYPE_SETTER -> NORMALIZER -> CATEGORICAL_ENCODER (ML prep pipeline)
ML_PREP_PIPELINE_EXAMPLE = """
import pandas as pd
import numpy as np

df = pd.read_csv('raw_features.csv')

# TYPE_SETTER: Ensure correct types
df['age'] = df['age'].astype(float)
df['income'] = df['income'].astype(float)
df['category'] = df['category'].astype(str)

# NORMALIZER: Normalize numeric features
numeric_cols = ['age', 'income', 'score']
for col in numeric_cols:
    df[f'{col}_normalized'] = (df[col] - df[col].mean()) / df[col].std()
    df[f'{col}_minmax'] = (df[col] - df[col].min()) / (df[col].max() - df[col].min())

# CATEGORICAL_ENCODER: Encode categorical features
df_encoded = pd.get_dummies(df, columns=['category', 'region'], prefix=['cat', 'reg'])

df_encoded.to_csv('ml_features.csv', index=False)
"""

# 9-15: Additional processor combinations
ALL_FILTER_PROCESSORS_EXAMPLE = """
import pandas as pd
from datetime import datetime, timedelta

df = pd.read_csv('data.csv')
df['date'] = pd.to_datetime(df['date'])

# FILTER_ON_VALUE: Exact value filter
df = df[df['status'] == 'active']

# FILTER_ON_FORMULA: Complex condition
df = df[(df['amount'] > 100) | (df['priority'] == 'high')]

# FILTER_ON_DATE_RANGE: Date filter
cutoff = datetime.now() - timedelta(days=90)
df = df[df['date'] >= cutoff]

# FILTER_ON_NUMERIC_RANGE: Numeric filter
df = df[df['score'].between(0, 100)]

# FILTER_ON_BAD_TYPE: Type validation
df['amount_valid'] = pd.to_numeric(df['amount'], errors='coerce')
df = df[df['amount_valid'].notna()]

df.to_csv('filtered_data.csv', index=False)
"""

ALL_FLAG_PROCESSORS_EXAMPLE = """
import pandas as pd
from datetime import datetime, timedelta

df = pd.read_csv('data.csv')
df['date'] = pd.to_datetime(df['date'])

# FLAG_ON_VALUE
df['is_premium'] = (df['tier'] == 'premium').astype(int)

# FLAG_ON_FORMULA
df['high_value_recent'] = (
    (df['amount'] >= 1000) &
    (df['date'] >= datetime.now() - timedelta(days=30))
).astype(int)

# FLAG_ON_BAD_TYPE
df['has_valid_email'] = df['email'].str.contains('@', na=False).astype(int)

# FLAG_ON_DATE_RANGE
df['is_q1'] = df['date'].dt.quarter.eq(1).astype(int)

# FLAG_ON_NUMERIC_RANGE
df['score_in_range'] = df['score'].between(50, 100).astype(int)

df.to_csv('flagged_data.csv', index=False)
"""

ALL_MISSING_VALUE_PROCESSORS_EXAMPLE = """
import pandas as pd

df = pd.read_csv('data_with_nulls.csv')

# FILL_EMPTY_WITH_VALUE: Constant fill
df['category'] = df['category'].fillna('Unknown')

# FILL_EMPTY_WITH_COMPUTED_VALUE: Computed fill
df['amount'] = df['amount'].fillna(df['amount'].mean())
df['score'] = df.groupby('category')['score'].transform(lambda x: x.fillna(x.median()))

# FILL_EMPTY_WITH_PREVIOUS_NEXT: Forward/backward fill
df = df.sort_values('date')
df['metric'] = df['metric'].ffill()
df['metric'] = df['metric'].bfill()

# REMOVE_ROWS_ON_EMPTY: Drop rows
df = df.dropna(subset=['customer_id', 'email'])

df.to_csv('no_missing_data.csv', index=False)
"""

# =============================================================================
# COMBINATION EXAMPLES REGISTRY
# =============================================================================

COMBINATION_EXAMPLES: Dict[str, str] = {
    # Recipe Combinations
    "prepare_grouping_prepare": PREPARE_GROUPING_PREPARE_EXAMPLE,
    "join_window_split": JOIN_WINDOW_SPLIT_EXAMPLE,
    "stack_distinct_sort": STACK_DISTINCT_SORT_EXAMPLE,
    "grouping_pivot_prepare": GROUPING_PIVOT_PREPARE_EXAMPLE,
    "split_join_grouping": SPLIT_JOIN_GROUPING_EXAMPLE,
    "prepare_topn_prepare": PREPARE_TOPN_PREPARE_EXAMPLE,
    "sampling_prepare_grouping": SAMPLING_PREPARE_GROUPING_EXAMPLE,
    "multi_join_grouping": MULTI_JOIN_GROUPING_EXAMPLE,
    "multi_stack_distinct": MULTI_STACK_DISTINCT_EXAMPLE,
    "window_grouping_sort": WINDOW_GROUPING_SORT_EXAMPLE,
    "full_etl_pipeline": FULL_ETL_PIPELINE_EXAMPLE,

    # Processor Combinations
    "text_pipeline": TEXT_PIPELINE_EXAMPLE,
    "date_pipeline": DATE_PIPELINE_EXAMPLE,
    "column_pipeline": COLUMN_PIPELINE_EXAMPLE,
    "numeric_pipeline": NUMERIC_PIPELINE_EXAMPLE,
    "text_extraction_pipeline": TEXT_EXTRACTION_PIPELINE_EXAMPLE,
    "cleaning_pipeline": CLEANING_PIPELINE_EXAMPLE,
    "flagging_pipeline": FLAGGING_PIPELINE_EXAMPLE,
    "ml_prep_pipeline": ML_PREP_PIPELINE_EXAMPLE,
    "all_filter_processors": ALL_FILTER_PROCESSORS_EXAMPLE,
    "all_flag_processors": ALL_FLAG_PROCESSORS_EXAMPLE,
    "all_missing_value_processors": ALL_MISSING_VALUE_PROCESSORS_EXAMPLE,
}


def get_combination_example(name: str) -> str:
    """Get a combination example by name."""
    return COMBINATION_EXAMPLES.get(name, "")


def list_combination_examples() -> list:
    """List all available combination examples."""
    return list(COMBINATION_EXAMPLES.keys())
