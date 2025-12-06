"""
Comprehensive examples for every Dataiku DSS processor type.

This module provides Python code examples that map to each Dataiku Prepare
recipe processor type, demonstrating how py2dataiku detects and converts
various pandas operations into their corresponding processor configurations.
"""

from typing import Dict, Any

# =============================================================================
# COLUMN MANIPULATION PROCESSORS
# =============================================================================

COLUMN_RENAMER_EXAMPLE = """
import pandas as pd

df = pd.read_csv('data.csv')

# Rename single column
df = df.rename(columns={'old_name': 'new_name'})

# Rename multiple columns
df = df.rename(columns={
    'cust_id': 'customer_id',
    'prod_name': 'product_name',
    'qty': 'quantity',
    'amt': 'amount'
})

df.to_csv('renamed.csv', index=False)
"""

COLUMN_COPIER_EXAMPLE = """
import pandas as pd

df = pd.read_csv('data.csv')

# Copy column with new name
df['customer_id_backup'] = df['customer_id']
df['amount_original'] = df['amount']

# Copy with transformation
df['amount_copy'] = df['amount'].copy()

df.to_csv('copied.csv', index=False)
"""

COLUMN_DELETER_EXAMPLE = """
import pandas as pd

df = pd.read_csv('data.csv')

# Delete single column
df = df.drop(columns=['unnecessary_column'])

# Delete multiple columns
df = df.drop(columns=['temp1', 'temp2', 'debug_info'])

# Delete using del
del df['another_column']

df.to_csv('reduced.csv', index=False)
"""

COLUMNS_SELECTOR_EXAMPLE = """
import pandas as pd

df = pd.read_csv('data.csv')

# Select specific columns
df = df[['customer_id', 'name', 'email', 'amount']]

# Select using column list
cols_to_keep = ['id', 'date', 'value']
df = df[cols_to_keep]

df.to_csv('selected.csv', index=False)
"""

COLUMN_REORDER_EXAMPLE = """
import pandas as pd

df = pd.read_csv('data.csv')

# Reorder columns
new_order = ['customer_id', 'name', 'email', 'phone', 'address', 'created_date']
df = df[new_order]

# Reorder with some columns first
priority_cols = ['id', 'status']
other_cols = [c for c in df.columns if c not in priority_cols]
df = df[priority_cols + other_cols]

df.to_csv('reordered.csv', index=False)
"""

COLUMNS_CONCATENATOR_EXAMPLE = """
import pandas as pd

df = pd.read_csv('data.csv')

# Concatenate columns into new column
df['full_name'] = df['first_name'] + ' ' + df['last_name']

# Concatenate with separator
df['full_address'] = df['street'] + ', ' + df['city'] + ', ' + df['state'] + ' ' + df['zip']

df.to_csv('concatenated.csv', index=False)
"""

# =============================================================================
# MISSING VALUE HANDLING PROCESSORS
# =============================================================================

FILL_EMPTY_WITH_VALUE_EXAMPLE = """
import pandas as pd

df = pd.read_csv('data.csv')

# Fill with constant value
df['category'] = df['category'].fillna('Unknown')
df['count'] = df['count'].fillna(0)
df['active'] = df['active'].fillna(False)

# Fill multiple columns
df.fillna({'status': 'pending', 'priority': 'medium', 'score': 0}, inplace=True)

df.to_csv('filled.csv', index=False)
"""

REMOVE_ROWS_ON_EMPTY_EXAMPLE = """
import pandas as pd

df = pd.read_csv('data.csv')

# Remove rows where any column is null
df = df.dropna()

# Remove rows where specific columns are null
df = df.dropna(subset=['customer_id', 'email'])

# Remove rows where all specified columns are null
df = df.dropna(subset=['phone', 'email'], how='all')

df.to_csv('no_nulls.csv', index=False)
"""

FILL_EMPTY_WITH_PREVIOUS_NEXT_EXAMPLE = """
import pandas as pd

df = pd.read_csv('timeseries.csv')
df = df.sort_values('date')

# Forward fill (use previous value)
df['value'] = df['value'].ffill()

# Backward fill (use next value)
df['value'] = df['value'].bfill()

# Forward fill with limit
df['metric'] = df['metric'].ffill(limit=3)

df.to_csv('filled_timeseries.csv', index=False)
"""

FILL_EMPTY_WITH_COMPUTED_VALUE_EXAMPLE = """
import pandas as pd

df = pd.read_csv('data.csv')

# Fill with mean
df['score'] = df['score'].fillna(df['score'].mean())

# Fill with median
df['age'] = df['age'].fillna(df['age'].median())

# Fill with mode
df['category'] = df['category'].fillna(df['category'].mode()[0])

# Fill with grouped mean
df['amount'] = df.groupby('category')['amount'].transform(
    lambda x: x.fillna(x.mean())
)

df.to_csv('computed_fill.csv', index=False)
"""

IMPUTE_WITH_ML_EXAMPLE = """
import pandas as pd
from sklearn.impute import KNNImputer
import numpy as np

df = pd.read_csv('data.csv')

# KNN imputation for numeric columns
numeric_cols = df.select_dtypes(include=[np.number]).columns
imputer = KNNImputer(n_neighbors=5)
df[numeric_cols] = imputer.fit_transform(df[numeric_cols])

df.to_csv('ml_imputed.csv', index=False)
"""

# =============================================================================
# STRING TRANSFORMATION PROCESSORS
# =============================================================================

STRING_TRANSFORMER_UPPERCASE_EXAMPLE = """
import pandas as pd

df = pd.read_csv('data.csv')

# Convert to uppercase
df['name'] = df['name'].str.upper()
df['code'] = df['code'].str.upper()

df.to_csv('uppercase.csv', index=False)
"""

STRING_TRANSFORMER_LOWERCASE_EXAMPLE = """
import pandas as pd

df = pd.read_csv('data.csv')

# Convert to lowercase
df['email'] = df['email'].str.lower()
df['username'] = df['username'].str.lower()

df.to_csv('lowercase.csv', index=False)
"""

STRING_TRANSFORMER_TITLECASE_EXAMPLE = """
import pandas as pd

df = pd.read_csv('data.csv')

# Convert to title case
df['name'] = df['name'].str.title()
df['city'] = df['city'].str.title()

df.to_csv('titlecase.csv', index=False)
"""

STRING_TRANSFORMER_TRIM_EXAMPLE = """
import pandas as pd

df = pd.read_csv('data.csv')

# Trim whitespace from both sides
df['name'] = df['name'].str.strip()

# Left trim only
df['code'] = df['code'].str.lstrip()

# Right trim only
df['description'] = df['description'].str.rstrip()

df.to_csv('trimmed.csv', index=False)
"""

STRING_TRANSFORMER_NORMALIZE_WHITESPACE_EXAMPLE = """
import pandas as pd
import re

df = pd.read_csv('data.csv')

# Normalize whitespace (multiple spaces to single)
df['text'] = df['text'].str.replace(r'\\s+', ' ', regex=True)

# Remove all whitespace
df['code'] = df['code'].str.replace(' ', '')

df.to_csv('normalized_whitespace.csv', index=False)
"""

TOKENIZER_EXAMPLE = """
import pandas as pd

df = pd.read_csv('data.csv')

# Split string into tokens
df['words'] = df['sentence'].str.split()

# Split by specific delimiter
df['tags'] = df['tag_string'].str.split(',')

# Split and expand into columns
split_cols = df['full_name'].str.split(' ', expand=True)
df['first_name'] = split_cols[0]
df['last_name'] = split_cols[1]

df.to_csv('tokenized.csv', index=False)
"""

REGEXP_EXTRACTOR_EXAMPLE = """
import pandas as pd

df = pd.read_csv('data.csv')

# Extract with regex pattern
df['area_code'] = df['phone'].str.extract(r'\\((\\d{3})\\)')
df['email_domain'] = df['email'].str.extract(r'@(.+)$')

# Extract multiple groups
extracted = df['address'].str.extract(r'(\\d+)\\s+(.+),\\s+(\\w+)')
df['street_num'] = extracted[0]
df['street_name'] = extracted[1]
df['city'] = extracted[2]

df.to_csv('extracted.csv', index=False)
"""

FIND_REPLACE_EXAMPLE = """
import pandas as pd

df = pd.read_csv('data.csv')

# Simple find and replace
df['status'] = df['status'].str.replace('ACTV', 'Active')
df['status'] = df['status'].str.replace('INACTV', 'Inactive')

# Replace with regex
df['phone'] = df['phone'].str.replace(r'[^\\d]', '', regex=True)

# Multiple replacements
replacements = {'NY': 'New York', 'CA': 'California', 'TX': 'Texas'}
df['state'] = df['state'].replace(replacements)

df.to_csv('replaced.csv', index=False)
"""

SPLIT_COLUMN_EXAMPLE = """
import pandas as pd

df = pd.read_csv('data.csv')

# Split column into multiple
df[['first_name', 'last_name']] = df['full_name'].str.split(' ', n=1, expand=True)

# Split by delimiter
df[['year', 'month', 'day']] = df['date_str'].str.split('-', expand=True)

# Split and get specific part
df['domain'] = df['email'].str.split('@').str[1]

df.to_csv('split.csv', index=False)
"""

CONCAT_COLUMNS_EXAMPLE = """
import pandas as pd

df = pd.read_csv('data.csv')

# Simple concatenation
df['full_name'] = df['first_name'] + ' ' + df['last_name']

# Concatenation with multiple columns
df['full_address'] = (
    df['street'] + ', ' +
    df['city'] + ', ' +
    df['state'] + ' ' +
    df['zip'].astype(str)
)

# Using string format
df['display'] = df['id'].astype(str) + ': ' + df['name']

df.to_csv('concatenated.csv', index=False)
"""

HTML_STRIPPER_EXAMPLE = """
import pandas as pd
import re

df = pd.read_csv('data.csv')

# Remove HTML tags
df['clean_text'] = df['html_content'].str.replace(r'<[^>]+>', '', regex=True)

# Remove specific tags
df['no_script'] = df['content'].str.replace(r'<script[^>]*>.*?</script>', '', regex=True)

df.to_csv('stripped_html.csv', index=False)
"""

NGRAMMER_EXAMPLE = """
import pandas as pd
from sklearn.feature_extraction.text import CountVectorizer

df = pd.read_csv('text_data.csv')

# Generate bigrams
vectorizer = CountVectorizer(ngram_range=(2, 2), analyzer='word')
bigrams = vectorizer.fit_transform(df['text'])
df['bigram_features'] = [' '.join(vectorizer.get_feature_names_out())] * len(df)

df.to_csv('ngrams.csv', index=False)
"""

TEXT_SIMPLIFIER_EXAMPLE = """
import pandas as pd
import unicodedata

df = pd.read_csv('data.csv')

# Remove accents
df['simplified'] = df['text'].apply(
    lambda x: unicodedata.normalize('NFKD', str(x)).encode('ASCII', 'ignore').decode()
)

# Remove non-alphanumeric
df['clean'] = df['text'].str.replace(r'[^a-zA-Z0-9\\s]', '', regex=True)

df.to_csv('simplified.csv', index=False)
"""

STEM_TEXT_EXAMPLE = """
import pandas as pd
from nltk.stem import PorterStemmer

df = pd.read_csv('text_data.csv')

stemmer = PorterStemmer()
df['stemmed'] = df['text'].apply(
    lambda x: ' '.join([stemmer.stem(word) for word in str(x).split()])
)

df.to_csv('stemmed.csv', index=False)
"""

LEMMATIZE_TEXT_EXAMPLE = """
import pandas as pd
from nltk.stem import WordNetLemmatizer

df = pd.read_csv('text_data.csv')

lemmatizer = WordNetLemmatizer()
df['lemmatized'] = df['text'].apply(
    lambda x: ' '.join([lemmatizer.lemmatize(word) for word in str(x).split()])
)

df.to_csv('lemmatized.csv', index=False)
"""

URL_PARSER_EXAMPLE = """
import pandas as pd
from urllib.parse import urlparse

df = pd.read_csv('data.csv')

# Parse URL components
df['domain'] = df['url'].apply(lambda x: urlparse(str(x)).netloc)
df['path'] = df['url'].apply(lambda x: urlparse(str(x)).path)
df['scheme'] = df['url'].apply(lambda x: urlparse(str(x)).scheme)

df.to_csv('parsed_urls.csv', index=False)
"""

EMAIL_DOMAIN_EXTRACTOR_EXAMPLE = """
import pandas as pd

df = pd.read_csv('data.csv')

# Extract email domain
df['email_domain'] = df['email'].str.split('@').str[1]

# Extract email username
df['email_user'] = df['email'].str.split('@').str[0]

df.to_csv('email_parsed.csv', index=False)
"""

# =============================================================================
# NUMERIC TRANSFORMATION PROCESSORS
# =============================================================================

NUMERICAL_TRANSFORMER_MULTIPLY_EXAMPLE = """
import pandas as pd

df = pd.read_csv('data.csv')

# Multiply by constant
df['amount_cents'] = df['amount'] * 100
df['doubled'] = df['value'] * 2

df.to_csv('multiplied.csv', index=False)
"""

NUMERICAL_TRANSFORMER_DIVIDE_EXAMPLE = """
import pandas as pd

df = pd.read_csv('data.csv')

# Divide by constant
df['amount_thousands'] = df['amount'] / 1000
df['halved'] = df['value'] / 2

df.to_csv('divided.csv', index=False)
"""

NUMERICAL_TRANSFORMER_ADD_EXAMPLE = """
import pandas as pd

df = pd.read_csv('data.csv')

# Add constant
df['adjusted_price'] = df['price'] + 10
df['score_bonus'] = df['score'] + 5

df.to_csv('added.csv', index=False)
"""

NUMERICAL_TRANSFORMER_SUBTRACT_EXAMPLE = """
import pandas as pd

df = pd.read_csv('data.csv')

# Subtract constant
df['net_amount'] = df['gross_amount'] - df['tax']
df['adjusted'] = df['value'] - 100

df.to_csv('subtracted.csv', index=False)
"""

NUMERICAL_TRANSFORMER_POWER_EXAMPLE = """
import pandas as pd
import numpy as np

df = pd.read_csv('data.csv')

# Raise to power
df['squared'] = df['value'] ** 2
df['cubed'] = df['value'] ** 3
df['sqrt'] = np.sqrt(df['value'])

df.to_csv('powered.csv', index=False)
"""

NUMERICAL_TRANSFORMER_LOG_EXAMPLE = """
import pandas as pd
import numpy as np

df = pd.read_csv('data.csv')

# Logarithmic transformations
df['log_amount'] = np.log(df['amount'])
df['log10_amount'] = np.log10(df['amount'])
df['log1p_amount'] = np.log1p(df['amount'])

df.to_csv('logged.csv', index=False)
"""

ROUND_COLUMN_EXAMPLE = """
import pandas as pd

df = pd.read_csv('data.csv')

# Round to decimal places
df['amount_rounded'] = df['amount'].round(2)
df['score_rounded'] = df['score'].round(0)

# Round to significant figures
df['value_rounded'] = df['value'].round(-2)  # Round to nearest 100

df.to_csv('rounded.csv', index=False)
"""

ABS_COLUMN_EXAMPLE = """
import pandas as pd

df = pd.read_csv('data.csv')

# Absolute value
df['abs_change'] = df['change'].abs()
df['abs_delta'] = df['delta'].abs()

df.to_csv('absolute.csv', index=False)
"""

CLIP_COLUMN_EXAMPLE = """
import pandas as pd

df = pd.read_csv('data.csv')

# Clip to range
df['clipped_score'] = df['score'].clip(lower=0, upper=100)
df['clipped_amount'] = df['amount'].clip(lower=0)  # Only lower bound

df.to_csv('clipped.csv', index=False)
"""

BINNER_EXAMPLE = """
import pandas as pd

df = pd.read_csv('data.csv')

# Create bins with pd.cut
df['age_group'] = pd.cut(
    df['age'],
    bins=[0, 18, 35, 50, 65, 100],
    labels=['Child', 'Young Adult', 'Adult', 'Middle Age', 'Senior']
)

# Equal-width binning
df['score_bin'] = pd.cut(df['score'], bins=5, labels=['Very Low', 'Low', 'Medium', 'High', 'Very High'])

# Quantile-based binning
df['income_quartile'] = pd.qcut(df['income'], q=4, labels=['Q1', 'Q2', 'Q3', 'Q4'])

df.to_csv('binned.csv', index=False)
"""

NORMALIZER_EXAMPLE = """
import pandas as pd
import numpy as np

df = pd.read_csv('data.csv')

# Min-Max normalization
df['norm_minmax'] = (df['value'] - df['value'].min()) / (df['value'].max() - df['value'].min())

# Z-score normalization
df['norm_zscore'] = (df['value'] - df['value'].mean()) / df['value'].std()

# Robust scaling (using median and IQR)
q1 = df['value'].quantile(0.25)
q3 = df['value'].quantile(0.75)
df['norm_robust'] = (df['value'] - df['value'].median()) / (q3 - q1)

df.to_csv('normalized.csv', index=False)
"""

DISCRETIZER_EXAMPLE = """
import pandas as pd
from sklearn.preprocessing import KBinsDiscretizer

df = pd.read_csv('data.csv')

# Discretize continuous variable
discretizer = KBinsDiscretizer(n_bins=5, encode='ordinal', strategy='quantile')
df['value_discrete'] = discretizer.fit_transform(df[['value']])

df.to_csv('discretized.csv', index=False)
"""

# =============================================================================
# TYPE CONVERSION PROCESSORS
# =============================================================================

TYPE_SETTER_EXAMPLE = """
import pandas as pd

df = pd.read_csv('data.csv')

# Convert types
df['customer_id'] = df['customer_id'].astype(str)
df['amount'] = df['amount'].astype(float)
df['quantity'] = df['quantity'].astype(int)
df['is_active'] = df['is_active'].astype(bool)

df.to_csv('typed.csv', index=False)
"""

DATE_PARSER_EXAMPLE = """
import pandas as pd

df = pd.read_csv('data.csv')

# Parse dates
df['date'] = pd.to_datetime(df['date_string'])
df['timestamp'] = pd.to_datetime(df['ts_string'], format='%Y-%m-%d %H:%M:%S')
df['custom_date'] = pd.to_datetime(df['date_str'], format='%d/%m/%Y')

df.to_csv('parsed_dates.csv', index=False)
"""

DATE_FORMATTER_EXAMPLE = """
import pandas as pd

df = pd.read_csv('data.csv')
df['date'] = pd.to_datetime(df['date'])

# Format dates
df['date_formatted'] = df['date'].dt.strftime('%Y-%m-%d')
df['date_display'] = df['date'].dt.strftime('%B %d, %Y')
df['date_short'] = df['date'].dt.strftime('%m/%d/%y')

df.to_csv('formatted_dates.csv', index=False)
"""

BOOLEAN_CONVERTER_EXAMPLE = """
import pandas as pd

df = pd.read_csv('data.csv')

# Convert to boolean
df['is_active'] = df['status'].map({'active': True, 'inactive': False})
df['has_value'] = df['value'].notna()
df['is_positive'] = df['amount'] > 0

df.to_csv('boolean.csv', index=False)
"""

# =============================================================================
# DATE/TIME OPERATION PROCESSORS
# =============================================================================

DATE_COMPONENTS_EXTRACTOR_EXAMPLE = """
import pandas as pd

df = pd.read_csv('data.csv')
df['date'] = pd.to_datetime(df['date'])

# Extract date components
df['year'] = df['date'].dt.year
df['month'] = df['date'].dt.month
df['day'] = df['date'].dt.day
df['day_of_week'] = df['date'].dt.dayofweek
df['day_of_year'] = df['date'].dt.dayofyear
df['week_of_year'] = df['date'].dt.isocalendar().week
df['quarter'] = df['date'].dt.quarter
df['hour'] = df['date'].dt.hour
df['minute'] = df['date'].dt.minute

df.to_csv('date_components.csv', index=False)
"""

DATE_DIFF_CALCULATOR_EXAMPLE = """
import pandas as pd

df = pd.read_csv('data.csv')
df['start_date'] = pd.to_datetime(df['start_date'])
df['end_date'] = pd.to_datetime(df['end_date'])

# Calculate date differences
df['days_diff'] = (df['end_date'] - df['start_date']).dt.days
df['hours_diff'] = (df['end_date'] - df['start_date']).dt.total_seconds() / 3600
df['weeks_diff'] = df['days_diff'] / 7

# Days since reference date
df['days_since_2020'] = (df['date'] - pd.Timestamp('2020-01-01')).dt.days

df.to_csv('date_diffs.csv', index=False)
"""

TIMEZONE_CONVERTER_EXAMPLE = """
import pandas as pd

df = pd.read_csv('data.csv')
df['timestamp'] = pd.to_datetime(df['timestamp'])

# Convert timezone
df['timestamp_utc'] = df['timestamp'].dt.tz_localize('America/New_York').dt.tz_convert('UTC')
df['timestamp_pacific'] = df['timestamp_utc'].dt.tz_convert('America/Los_Angeles')

df.to_csv('timezone_converted.csv', index=False)
"""

# =============================================================================
# FILTERING PROCESSORS
# =============================================================================

FILTER_ON_VALUE_EXAMPLE = """
import pandas as pd

df = pd.read_csv('data.csv')

# Filter by exact value
df = df[df['status'] == 'active']
df = df[df['category'] != 'deprecated']

# Filter by multiple values
df = df[df['region'].isin(['North', 'South', 'East'])]

df.to_csv('filtered_value.csv', index=False)
"""

FILTER_ON_BAD_TYPE_EXAMPLE = """
import pandas as pd

df = pd.read_csv('data.csv')

# Filter rows with valid numeric values
df['amount_numeric'] = pd.to_numeric(df['amount'], errors='coerce')
df = df[df['amount_numeric'].notna()]

# Filter rows with valid dates
df['date_parsed'] = pd.to_datetime(df['date_string'], errors='coerce')
df = df[df['date_parsed'].notna()]

df.to_csv('filtered_types.csv', index=False)
"""

FILTER_ON_FORMULA_EXAMPLE = """
import pandas as pd

df = pd.read_csv('data.csv')

# Complex filter expression
df = df[(df['amount'] > 100) & (df['status'] == 'active') | (df['priority'] == 'high')]

# Filter using query
df = df.query('amount > 100 and status == "active"')

df.to_csv('filtered_formula.csv', index=False)
"""

FILTER_ON_DATE_RANGE_EXAMPLE = """
import pandas as pd

df = pd.read_csv('data.csv')
df['date'] = pd.to_datetime(df['date'])

# Filter by date range
start_date = pd.Timestamp('2023-01-01')
end_date = pd.Timestamp('2023-12-31')
df = df[(df['date'] >= start_date) & (df['date'] <= end_date)]

# Filter last N days
from datetime import datetime, timedelta
cutoff = datetime.now() - timedelta(days=30)
df = df[df['date'] >= cutoff]

df.to_csv('filtered_dates.csv', index=False)
"""

FILTER_ON_NUMERIC_RANGE_EXAMPLE = """
import pandas as pd

df = pd.read_csv('data.csv')

# Filter by numeric range
df = df[(df['amount'] >= 100) & (df['amount'] <= 1000)]

# Filter with between
df = df[df['score'].between(50, 100)]

df.to_csv('filtered_numeric.csv', index=False)
"""

FILTER_ON_MULTIPLE_VALUES_EXAMPLE = """
import pandas as pd

df = pd.read_csv('data.csv')

# Filter on multiple values using isin
allowed_statuses = ['active', 'pending', 'approved']
df = df[df['status'].isin(allowed_statuses)]

# Exclude multiple values
excluded_categories = ['test', 'demo', 'sample']
df = df[~df['category'].isin(excluded_categories)]

df.to_csv('filtered_multiple.csv', index=False)
"""

# =============================================================================
# FLAGGING PROCESSORS
# =============================================================================

FLAG_ON_VALUE_EXAMPLE = """
import pandas as pd

df = pd.read_csv('data.csv')

# Create flag based on value
df['is_premium'] = (df['tier'] == 'premium').astype(int)
df['is_active'] = (df['status'] == 'active').astype(int)

df.to_csv('flagged_value.csv', index=False)
"""

FLAG_ON_FORMULA_EXAMPLE = """
import pandas as pd

df = pd.read_csv('data.csv')

# Create flag based on formula
df['high_value'] = ((df['amount'] > 1000) & (df['quantity'] > 10)).astype(int)
df['needs_review'] = ((df['status'] == 'pending') | (df['age'] > 30)).astype(int)

df.to_csv('flagged_formula.csv', index=False)
"""

FLAG_ON_BAD_TYPE_EXAMPLE = """
import pandas as pd

df = pd.read_csv('data.csv')

# Flag rows with type issues
df['invalid_amount'] = pd.to_numeric(df['amount'], errors='coerce').isna().astype(int)
df['invalid_date'] = pd.to_datetime(df['date'], errors='coerce').isna().astype(int)

df.to_csv('flagged_types.csv', index=False)
"""

FLAG_ON_DATE_RANGE_EXAMPLE = """
import pandas as pd

df = pd.read_csv('data.csv')
df['date'] = pd.to_datetime(df['date'])

# Flag based on date range
df['is_recent'] = (df['date'] >= '2023-01-01').astype(int)
df['is_q1'] = ((df['date'].dt.month >= 1) & (df['date'].dt.month <= 3)).astype(int)

df.to_csv('flagged_dates.csv', index=False)
"""

FLAG_ON_NUMERIC_RANGE_EXAMPLE = """
import pandas as pd

df = pd.read_csv('data.csv')

# Flag based on numeric range
df['in_range'] = df['score'].between(50, 100).astype(int)
df['outlier'] = ((df['value'] < df['value'].quantile(0.05)) |
                  (df['value'] > df['value'].quantile(0.95))).astype(int)

df.to_csv('flagged_numeric.csv', index=False)
"""

# =============================================================================
# ROW OPERATION PROCESSORS
# =============================================================================

REMOVE_DUPLICATES_EXAMPLE = """
import pandas as pd

df = pd.read_csv('data.csv')

# Remove complete duplicates
df = df.drop_duplicates()

# Remove duplicates based on subset
df = df.drop_duplicates(subset=['customer_id', 'date'])

# Keep first/last occurrence
df = df.drop_duplicates(subset=['email'], keep='first')

df.to_csv('deduplicated.csv', index=False)
"""

SORT_ROWS_EXAMPLE = """
import pandas as pd

df = pd.read_csv('data.csv')

# Sort by single column
df = df.sort_values('date')

# Sort by multiple columns
df = df.sort_values(['category', 'amount'], ascending=[True, False])

df.to_csv('sorted.csv', index=False)
"""

SAMPLE_ROWS_EXAMPLE = """
import pandas as pd

df = pd.read_csv('data.csv')

# Random sample
df_sample = df.sample(n=1000, random_state=42)

# Percentage sample
df_sample_pct = df.sample(frac=0.1, random_state=42)

df_sample.to_csv('sampled.csv', index=False)
"""

SHUFFLE_ROWS_EXAMPLE = """
import pandas as pd

df = pd.read_csv('data.csv')

# Shuffle rows
df = df.sample(frac=1, random_state=42).reset_index(drop=True)

df.to_csv('shuffled.csv', index=False)
"""

# =============================================================================
# COMPUTED COLUMN PROCESSORS
# =============================================================================

CREATE_COLUMN_WITH_GREL_EXAMPLE = """
import pandas as pd

df = pd.read_csv('data.csv')

# GREL-like expression (complex formula)
df['computed'] = df.apply(
    lambda row: f"{row['first_name']} {row['last_name']} ({row['department']})",
    axis=1
)

# Conditional expression
df['tier'] = df.apply(
    lambda row: 'Premium' if row['amount'] > 1000 else 'Standard',
    axis=1
)

df.to_csv('grel_computed.csv', index=False)
"""

FORMULA_EXAMPLE = """
import pandas as pd

df = pd.read_csv('data.csv')

# Simple formula
df['total'] = df['quantity'] * df['unit_price']
df['discount_amount'] = df['total'] * df['discount_rate']
df['final_amount'] = df['total'] - df['discount_amount']

# Multi-column formula
df['weighted_score'] = (df['score1'] * 0.3 + df['score2'] * 0.5 + df['score3'] * 0.2)

df.to_csv('formula.csv', index=False)
"""

MULTI_COLUMN_FORMULA_EXAMPLE = """
import pandas as pd

df = pd.read_csv('data.csv')

# Apply formula across multiple columns
numeric_cols = ['col1', 'col2', 'col3']
for col in numeric_cols:
    df[f'{col}_normalized'] = (df[col] - df[col].mean()) / df[col].std()

df.to_csv('multi_formula.csv', index=False)
"""

HASH_COMPUTER_EXAMPLE = """
import pandas as pd
import hashlib

df = pd.read_csv('data.csv')

# Compute hash
df['hash'] = df['email'].apply(
    lambda x: hashlib.sha256(str(x).encode()).hexdigest()
)

# MD5 hash
df['md5'] = df['customer_id'].apply(
    lambda x: hashlib.md5(str(x).encode()).hexdigest()
)

df.to_csv('hashed.csv', index=False)
"""

UUID_GENERATOR_EXAMPLE = """
import pandas as pd
import uuid

df = pd.read_csv('data.csv')

# Generate UUID for each row
df['uuid'] = [str(uuid.uuid4()) for _ in range(len(df))]

df.to_csv('with_uuid.csv', index=False)
"""

# =============================================================================
# CATEGORICAL PROCESSORS
# =============================================================================

MERGE_LONG_TAIL_VALUES_EXAMPLE = """
import pandas as pd

df = pd.read_csv('data.csv')

# Merge rare categories into 'Other'
value_counts = df['category'].value_counts()
rare_categories = value_counts[value_counts < 10].index
df['category_merged'] = df['category'].apply(
    lambda x: 'Other' if x in rare_categories else x
)

df.to_csv('merged_categories.csv', index=False)
"""

CATEGORICAL_ENCODER_EXAMPLE = """
import pandas as pd

df = pd.read_csv('data.csv')

# One-hot encoding
df_encoded = pd.get_dummies(df, columns=['category', 'status'])

df_encoded.to_csv('encoded.csv', index=False)
"""

ONE_HOT_ENCODER_EXAMPLE = """
import pandas as pd

df = pd.read_csv('data.csv')

# One-hot encoding for specific columns
df_onehot = pd.get_dummies(df, columns=['color', 'size'], prefix=['color', 'size'])

df_onehot.to_csv('onehot.csv', index=False)
"""

LABEL_ENCODER_EXAMPLE = """
import pandas as pd
from sklearn.preprocessing import LabelEncoder

df = pd.read_csv('data.csv')

# Label encoding
le = LabelEncoder()
df['category_encoded'] = le.fit_transform(df['category'])

df.to_csv('label_encoded.csv', index=False)
"""

TARGET_ENCODER_EXAMPLE = """
import pandas as pd

df = pd.read_csv('data.csv')

# Target encoding (mean encoding)
target_means = df.groupby('category')['target'].mean()
df['category_target_encoded'] = df['category'].map(target_means)

df.to_csv('target_encoded.csv', index=False)
"""

# =============================================================================
# GEOGRAPHIC PROCESSORS
# =============================================================================

GEO_POINT_CREATOR_EXAMPLE = """
import pandas as pd

df = pd.read_csv('data.csv')

# Create geo point string from lat/lon
df['geo_point'] = df.apply(
    lambda row: f"POINT({row['longitude']} {row['latitude']})",
    axis=1
)

df.to_csv('geo_points.csv', index=False)
"""

GEO_ENCODER_EXAMPLE = """
import pandas as pd

df = pd.read_csv('addresses.csv')

# Simulated geocoding (in practice, use a geocoding API)
# This is a placeholder showing the pattern
df['latitude'] = 0.0
df['longitude'] = 0.0

df.to_csv('geocoded.csv', index=False)
"""

GEO_DISTANCE_CALCULATOR_EXAMPLE = """
import pandas as pd
import numpy as np

df = pd.read_csv('locations.csv')

# Haversine distance calculation
def haversine(lat1, lon1, lat2, lon2):
    R = 6371  # Earth's radius in km
    lat1, lon1, lat2, lon2 = map(np.radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = np.sin(dlat/2)**2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon/2)**2
    return 2 * R * np.arcsin(np.sqrt(a))

df['distance_km'] = haversine(
    df['lat1'], df['lon1'],
    df['lat2'], df['lon2']
)

df.to_csv('distances.csv', index=False)
"""

# =============================================================================
# ARRAY/JSON PROCESSORS
# =============================================================================

ARRAY_SPLITTER_EXAMPLE = """
import pandas as pd

df = pd.read_csv('data.csv')

# Split array string into rows (explode)
df['tags'] = df['tags_string'].str.split(',')
df_exploded = df.explode('tags')

df_exploded.to_csv('array_split.csv', index=False)
"""

ARRAY_JOINER_EXAMPLE = """
import pandas as pd

df = pd.read_csv('data.csv')

# Join array elements into string
df['tags_joined'] = df['tags'].apply(lambda x: ','.join(x) if isinstance(x, list) else x)

df.to_csv('array_joined.csv', index=False)
"""

JSON_FLATTENER_EXAMPLE = """
import pandas as pd
import json

df = pd.read_csv('data.csv')

# Flatten JSON column
df['json_data'] = df['json_string'].apply(json.loads)
df_flat = pd.json_normalize(df['json_data'])
df = pd.concat([df.drop('json_data', axis=1), df_flat], axis=1)

df.to_csv('flattened.csv', index=False)
"""

JSON_EXTRACTOR_EXAMPLE = """
import pandas as pd
import json

df = pd.read_csv('data.csv')

# Extract specific JSON fields
def extract_json_field(json_str, field):
    try:
        data = json.loads(json_str)
        return data.get(field)
    except:
        return None

df['name'] = df['json_data'].apply(lambda x: extract_json_field(x, 'name'))
df['value'] = df['json_data'].apply(lambda x: extract_json_field(x, 'value'))

df.to_csv('json_extracted.csv', index=False)
"""

# =============================================================================
# PYTHON UDF PROCESSOR
# =============================================================================

PYTHON_UDF_EXAMPLE = """
import pandas as pd

df = pd.read_csv('data.csv')

# Custom Python function
def custom_transform(row):
    if row['type'] == 'A':
        return row['value'] * 1.1
    elif row['type'] == 'B':
        return row['value'] * 0.9
    else:
        return row['value']

df['transformed'] = df.apply(custom_transform, axis=1)

df.to_csv('udf_result.csv', index=False)
"""

# =============================================================================
# PROCESSOR EXAMPLES REGISTRY
# =============================================================================

PROCESSOR_EXAMPLES: Dict[str, str] = {
    # Column Manipulation
    "column_renamer": COLUMN_RENAMER_EXAMPLE,
    "column_copier": COLUMN_COPIER_EXAMPLE,
    "column_deleter": COLUMN_DELETER_EXAMPLE,
    "columns_selector": COLUMNS_SELECTOR_EXAMPLE,
    "column_reorder": COLUMN_REORDER_EXAMPLE,
    "columns_concatenator": COLUMNS_CONCATENATOR_EXAMPLE,

    # Missing Value Handling
    "fill_empty_with_value": FILL_EMPTY_WITH_VALUE_EXAMPLE,
    "remove_rows_on_empty": REMOVE_ROWS_ON_EMPTY_EXAMPLE,
    "fill_empty_with_previous_next": FILL_EMPTY_WITH_PREVIOUS_NEXT_EXAMPLE,
    "fill_empty_with_computed_value": FILL_EMPTY_WITH_COMPUTED_VALUE_EXAMPLE,
    "impute_with_ml": IMPUTE_WITH_ML_EXAMPLE,

    # String Transformations
    "string_transformer_uppercase": STRING_TRANSFORMER_UPPERCASE_EXAMPLE,
    "string_transformer_lowercase": STRING_TRANSFORMER_LOWERCASE_EXAMPLE,
    "string_transformer_titlecase": STRING_TRANSFORMER_TITLECASE_EXAMPLE,
    "string_transformer_trim": STRING_TRANSFORMER_TRIM_EXAMPLE,
    "string_transformer_normalize_whitespace": STRING_TRANSFORMER_NORMALIZE_WHITESPACE_EXAMPLE,
    "tokenizer": TOKENIZER_EXAMPLE,
    "regexp_extractor": REGEXP_EXTRACTOR_EXAMPLE,
    "find_replace": FIND_REPLACE_EXAMPLE,
    "split_column": SPLIT_COLUMN_EXAMPLE,
    "concat_columns": CONCAT_COLUMNS_EXAMPLE,
    "html_stripper": HTML_STRIPPER_EXAMPLE,
    "ngrammer": NGRAMMER_EXAMPLE,
    "text_simplifier": TEXT_SIMPLIFIER_EXAMPLE,
    "stem_text": STEM_TEXT_EXAMPLE,
    "lemmatize_text": LEMMATIZE_TEXT_EXAMPLE,
    "url_parser": URL_PARSER_EXAMPLE,
    "email_domain_extractor": EMAIL_DOMAIN_EXTRACTOR_EXAMPLE,

    # Numeric Transformations
    "numerical_transformer_multiply": NUMERICAL_TRANSFORMER_MULTIPLY_EXAMPLE,
    "numerical_transformer_divide": NUMERICAL_TRANSFORMER_DIVIDE_EXAMPLE,
    "numerical_transformer_add": NUMERICAL_TRANSFORMER_ADD_EXAMPLE,
    "numerical_transformer_subtract": NUMERICAL_TRANSFORMER_SUBTRACT_EXAMPLE,
    "numerical_transformer_power": NUMERICAL_TRANSFORMER_POWER_EXAMPLE,
    "numerical_transformer_log": NUMERICAL_TRANSFORMER_LOG_EXAMPLE,
    "round_column": ROUND_COLUMN_EXAMPLE,
    "abs_column": ABS_COLUMN_EXAMPLE,
    "clip_column": CLIP_COLUMN_EXAMPLE,
    "binner": BINNER_EXAMPLE,
    "normalizer": NORMALIZER_EXAMPLE,
    "discretizer": DISCRETIZER_EXAMPLE,

    # Type Conversion
    "type_setter": TYPE_SETTER_EXAMPLE,
    "date_parser": DATE_PARSER_EXAMPLE,
    "date_formatter": DATE_FORMATTER_EXAMPLE,
    "boolean_converter": BOOLEAN_CONVERTER_EXAMPLE,

    # Date/Time Operations
    "date_components_extractor": DATE_COMPONENTS_EXTRACTOR_EXAMPLE,
    "date_diff_calculator": DATE_DIFF_CALCULATOR_EXAMPLE,
    "timezone_converter": TIMEZONE_CONVERTER_EXAMPLE,

    # Filtering
    "filter_on_value": FILTER_ON_VALUE_EXAMPLE,
    "filter_on_bad_type": FILTER_ON_BAD_TYPE_EXAMPLE,
    "filter_on_formula": FILTER_ON_FORMULA_EXAMPLE,
    "filter_on_date_range": FILTER_ON_DATE_RANGE_EXAMPLE,
    "filter_on_numeric_range": FILTER_ON_NUMERIC_RANGE_EXAMPLE,
    "filter_on_multiple_values": FILTER_ON_MULTIPLE_VALUES_EXAMPLE,

    # Flagging
    "flag_on_value": FLAG_ON_VALUE_EXAMPLE,
    "flag_on_formula": FLAG_ON_FORMULA_EXAMPLE,
    "flag_on_bad_type": FLAG_ON_BAD_TYPE_EXAMPLE,
    "flag_on_date_range": FLAG_ON_DATE_RANGE_EXAMPLE,
    "flag_on_numeric_range": FLAG_ON_NUMERIC_RANGE_EXAMPLE,

    # Row Operations
    "remove_duplicates": REMOVE_DUPLICATES_EXAMPLE,
    "sort_rows": SORT_ROWS_EXAMPLE,
    "sample_rows": SAMPLE_ROWS_EXAMPLE,
    "shuffle_rows": SHUFFLE_ROWS_EXAMPLE,

    # Computed Columns
    "create_column_with_grel": CREATE_COLUMN_WITH_GREL_EXAMPLE,
    "formula": FORMULA_EXAMPLE,
    "multi_column_formula": MULTI_COLUMN_FORMULA_EXAMPLE,
    "hash_computer": HASH_COMPUTER_EXAMPLE,
    "uuid_generator": UUID_GENERATOR_EXAMPLE,

    # Categorical
    "merge_long_tail_values": MERGE_LONG_TAIL_VALUES_EXAMPLE,
    "categorical_encoder": CATEGORICAL_ENCODER_EXAMPLE,
    "one_hot_encoder": ONE_HOT_ENCODER_EXAMPLE,
    "label_encoder": LABEL_ENCODER_EXAMPLE,
    "target_encoder": TARGET_ENCODER_EXAMPLE,

    # Geographic
    "geo_point_creator": GEO_POINT_CREATOR_EXAMPLE,
    "geo_encoder": GEO_ENCODER_EXAMPLE,
    "geo_distance_calculator": GEO_DISTANCE_CALCULATOR_EXAMPLE,

    # Array/JSON
    "array_splitter": ARRAY_SPLITTER_EXAMPLE,
    "array_joiner": ARRAY_JOINER_EXAMPLE,
    "json_flattener": JSON_FLATTENER_EXAMPLE,
    "json_extractor": JSON_EXTRACTOR_EXAMPLE,

    # Python UDF
    "python_udf": PYTHON_UDF_EXAMPLE,
}


def get_processor_example(name: str) -> str:
    """Get a processor example by name."""
    return PROCESSOR_EXAMPLES.get(name, "")


def list_processor_examples() -> list:
    """List all available processor examples."""
    return list(PROCESSOR_EXAMPLES.keys())
