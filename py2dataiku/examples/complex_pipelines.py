"""
Complex Enterprise-Grade Data Processing Pipelines

These pipelines demonstrate sophisticated multi-stage transformations,
complex joins, advanced feature engineering, and production-grade
data processing patterns used in enterprise environments.
"""

# =============================================================================
# 1. REAL-TIME FRAUD DETECTION FEATURE ENGINEERING
# =============================================================================
FRAUD_DETECTION_PIPELINE = """
import pandas as pd
import numpy as np

# Load transaction streams
transactions = pd.read_csv('transactions.csv')
user_profiles = pd.read_csv('user_profiles.csv')
device_fingerprints = pd.read_csv('device_fingerprints.csv')
merchant_risk_scores = pd.read_csv('merchant_risk_scores.csv')
historical_fraud = pd.read_csv('historical_fraud.csv')
ip_geolocation = pd.read_csv('ip_geolocation.csv')

# Parse timestamps
transactions['timestamp'] = pd.to_datetime(transactions['timestamp'])
transactions['date'] = transactions['timestamp'].dt.date
transactions['hour'] = transactions['timestamp'].dt.hour
transactions['minute'] = transactions['timestamp'].dt.minute
transactions['day_of_week'] = transactions['timestamp'].dt.dayofweek
transactions['is_weekend'] = transactions['day_of_week'].isin([5, 6]).astype(int)
transactions['is_night'] = transactions['hour'].between(0, 6).astype(int)

# Enrich with user profile data
transactions_enriched = pd.merge(
    transactions,
    user_profiles[['user_id', 'account_age_days', 'verification_level',
                   'avg_transaction_amount', 'typical_login_hour',
                   'home_country', 'risk_tier']],
    on='user_id',
    how='left'
)

# Add device fingerprint risk
transactions_enriched = pd.merge(
    transactions_enriched,
    device_fingerprints[['device_id', 'device_trust_score', 'is_known_device',
                         'browser_anomaly_score', 'last_seen_country']],
    on='device_id',
    how='left'
)

# Add merchant risk scores
transactions_enriched = pd.merge(
    transactions_enriched,
    merchant_risk_scores[['merchant_id', 'merchant_risk_score',
                          'chargeback_rate', 'merchant_category']],
    on='merchant_id',
    how='left'
)

# Add IP geolocation
transactions_enriched = pd.merge(
    transactions_enriched,
    ip_geolocation[['ip_address', 'ip_country', 'ip_city',
                    'is_vpn', 'is_tor', 'ip_risk_score']],
    on='ip_address',
    how='left'
)

# Calculate velocity features - transactions per user in last N minutes
transactions_enriched = transactions_enriched.sort_values(['user_id', 'timestamp'])

# Rolling window aggregations per user
user_velocity = transactions_enriched.groupby('user_id').agg({
    'transaction_id': 'count',
    'amount': ['sum', 'mean', 'std', 'max'],
    'merchant_id': 'nunique',
    'ip_address': 'nunique',
    'device_id': 'nunique'
}).reset_index()
user_velocity.columns = ['user_id', 'tx_count_session', 'total_amount_session',
                         'avg_amount_session', 'std_amount_session', 'max_amount_session',
                         'unique_merchants', 'unique_ips', 'unique_devices']

transactions_enriched = pd.merge(
    transactions_enriched,
    user_velocity,
    on='user_id',
    how='left'
)

# Calculate deviation from user's typical behavior
transactions_enriched['amount_deviation'] = (
    (transactions_enriched['amount'] - transactions_enriched['avg_transaction_amount']) /
    transactions_enriched['avg_transaction_amount'].replace(0, 1)
)

transactions_enriched['hour_deviation'] = abs(
    transactions_enriched['hour'] - transactions_enriched['typical_login_hour']
)

# Geographic anomaly detection
transactions_enriched['country_mismatch'] = (
    transactions_enriched['ip_country'] != transactions_enriched['home_country']
).astype(int)

transactions_enriched['device_country_mismatch'] = (
    transactions_enriched['ip_country'] != transactions_enriched['last_seen_country']
).astype(int)

# Composite risk score calculation
transactions_enriched['composite_risk_score'] = (
    transactions_enriched['ip_risk_score'] * 0.2 +
    transactions_enriched['merchant_risk_score'] * 0.15 +
    (1 - transactions_enriched['device_trust_score']) * 0.2 +
    transactions_enriched['amount_deviation'].clip(0, 5) * 0.15 +
    transactions_enriched['country_mismatch'] * 0.15 +
    transactions_enriched['is_vpn'] * 0.1 +
    transactions_enriched['is_tor'] * 0.05
)

# Flag high-risk transactions
transactions_enriched['is_high_risk'] = (
    transactions_enriched['composite_risk_score'] > 0.7
).astype(int)

# Join historical fraud patterns
fraud_patterns = historical_fraud.groupby('user_id').agg({
    'fraud_flag': 'sum',
    'transaction_id': 'count'
}).reset_index()
fraud_patterns.columns = ['user_id', 'historical_fraud_count', 'historical_tx_count']
fraud_patterns['historical_fraud_rate'] = (
    fraud_patterns['historical_fraud_count'] / fraud_patterns['historical_tx_count']
)

transactions_enriched = pd.merge(
    transactions_enriched,
    fraud_patterns[['user_id', 'historical_fraud_rate']],
    on='user_id',
    how='left'
)
transactions_enriched['historical_fraud_rate'] = transactions_enriched['historical_fraud_rate'].fillna(0)

# Final feature selection for ML model
ml_features = transactions_enriched[[
    'transaction_id', 'user_id', 'amount', 'amount_deviation',
    'hour_deviation', 'is_weekend', 'is_night',
    'device_trust_score', 'is_known_device', 'browser_anomaly_score',
    'merchant_risk_score', 'chargeback_rate',
    'ip_risk_score', 'is_vpn', 'is_tor',
    'country_mismatch', 'device_country_mismatch',
    'tx_count_session', 'unique_merchants', 'unique_ips', 'unique_devices',
    'composite_risk_score', 'historical_fraud_rate', 'is_high_risk'
]].copy()

ml_features.to_csv('fraud_detection_features.csv', index=False)
transactions_enriched.to_csv('transactions_enriched_full.csv', index=False)
"""

# =============================================================================
# 2. CUSTOMER 360 DATA LAKE INTEGRATION
# =============================================================================
CUSTOMER_360_PIPELINE = """
import pandas as pd
import numpy as np

# Load data from multiple source systems
crm_customers = pd.read_csv('crm_customers.csv')
ecommerce_users = pd.read_csv('ecommerce_users.csv')
mobile_app_users = pd.read_csv('mobile_app_users.csv')
call_center_interactions = pd.read_csv('call_center_interactions.csv')
email_campaigns = pd.read_csv('email_campaigns.csv')
web_analytics = pd.read_csv('web_analytics.csv')
social_media = pd.read_csv('social_media.csv')
loyalty_program = pd.read_csv('loyalty_program.csv')
support_tickets = pd.read_csv('support_tickets.csv')
nps_surveys = pd.read_csv('nps_surveys.csv')

# Standardize customer identifiers across systems
crm_customers['source'] = 'crm'
crm_customers['master_id'] = crm_customers['crm_id']

ecommerce_users['source'] = 'ecommerce'
ecommerce_users = pd.merge(
    ecommerce_users,
    crm_customers[['email', 'crm_id']],
    on='email',
    how='left'
)
ecommerce_users['master_id'] = ecommerce_users['crm_id'].fillna(
    'ECO_' + ecommerce_users['ecommerce_user_id'].astype(str)
)

mobile_app_users['source'] = 'mobile'
mobile_app_users = pd.merge(
    mobile_app_users,
    crm_customers[['phone', 'crm_id']],
    on='phone',
    how='left'
)
mobile_app_users['master_id'] = mobile_app_users['crm_id'].fillna(
    'MOB_' + mobile_app_users['app_user_id'].astype(str)
)

# Create unified customer profile
customer_base = crm_customers[['master_id', 'email', 'phone', 'first_name',
                               'last_name', 'date_of_birth', 'gender',
                               'address', 'city', 'state', 'country',
                               'customer_since']].copy()

# Aggregate e-commerce behavior
ecommerce_metrics = ecommerce_users.groupby('master_id').agg({
    'order_id': 'count',
    'order_total': ['sum', 'mean', 'max'],
    'items_purchased': 'sum',
    'last_order_date': 'max',
    'cart_abandonment_count': 'sum'
}).reset_index()
ecommerce_metrics.columns = ['master_id', 'ecom_order_count', 'ecom_total_spend',
                              'ecom_avg_order', 'ecom_max_order', 'ecom_items_total',
                              'ecom_last_order', 'ecom_cart_abandonments']

# Aggregate mobile app engagement
mobile_metrics = mobile_app_users.groupby('master_id').agg({
    'session_count': 'sum',
    'total_time_minutes': 'sum',
    'push_notifications_clicked': 'sum',
    'app_crashes': 'sum',
    'features_used': lambda x: len(set(','.join(x.dropna()).split(','))),
    'last_active_date': 'max'
}).reset_index()
mobile_metrics.columns = ['master_id', 'app_sessions', 'app_time_minutes',
                          'push_clicks', 'app_crashes', 'features_used_count',
                          'app_last_active']

# Aggregate call center interactions
call_metrics = call_center_interactions.groupby('master_id').agg({
    'call_id': 'count',
    'call_duration_seconds': ['sum', 'mean'],
    'issue_resolved': 'mean',
    'escalated': 'sum',
    'sentiment_score': 'mean'
}).reset_index()
call_metrics.columns = ['master_id', 'call_count', 'total_call_duration',
                        'avg_call_duration', 'resolution_rate',
                        'escalation_count', 'call_sentiment']

# Aggregate email engagement
email_metrics = email_campaigns.groupby('master_id').agg({
    'email_sent': 'sum',
    'email_opened': 'sum',
    'email_clicked': 'sum',
    'unsubscribed': 'max'
}).reset_index()
email_metrics['email_open_rate'] = email_metrics['email_opened'] / email_metrics['email_sent']
email_metrics['email_click_rate'] = email_metrics['email_clicked'] / email_metrics['email_opened'].replace(0, 1)

# Aggregate web analytics
web_metrics = web_analytics.groupby('master_id').agg({
    'page_views': 'sum',
    'unique_sessions': 'sum',
    'bounce_rate': 'mean',
    'avg_session_duration': 'mean',
    'conversion_events': 'sum'
}).reset_index()

# Aggregate loyalty program data
loyalty_metrics = loyalty_program.groupby('master_id').agg({
    'points_earned': 'sum',
    'points_redeemed': 'sum',
    'tier_level': 'max',
    'referrals_made': 'sum'
}).reset_index()
loyalty_metrics['points_balance'] = loyalty_metrics['points_earned'] - loyalty_metrics['points_redeemed']

# Aggregate support tickets
support_metrics = support_tickets.groupby('master_id').agg({
    'ticket_id': 'count',
    'resolution_time_hours': 'mean',
    'satisfaction_rating': 'mean',
    'ticket_reopened': 'sum'
}).reset_index()
support_metrics.columns = ['master_id', 'ticket_count', 'avg_resolution_time',
                           'support_satisfaction', 'tickets_reopened']

# Aggregate NPS surveys
nps_metrics = nps_surveys.groupby('master_id').agg({
    'nps_score': 'mean',
    'survey_id': 'count',
    'would_recommend': 'mean'
}).reset_index()
nps_metrics.columns = ['master_id', 'avg_nps_score', 'surveys_completed', 'recommend_rate']

# Merge all metrics into unified customer 360 view
customer_360 = customer_base.copy()

for metrics_df in [ecommerce_metrics, mobile_metrics, call_metrics,
                   email_metrics, web_metrics, loyalty_metrics,
                   support_metrics, nps_metrics]:
    customer_360 = pd.merge(customer_360, metrics_df, on='master_id', how='left')

# Fill missing values appropriately
numeric_cols = customer_360.select_dtypes(include=[np.number]).columns
customer_360[numeric_cols] = customer_360[numeric_cols].fillna(0)

# Calculate derived metrics
customer_360['total_interactions'] = (
    customer_360['ecom_order_count'] +
    customer_360['app_sessions'] +
    customer_360['call_count'] +
    customer_360['ticket_count']
)

customer_360['digital_engagement_score'] = (
    customer_360['app_sessions'] * 0.3 +
    customer_360['email_open_rate'] * 20 +
    customer_360['page_views'] * 0.1 +
    customer_360['push_clicks'] * 0.5
).clip(0, 100)

customer_360['customer_health_score'] = (
    customer_360['avg_nps_score'] / 10 * 25 +
    customer_360['resolution_rate'] * 25 +
    customer_360['support_satisfaction'] / 5 * 25 +
    (1 - customer_360['escalation_count'].clip(0, 5) / 5) * 25
)

# Customer segmentation
customer_360['value_segment'] = pd.cut(
    customer_360['ecom_total_spend'],
    bins=[-np.inf, 100, 500, 2000, 10000, np.inf],
    labels=['Dormant', 'Bronze', 'Silver', 'Gold', 'Platinum']
)

customer_360['engagement_segment'] = pd.cut(
    customer_360['digital_engagement_score'],
    bins=[-np.inf, 20, 40, 60, 80, np.inf],
    labels=['Inactive', 'Low', 'Medium', 'High', 'Power User']
)

# Calculate churn risk
customer_360['days_since_activity'] = (
    pd.to_datetime('today') - pd.to_datetime(customer_360['ecom_last_order'])
).dt.days.fillna(999)

customer_360['churn_risk_score'] = (
    customer_360['days_since_activity'] / 365 * 30 +
    (1 - customer_360['email_open_rate'].fillna(0)) * 20 +
    customer_360['tickets_reopened'] * 10 +
    (10 - customer_360['avg_nps_score'].fillna(5)) * 4
).clip(0, 100)

# Save outputs
customer_360.to_csv('customer_360_unified.csv', index=False)
"""

# =============================================================================
# 3. SUPPLY CHAIN OPTIMIZATION & DEMAND FORECASTING
# =============================================================================
SUPPLY_CHAIN_PIPELINE = """
import pandas as pd
import numpy as np

# Load supply chain data
sales_history = pd.read_csv('sales_history.csv')
inventory_levels = pd.read_csv('inventory_levels.csv')
supplier_data = pd.read_csv('supplier_data.csv')
warehouse_locations = pd.read_csv('warehouse_locations.csv')
shipping_costs = pd.read_csv('shipping_costs.csv')
product_catalog = pd.read_csv('product_catalog.csv')
promotions_calendar = pd.read_csv('promotions_calendar.csv')
weather_data = pd.read_csv('weather_data.csv')
economic_indicators = pd.read_csv('economic_indicators.csv')

# Parse dates
sales_history['sale_date'] = pd.to_datetime(sales_history['sale_date'])
sales_history['year'] = sales_history['sale_date'].dt.year
sales_history['month'] = sales_history['sale_date'].dt.month
sales_history['week'] = sales_history['sale_date'].dt.isocalendar().week
sales_history['day_of_week'] = sales_history['sale_date'].dt.dayofweek
sales_history['is_weekend'] = sales_history['day_of_week'].isin([5, 6]).astype(int)

# Enrich sales with product info
sales_enriched = pd.merge(
    sales_history,
    product_catalog[['product_id', 'category', 'subcategory', 'brand',
                     'unit_cost', 'weight_kg', 'is_perishable', 'shelf_life_days']],
    on='product_id',
    how='left'
)

# Add promotion flags
promotions_calendar['promo_date'] = pd.to_datetime(promotions_calendar['promo_date'])
sales_enriched = pd.merge(
    sales_enriched,
    promotions_calendar[['product_id', 'promo_date', 'discount_pct', 'promo_type']],
    left_on=['product_id', 'sale_date'],
    right_on=['product_id', 'promo_date'],
    how='left'
)
sales_enriched['is_promotion'] = sales_enriched['discount_pct'].notna().astype(int)
sales_enriched['discount_pct'] = sales_enriched['discount_pct'].fillna(0)

# Add weather impact
weather_data['date'] = pd.to_datetime(weather_data['date'])
sales_enriched = pd.merge(
    sales_enriched,
    weather_data[['date', 'region', 'temperature', 'precipitation', 'weather_condition']],
    left_on=['sale_date', 'region'],
    right_on=['date', 'region'],
    how='left'
)

# Calculate time-based aggregations for demand patterns
daily_demand = sales_enriched.groupby(['product_id', 'warehouse_id', 'sale_date']).agg({
    'quantity': 'sum',
    'revenue': 'sum',
    'is_promotion': 'max',
    'temperature': 'mean'
}).reset_index()

# Calculate rolling averages for demand forecasting
daily_demand = daily_demand.sort_values(['product_id', 'warehouse_id', 'sale_date'])
daily_demand['demand_7d_avg'] = daily_demand.groupby(['product_id', 'warehouse_id'])['quantity'].transform(
    lambda x: x.rolling(7, min_periods=1).mean()
)
daily_demand['demand_30d_avg'] = daily_demand.groupby(['product_id', 'warehouse_id'])['quantity'].transform(
    lambda x: x.rolling(30, min_periods=1).mean()
)
daily_demand['demand_90d_avg'] = daily_demand.groupby(['product_id', 'warehouse_id'])['quantity'].transform(
    lambda x: x.rolling(90, min_periods=1).mean()
)

# Calculate demand volatility
daily_demand['demand_7d_std'] = daily_demand.groupby(['product_id', 'warehouse_id'])['quantity'].transform(
    lambda x: x.rolling(7, min_periods=1).std()
)
daily_demand['demand_coefficient_variation'] = (
    daily_demand['demand_7d_std'] / daily_demand['demand_7d_avg'].replace(0, 1)
)

# Seasonality detection
monthly_patterns = sales_enriched.groupby(['product_id', 'month']).agg({
    'quantity': 'mean'
}).reset_index()
monthly_patterns.columns = ['product_id', 'month', 'monthly_avg_demand']

yearly_avg = monthly_patterns.groupby('product_id')['monthly_avg_demand'].transform('mean')
monthly_patterns['seasonality_index'] = monthly_patterns['monthly_avg_demand'] / yearly_avg

# Join current inventory levels
inventory_current = inventory_levels.groupby(['product_id', 'warehouse_id']).agg({
    'quantity_on_hand': 'sum',
    'quantity_reserved': 'sum',
    'quantity_in_transit': 'sum',
    'last_restock_date': 'max'
}).reset_index()
inventory_current['available_inventory'] = (
    inventory_current['quantity_on_hand'] - inventory_current['quantity_reserved']
)

# Calculate days of supply
inventory_analysis = pd.merge(
    inventory_current,
    daily_demand.groupby(['product_id', 'warehouse_id']).agg({
        'demand_30d_avg': 'last'
    }).reset_index(),
    on=['product_id', 'warehouse_id'],
    how='left'
)
inventory_analysis['days_of_supply'] = (
    inventory_analysis['available_inventory'] /
    inventory_analysis['demand_30d_avg'].replace(0, 0.1)
)

# Add supplier lead times
inventory_analysis = pd.merge(
    inventory_analysis,
    supplier_data[['product_id', 'supplier_id', 'lead_time_days',
                   'min_order_qty', 'unit_cost', 'reliability_score']],
    on='product_id',
    how='left'
)

# Calculate reorder points with safety stock
inventory_analysis['safety_stock'] = (
    inventory_analysis['demand_30d_avg'] *
    inventory_analysis['lead_time_days'] * 0.5  # Safety factor
)
inventory_analysis['reorder_point'] = (
    inventory_analysis['demand_30d_avg'] * inventory_analysis['lead_time_days'] +
    inventory_analysis['safety_stock']
)

# Flag items needing reorder
inventory_analysis['needs_reorder'] = (
    inventory_analysis['available_inventory'] < inventory_analysis['reorder_point']
).astype(int)

# Calculate optimal order quantity (EOQ approximation)
inventory_analysis['holding_cost_annual'] = inventory_analysis['unit_cost'] * 0.25
inventory_analysis['order_cost'] = 50  # Fixed ordering cost
inventory_analysis['annual_demand'] = inventory_analysis['demand_30d_avg'] * 12 * 30

inventory_analysis['economic_order_qty'] = np.sqrt(
    2 * inventory_analysis['annual_demand'] * inventory_analysis['order_cost'] /
    inventory_analysis['holding_cost_annual'].replace(0, 1)
)

# Calculate shipping optimization
shipping_analysis = pd.merge(
    inventory_analysis,
    warehouse_locations[['warehouse_id', 'latitude', 'longitude', 'capacity_units']],
    on='warehouse_id',
    how='left'
)

# Add shipping costs
shipping_analysis = pd.merge(
    shipping_analysis,
    shipping_costs,
    on='warehouse_id',
    how='left'
)

# Calculate total landed cost
shipping_analysis['landed_cost'] = (
    shipping_analysis['unit_cost'] +
    shipping_analysis['shipping_cost_per_unit'] +
    shipping_analysis['handling_cost']
)

# Identify stock-out risk
shipping_analysis['stockout_risk'] = np.where(
    shipping_analysis['days_of_supply'] < shipping_analysis['lead_time_days'],
    'High',
    np.where(
        shipping_analysis['days_of_supply'] < shipping_analysis['lead_time_days'] * 1.5,
        'Medium',
        'Low'
    )
)

# Save outputs
daily_demand.to_csv('demand_forecast_features.csv', index=False)
inventory_analysis.to_csv('inventory_optimization.csv', index=False)
shipping_analysis.to_csv('supply_chain_analysis.csv', index=False)
monthly_patterns.to_csv('seasonality_patterns.csv', index=False)
"""

# =============================================================================
# 4. MULTI-TOUCH ATTRIBUTION & MARKETING MIX MODELING
# =============================================================================
MARKETING_ATTRIBUTION_PIPELINE = """
import pandas as pd
import numpy as np

# Load marketing data
touchpoints = pd.read_csv('touchpoints.csv')
conversions = pd.read_csv('conversions.csv')
ad_spend = pd.read_csv('ad_spend.csv')
channel_costs = pd.read_csv('channel_costs.csv')
campaign_metadata = pd.read_csv('campaign_metadata.csv')
customer_journeys = pd.read_csv('customer_journeys.csv')
organic_traffic = pd.read_csv('organic_traffic.csv')
offline_media = pd.read_csv('offline_media.csv')

# Parse timestamps
touchpoints['touchpoint_time'] = pd.to_datetime(touchpoints['touchpoint_time'])
conversions['conversion_time'] = pd.to_datetime(conversions['conversion_time'])

# Create customer journey sequences
touchpoints_sorted = touchpoints.sort_values(['customer_id', 'touchpoint_time'])

# Assign journey IDs (new journey if gap > 30 days)
touchpoints_sorted['time_since_last'] = touchpoints_sorted.groupby('customer_id')['touchpoint_time'].diff()
touchpoints_sorted['new_journey'] = (
    touchpoints_sorted['time_since_last'] > pd.Timedelta(days=30)
).fillna(True).astype(int)
touchpoints_sorted['journey_id'] = touchpoints_sorted.groupby('customer_id')['new_journey'].cumsum()

# Create journey-level aggregations
journey_touchpoints = touchpoints_sorted.groupby(['customer_id', 'journey_id']).agg({
    'touchpoint_id': 'count',
    'channel': lambda x: ' > '.join(x),
    'campaign_id': lambda x: list(x.unique()),
    'touchpoint_time': ['min', 'max'],
    'cost': 'sum'
}).reset_index()
journey_touchpoints.columns = ['customer_id', 'journey_id', 'touchpoint_count',
                                'channel_path', 'campaigns_touched',
                                'journey_start', 'journey_end', 'journey_cost']

# Calculate journey duration
journey_touchpoints['journey_duration_days'] = (
    journey_touchpoints['journey_end'] - journey_touchpoints['journey_start']
).dt.total_seconds() / 86400

# Join with conversions
journey_conversions = pd.merge(
    journey_touchpoints,
    conversions[['customer_id', 'conversion_time', 'conversion_value', 'product_category']],
    on='customer_id',
    how='left'
)

# Filter to conversions within journey window
journey_conversions['converted'] = (
    (journey_conversions['conversion_time'] >= journey_conversions['journey_start']) &
    (journey_conversions['conversion_time'] <= journey_conversions['journey_end'] + pd.Timedelta(days=7))
).astype(int)

journey_conversions['conversion_value'] = np.where(
    journey_conversions['converted'] == 1,
    journey_conversions['conversion_value'],
    0
)

# Calculate attribution models

# 1. First-touch attribution
touchpoints_sorted['is_first_touch'] = touchpoints_sorted.groupby(
    ['customer_id', 'journey_id']
).cumcount() == 0

first_touch = touchpoints_sorted[touchpoints_sorted['is_first_touch']].copy()
first_touch_attribution = first_touch.groupby('channel').agg({
    'touchpoint_id': 'count',
    'cost': 'sum'
}).reset_index()
first_touch_attribution.columns = ['channel', 'first_touch_count', 'first_touch_cost']

# 2. Last-touch attribution
last_touch = touchpoints_sorted.groupby(['customer_id', 'journey_id']).last().reset_index()
last_touch_attribution = last_touch.groupby('channel').agg({
    'touchpoint_id': 'count',
    'cost': 'sum'
}).reset_index()
last_touch_attribution.columns = ['channel', 'last_touch_count', 'last_touch_cost']

# 3. Linear attribution (equal credit to all touchpoints)
journey_conversions_exploded = journey_conversions.explode('campaigns_touched')
journey_conversions_exploded['linear_credit'] = (
    journey_conversions_exploded['conversion_value'] /
    journey_conversions_exploded['touchpoint_count']
)

# 4. Time-decay attribution
touchpoints_with_conversion = pd.merge(
    touchpoints_sorted,
    journey_conversions[['customer_id', 'journey_id', 'conversion_time', 'conversion_value', 'converted']],
    on=['customer_id', 'journey_id'],
    how='left'
)

touchpoints_with_conversion['days_to_conversion'] = (
    touchpoints_with_conversion['conversion_time'] - touchpoints_with_conversion['touchpoint_time']
).dt.total_seconds() / 86400

# Exponential decay weight (half-life = 7 days)
touchpoints_with_conversion['decay_weight'] = np.exp(
    -touchpoints_with_conversion['days_to_conversion'] / 7
)

# Normalize weights within journey
touchpoints_with_conversion['weight_sum'] = touchpoints_with_conversion.groupby(
    ['customer_id', 'journey_id']
)['decay_weight'].transform('sum')

touchpoints_with_conversion['time_decay_credit'] = (
    touchpoints_with_conversion['decay_weight'] /
    touchpoints_with_conversion['weight_sum'].replace(0, 1) *
    touchpoints_with_conversion['conversion_value']
)

# 5. Position-based attribution (40% first, 40% last, 20% middle)
touchpoints_with_conversion['position'] = touchpoints_with_conversion.groupby(
    ['customer_id', 'journey_id']
).cumcount() + 1

touchpoints_with_conversion['total_positions'] = touchpoints_with_conversion.groupby(
    ['customer_id', 'journey_id']
)['position'].transform('max')

touchpoints_with_conversion['position_weight'] = np.where(
    touchpoints_with_conversion['position'] == 1,
    0.4,
    np.where(
        touchpoints_with_conversion['position'] == touchpoints_with_conversion['total_positions'],
        0.4,
        0.2 / (touchpoints_with_conversion['total_positions'] - 2).replace(0, 1)
    )
)

touchpoints_with_conversion['position_based_credit'] = (
    touchpoints_with_conversion['position_weight'] *
    touchpoints_with_conversion['conversion_value']
)

# Aggregate attribution by channel
channel_attribution = touchpoints_with_conversion.groupby('channel').agg({
    'touchpoint_id': 'count',
    'cost': 'sum',
    'linear_credit': 'sum',
    'time_decay_credit': 'sum',
    'position_based_credit': 'sum'
}).reset_index()

channel_attribution = pd.merge(channel_attribution, first_touch_attribution, on='channel', how='left')
channel_attribution = pd.merge(channel_attribution, last_touch_attribution, on='channel', how='left')

# Calculate ROI by attribution model
channel_attribution['roi_linear'] = (
    channel_attribution['linear_credit'] - channel_attribution['cost']
) / channel_attribution['cost'].replace(0, 1)

channel_attribution['roi_time_decay'] = (
    channel_attribution['time_decay_credit'] - channel_attribution['cost']
) / channel_attribution['cost'].replace(0, 1)

channel_attribution['roi_position'] = (
    channel_attribution['position_based_credit'] - channel_attribution['cost']
) / channel_attribution['cost'].replace(0, 1)

# Marketing mix modeling aggregations
daily_spend = ad_spend.groupby(['date', 'channel']).agg({
    'spend': 'sum',
    'impressions': 'sum',
    'clicks': 'sum'
}).reset_index()

daily_spend['cpm'] = daily_spend['spend'] / daily_spend['impressions'] * 1000
daily_spend['cpc'] = daily_spend['spend'] / daily_spend['clicks'].replace(0, 1)
daily_spend['ctr'] = daily_spend['clicks'] / daily_spend['impressions'].replace(0, 1)

# Add adstock transformation (carryover effect)
daily_spend = daily_spend.sort_values(['channel', 'date'])
daily_spend['spend_adstock'] = daily_spend.groupby('channel')['spend'].transform(
    lambda x: x.ewm(halflife=7).mean()
)

# Save outputs
journey_touchpoints.to_csv('customer_journeys_analyzed.csv', index=False)
channel_attribution.to_csv('channel_attribution_models.csv', index=False)
touchpoints_with_conversion.to_csv('touchpoint_attribution_detail.csv', index=False)
daily_spend.to_csv('marketing_mix_features.csv', index=False)
"""

# =============================================================================
# 5. IOT SENSOR DATA PROCESSING & PREDICTIVE MAINTENANCE
# =============================================================================
IOT_PREDICTIVE_MAINTENANCE_PIPELINE = """
import pandas as pd
import numpy as np

# Load IoT sensor data
sensor_readings = pd.read_csv('sensor_readings.csv')
equipment_registry = pd.read_csv('equipment_registry.csv')
maintenance_history = pd.read_csv('maintenance_history.csv')
failure_logs = pd.read_csv('failure_logs.csv')
operating_conditions = pd.read_csv('operating_conditions.csv')
parts_inventory = pd.read_csv('parts_inventory.csv')
technician_schedules = pd.read_csv('technician_schedules.csv')

# Parse timestamps
sensor_readings['reading_time'] = pd.to_datetime(sensor_readings['reading_time'])
maintenance_history['maintenance_date'] = pd.to_datetime(maintenance_history['maintenance_date'])
failure_logs['failure_time'] = pd.to_datetime(failure_logs['failure_time'])

# Clean sensor data - remove outliers
sensor_readings = sensor_readings.sort_values(['equipment_id', 'sensor_type', 'reading_time'])

# Calculate rolling statistics per sensor
sensor_readings['value_1h_mean'] = sensor_readings.groupby(
    ['equipment_id', 'sensor_type']
)['sensor_value'].transform(lambda x: x.rolling('1H', on=sensor_readings['reading_time']).mean())

sensor_readings['value_1h_std'] = sensor_readings.groupby(
    ['equipment_id', 'sensor_type']
)['sensor_value'].transform(lambda x: x.rolling('1H', on=sensor_readings['reading_time']).std())

sensor_readings['value_24h_mean'] = sensor_readings.groupby(
    ['equipment_id', 'sensor_type']
)['sensor_value'].transform(lambda x: x.rolling('24H', on=sensor_readings['reading_time']).mean())

sensor_readings['value_24h_max'] = sensor_readings.groupby(
    ['equipment_id', 'sensor_type']
)['sensor_value'].transform(lambda x: x.rolling('24H', on=sensor_readings['reading_time']).max())

sensor_readings['value_24h_min'] = sensor_readings.groupby(
    ['equipment_id', 'sensor_type']
)['sensor_value'].transform(lambda x: x.rolling('24H', on=sensor_readings['reading_time']).min())

# Calculate rate of change
sensor_readings['value_diff'] = sensor_readings.groupby(
    ['equipment_id', 'sensor_type']
)['sensor_value'].diff()

sensor_readings['value_pct_change'] = sensor_readings.groupby(
    ['equipment_id', 'sensor_type']
)['sensor_value'].pct_change()

# Detect anomalies using z-score
sensor_readings['z_score'] = (
    (sensor_readings['sensor_value'] - sensor_readings['value_24h_mean']) /
    sensor_readings['value_1h_std'].replace(0, 1)
)
sensor_readings['is_anomaly'] = (abs(sensor_readings['z_score']) > 3).astype(int)

# Pivot sensor types to create feature vectors
sensor_features = sensor_readings.pivot_table(
    index=['equipment_id', 'reading_time'],
    columns='sensor_type',
    values=['sensor_value', 'value_1h_mean', 'value_24h_max', 'z_score', 'is_anomaly'],
    aggfunc='first'
).reset_index()

# Flatten column names
sensor_features.columns = ['_'.join(str(c) for c in col).strip('_')
                           for col in sensor_features.columns]

# Add equipment metadata
sensor_features = pd.merge(
    sensor_features,
    equipment_registry[['equipment_id', 'equipment_type', 'manufacturer',
                        'installation_date', 'rated_capacity', 'location']],
    on='equipment_id',
    how='left'
)

# Calculate equipment age
sensor_features['installation_date'] = pd.to_datetime(sensor_features['installation_date'])
sensor_features['equipment_age_days'] = (
    sensor_features['reading_time'] - sensor_features['installation_date']
).dt.days

# Add operating conditions
operating_conditions['condition_time'] = pd.to_datetime(operating_conditions['condition_time'])
sensor_features = pd.merge_asof(
    sensor_features.sort_values('reading_time'),
    operating_conditions.sort_values('condition_time'),
    left_on='reading_time',
    right_on='condition_time',
    by='equipment_id',
    direction='backward'
)

# Calculate maintenance history features
maintenance_agg = maintenance_history.groupby('equipment_id').agg({
    'maintenance_id': 'count',
    'maintenance_date': 'max',
    'maintenance_cost': 'sum',
    'downtime_hours': 'sum'
}).reset_index()
maintenance_agg.columns = ['equipment_id', 'total_maintenance_count',
                           'last_maintenance_date', 'total_maintenance_cost',
                           'total_downtime_hours']

sensor_features = pd.merge(
    sensor_features,
    maintenance_agg,
    on='equipment_id',
    how='left'
)

# Calculate days since last maintenance
sensor_features['last_maintenance_date'] = pd.to_datetime(sensor_features['last_maintenance_date'])
sensor_features['days_since_maintenance'] = (
    sensor_features['reading_time'] - sensor_features['last_maintenance_date']
).dt.days

# Calculate failure history features
failure_agg = failure_logs.groupby('equipment_id').agg({
    'failure_id': 'count',
    'failure_time': 'max',
    'failure_severity': 'mean',
    'repair_time_hours': 'sum'
}).reset_index()
failure_agg.columns = ['equipment_id', 'total_failures', 'last_failure_date',
                       'avg_failure_severity', 'total_repair_hours']

sensor_features = pd.merge(
    sensor_features,
    failure_agg,
    on='equipment_id',
    how='left'
)

# Create target variable: failure within next N days
failure_logs_sorted = failure_logs.sort_values(['equipment_id', 'failure_time'])
sensor_features = pd.merge_asof(
    sensor_features.sort_values('reading_time'),
    failure_logs_sorted[['equipment_id', 'failure_time']].rename(
        columns={'failure_time': 'next_failure_time'}
    ),
    left_on='reading_time',
    right_on='next_failure_time',
    by='equipment_id',
    direction='forward'
)

sensor_features['days_to_failure'] = (
    sensor_features['next_failure_time'] - sensor_features['reading_time']
).dt.total_seconds() / 86400

sensor_features['failure_within_7d'] = (sensor_features['days_to_failure'] <= 7).astype(int)
sensor_features['failure_within_30d'] = (sensor_features['days_to_failure'] <= 30).astype(int)

# Calculate health score
sensor_features['anomaly_count_24h'] = sensor_features.groupby('equipment_id')['is_anomaly_temperature'].transform(
    lambda x: x.rolling('24H', on=sensor_features['reading_time']).sum()
)

sensor_features['health_score'] = 100 - (
    sensor_features['anomaly_count_24h'] * 5 +
    sensor_features['total_failures'].fillna(0) * 2 +
    np.minimum(sensor_features['days_since_maintenance'].fillna(0) / 365, 1) * 20
).clip(0, 100)

# Prioritize maintenance
sensor_features['maintenance_priority'] = np.where(
    sensor_features['health_score'] < 50, 'Critical',
    np.where(sensor_features['health_score'] < 70, 'High',
    np.where(sensor_features['health_score'] < 85, 'Medium', 'Low'))
)

# Join parts availability
parts_available = parts_inventory.groupby('equipment_type').agg({
    'part_id': 'count',
    'quantity_available': 'sum',
    'lead_time_days': 'mean'
}).reset_index()
parts_available.columns = ['equipment_type', 'part_types_available',
                           'total_parts_stock', 'avg_part_lead_time']

sensor_features = pd.merge(
    sensor_features,
    parts_available,
    on='equipment_type',
    how='left'
)

# Save outputs
sensor_features.to_csv('predictive_maintenance_features.csv', index=False)

# Create maintenance schedule recommendations
maintenance_schedule = sensor_features[sensor_features['maintenance_priority'].isin(['Critical', 'High'])].groupby(
    'equipment_id'
).agg({
    'health_score': 'min',
    'maintenance_priority': 'first',
    'days_since_maintenance': 'max',
    'reading_time': 'max'
}).reset_index()

maintenance_schedule.columns = ['equipment_id', 'current_health', 'priority',
                                'days_since_last_maintenance', 'last_reading']
maintenance_schedule.to_csv('maintenance_schedule_recommendations.csv', index=False)
"""

# =============================================================================
# 6. GENOMIC DATA PROCESSING & VARIANT ANALYSIS
# =============================================================================
GENOMIC_ANALYSIS_PIPELINE = """
import pandas as pd
import numpy as np

# Load genomic data
variants = pd.read_csv('variants.csv')
samples = pd.read_csv('samples.csv')
gene_annotations = pd.read_csv('gene_annotations.csv')
clinical_data = pd.read_csv('clinical_data.csv')
pathway_mappings = pd.read_csv('pathway_mappings.csv')
population_frequencies = pd.read_csv('population_frequencies.csv')
functional_predictions = pd.read_csv('functional_predictions.csv')
disease_associations = pd.read_csv('disease_associations.csv')

# Standardize variant identifiers
variants['variant_id'] = (
    variants['chromosome'].astype(str) + ':' +
    variants['position'].astype(str) + ':' +
    variants['reference'] + '>' + variants['alternate']
)

# Calculate variant quality metrics
variants['quality_pass'] = (
    (variants['quality_score'] >= 30) &
    (variants['read_depth'] >= 10) &
    (variants['allele_frequency'] >= 0.2)
).astype(int)

# Filter high-quality variants
high_quality_variants = variants[variants['quality_pass'] == 1].copy()

# Annotate with gene information
high_quality_variants = pd.merge(
    high_quality_variants,
    gene_annotations[['chromosome', 'start_position', 'end_position',
                      'gene_symbol', 'gene_type', 'strand']],
    on='chromosome',
    how='left'
)

# Filter to variants within gene boundaries
high_quality_variants = high_quality_variants[
    (high_quality_variants['position'] >= high_quality_variants['start_position']) &
    (high_quality_variants['position'] <= high_quality_variants['end_position'])
]

# Add functional impact predictions
high_quality_variants = pd.merge(
    high_quality_variants,
    functional_predictions[['variant_id', 'sift_score', 'polyphen_score',
                            'cadd_score', 'predicted_impact']],
    on='variant_id',
    how='left'
)

# Classify variant impact
high_quality_variants['impact_category'] = np.where(
    (high_quality_variants['sift_score'] < 0.05) | (high_quality_variants['polyphen_score'] > 0.85),
    'Damaging',
    np.where(
        (high_quality_variants['sift_score'] < 0.1) | (high_quality_variants['polyphen_score'] > 0.5),
        'Possibly_Damaging',
        'Benign'
    )
)

# Add population allele frequencies
high_quality_variants = pd.merge(
    high_quality_variants,
    population_frequencies[['variant_id', 'gnomad_af', 'gnomad_af_eas',
                            'gnomad_af_eur', 'gnomad_af_afr']],
    on='variant_id',
    how='left'
)

# Flag rare variants (MAF < 1%)
high_quality_variants['is_rare'] = (high_quality_variants['gnomad_af'] < 0.01).astype(int)
high_quality_variants['is_ultra_rare'] = (high_quality_variants['gnomad_af'] < 0.001).astype(int)

# Add disease associations
high_quality_variants = pd.merge(
    high_quality_variants,
    disease_associations[['gene_symbol', 'disease_name', 'inheritance_pattern',
                          'clinical_significance']],
    on='gene_symbol',
    how='left'
)

# Calculate per-sample variant burden
sample_burden = high_quality_variants.groupby('sample_id').agg({
    'variant_id': 'count',
    'is_rare': 'sum',
    'impact_category': lambda x: (x == 'Damaging').sum()
}).reset_index()
sample_burden.columns = ['sample_id', 'total_variants', 'rare_variants', 'damaging_variants']

# Add clinical phenotype data
sample_burden = pd.merge(
    sample_burden,
    samples[['sample_id', 'patient_id', 'tissue_type', 'collection_date']],
    on='sample_id',
    how='left'
)

sample_burden = pd.merge(
    sample_burden,
    clinical_data[['patient_id', 'diagnosis', 'age_at_diagnosis',
                   'sex', 'ethnicity', 'family_history']],
    on='patient_id',
    how='left'
)

# Calculate gene-level burden
gene_burden = high_quality_variants.groupby(['sample_id', 'gene_symbol']).agg({
    'variant_id': 'count',
    'is_rare': 'sum',
    'impact_category': lambda x: (x == 'Damaging').sum(),
    'cadd_score': 'max'
}).reset_index()
gene_burden.columns = ['sample_id', 'gene_symbol', 'variants_in_gene',
                       'rare_in_gene', 'damaging_in_gene', 'max_cadd']

# Add pathway information
gene_burden = pd.merge(
    gene_burden,
    pathway_mappings[['gene_symbol', 'pathway_id', 'pathway_name']],
    on='gene_symbol',
    how='left'
)

# Calculate pathway-level burden
pathway_burden = gene_burden.groupby(['sample_id', 'pathway_id', 'pathway_name']).agg({
    'gene_symbol': 'nunique',
    'variants_in_gene': 'sum',
    'damaging_in_gene': 'sum',
    'max_cadd': 'max'
}).reset_index()
pathway_burden.columns = ['sample_id', 'pathway_id', 'pathway_name',
                          'genes_affected', 'pathway_variants',
                          'pathway_damaging', 'pathway_max_cadd']

# Identify potentially pathogenic variants
pathogenic_candidates = high_quality_variants[
    (high_quality_variants['impact_category'] == 'Damaging') &
    (high_quality_variants['is_rare'] == 1) &
    (high_quality_variants['clinical_significance'].isin(['Pathogenic', 'Likely_Pathogenic']).fillna(False))
].copy()

# Create variant report
variant_report = pathogenic_candidates.groupby(['sample_id', 'gene_symbol']).agg({
    'variant_id': lambda x: '; '.join(x),
    'disease_name': 'first',
    'inheritance_pattern': 'first',
    'cadd_score': 'max'
}).reset_index()

# Save outputs
high_quality_variants.to_csv('annotated_variants.csv', index=False)
sample_burden.to_csv('sample_variant_burden.csv', index=False)
gene_burden.to_csv('gene_level_burden.csv', index=False)
pathway_burden.to_csv('pathway_analysis.csv', index=False)
variant_report.to_csv('pathogenic_variant_report.csv', index=False)
"""

# =============================================================================
# 7. REAL-TIME CLICKSTREAM & SESSION ANALYSIS
# =============================================================================
CLICKSTREAM_ANALYSIS_PIPELINE = """
import pandas as pd
import numpy as np

# Load clickstream data
page_views = pd.read_csv('page_views.csv')
click_events = pd.read_csv('click_events.csv')
form_submissions = pd.read_csv('form_submissions.csv')
search_queries = pd.read_csv('search_queries.csv')
product_impressions = pd.read_csv('product_impressions.csv')
cart_events = pd.read_csv('cart_events.csv')
user_agents = pd.read_csv('user_agents.csv')
geo_locations = pd.read_csv('geo_locations.csv')

# Parse timestamps
page_views['timestamp'] = pd.to_datetime(page_views['timestamp'])
click_events['timestamp'] = pd.to_datetime(click_events['timestamp'])

# Combine all events
page_views['event_type'] = 'page_view'
click_events['event_type'] = 'click'
form_submissions['event_type'] = 'form_submit'
search_queries['event_type'] = 'search'
cart_events['event_type'] = cart_events['cart_action']

all_events = pd.concat([
    page_views[['session_id', 'user_id', 'timestamp', 'event_type', 'page_url', 'referrer']],
    click_events[['session_id', 'user_id', 'timestamp', 'event_type', 'element_id', 'page_url']],
    form_submissions[['session_id', 'user_id', 'timestamp', 'event_type', 'form_id', 'page_url']],
    search_queries[['session_id', 'user_id', 'timestamp', 'event_type', 'query', 'results_count']],
    cart_events[['session_id', 'user_id', 'timestamp', 'event_type', 'product_id', 'quantity']]
], ignore_index=True, sort=False)

all_events = all_events.sort_values(['session_id', 'timestamp'])

# Session-level aggregations
session_metrics = all_events.groupby('session_id').agg({
    'user_id': 'first',
    'timestamp': ['min', 'max', 'count'],
    'page_url': 'nunique',
    'event_type': lambda x: x.value_counts().to_dict()
}).reset_index()

session_metrics.columns = ['session_id', 'user_id', 'session_start',
                            'session_end', 'total_events', 'unique_pages', 'event_breakdown']

# Calculate session duration
session_metrics['session_duration_seconds'] = (
    session_metrics['session_end'] - session_metrics['session_start']
).dt.total_seconds()

# Extract event counts
session_metrics['page_views'] = session_metrics['event_breakdown'].apply(
    lambda x: x.get('page_view', 0) if isinstance(x, dict) else 0
)
session_metrics['clicks'] = session_metrics['event_breakdown'].apply(
    lambda x: x.get('click', 0) if isinstance(x, dict) else 0
)
session_metrics['searches'] = session_metrics['event_breakdown'].apply(
    lambda x: x.get('search', 0) if isinstance(x, dict) else 0
)
session_metrics['cart_adds'] = session_metrics['event_breakdown'].apply(
    lambda x: x.get('add_to_cart', 0) if isinstance(x, dict) else 0
)

# Calculate engagement metrics
session_metrics['pages_per_minute'] = (
    session_metrics['unique_pages'] /
    (session_metrics['session_duration_seconds'] / 60).replace(0, 1)
)
session_metrics['events_per_page'] = (
    session_metrics['total_events'] / session_metrics['unique_pages'].replace(0, 1)
)

# Identify bounce sessions
session_metrics['is_bounce'] = (
    (session_metrics['unique_pages'] == 1) &
    (session_metrics['session_duration_seconds'] < 10)
).astype(int)

# Create page flow sequences
page_sequences = all_events[all_events['event_type'] == 'page_view'].copy()
page_sequences['page_order'] = page_sequences.groupby('session_id').cumcount() + 1
page_sequences['next_page'] = page_sequences.groupby('session_id')['page_url'].shift(-1)

# Calculate page transitions
page_transitions = page_sequences.groupby(['page_url', 'next_page']).size().reset_index(name='transition_count')
page_transitions = page_transitions[page_transitions['next_page'].notna()]

# Calculate exit rates per page
page_stats = page_sequences.groupby('page_url').agg({
    'session_id': 'count',
    'next_page': lambda x: x.isna().sum()
}).reset_index()
page_stats.columns = ['page_url', 'total_views', 'exits']
page_stats['exit_rate'] = page_stats['exits'] / page_stats['total_views']

# Analyze search behavior
search_analysis = search_queries.groupby('session_id').agg({
    'query': ['count', lambda x: ' | '.join(x)],
    'results_count': ['mean', 'min'],
    'clicked_result': 'sum'
}).reset_index()
search_analysis.columns = ['session_id', 'search_count', 'search_queries',
                            'avg_results', 'min_results', 'result_clicks']
search_analysis['search_success_rate'] = (
    search_analysis['result_clicks'] / search_analysis['search_count'].replace(0, 1)
)

# Analyze cart behavior
cart_analysis = cart_events.groupby('session_id').agg({
    'product_id': 'nunique',
    'quantity': 'sum',
    'cart_action': lambda x: (x == 'add_to_cart').sum()
}).reset_index()
cart_analysis.columns = ['session_id', 'unique_cart_products',
                          'total_cart_quantity', 'add_to_cart_events']

# Add purchase flag
purchases = cart_events[cart_events['cart_action'] == 'purchase'].groupby('session_id').agg({
    'order_value': 'sum'
}).reset_index()

cart_analysis = pd.merge(cart_analysis, purchases, on='session_id', how='left')
cart_analysis['converted'] = cart_analysis['order_value'].notna().astype(int)
cart_analysis['order_value'] = cart_analysis['order_value'].fillna(0)

# Merge all session data
session_complete = session_metrics.copy()
session_complete = pd.merge(session_complete, search_analysis, on='session_id', how='left')
session_complete = pd.merge(session_complete, cart_analysis, on='session_id', how='left')

# Add user agent info
session_complete = pd.merge(
    session_complete,
    user_agents[['session_id', 'device_type', 'browser', 'os', 'is_mobile']],
    on='session_id',
    how='left'
)

# Add geo location
session_complete = pd.merge(
    session_complete,
    geo_locations[['session_id', 'country', 'region', 'city', 'timezone']],
    on='session_id',
    how='left'
)

# Calculate user-level aggregations
user_metrics = session_complete.groupby('user_id').agg({
    'session_id': 'count',
    'session_duration_seconds': ['mean', 'sum'],
    'page_views': ['mean', 'sum'],
    'converted': 'sum',
    'order_value': 'sum',
    'session_start': ['min', 'max']
}).reset_index()

user_metrics.columns = ['user_id', 'total_sessions', 'avg_session_duration',
                        'total_time_spent', 'avg_pages_per_session', 'total_pages_viewed',
                        'total_conversions', 'total_revenue', 'first_visit', 'last_visit']

user_metrics['conversion_rate'] = (
    user_metrics['total_conversions'] / user_metrics['total_sessions']
)
user_metrics['avg_order_value'] = (
    user_metrics['total_revenue'] / user_metrics['total_conversions'].replace(0, 1)
)

# Segment users by engagement
user_metrics['engagement_segment'] = pd.cut(
    user_metrics['total_time_spent'] / 3600,
    bins=[-np.inf, 0.1, 1, 5, 20, np.inf],
    labels=['Minimal', 'Light', 'Medium', 'Heavy', 'Power']
)

# Save outputs
session_complete.to_csv('session_analytics.csv', index=False)
user_metrics.to_csv('user_engagement_metrics.csv', index=False)
page_stats.to_csv('page_performance.csv', index=False)
page_transitions.to_csv('page_flow_analysis.csv', index=False)
"""

# =============================================================================
# 8. FINANCIAL PORTFOLIO RISK ANALYSIS
# =============================================================================
PORTFOLIO_RISK_PIPELINE = """
import pandas as pd
import numpy as np

# Load financial data
positions = pd.read_csv('positions.csv')
price_history = pd.read_csv('price_history.csv')
instruments = pd.read_csv('instruments.csv')
market_data = pd.read_csv('market_data.csv')
fx_rates = pd.read_csv('fx_rates.csv')
benchmark_returns = pd.read_csv('benchmark_returns.csv')
factor_exposures = pd.read_csv('factor_exposures.csv')
credit_ratings = pd.read_csv('credit_ratings.csv')

# Parse dates
price_history['date'] = pd.to_datetime(price_history['date'])
market_data['date'] = pd.to_datetime(market_data['date'])
fx_rates['date'] = pd.to_datetime(fx_rates['date'])

# Calculate daily returns
price_history = price_history.sort_values(['instrument_id', 'date'])
price_history['daily_return'] = price_history.groupby('instrument_id')['close_price'].pct_change()
price_history['log_return'] = np.log(
    price_history['close_price'] / price_history.groupby('instrument_id')['close_price'].shift(1)
)

# Calculate rolling volatility
price_history['volatility_20d'] = price_history.groupby('instrument_id')['daily_return'].transform(
    lambda x: x.rolling(20).std() * np.sqrt(252)
)
price_history['volatility_60d'] = price_history.groupby('instrument_id')['daily_return'].transform(
    lambda x: x.rolling(60).std() * np.sqrt(252)
)

# Calculate rolling beta to market
market_returns = market_data[market_data['index_id'] == 'SPX'][['date', 'daily_return']].copy()
market_returns.columns = ['date', 'market_return']

price_with_market = pd.merge(price_history, market_returns, on='date', how='left')

def calculate_beta(group):
    if len(group) < 60:
        return np.nan
    cov = group['daily_return'].cov(group['market_return'])
    var = group['market_return'].var()
    return cov / var if var != 0 else np.nan

price_with_market['beta'] = price_with_market.groupby('instrument_id').apply(
    lambda x: x['daily_return'].rolling(60).cov(x['market_return']) /
              x['market_return'].rolling(60).var()
).reset_index(level=0, drop=True)

# Enrich positions with instrument details
positions_enriched = pd.merge(
    positions,
    instruments[['instrument_id', 'instrument_type', 'currency', 'sector',
                 'country', 'maturity_date', 'coupon_rate', 'issuer']],
    on='instrument_id',
    how='left'
)

# Get latest prices and metrics
latest_prices = price_with_market.groupby('instrument_id').last().reset_index()
positions_enriched = pd.merge(
    positions_enriched,
    latest_prices[['instrument_id', 'close_price', 'daily_return',
                   'volatility_20d', 'volatility_60d', 'beta']],
    on='instrument_id',
    how='left'
)

# Convert to base currency (USD)
fx_latest = fx_rates.groupby('currency_pair').last().reset_index()
fx_latest['to_currency'] = fx_latest['currency_pair'].str[-3:]
fx_latest['from_currency'] = fx_latest['currency_pair'].str[:3]

positions_enriched = pd.merge(
    positions_enriched,
    fx_latest[['from_currency', 'rate']].rename(columns={'from_currency': 'currency', 'rate': 'fx_rate'}),
    on='currency',
    how='left'
)
positions_enriched['fx_rate'] = positions_enriched['fx_rate'].fillna(1.0)

# Calculate market values
positions_enriched['market_value_local'] = positions_enriched['quantity'] * positions_enriched['close_price']
positions_enriched['market_value_usd'] = positions_enriched['market_value_local'] / positions_enriched['fx_rate']

# Calculate position-level risk metrics
positions_enriched['position_volatility'] = (
    positions_enriched['market_value_usd'] * positions_enriched['volatility_20d']
)

# Portfolio-level calculations
portfolio_value = positions_enriched.groupby('portfolio_id')['market_value_usd'].sum().reset_index()
portfolio_value.columns = ['portfolio_id', 'total_nav']

positions_enriched = pd.merge(positions_enriched, portfolio_value, on='portfolio_id', how='left')
positions_enriched['weight'] = positions_enriched['market_value_usd'] / positions_enriched['total_nav']

# Calculate weighted portfolio beta
portfolio_beta = positions_enriched.groupby('portfolio_id').apply(
    lambda x: (x['weight'] * x['beta']).sum()
).reset_index(name='portfolio_beta')

# Calculate portfolio volatility (simplified - assuming no correlation)
portfolio_vol_contrib = positions_enriched.groupby('portfolio_id').apply(
    lambda x: np.sqrt((x['weight']**2 * x['volatility_20d']**2).sum())
).reset_index(name='portfolio_volatility')

# Sector concentration
sector_concentration = positions_enriched.groupby(['portfolio_id', 'sector']).agg({
    'market_value_usd': 'sum',
    'weight': 'sum'
}).reset_index()
sector_concentration.columns = ['portfolio_id', 'sector', 'sector_value', 'sector_weight']

# Country concentration
country_concentration = positions_enriched.groupby(['portfolio_id', 'country']).agg({
    'market_value_usd': 'sum',
    'weight': 'sum'
}).reset_index()

# Add credit risk for fixed income
positions_enriched = pd.merge(
    positions_enriched,
    credit_ratings[['issuer', 'rating', 'rating_numeric', 'default_probability']],
    on='issuer',
    how='left'
)

# Calculate credit VaR contribution
positions_enriched['credit_var_contrib'] = (
    positions_enriched['market_value_usd'] *
    positions_enriched['default_probability'].fillna(0) *
    (1 - 0.4)  # Assuming 40% recovery rate
)

# Calculate VaR (parametric approach)
confidence_level = 0.99
z_score = 2.326  # 99% confidence

positions_enriched['var_1d'] = (
    positions_enriched['market_value_usd'] *
    positions_enriched['volatility_20d'] / np.sqrt(252) *
    z_score
)

portfolio_var = positions_enriched.groupby('portfolio_id')['var_1d'].sum().reset_index()
portfolio_var.columns = ['portfolio_id', 'total_var_1d']

# Historical VaR calculation
returns_pivot = price_history.pivot_table(
    index='date',
    columns='instrument_id',
    values='daily_return'
).fillna(0)

# Calculate portfolio returns for each portfolio
portfolio_returns = []
for portfolio_id in positions_enriched['portfolio_id'].unique():
    port_positions = positions_enriched[positions_enriched['portfolio_id'] == portfolio_id]
    weights = port_positions.set_index('instrument_id')['weight'].to_dict()

    port_return = returns_pivot[list(weights.keys())].mul(
        pd.Series(weights)
    ).sum(axis=1)

    portfolio_returns.append(pd.DataFrame({
        'portfolio_id': portfolio_id,
        'date': returns_pivot.index,
        'portfolio_return': port_return
    }))

portfolio_returns_df = pd.concat(portfolio_returns, ignore_index=True)

# Calculate historical VaR
historical_var = portfolio_returns_df.groupby('portfolio_id')['portfolio_return'].apply(
    lambda x: x.quantile(1 - confidence_level)
).reset_index(name='historical_var_1d')

# Calculate Sharpe ratio
risk_free_rate = 0.05 / 252  # Daily risk-free rate

portfolio_sharpe = portfolio_returns_df.groupby('portfolio_id').agg({
    'portfolio_return': ['mean', 'std']
}).reset_index()
portfolio_sharpe.columns = ['portfolio_id', 'avg_return', 'return_std']
portfolio_sharpe['sharpe_ratio'] = (
    (portfolio_sharpe['avg_return'] - risk_free_rate) / portfolio_sharpe['return_std']
) * np.sqrt(252)

# Compile portfolio risk summary
portfolio_risk = portfolio_value.copy()
portfolio_risk = pd.merge(portfolio_risk, portfolio_beta, on='portfolio_id', how='left')
portfolio_risk = pd.merge(portfolio_risk, portfolio_vol_contrib, on='portfolio_id', how='left')
portfolio_risk = pd.merge(portfolio_risk, portfolio_var, on='portfolio_id', how='left')
portfolio_risk = pd.merge(portfolio_risk, historical_var, on='portfolio_id', how='left')
portfolio_risk = pd.merge(portfolio_risk, portfolio_sharpe, on='portfolio_id', how='left')

# Save outputs
positions_enriched.to_csv('positions_with_risk.csv', index=False)
portfolio_risk.to_csv('portfolio_risk_summary.csv', index=False)
sector_concentration.to_csv('sector_concentration.csv', index=False)
country_concentration.to_csv('country_concentration.csv', index=False)
portfolio_returns_df.to_csv('portfolio_returns_history.csv', index=False)
"""

# =============================================================================
# COMPLEX PIPELINE COLLECTION
# =============================================================================
COMPLEX_EXAMPLES = {
    "fraud_detection": FRAUD_DETECTION_PIPELINE,
    "customer_360": CUSTOMER_360_PIPELINE,
    "supply_chain": SUPPLY_CHAIN_PIPELINE,
    "marketing_attribution": MARKETING_ATTRIBUTION_PIPELINE,
    "iot_predictive_maintenance": IOT_PREDICTIVE_MAINTENANCE_PIPELINE,
    "genomic_analysis": GENOMIC_ANALYSIS_PIPELINE,
    "clickstream_analysis": CLICKSTREAM_ANALYSIS_PIPELINE,
    "portfolio_risk": PORTFOLIO_RISK_PIPELINE,
}

# Pipeline metadata
COMPLEX_PIPELINE_METADATA = {
    "fraud_detection": {
        "name": "Real-Time Fraud Detection",
        "description": "Multi-source fraud detection with velocity features, device fingerprinting, and composite risk scoring",
        "data_sources": 6,
        "estimated_recipes": 15,
        "key_operations": ["joins", "aggregations", "window functions", "feature engineering"]
    },
    "customer_360": {
        "name": "Customer 360 Data Lake",
        "description": "Unified customer view integrating CRM, e-commerce, mobile, call center, and marketing data",
        "data_sources": 10,
        "estimated_recipes": 20,
        "key_operations": ["identity resolution", "multi-source joins", "metric aggregations", "segmentation"]
    },
    "supply_chain": {
        "name": "Supply Chain Optimization",
        "description": "Demand forecasting, inventory optimization, and shipping cost analysis",
        "data_sources": 9,
        "estimated_recipes": 18,
        "key_operations": ["time series features", "rolling aggregations", "EOQ calculations", "risk scoring"]
    },
    "marketing_attribution": {
        "name": "Multi-Touch Attribution",
        "description": "Customer journey analysis with multiple attribution models (first-touch, last-touch, linear, time-decay, position-based)",
        "data_sources": 8,
        "estimated_recipes": 16,
        "key_operations": ["sequence analysis", "attribution modeling", "ROI calculations", "adstock transformation"]
    },
    "iot_predictive_maintenance": {
        "name": "IoT Predictive Maintenance",
        "description": "Sensor data processing with anomaly detection and equipment health scoring",
        "data_sources": 7,
        "estimated_recipes": 14,
        "key_operations": ["time series aggregations", "z-score anomaly detection", "rolling statistics", "failure prediction"]
    },
    "genomic_analysis": {
        "name": "Genomic Variant Analysis",
        "description": "Variant annotation, burden analysis, and pathogenicity prediction",
        "data_sources": 8,
        "estimated_recipes": 12,
        "key_operations": ["variant annotation", "quality filtering", "burden calculation", "pathway analysis"]
    },
    "clickstream_analysis": {
        "name": "Clickstream & Session Analytics",
        "description": "User behavior analysis with page flow, conversion tracking, and engagement metrics",
        "data_sources": 8,
        "estimated_recipes": 15,
        "key_operations": ["event aggregation", "session reconstruction", "funnel analysis", "user segmentation"]
    },
    "portfolio_risk": {
        "name": "Financial Portfolio Risk",
        "description": "Multi-asset portfolio risk analysis with VaR, volatility, and concentration metrics",
        "data_sources": 8,
        "estimated_recipes": 14,
        "key_operations": ["return calculations", "VaR computation", "beta calculation", "concentration analysis"]
    }
}


def get_complex_example(name: str) -> str:
    """Get a complex pipeline example by name."""
    return COMPLEX_EXAMPLES.get(name, "")


def list_complex_examples() -> list:
    """List all available complex pipeline examples."""
    return list(COMPLEX_EXAMPLES.keys())


def get_pipeline_metadata(name: str) -> dict:
    """Get metadata for a complex pipeline."""
    return COMPLEX_PIPELINE_METADATA.get(name, {})
