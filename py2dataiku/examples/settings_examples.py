"""
Comprehensive examples for every Dataiku DSS recipe setting.

This module provides Python code examples that demonstrate all possible
settings for various Dataiku recipes including join types, aggregation
functions, string transformer modes, numerical transformer modes, and more.
"""

from typing import Dict, Any

# =============================================================================
# JOIN TYPE SETTINGS
# =============================================================================

JOIN_TYPE_INNER_EXAMPLE = """
import pandas as pd

left = pd.read_csv('customers.csv')
right = pd.read_csv('orders.csv')

# INNER join - only matching rows from both tables
result = pd.merge(left, right, on='customer_id', how='inner')

result.to_csv('inner_join.csv', index=False)
"""

JOIN_TYPE_LEFT_EXAMPLE = """
import pandas as pd

left = pd.read_csv('customers.csv')
right = pd.read_csv('orders.csv')

# LEFT join - all rows from left, matching from right
result = pd.merge(left, right, on='customer_id', how='left')

result.to_csv('left_join.csv', index=False)
"""

JOIN_TYPE_RIGHT_EXAMPLE = """
import pandas as pd

left = pd.read_csv('customers.csv')
right = pd.read_csv('orders.csv')

# RIGHT join - all rows from right, matching from left
result = pd.merge(left, right, on='customer_id', how='right')

result.to_csv('right_join.csv', index=False)
"""

JOIN_TYPE_OUTER_EXAMPLE = """
import pandas as pd

left = pd.read_csv('customers.csv')
right = pd.read_csv('orders.csv')

# OUTER/FULL join - all rows from both tables
result = pd.merge(left, right, on='customer_id', how='outer')

result.to_csv('outer_join.csv', index=False)
"""

JOIN_TYPE_CROSS_EXAMPLE = """
import pandas as pd

products = pd.read_csv('products.csv')
regions = pd.read_csv('regions.csv')

# CROSS join - cartesian product
result = pd.merge(products, regions, how='cross')

result.to_csv('cross_join.csv', index=False)
"""

JOIN_TYPE_LEFT_ANTI_EXAMPLE = """
import pandas as pd

all_customers = pd.read_csv('customers.csv')
active_orders = pd.read_csv('orders.csv')

# LEFT ANTI join - rows in left that don't match right
merged = pd.merge(all_customers, active_orders, on='customer_id', how='left', indicator=True)
result = merged[merged['_merge'] == 'left_only'].drop('_merge', axis=1)

result.to_csv('left_anti_join.csv', index=False)
"""

# =============================================================================
# AGGREGATION FUNCTION SETTINGS
# =============================================================================

AGG_SUM_EXAMPLE = """
import pandas as pd

df = pd.read_csv('sales.csv')

# SUM aggregation
result = df.groupby('category').agg({'amount': 'sum'}).reset_index()
result.columns = ['category', 'total_amount']

result.to_csv('sum_agg.csv', index=False)
"""

AGG_AVG_EXAMPLE = """
import pandas as pd

df = pd.read_csv('sales.csv')

# AVG/MEAN aggregation
result = df.groupby('category').agg({'amount': 'mean'}).reset_index()
result.columns = ['category', 'avg_amount']

result.to_csv('avg_agg.csv', index=False)
"""

AGG_COUNT_EXAMPLE = """
import pandas as pd

df = pd.read_csv('sales.csv')

# COUNT aggregation
result = df.groupby('category').agg({'transaction_id': 'count'}).reset_index()
result.columns = ['category', 'transaction_count']

result.to_csv('count_agg.csv', index=False)
"""

AGG_MIN_EXAMPLE = """
import pandas as pd

df = pd.read_csv('sales.csv')

# MIN aggregation
result = df.groupby('category').agg({'amount': 'min'}).reset_index()
result.columns = ['category', 'min_amount']

result.to_csv('min_agg.csv', index=False)
"""

AGG_MAX_EXAMPLE = """
import pandas as pd

df = pd.read_csv('sales.csv')

# MAX aggregation
result = df.groupby('category').agg({'amount': 'max'}).reset_index()
result.columns = ['category', 'max_amount']

result.to_csv('max_agg.csv', index=False)
"""

AGG_FIRST_EXAMPLE = """
import pandas as pd

df = pd.read_csv('sales.csv')

# FIRST aggregation
result = df.groupby('category').agg({'date': 'first'}).reset_index()
result.columns = ['category', 'first_date']

result.to_csv('first_agg.csv', index=False)
"""

AGG_LAST_EXAMPLE = """
import pandas as pd

df = pd.read_csv('sales.csv')

# LAST aggregation
result = df.groupby('category').agg({'date': 'last'}).reset_index()
result.columns = ['category', 'last_date']

result.to_csv('last_agg.csv', index=False)
"""

AGG_STD_EXAMPLE = """
import pandas as pd

df = pd.read_csv('sales.csv')

# STD (standard deviation) aggregation
result = df.groupby('category').agg({'amount': 'std'}).reset_index()
result.columns = ['category', 'amount_std']

result.to_csv('std_agg.csv', index=False)
"""

AGG_VAR_EXAMPLE = """
import pandas as pd

df = pd.read_csv('sales.csv')

# VAR (variance) aggregation
result = df.groupby('category').agg({'amount': 'var'}).reset_index()
result.columns = ['category', 'amount_var']

result.to_csv('var_agg.csv', index=False)
"""

AGG_NUNIQUE_EXAMPLE = """
import pandas as pd

df = pd.read_csv('sales.csv')

# NUNIQUE (count unique) aggregation
result = df.groupby('category').agg({'customer_id': 'nunique'}).reset_index()
result.columns = ['category', 'unique_customers']

result.to_csv('nunique_agg.csv', index=False)
"""

AGG_MEDIAN_EXAMPLE = """
import pandas as pd

df = pd.read_csv('sales.csv')

# MEDIAN aggregation
result = df.groupby('category').agg({'amount': 'median'}).reset_index()
result.columns = ['category', 'median_amount']

result.to_csv('median_agg.csv', index=False)
"""

AGG_MODE_EXAMPLE = """
import pandas as pd

df = pd.read_csv('sales.csv')

# MODE aggregation
result = df.groupby('category')['product'].agg(
    lambda x: x.mode()[0] if len(x.mode()) > 0 else None
).reset_index()
result.columns = ['category', 'most_common_product']

result.to_csv('mode_agg.csv', index=False)
"""

AGG_PERCENTILE_EXAMPLE = """
import pandas as pd
import numpy as np

df = pd.read_csv('sales.csv')

# PERCENTILE aggregations
result = df.groupby('category').agg({
    'amount': [
        lambda x: np.percentile(x, 25),  # P25
        lambda x: np.percentile(x, 50),  # P50 (median)
        lambda x: np.percentile(x, 75),  # P75
        lambda x: np.percentile(x, 90),  # P90
        lambda x: np.percentile(x, 95),  # P95
        lambda x: np.percentile(x, 99),  # P99
    ]
}).reset_index()
result.columns = ['category', 'p25', 'p50', 'p75', 'p90', 'p95', 'p99']

result.to_csv('percentile_agg.csv', index=False)
"""

AGG_MIXED_EXAMPLE = """
import pandas as pd

df = pd.read_csv('sales.csv')

# Mixed aggregations on single groupby
result = df.groupby('category').agg({
    'amount': ['sum', 'mean', 'std', 'min', 'max'],
    'quantity': ['sum', 'mean'],
    'customer_id': 'nunique',
    'transaction_id': 'count'
}).reset_index()

# Flatten column names
result.columns = ['_'.join(col).strip('_') for col in result.columns]

result.to_csv('mixed_agg.csv', index=False)
"""

# =============================================================================
# STRING TRANSFORMER MODE SETTINGS
# =============================================================================

STRING_MODE_TO_UPPER_EXAMPLE = """
import pandas as pd

df = pd.read_csv('data.csv')

# TO_UPPER mode
df['name_upper'] = df['name'].str.upper()

df.to_csv('upper.csv', index=False)
"""

STRING_MODE_TO_LOWER_EXAMPLE = """
import pandas as pd

df = pd.read_csv('data.csv')

# TO_LOWER mode
df['email_lower'] = df['email'].str.lower()

df.to_csv('lower.csv', index=False)
"""

STRING_MODE_TITLECASE_EXAMPLE = """
import pandas as pd

df = pd.read_csv('data.csv')

# TITLECASE mode
df['name_title'] = df['name'].str.title()

df.to_csv('title.csv', index=False)
"""

STRING_MODE_CAPITALIZE_EXAMPLE = """
import pandas as pd

df = pd.read_csv('data.csv')

# CAPITALIZE mode (first letter uppercase)
df['sentence_cap'] = df['sentence'].str.capitalize()

df.to_csv('capitalize.csv', index=False)
"""

STRING_MODE_SWAPCASE_EXAMPLE = """
import pandas as pd

df = pd.read_csv('data.csv')

# SWAPCASE mode
df['text_swapped'] = df['text'].str.swapcase()

df.to_csv('swapcase.csv', index=False)
"""

STRING_MODE_TRIM_EXAMPLE = """
import pandas as pd

df = pd.read_csv('data.csv')

# TRIM mode (both sides)
df['name_trimmed'] = df['name'].str.strip()

df.to_csv('trim.csv', index=False)
"""

STRING_MODE_TRIM_LEFT_EXAMPLE = """
import pandas as pd

df = pd.read_csv('data.csv')

# TRIM_LEFT mode
df['text_ltrim'] = df['text'].str.lstrip()

df.to_csv('ltrim.csv', index=False)
"""

STRING_MODE_TRIM_RIGHT_EXAMPLE = """
import pandas as pd

df = pd.read_csv('data.csv')

# TRIM_RIGHT mode
df['text_rtrim'] = df['text'].str.rstrip()

df.to_csv('rtrim.csv', index=False)
"""

STRING_MODE_NORMALIZE_WHITESPACE_EXAMPLE = """
import pandas as pd

df = pd.read_csv('data.csv')

# NORMALIZE_WHITESPACE mode (multiple spaces to single)
df['text_normalized'] = df['text'].str.replace(r'\\s+', ' ', regex=True).str.strip()

df.to_csv('normalize_whitespace.csv', index=False)
"""

STRING_MODE_REMOVE_WHITESPACE_EXAMPLE = """
import pandas as pd

df = pd.read_csv('data.csv')

# REMOVE_WHITESPACE mode
df['code_no_spaces'] = df['code'].str.replace(' ', '')

df.to_csv('remove_whitespace.csv', index=False)
"""

STRING_MODE_REMOVE_ACCENTS_EXAMPLE = """
import pandas as pd
import unicodedata

df = pd.read_csv('data.csv')

# REMOVE_ACCENTS mode
def remove_accents(text):
    return ''.join(
        c for c in unicodedata.normalize('NFD', str(text))
        if unicodedata.category(c) != 'Mn'
    )

df['name_no_accents'] = df['name'].apply(remove_accents)

df.to_csv('remove_accents.csv', index=False)
"""

STRING_MODE_ALL_MODES_EXAMPLE = """
import pandas as pd
import unicodedata

df = pd.read_csv('data.csv')

# Apply all string transformer modes to demonstrate each
df['mode_upper'] = df['text'].str.upper()
df['mode_lower'] = df['text'].str.lower()
df['mode_title'] = df['text'].str.title()
df['mode_capitalize'] = df['text'].str.capitalize()
df['mode_swapcase'] = df['text'].str.swapcase()
df['mode_trim'] = df['text'].str.strip()
df['mode_ltrim'] = df['text'].str.lstrip()
df['mode_rtrim'] = df['text'].str.rstrip()
df['mode_normalize_ws'] = df['text'].str.replace(r'\\s+', ' ', regex=True)
df['mode_remove_ws'] = df['text'].str.replace(' ', '')

df.to_csv('all_string_modes.csv', index=False)
"""

# =============================================================================
# NUMERICAL TRANSFORMER MODE SETTINGS
# =============================================================================

NUMERICAL_MODE_MULTIPLY_EXAMPLE = """
import pandas as pd

df = pd.read_csv('data.csv')

# MULTIPLY mode
df['amount_doubled'] = df['amount'] * 2
df['cents'] = df['dollars'] * 100

df.to_csv('multiply.csv', index=False)
"""

NUMERICAL_MODE_DIVIDE_EXAMPLE = """
import pandas as pd

df = pd.read_csv('data.csv')

# DIVIDE mode
df['amount_halved'] = df['amount'] / 2
df['thousands'] = df['value'] / 1000

df.to_csv('divide.csv', index=False)
"""

NUMERICAL_MODE_ADD_EXAMPLE = """
import pandas as pd

df = pd.read_csv('data.csv')

# ADD mode
df['score_plus_10'] = df['score'] + 10
df['adjusted'] = df['value'] + 100

df.to_csv('add.csv', index=False)
"""

NUMERICAL_MODE_SUBTRACT_EXAMPLE = """
import pandas as pd

df = pd.read_csv('data.csv')

# SUBTRACT mode
df['net'] = df['gross'] - df['deductions']
df['adjusted'] = df['value'] - 50

df.to_csv('subtract.csv', index=False)
"""

NUMERICAL_MODE_POWER_EXAMPLE = """
import pandas as pd
import numpy as np

df = pd.read_csv('data.csv')

# POWER mode
df['squared'] = df['value'] ** 2
df['cubed'] = df['value'] ** 3
df['sqrt'] = df['value'] ** 0.5

df.to_csv('power.csv', index=False)
"""

NUMERICAL_MODE_LOG_EXAMPLE = """
import pandas as pd
import numpy as np

df = pd.read_csv('data.csv')

# LOG mode variants
df['log_natural'] = np.log(df['value'])
df['log10'] = np.log10(df['value'])
df['log2'] = np.log2(df['value'])
df['log1p'] = np.log1p(df['value'])

df.to_csv('log.csv', index=False)
"""

NUMERICAL_MODE_EXP_EXAMPLE = """
import pandas as pd
import numpy as np

df = pd.read_csv('data.csv')

# EXP mode
df['exp_value'] = np.exp(df['value'])
df['expm1'] = np.expm1(df['value'])

df.to_csv('exp.csv', index=False)
"""

NUMERICAL_MODE_ABS_EXAMPLE = """
import pandas as pd

df = pd.read_csv('data.csv')

# ABS mode
df['abs_change'] = df['change'].abs()
df['abs_delta'] = df['delta'].abs()

df.to_csv('abs.csv', index=False)
"""

NUMERICAL_MODE_ROUND_EXAMPLE = """
import pandas as pd

df = pd.read_csv('data.csv')

# ROUND mode
df['rounded_2'] = df['amount'].round(2)
df['rounded_0'] = df['amount'].round(0)
df['rounded_neg1'] = df['amount'].round(-1)  # To nearest 10

df.to_csv('round.csv', index=False)
"""

NUMERICAL_MODE_FLOOR_EXAMPLE = """
import pandas as pd
import numpy as np

df = pd.read_csv('data.csv')

# FLOOR mode
df['floored'] = np.floor(df['value'])

df.to_csv('floor.csv', index=False)
"""

NUMERICAL_MODE_CEIL_EXAMPLE = """
import pandas as pd
import numpy as np

df = pd.read_csv('data.csv')

# CEIL mode
df['ceiling'] = np.ceil(df['value'])

df.to_csv('ceil.csv', index=False)
"""

NUMERICAL_MODE_TRUNCATE_EXAMPLE = """
import pandas as pd
import numpy as np

df = pd.read_csv('data.csv')

# TRUNCATE mode
df['truncated'] = np.trunc(df['value'])

df.to_csv('truncate.csv', index=False)
"""

NUMERICAL_MODE_SIN_EXAMPLE = """
import pandas as pd
import numpy as np

df = pd.read_csv('data.csv')

# SIN mode (trigonometric)
df['sin_value'] = np.sin(df['angle_radians'])

df.to_csv('sin.csv', index=False)
"""

NUMERICAL_MODE_COS_EXAMPLE = """
import pandas as pd
import numpy as np

df = pd.read_csv('data.csv')

# COS mode (trigonometric)
df['cos_value'] = np.cos(df['angle_radians'])

df.to_csv('cos.csv', index=False)
"""

NUMERICAL_MODE_ALL_MODES_EXAMPLE = """
import pandas as pd
import numpy as np

df = pd.read_csv('data.csv')

# Apply all numerical transformer modes
df['mode_multiply'] = df['value'] * 2
df['mode_divide'] = df['value'] / 2
df['mode_add'] = df['value'] + 10
df['mode_subtract'] = df['value'] - 10
df['mode_power'] = df['value'] ** 2
df['mode_sqrt'] = np.sqrt(df['value'].abs())
df['mode_log'] = np.log(df['value'].clip(lower=0.001))
df['mode_exp'] = np.exp(df['value'].clip(upper=10))
df['mode_abs'] = df['value'].abs()
df['mode_round'] = df['value'].round(2)
df['mode_floor'] = np.floor(df['value'])
df['mode_ceil'] = np.ceil(df['value'])

df.to_csv('all_numerical_modes.csv', index=False)
"""

# =============================================================================
# WINDOW FUNCTION SETTINGS
# =============================================================================

WINDOW_ROW_NUMBER_EXAMPLE = """
import pandas as pd

df = pd.read_csv('data.csv')
df = df.sort_values(['category', 'date'])

# ROW_NUMBER
df['row_num'] = df.groupby('category').cumcount() + 1

df.to_csv('row_number.csv', index=False)
"""

WINDOW_RANK_EXAMPLE = """
import pandas as pd

df = pd.read_csv('data.csv')

# RANK
df['rank'] = df.groupby('category')['score'].rank(method='min')

df.to_csv('rank.csv', index=False)
"""

WINDOW_DENSE_RANK_EXAMPLE = """
import pandas as pd

df = pd.read_csv('data.csv')

# DENSE_RANK
df['dense_rank'] = df.groupby('category')['score'].rank(method='dense')

df.to_csv('dense_rank.csv', index=False)
"""

WINDOW_LAG_EXAMPLE = """
import pandas as pd

df = pd.read_csv('data.csv')
df = df.sort_values(['category', 'date'])

# LAG
df['prev_value'] = df.groupby('category')['value'].shift(1)
df['prev_2_value'] = df.groupby('category')['value'].shift(2)

df.to_csv('lag.csv', index=False)
"""

WINDOW_LEAD_EXAMPLE = """
import pandas as pd

df = pd.read_csv('data.csv')
df = df.sort_values(['category', 'date'])

# LEAD
df['next_value'] = df.groupby('category')['value'].shift(-1)
df['next_2_value'] = df.groupby('category')['value'].shift(-2)

df.to_csv('lead.csv', index=False)
"""

WINDOW_RUNNING_SUM_EXAMPLE = """
import pandas as pd

df = pd.read_csv('data.csv')
df = df.sort_values(['category', 'date'])

# RUNNING_SUM
df['running_sum'] = df.groupby('category')['value'].cumsum()

df.to_csv('running_sum.csv', index=False)
"""

WINDOW_RUNNING_AVG_EXAMPLE = """
import pandas as pd

df = pd.read_csv('data.csv')
df = df.sort_values(['category', 'date'])

# RUNNING_AVG
df['running_avg'] = df.groupby('category')['value'].expanding().mean().reset_index(level=0, drop=True)

df.to_csv('running_avg.csv', index=False)
"""

WINDOW_MOVING_AVG_EXAMPLE = """
import pandas as pd

df = pd.read_csv('data.csv')
df = df.sort_values(['category', 'date'])

# MOVING_AVG (rolling)
df['moving_avg_7'] = df.groupby('category')['value'].transform(
    lambda x: x.rolling(window=7, min_periods=1).mean()
)

df.to_csv('moving_avg.csv', index=False)
"""

WINDOW_MOVING_SUM_EXAMPLE = """
import pandas as pd

df = pd.read_csv('data.csv')
df = df.sort_values(['category', 'date'])

# MOVING_SUM (rolling)
df['moving_sum_7'] = df.groupby('category')['value'].transform(
    lambda x: x.rolling(window=7, min_periods=1).sum()
)

df.to_csv('moving_sum.csv', index=False)
"""

# =============================================================================
# SETTINGS EXAMPLES REGISTRY
# =============================================================================

SETTINGS_EXAMPLES: Dict[str, str] = {
    # Join Types
    "join_inner": JOIN_TYPE_INNER_EXAMPLE,
    "join_left": JOIN_TYPE_LEFT_EXAMPLE,
    "join_right": JOIN_TYPE_RIGHT_EXAMPLE,
    "join_outer": JOIN_TYPE_OUTER_EXAMPLE,
    "join_cross": JOIN_TYPE_CROSS_EXAMPLE,
    "join_left_anti": JOIN_TYPE_LEFT_ANTI_EXAMPLE,

    # Aggregation Functions
    "agg_sum": AGG_SUM_EXAMPLE,
    "agg_avg": AGG_AVG_EXAMPLE,
    "agg_count": AGG_COUNT_EXAMPLE,
    "agg_min": AGG_MIN_EXAMPLE,
    "agg_max": AGG_MAX_EXAMPLE,
    "agg_first": AGG_FIRST_EXAMPLE,
    "agg_last": AGG_LAST_EXAMPLE,
    "agg_std": AGG_STD_EXAMPLE,
    "agg_var": AGG_VAR_EXAMPLE,
    "agg_nunique": AGG_NUNIQUE_EXAMPLE,
    "agg_median": AGG_MEDIAN_EXAMPLE,
    "agg_mode": AGG_MODE_EXAMPLE,
    "agg_percentile": AGG_PERCENTILE_EXAMPLE,
    "agg_mixed": AGG_MIXED_EXAMPLE,

    # String Transformer Modes
    "string_upper": STRING_MODE_TO_UPPER_EXAMPLE,
    "string_lower": STRING_MODE_TO_LOWER_EXAMPLE,
    "string_title": STRING_MODE_TITLECASE_EXAMPLE,
    "string_capitalize": STRING_MODE_CAPITALIZE_EXAMPLE,
    "string_swapcase": STRING_MODE_SWAPCASE_EXAMPLE,
    "string_trim": STRING_MODE_TRIM_EXAMPLE,
    "string_ltrim": STRING_MODE_TRIM_LEFT_EXAMPLE,
    "string_rtrim": STRING_MODE_TRIM_RIGHT_EXAMPLE,
    "string_normalize_ws": STRING_MODE_NORMALIZE_WHITESPACE_EXAMPLE,
    "string_remove_ws": STRING_MODE_REMOVE_WHITESPACE_EXAMPLE,
    "string_remove_accents": STRING_MODE_REMOVE_ACCENTS_EXAMPLE,
    "string_all_modes": STRING_MODE_ALL_MODES_EXAMPLE,

    # Numerical Transformer Modes
    "num_multiply": NUMERICAL_MODE_MULTIPLY_EXAMPLE,
    "num_divide": NUMERICAL_MODE_DIVIDE_EXAMPLE,
    "num_add": NUMERICAL_MODE_ADD_EXAMPLE,
    "num_subtract": NUMERICAL_MODE_SUBTRACT_EXAMPLE,
    "num_power": NUMERICAL_MODE_POWER_EXAMPLE,
    "num_log": NUMERICAL_MODE_LOG_EXAMPLE,
    "num_exp": NUMERICAL_MODE_EXP_EXAMPLE,
    "num_abs": NUMERICAL_MODE_ABS_EXAMPLE,
    "num_round": NUMERICAL_MODE_ROUND_EXAMPLE,
    "num_floor": NUMERICAL_MODE_FLOOR_EXAMPLE,
    "num_ceil": NUMERICAL_MODE_CEIL_EXAMPLE,
    "num_truncate": NUMERICAL_MODE_TRUNCATE_EXAMPLE,
    "num_sin": NUMERICAL_MODE_SIN_EXAMPLE,
    "num_cos": NUMERICAL_MODE_COS_EXAMPLE,
    "num_all_modes": NUMERICAL_MODE_ALL_MODES_EXAMPLE,

    # Window Functions
    "window_row_number": WINDOW_ROW_NUMBER_EXAMPLE,
    "window_rank": WINDOW_RANK_EXAMPLE,
    "window_dense_rank": WINDOW_DENSE_RANK_EXAMPLE,
    "window_lag": WINDOW_LAG_EXAMPLE,
    "window_lead": WINDOW_LEAD_EXAMPLE,
    "window_running_sum": WINDOW_RUNNING_SUM_EXAMPLE,
    "window_running_avg": WINDOW_RUNNING_AVG_EXAMPLE,
    "window_moving_avg": WINDOW_MOVING_AVG_EXAMPLE,
    "window_moving_sum": WINDOW_MOVING_SUM_EXAMPLE,
}


def get_settings_example(name: str) -> str:
    """Get a settings example by name."""
    return SETTINGS_EXAMPLES.get(name, "")


def list_settings_examples() -> list:
    """List all available settings examples."""
    return list(SETTINGS_EXAMPLES.keys())
