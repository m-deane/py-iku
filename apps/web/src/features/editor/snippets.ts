/**
 * Curated Python snippets for the convert-page editor.
 *
 * Every snippet is paraphrased from `py2dataiku/examples/recipe_examples.py`
 * (or `processor_examples.py`) so the conversion engine has a deterministic
 * mapping back to a real RecipeType / ProcessorType. Do not invent new
 * snippets without first adding a matching example to the py-iku library —
 * otherwise users land on a "no recipe detected" failure on first run.
 */

export interface Snippet {
  id: string;
  name: string;
  description: string;
  code: string;
  /** Free-form labels surfaced by the picker filter. */
  tags: string[];
}

export const SNIPPETS: readonly Snippet[] = [
  {
    id: "groupby-agg",
    name: "Read CSV + groupby + agg",
    description:
      "Aggregate transactions by category. Maps to a GROUPING recipe.",
    tags: ["pandas", "groupby", "aggregation", "GROUPING"],
    code: `import pandas as pd

# Load data
df = pd.read_csv('transactions.csv')

# Group by single column with multiple aggregations
category_summary = df.groupby('category').agg({
    'amount': 'sum',
    'quantity': 'mean',
    'transaction_id': 'count',
}).reset_index()
category_summary.columns = ['category', 'total_amount', 'avg_quantity', 'transaction_count']

# Save output
category_summary.to_csv('category_summary.csv', index=False)
`,
  },
  {
    id: "merge-two-dataframes",
    name: "Merge two DataFrames",
    description:
      "Inner join customers and orders on customer_id. Maps to a JOIN recipe.",
    tags: ["pandas", "merge", "join", "JOIN"],
    code: `import pandas as pd

# Load datasets
customers = pd.read_csv('customers.csv')
orders = pd.read_csv('orders.csv')

# Inner join
customer_orders = pd.merge(
    customers,
    orders,
    on='customer_id',
    how='inner',
)

# Save output
customer_orders.to_csv('customer_orders.csv', index=False)
`,
  },
  {
    id: "sort-top-n",
    name: "Sort + select top-N",
    description:
      "Sort by sales then keep the top 10 rows. Maps to a SORT recipe followed by a TOP_N recipe.",
    tags: ["pandas", "sort", "nlargest", "SORT", "TOP_N"],
    code: `import pandas as pd

# Load data
df = pd.read_csv('sales.csv')

# Sort by sales amount descending
sorted_sales = df.sort_values('sales_amount', ascending=False)

# Top 10 by sales amount
top_10_sales = sorted_sales.nlargest(10, 'sales_amount')

# Save outputs
sorted_sales.to_csv('sales_sorted.csv', index=False)
top_10_sales.to_csv('top_10_sales.csv', index=False)
`,
  },
  {
    id: "pivot-melt",
    name: "Pivot / unpivot (melt)",
    description:
      "Reshape a wide monthly metrics table into long format. Maps to a PREPARE recipe with the FOLD_MULTIPLE_COLUMNS processor.",
    tags: ["pandas", "melt", "unpivot", "PREPARE", "FOLD_MULTIPLE_COLUMNS"],
    code: `import pandas as pd

# Load wide data
wide_df = pd.read_csv('monthly_metrics.csv')

# Melt (unpivot) wide -> long format
long_df = pd.melt(
    wide_df,
    id_vars=['product_id', 'product_name'],
    value_vars=['jan', 'feb', 'mar', 'apr', 'may', 'jun'],
    var_name='month',
    value_name='sales',
)

# Save output
long_df.to_csv('monthly_metrics_long.csv', index=False)
`,
  },
  {
    id: "window-rolling",
    name: "Window: rolling mean",
    description:
      "Compute rolling 7- and 30-day metrics on a time series. Maps to a WINDOW recipe.",
    tags: ["pandas", "rolling", "window", "WINDOW"],
    code: `import pandas as pd

# Load time series data
df = pd.read_csv('daily_metrics.csv')
df['date'] = pd.to_datetime(df['date'])
df = df.sort_values('date')

# Rolling window calculations
df['rolling_7d_avg'] = df['value'].rolling(window=7).mean()
df['rolling_30d_sum'] = df['value'].rolling(window=30).sum()
df['cumulative_sum'] = df['value'].cumsum()

# Save output
df.to_csv('metrics_with_windows.csv', index=False)
`,
  },
  {
    id: "sklearn-train-test-logistic",
    name: "Sklearn: train/test split + LogisticRegression",
    description:
      "Split a dataset and fit a logistic regression. Maps to a SPLIT recipe and a sklearn-model handler in py-iku.",
    tags: ["sklearn", "train_test_split", "LogisticRegression", "SPLIT"],
    code: `import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression

# Load data
df = pd.read_csv('customers.csv')

# Train / test split (stratified)
train, test = train_test_split(
    df,
    test_size=0.2,
    stratify=df['segment'],
    random_state=42,
)

# Fit a logistic regression on the training set
features = ['age', 'income', 'tenure_months']
model = LogisticRegression(max_iter=1000)
model.fit(train[features], train['churned'])

# Save outputs
train.to_csv('train_set.csv', index=False)
test.to_csv('test_set.csv', index=False)
`,
  },
];

/** Default snippet shown when the editor first mounts. */
export const DEFAULT_SNIPPET_ID = "groupby-agg";

export function getSnippet(id: string): Snippet | undefined {
  return SNIPPETS.find((s) => s.id === id);
}

export function getDefaultCode(): string {
  const fallback = SNIPPETS[0];
  return getSnippet(DEFAULT_SNIPPET_ID)?.code ?? fallback?.code ?? "";
}
