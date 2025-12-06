"""
Advanced data processing pipeline examples for py2dataiku.

These examples demonstrate complex, production-grade data pipelines with
multiple data sources, sophisticated transformations, and ML preprocessing.
"""

# Example 1: E-Commerce Analytics Pipeline
ECOMMERCE_ANALYTICS = """
import pandas as pd
import numpy as np

# Load all data sources
customers = pd.read_csv('customers.csv')
orders = pd.read_csv('orders.csv')
order_items = pd.read_csv('order_items.csv')
products = pd.read_csv('products.csv')
categories = pd.read_csv('categories.csv')

# Clean customer data
customers['email'] = customers['email'].str.lower().str.strip()
customers['name'] = customers['name'].str.strip().str.title()
customers = customers.drop_duplicates(subset=['email'])

# Join order items with products
items_with_products = pd.merge(
    order_items,
    products[['product_id', 'product_name', 'category_id', 'unit_cost']],
    on='product_id',
    how='left'
)

# Add category info
items_enriched = pd.merge(
    items_with_products,
    categories[['category_id', 'category_name']],
    on='category_id',
    how='left'
)

# Calculate item metrics
items_enriched['line_total'] = items_enriched['quantity'] * items_enriched['unit_price']
items_enriched['profit'] = items_enriched['line_total'] - (items_enriched['quantity'] * items_enriched['unit_cost'])

# Aggregate to order level
order_summary = items_enriched.groupby('order_id').agg({
    'line_total': 'sum',
    'profit': 'sum',
    'quantity': 'sum',
    'product_id': 'nunique'
}).reset_index()

order_summary.columns = ['order_id', 'order_total', 'order_profit', 'total_items', 'unique_products']

# Join with orders
orders_complete = pd.merge(orders, order_summary, on='order_id', how='left')

# Parse dates
orders_complete['order_date'] = pd.to_datetime(orders_complete['order_date'])

# Join with customers
customer_orders = pd.merge(
    orders_complete,
    customers[['customer_id', 'name', 'email', 'signup_date', 'region']],
    on='customer_id',
    how='left'
)

# Calculate customer lifetime metrics
customer_lifetime = customer_orders.groupby('customer_id').agg({
    'order_id': 'count',
    'order_total': 'sum',
    'order_profit': 'sum',
    'order_date': ['min', 'max']
}).reset_index()

customer_lifetime.columns = [
    'customer_id', 'total_orders', 'lifetime_value',
    'lifetime_profit', 'first_order', 'last_order'
]

# Calculate days since last order
customer_lifetime['days_since_last_order'] = (
    pd.Timestamp.now() - customer_lifetime['last_order']
).dt.days

# Segment customers
customer_lifetime['value_segment'] = pd.cut(
    customer_lifetime['lifetime_value'],
    bins=[0, 100, 500, 2000, float('inf')],
    labels=['Bronze', 'Silver', 'Gold', 'Platinum']
)

# Save all outputs
customer_orders.to_csv('customer_orders_enriched.csv', index=False)
customer_lifetime.to_csv('customer_lifetime_metrics.csv', index=False)
"""

# Example 2: Financial Transaction Processing
FINANCIAL_TRANSACTION_PIPELINE = """
import pandas as pd
import numpy as np

# Load data
transactions = pd.read_csv('transactions.csv')
accounts = pd.read_csv('accounts.csv')
merchants = pd.read_csv('merchants.csv')
fraud_labels = pd.read_csv('fraud_labels.csv')

# Parse transaction timestamps
transactions['transaction_time'] = pd.to_datetime(transactions['transaction_time'])

# Clean and validate
transactions = transactions.dropna(subset=['account_id', 'amount'])
transactions['amount'] = transactions['amount'].abs()  # Ensure positive amounts

# Add time features
transactions['hour'] = transactions['transaction_time'].dt.hour
transactions['day_of_week'] = transactions['transaction_time'].dt.dayofweek
transactions['is_weekend'] = transactions['day_of_week'].isin([5, 6]).astype(int)
transactions['is_night'] = transactions['hour'].between(22, 6).astype(int)

# Join with account info
transactions_enriched = pd.merge(
    transactions,
    accounts[['account_id', 'account_type', 'credit_limit', 'customer_id', 'open_date']],
    on='account_id',
    how='left'
)

# Join with merchant info
transactions_enriched = pd.merge(
    transactions_enriched,
    merchants[['merchant_id', 'merchant_category', 'merchant_country', 'risk_score']],
    on='merchant_id',
    how='left'
)

# Calculate account-level aggregates
account_stats = transactions_enriched.groupby('account_id').agg({
    'amount': ['mean', 'std', 'max', 'count'],
    'merchant_id': 'nunique'
}).reset_index()
account_stats.columns = ['account_id', 'avg_amount', 'std_amount', 'max_amount',
                         'transaction_count', 'unique_merchants']

# Join stats back
transactions_enriched = pd.merge(
    transactions_enriched,
    account_stats,
    on='account_id',
    how='left'
)

# Calculate deviation from normal
transactions_enriched['amount_zscore'] = (
    (transactions_enriched['amount'] - transactions_enriched['avg_amount']) /
    transactions_enriched['std_amount'].replace(0, 1)
)

# Flag suspicious transactions
transactions_enriched['high_amount_flag'] = (transactions_enriched['amount_zscore'] > 3).astype(int)
transactions_enriched['new_merchant_flag'] = 0  # Would need historical data

# Join with fraud labels for training
labeled_transactions = pd.merge(
    transactions_enriched,
    fraud_labels[['transaction_id', 'is_fraud']],
    on='transaction_id',
    how='left'
)

# Fill unlabeled as not fraud
labeled_transactions['is_fraud'] = labeled_transactions['is_fraud'].fillna(0)

# Save outputs
labeled_transactions.to_csv('transactions_processed.csv', index=False)
account_stats.to_csv('account_statistics.csv', index=False)
"""

# Example 3: Supply Chain Inventory Pipeline
SUPPLY_CHAIN_PIPELINE = """
import pandas as pd
import numpy as np

# Load data sources
inventory = pd.read_csv('inventory.csv')
sales_history = pd.read_csv('sales_history.csv')
suppliers = pd.read_csv('suppliers.csv')
warehouses = pd.read_csv('warehouses.csv')
purchase_orders = pd.read_csv('purchase_orders.csv')

# Clean data
inventory = inventory.dropna(subset=['sku', 'warehouse_id'])
sales_history['sale_date'] = pd.to_datetime(sales_history['sale_date'])

# Calculate sales velocity (daily average over last 30 days)
recent_sales = sales_history[
    sales_history['sale_date'] >= (pd.Timestamp.now() - pd.Timedelta(days=30))
]

sales_velocity = recent_sales.groupby(['sku', 'warehouse_id']).agg({
    'quantity_sold': 'sum'
}).reset_index()
sales_velocity['daily_velocity'] = sales_velocity['quantity_sold'] / 30

# Join inventory with velocity
inventory_enriched = pd.merge(
    inventory,
    sales_velocity[['sku', 'warehouse_id', 'daily_velocity']],
    on=['sku', 'warehouse_id'],
    how='left'
)
inventory_enriched['daily_velocity'] = inventory_enriched['daily_velocity'].fillna(0)

# Calculate days of supply
inventory_enriched['days_of_supply'] = np.where(
    inventory_enriched['daily_velocity'] > 0,
    inventory_enriched['quantity_on_hand'] / inventory_enriched['daily_velocity'],
    999  # Infinite supply if no velocity
)

# Join with warehouse info
inventory_enriched = pd.merge(
    inventory_enriched,
    warehouses[['warehouse_id', 'warehouse_name', 'region', 'capacity']],
    on='warehouse_id',
    how='left'
)

# Join with supplier info
inventory_enriched = pd.merge(
    inventory_enriched,
    suppliers[['supplier_id', 'supplier_name', 'lead_time_days', 'reliability_score']],
    left_on='primary_supplier_id',
    right_on='supplier_id',
    how='left'
)

# Calculate reorder flags
inventory_enriched['needs_reorder'] = (
    inventory_enriched['days_of_supply'] < inventory_enriched['lead_time_days'] * 1.5
).astype(int)

inventory_enriched['critical_low'] = (
    inventory_enriched['days_of_supply'] < inventory_enriched['lead_time_days']
).astype(int)

# Calculate suggested order quantity
inventory_enriched['suggested_order_qty'] = np.where(
    inventory_enriched['needs_reorder'] == 1,
    inventory_enriched['daily_velocity'] * 30 - inventory_enriched['quantity_on_hand'],
    0
).clip(lower=0)

# Aggregate by region for reporting
regional_summary = inventory_enriched.groupby('region').agg({
    'quantity_on_hand': 'sum',
    'needs_reorder': 'sum',
    'critical_low': 'sum',
    'sku': 'count'
}).reset_index()
regional_summary.columns = ['region', 'total_inventory', 'items_need_reorder',
                           'critical_items', 'total_skus']

# Save outputs
inventory_enriched.to_csv('inventory_analysis.csv', index=False)
regional_summary.to_csv('regional_inventory_summary.csv', index=False)
"""

# Example 4: Marketing Campaign Analysis
MARKETING_CAMPAIGN_PIPELINE = """
import pandas as pd
import numpy as np

# Load campaign data
campaigns = pd.read_csv('campaigns.csv')
impressions = pd.read_csv('ad_impressions.csv')
clicks = pd.read_csv('ad_clicks.csv')
conversions = pd.read_csv('conversions.csv')
customers = pd.read_csv('customers.csv')
orders = pd.read_csv('orders.csv')

# Parse dates
impressions['impression_time'] = pd.to_datetime(impressions['impression_time'])
clicks['click_time'] = pd.to_datetime(clicks['click_time'])
conversions['conversion_time'] = pd.to_datetime(conversions['conversion_time'])

# Aggregate impressions by campaign
campaign_impressions = impressions.groupby('campaign_id').agg({
    'impression_id': 'count',
    'user_id': 'nunique'
}).reset_index()
campaign_impressions.columns = ['campaign_id', 'total_impressions', 'unique_reach']

# Aggregate clicks by campaign
campaign_clicks = clicks.groupby('campaign_id').agg({
    'click_id': 'count',
    'user_id': 'nunique'
}).reset_index()
campaign_clicks.columns = ['campaign_id', 'total_clicks', 'unique_clickers']

# Aggregate conversions
campaign_conversions = conversions.groupby('campaign_id').agg({
    'conversion_id': 'count',
    'conversion_value': 'sum',
    'user_id': 'nunique'
}).reset_index()
campaign_conversions.columns = ['campaign_id', 'total_conversions',
                                'total_revenue', 'unique_converters']

# Combine metrics
campaign_metrics = pd.merge(campaigns, campaign_impressions, on='campaign_id', how='left')
campaign_metrics = pd.merge(campaign_metrics, campaign_clicks, on='campaign_id', how='left')
campaign_metrics = pd.merge(campaign_metrics, campaign_conversions, on='campaign_id', how='left')

# Fill missing values
for col in ['total_impressions', 'unique_reach', 'total_clicks', 'unique_clickers',
            'total_conversions', 'total_revenue', 'unique_converters']:
    campaign_metrics[col] = campaign_metrics[col].fillna(0)

# Calculate rates
campaign_metrics['ctr'] = (
    campaign_metrics['total_clicks'] / campaign_metrics['total_impressions'].replace(0, 1)
) * 100

campaign_metrics['conversion_rate'] = (
    campaign_metrics['total_conversions'] / campaign_metrics['total_clicks'].replace(0, 1)
) * 100

campaign_metrics['cost_per_click'] = (
    campaign_metrics['budget_spent'] / campaign_metrics['total_clicks'].replace(0, 1)
)

campaign_metrics['cost_per_conversion'] = (
    campaign_metrics['budget_spent'] / campaign_metrics['total_conversions'].replace(0, 1)
)

campaign_metrics['roas'] = (
    campaign_metrics['total_revenue'] / campaign_metrics['budget_spent'].replace(0, 1)
)

# Segment by performance
campaign_metrics['performance_tier'] = pd.cut(
    campaign_metrics['roas'],
    bins=[-float('inf'), 1, 2, 4, float('inf')],
    labels=['Poor', 'Break-even', 'Good', 'Excellent']
)

# Save results
campaign_metrics.to_csv('campaign_performance.csv', index=False)
"""

# Example 5: Healthcare Patient Journey
HEALTHCARE_PATIENT_PIPELINE = """
import pandas as pd
import numpy as np

# Load healthcare data
patients = pd.read_csv('patients.csv')
encounters = pd.read_csv('encounters.csv')
diagnoses = pd.read_csv('diagnoses.csv')
procedures = pd.read_csv('procedures.csv')
prescriptions = pd.read_csv('prescriptions.csv')
lab_results = pd.read_csv('lab_results.csv')

# Parse dates
encounters['encounter_date'] = pd.to_datetime(encounters['encounter_date'])
patients['birth_date'] = pd.to_datetime(patients['birth_date'])

# Calculate patient age
patients['age'] = (pd.Timestamp.now() - patients['birth_date']).dt.days // 365

# Age groups
patients['age_group'] = pd.cut(
    patients['age'],
    bins=[0, 18, 35, 50, 65, 100],
    labels=['Pediatric', 'Young Adult', 'Adult', 'Middle Age', 'Senior']
)

# Join diagnoses to encounters
encounters_with_dx = pd.merge(
    encounters,
    diagnoses[['encounter_id', 'diagnosis_code', 'diagnosis_description', 'is_primary']],
    on='encounter_id',
    how='left'
)

# Get primary diagnosis per encounter
primary_dx = encounters_with_dx[encounters_with_dx['is_primary'] == 1].copy()

# Aggregate encounters per patient
patient_encounter_summary = encounters.groupby('patient_id').agg({
    'encounter_id': 'count',
    'encounter_date': ['min', 'max'],
    'total_charges': 'sum'
}).reset_index()
patient_encounter_summary.columns = [
    'patient_id', 'total_encounters', 'first_encounter',
    'last_encounter', 'total_charges'
]

# Count diagnoses per patient
patient_dx_count = diagnoses.groupby(
    diagnoses.merge(encounters[['encounter_id', 'patient_id']], on='encounter_id')['patient_id']
).agg({
    'diagnosis_code': 'nunique'
}).reset_index()
patient_dx_count.columns = ['patient_id', 'unique_diagnoses']

# Count procedures per patient
patient_proc_count = procedures.merge(
    encounters[['encounter_id', 'patient_id']], on='encounter_id'
).groupby('patient_id').agg({
    'procedure_code': 'count'
}).reset_index()
patient_proc_count.columns = ['patient_id', 'total_procedures']

# Combine patient profile
patient_profile = pd.merge(patients, patient_encounter_summary, on='patient_id', how='left')
patient_profile = pd.merge(patient_profile, patient_dx_count, on='patient_id', how='left')
patient_profile = pd.merge(patient_profile, patient_proc_count, on='patient_id', how='left')

# Fill missing values
patient_profile['total_encounters'] = patient_profile['total_encounters'].fillna(0)
patient_profile['unique_diagnoses'] = patient_profile['unique_diagnoses'].fillna(0)
patient_profile['total_procedures'] = patient_profile['total_procedures'].fillna(0)
patient_profile['total_charges'] = patient_profile['total_charges'].fillna(0)

# Calculate risk score (simplified)
patient_profile['complexity_score'] = (
    patient_profile['unique_diagnoses'] * 0.3 +
    patient_profile['total_procedures'] * 0.2 +
    patient_profile['total_encounters'] * 0.1 +
    (patient_profile['age'] / 10) * 0.4
).round(2)

# Identify high-risk patients
patient_profile['high_risk'] = (patient_profile['complexity_score'] > 5).astype(int)

# Save outputs
patient_profile.to_csv('patient_profiles.csv', index=False)
"""

# All advanced examples
ADVANCED_EXAMPLES = {
    "ecommerce_analytics": ECOMMERCE_ANALYTICS,
    "financial_transactions": FINANCIAL_TRANSACTION_PIPELINE,
    "supply_chain": SUPPLY_CHAIN_PIPELINE,
    "marketing_campaign": MARKETING_CAMPAIGN_PIPELINE,
    "healthcare_patient": HEALTHCARE_PATIENT_PIPELINE,
}
