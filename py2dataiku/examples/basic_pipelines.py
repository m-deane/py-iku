"""
Basic data processing pipeline examples for py2dataiku.

These examples demonstrate simple, single-operation data transformations
that map directly to Dataiku visual recipes.
"""

# Example 1: Simple Data Cleaning
BASIC_CLEANING = """
import pandas as pd

# Load raw data
df = pd.read_csv('raw_data.csv')

# Remove rows with missing values
df = df.dropna()

# Save cleaned data
df.to_csv('cleaned_data.csv', index=False)
"""

# Example 2: Column Transformations
BASIC_COLUMN_TRANSFORM = """
import pandas as pd

# Load data
df = pd.read_csv('customers.csv')

# Clean text columns
df['name'] = df['name'].str.strip()
df['name'] = df['name'].str.title()
df['email'] = df['email'].str.lower()

# Save result
df.to_csv('customers_cleaned.csv', index=False)
"""

# Example 3: Filtering Data
BASIC_FILTERING = """
import pandas as pd

# Load sales data
sales = pd.read_csv('sales.csv')

# Filter to high-value transactions
high_value = sales[sales['amount'] > 1000]

# Save filtered data
high_value.to_csv('high_value_sales.csv', index=False)
"""

# Example 4: Simple Aggregation
BASIC_AGGREGATION = """
import pandas as pd

# Load transaction data
transactions = pd.read_csv('transactions.csv')

# Group by category and sum amounts
summary = transactions.groupby('category').agg({
    'amount': 'sum'
}).reset_index()

# Save summary
summary.to_csv('category_summary.csv', index=False)
"""

# Example 5: Sorting Data
BASIC_SORTING = """
import pandas as pd

# Load products
products = pd.read_csv('products.csv')

# Sort by price descending
products_sorted = products.sort_values('price', ascending=False)

# Save sorted data
products_sorted.to_csv('products_by_price.csv', index=False)
"""

# Example 6: Removing Duplicates
BASIC_DEDUPLICATION = """
import pandas as pd

# Load customer list
customers = pd.read_csv('customer_list.csv')

# Remove duplicate emails
customers_unique = customers.drop_duplicates(subset=['email'])

# Save deduplicated list
customers_unique.to_csv('unique_customers.csv', index=False)
"""

# Example 7: Type Conversion
BASIC_TYPE_CONVERSION = """
import pandas as pd

# Load data
df = pd.read_csv('data.csv')

# Convert date column
df['order_date'] = pd.to_datetime(df['order_date'])

# Convert amount to float
df['amount'] = df['amount'].astype(float)

# Save result
df.to_csv('data_typed.csv', index=False)
"""

# Example 8: Fill Missing Values
BASIC_FILL_MISSING = """
import pandas as pd

# Load survey data
survey = pd.read_csv('survey_responses.csv')

# Fill missing numeric values with 0
survey['score'] = survey['score'].fillna(0)

# Fill missing text with 'Unknown'
survey['category'] = survey['category'].fillna('Unknown')

# Save result
survey.to_csv('survey_complete.csv', index=False)
"""

# Example 9: Column Selection
BASIC_COLUMN_SELECTION = """
import pandas as pd

# Load full dataset
full_data = pd.read_csv('full_dataset.csv')

# Select only needed columns
selected = full_data[['id', 'name', 'email', 'created_at']]

# Save selected columns
selected.to_csv('selected_columns.csv', index=False)
"""

# Example 10: Top N Records
BASIC_TOP_N = """
import pandas as pd

# Load sales data
sales = pd.read_csv('sales.csv')

# Get top 10 highest sales
top_10 = sales.nlargest(10, 'amount')

# Save top records
top_10.to_csv('top_10_sales.csv', index=False)
"""

# All basic examples
BASIC_EXAMPLES = {
    "cleaning": BASIC_CLEANING,
    "column_transform": BASIC_COLUMN_TRANSFORM,
    "filtering": BASIC_FILTERING,
    "aggregation": BASIC_AGGREGATION,
    "sorting": BASIC_SORTING,
    "deduplication": BASIC_DEDUPLICATION,
    "type_conversion": BASIC_TYPE_CONVERSION,
    "fill_missing": BASIC_FILL_MISSING,
    "column_selection": BASIC_COLUMN_SELECTION,
    "top_n": BASIC_TOP_N,
}
