"""
Intermediate data processing pipeline examples for py2dataiku.

These examples demonstrate multi-step pipelines combining several operations
like joins, groupings, window functions, and data transformations.
"""

# Example 1: Customer Order Analysis
CUSTOMER_ORDER_ANALYSIS = """
import pandas as pd

# Load data
customers = pd.read_csv('customers.csv')
orders = pd.read_csv('orders.csv')

# Clean customer data
customers['name'] = customers['name'].str.strip().str.title()
customers = customers.dropna(subset=['customer_id'])

# Join customers with orders
customer_orders = pd.merge(
    customers,
    orders,
    on='customer_id',
    how='left'
)

# Calculate order statistics per customer
customer_summary = customer_orders.groupby('customer_id').agg({
    'order_id': 'count',
    'amount': 'sum'
}).reset_index()

customer_summary.columns = ['customer_id', 'order_count', 'total_amount']

# Save result
customer_summary.to_csv('customer_order_summary.csv', index=False)
"""

# Example 2: Sales with Product Details
SALES_PRODUCT_ENRICHMENT = """
import pandas as pd

# Load data
sales = pd.read_csv('sales.csv')
products = pd.read_csv('products.csv')
categories = pd.read_csv('categories.csv')

# Join sales with products
sales_with_products = pd.merge(
    sales,
    products[['product_id', 'product_name', 'category_id', 'unit_price']],
    on='product_id',
    how='inner'
)

# Join with categories
sales_enriched = pd.merge(
    sales_with_products,
    categories[['category_id', 'category_name']],
    on='category_id',
    how='left'
)

# Calculate line total
sales_enriched['line_total'] = sales_enriched['quantity'] * sales_enriched['unit_price']

# Save enriched data
sales_enriched.to_csv('sales_enriched.csv', index=False)
"""

# Example 3: Time-Based Aggregation
TIME_BASED_AGGREGATION = """
import pandas as pd

# Load transaction data
transactions = pd.read_csv('transactions.csv')

# Convert date column
transactions['transaction_date'] = pd.to_datetime(transactions['transaction_date'])

# Extract date parts
transactions['year'] = transactions['transaction_date'].dt.year
transactions['month'] = transactions['transaction_date'].dt.month
transactions['day_of_week'] = transactions['transaction_date'].dt.dayofweek

# Aggregate by month
monthly_summary = transactions.groupby(['year', 'month']).agg({
    'amount': ['sum', 'mean', 'count'],
    'customer_id': 'nunique'
}).reset_index()

monthly_summary.columns = ['year', 'month', 'total_amount', 'avg_amount',
                           'transaction_count', 'unique_customers']

# Save result
monthly_summary.to_csv('monthly_summary.csv', index=False)
"""

# Example 4: Customer Segmentation
CUSTOMER_SEGMENTATION = """
import pandas as pd

# Load customer transaction data
customers = pd.read_csv('customers.csv')
transactions = pd.read_csv('transactions.csv')

# Calculate customer metrics
customer_metrics = transactions.groupby('customer_id').agg({
    'amount': 'sum',
    'transaction_id': 'count',
    'transaction_date': 'max'
}).reset_index()

customer_metrics.columns = ['customer_id', 'total_spend', 'transaction_count', 'last_purchase']

# Join with customer info
customer_data = pd.merge(customers, customer_metrics, on='customer_id', how='left')

# Fill missing values for customers with no transactions
customer_data['total_spend'] = customer_data['total_spend'].fillna(0)
customer_data['transaction_count'] = customer_data['transaction_count'].fillna(0)

# Segment customers by spend
customer_data['segment'] = pd.cut(
    customer_data['total_spend'],
    bins=[0, 100, 500, 1000, float('inf')],
    labels=['Low', 'Medium', 'High', 'VIP']
)

# Save segmented data
customer_data.to_csv('customer_segments.csv', index=False)
"""

# Example 5: Stacking Multiple Data Sources
DATA_STACKING = """
import pandas as pd

# Load data from multiple sources
sales_2022 = pd.read_csv('sales_2022.csv')
sales_2023 = pd.read_csv('sales_2023.csv')
sales_2024 = pd.read_csv('sales_2024.csv')

# Add year column to each
sales_2022['data_year'] = 2022
sales_2023['data_year'] = 2023
sales_2024['data_year'] = 2024

# Stack all years together
all_sales = pd.concat([sales_2022, sales_2023, sales_2024], ignore_index=True)

# Remove duplicates
all_sales = all_sales.drop_duplicates(subset=['transaction_id'])

# Sort by date
all_sales = all_sales.sort_values('transaction_date')

# Save combined data
all_sales.to_csv('all_sales_combined.csv', index=False)
"""

# Example 6: Pivot Table Analysis
PIVOT_ANALYSIS = """
import pandas as pd

# Load sales data
sales = pd.read_csv('sales.csv')

# Create pivot table: products vs months
pivot_table = sales.pivot_table(
    values='amount',
    index='product_category',
    columns='month',
    aggfunc='sum',
    fill_value=0
)

# Reset index for export
pivot_table = pivot_table.reset_index()

# Save pivot table
pivot_table.to_csv('sales_pivot.csv', index=False)
"""

# Example 7: Window Functions - Running Totals
WINDOW_RUNNING_TOTAL = """
import pandas as pd

# Load daily sales
daily_sales = pd.read_csv('daily_sales.csv')

# Sort by date
daily_sales = daily_sales.sort_values('sale_date')

# Calculate running total
daily_sales['running_total'] = daily_sales['amount'].cumsum()

# Calculate 7-day moving average
daily_sales['moving_avg_7d'] = daily_sales['amount'].rolling(window=7).mean()

# Save with running calculations
daily_sales.to_csv('daily_sales_with_running.csv', index=False)
"""

# Example 8: Multi-Level Grouping
MULTI_LEVEL_GROUPING = """
import pandas as pd

# Load order data
orders = pd.read_csv('orders.csv')

# Group by region and product category
regional_summary = orders.groupby(['region', 'product_category']).agg({
    'order_id': 'count',
    'amount': ['sum', 'mean'],
    'quantity': 'sum'
}).reset_index()

# Flatten column names
regional_summary.columns = [
    'region', 'product_category', 'order_count',
    'total_amount', 'avg_amount', 'total_quantity'
]

# Sort by total amount
regional_summary = regional_summary.sort_values('total_amount', ascending=False)

# Save summary
regional_summary.to_csv('regional_product_summary.csv', index=False)
"""

# Example 9: Data Sampling and Validation Split
DATA_SAMPLING = """
import pandas as pd

# Load full dataset
full_data = pd.read_csv('full_dataset.csv')

# Remove any rows with critical missing values
full_data = full_data.dropna(subset=['target_column'])

# Create random sample for validation (10%)
validation_sample = full_data.sample(frac=0.1, random_state=42)

# Get training set (remaining 90%)
training_set = full_data.drop(validation_sample.index)

# Save splits
training_set.to_csv('training_set.csv', index=False)
validation_sample.to_csv('validation_set.csv', index=False)
"""

# Example 10: Feature Engineering
FEATURE_ENGINEERING = """
import pandas as pd
import numpy as np

# Load user activity data
activity = pd.read_csv('user_activity.csv')

# Parse timestamps
activity['timestamp'] = pd.to_datetime(activity['timestamp'])

# Create time-based features
activity['hour'] = activity['timestamp'].dt.hour
activity['day_of_week'] = activity['timestamp'].dt.dayofweek
activity['is_weekend'] = activity['day_of_week'].isin([5, 6]).astype(int)

# Create interaction features
activity['session_duration_minutes'] = activity['session_duration'] / 60
activity['pages_per_minute'] = activity['pages_viewed'] / activity['session_duration_minutes']

# Handle infinite values
activity['pages_per_minute'] = activity['pages_per_minute'].replace([np.inf, -np.inf], 0)

# Clip outliers
activity['session_duration_minutes'] = activity['session_duration_minutes'].clip(upper=120)

# Save engineered features
activity.to_csv('user_activity_features.csv', index=False)
"""

# All intermediate examples
INTERMEDIATE_EXAMPLES = {
    "customer_order_analysis": CUSTOMER_ORDER_ANALYSIS,
    "sales_product_enrichment": SALES_PRODUCT_ENRICHMENT,
    "time_based_aggregation": TIME_BASED_AGGREGATION,
    "customer_segmentation": CUSTOMER_SEGMENTATION,
    "data_stacking": DATA_STACKING,
    "pivot_analysis": PIVOT_ANALYSIS,
    "window_running_total": WINDOW_RUNNING_TOTAL,
    "multi_level_grouping": MULTI_LEVEL_GROUPING,
    "data_sampling": DATA_SAMPLING,
    "feature_engineering": FEATURE_ENGINEERING,
}
