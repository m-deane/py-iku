"""
Demonstration of py2dataiku LLM-based code analysis.

This demo shows the LLM-first approach to converting Python code
to Dataiku DSS recipes. It uses the mock provider by default,
but can be configured to use real LLM providers.

Usage:
    # With mock provider (no API key needed)
    python -m py2dataiku.examples.llm_demo

    # With Anthropic
    ANTHROPIC_API_KEY=your_key python -m py2dataiku.examples.llm_demo --provider anthropic

    # With OpenAI
    OPENAI_API_KEY=your_key python -m py2dataiku.examples.llm_demo --provider openai
"""

import json
import sys
from py2dataiku.llm.analyzer import LLMCodeAnalyzer
from py2dataiku.llm.providers import MockProvider, get_provider
from py2dataiku.generators.llm_flow_generator import LLMFlowGenerator
from py2dataiku.generators.diagram_generator import DiagramGenerator


# Realistic mock response for demo
MOCK_RESPONSE = json.dumps({
    "code_summary": "Customer analytics pipeline: Load customer and order data, clean customer records, join with orders, aggregate spending by customer, and filter high-value customers.",
    "total_operations": 7,
    "complexity_score": 6,
    "datasets": [
        {"name": "customers", "source": "customers.csv", "is_input": True, "is_output": False, "inferred_columns": ["customer_id", "name", "email", "signup_date"]},
        {"name": "orders", "source": "orders.csv", "is_input": True, "is_output": False, "inferred_columns": ["order_id", "customer_id", "amount", "order_date"]},
        {"name": "customers_cleaned", "is_input": False, "is_output": False},
        {"name": "merged", "is_input": False, "is_output": False},
        {"name": "summary", "is_input": False, "is_output": False},
        {"name": "high_value", "is_input": False, "is_output": True},
    ],
    "steps": [
        {
            "step_number": 1,
            "operation": "read_data",
            "description": "Load customer data from CSV file",
            "output_dataset": "customers",
            "suggested_recipe": "sync",
            "reasoning": "Direct file read maps to Sync recipe or input dataset"
        },
        {
            "step_number": 2,
            "operation": "read_data",
            "description": "Load order data from CSV file",
            "output_dataset": "orders",
            "suggested_recipe": "sync",
            "reasoning": "Direct file read maps to Sync recipe or input dataset"
        },
        {
            "step_number": 3,
            "operation": "transform_column",
            "description": "Clean customer names: strip whitespace and convert to title case",
            "input_datasets": ["customers"],
            "output_dataset": "customers_cleaned",
            "columns": ["name"],
            "column_transforms": [
                {"column": "name", "operation": "strip"},
                {"column": "name", "operation": "titlecase"}
            ],
            "suggested_recipe": "prepare",
            "suggested_processors": ["StringTransformer"],
            "reasoning": "String transformations map to Prepare recipe with StringTransformer processor"
        },
        {
            "step_number": 4,
            "operation": "drop_missing",
            "description": "Remove customers with missing customer_id",
            "input_datasets": ["customers_cleaned"],
            "output_dataset": "customers_cleaned",
            "columns": ["customer_id"],
            "suggested_recipe": "prepare",
            "suggested_processors": ["RemoveRowsOnEmpty"],
            "reasoning": "dropna maps to Prepare recipe with RemoveRowsOnEmpty processor"
        },
        {
            "step_number": 5,
            "operation": "join",
            "description": "Join customers with their orders using LEFT join on customer_id",
            "input_datasets": ["customers_cleaned", "orders"],
            "output_dataset": "merged",
            "join_conditions": [{"left_column": "customer_id", "right_column": "customer_id", "operator": "equals"}],
            "join_type": "left",
            "suggested_recipe": "join",
            "reasoning": "pd.merge with how='left' maps to Join recipe with LEFT join type"
        },
        {
            "step_number": 6,
            "operation": "group_aggregate",
            "description": "Calculate total spending and order count per customer",
            "input_datasets": ["merged"],
            "output_dataset": "summary",
            "group_by_columns": ["customer_id"],
            "aggregations": [
                {"column": "order_id", "function": "count", "output_column": "order_count"},
                {"column": "amount", "function": "sum", "output_column": "total_amount"}
            ],
            "suggested_recipe": "grouping",
            "reasoning": "groupby().agg() maps to Grouping recipe with COUNT and SUM aggregations"
        },
        {
            "step_number": 7,
            "operation": "filter",
            "description": "Filter to customers with total spending over $1000",
            "input_datasets": ["summary"],
            "output_dataset": "high_value",
            "filter_conditions": [{"column": "total_amount", "operator": "greater_than", "value": 1000}],
            "suggested_recipe": "split",
            "reasoning": "Conditional filter creates two output paths; Split recipe is optimal"
        }
    ],
    "recommendations": [
        "Consider moving the filter (step 7) before the join (step 5) to reduce data volume - filter customers before joining with orders",
        "The string transformations (step 3) and null removal (step 4) can be combined into a single Prepare recipe",
        "Consider adding a Distinct recipe after the join if duplicate customer records are possible"
    ],
    "warnings": [
        "LEFT join may produce null values in order columns for customers without orders"
    ]
})


def main():
    # Parse command line args
    provider_name = "mock"
    for i, arg in enumerate(sys.argv):
        if arg == "--provider" and i + 1 < len(sys.argv):
            provider_name = sys.argv[i + 1]

    # Example Python code
    python_code = '''
import pandas as pd

# Load data
customers = pd.read_csv('customers.csv')
orders = pd.read_csv('orders.csv')

# Clean customer data
customers['name'] = customers['name'].str.strip().str.title()
customers = customers.dropna(subset=['customer_id'])

# Join customers with orders
merged = pd.merge(customers, orders, on='customer_id', how='left')

# Aggregate by customer
summary = merged.groupby('customer_id').agg({
    'order_id': 'count',
    'amount': 'sum'
}).reset_index()
summary.columns = ['customer_id', 'order_count', 'total_amount']

# Filter high-value customers
high_value = summary[summary['total_amount'] > 1000]

# Save results
high_value.to_csv('high_value_customers.csv')
'''

    print("=" * 70)
    print("py2dataiku - LLM-Based Code Analysis Demo")
    print("=" * 70)
    print(f"\nUsing provider: {provider_name}")
    print()
    print("INPUT: Python Code")
    print("-" * 70)
    print(python_code)
    print()

    # Initialize provider
    if provider_name == "mock":
        provider = MockProvider(responses={"python": MOCK_RESPONSE})
    else:
        try:
            provider = get_provider(provider_name)
        except ValueError as e:
            print(f"Error: {e}")
            print("Set the appropriate API key environment variable and try again.")
            return

    # Step 1: Analyze with LLM
    print("STEP 1: LLM Code Analysis")
    print("-" * 70)
    analyzer = LLMCodeAnalyzer(provider=provider)
    analysis = analyzer.analyze(python_code)

    print(f"Code Summary: {analysis.code_summary}")
    print(f"Complexity Score: {analysis.complexity_score}/10")
    print(f"Total Operations: {analysis.total_operations}")
    print()

    print("Detected Datasets:")
    for ds in analysis.datasets:
        ds_type = "INPUT" if ds.is_input else ("OUTPUT" if ds.is_output else "INTERMEDIATE")
        source = f" (from {ds.source})" if ds.source else ""
        print(f"  - {ds.name} [{ds_type}]{source}")
    print()

    print("Extracted Data Steps:")
    for step in analysis.steps:
        print(f"  {step.step_number}. [{step.operation.value}] {step.description}")
        print(f"      → Dataiku: {step.suggested_recipe} recipe")
        if step.suggested_processors:
            print(f"      → Processors: {', '.join(step.suggested_processors)}")
        if step.reasoning:
            print(f"      → Reasoning: {step.reasoning}")
    print()

    if analysis.recommendations:
        print("LLM Recommendations:")
        for rec in analysis.recommendations:
            print(f"  💡 {rec}")
        print()

    if analysis.warnings:
        print("Warnings:")
        for warn in analysis.warnings:
            print(f"  ⚠️  {warn}")
        print()

    # Step 2: Generate Dataiku Flow
    print("STEP 2: Generate Dataiku Flow")
    print("-" * 70)
    generator = LLMFlowGenerator()
    flow = generator.generate(analysis, flow_name="customer_analytics_pipeline")

    print(flow.get_summary())
    print()

    # Step 3: Generate Mermaid Diagram
    print("STEP 3: Flow Diagram (Mermaid)")
    print("-" * 70)
    diagram_gen = DiagramGenerator()
    mermaid = diagram_gen.to_mermaid(flow)
    print("```mermaid")
    print(mermaid)
    print("```")
    print()

    # Step 4: Show Recipe Configurations
    print("STEP 4: Recipe Configurations (JSON)")
    print("-" * 70)
    for recipe in flow.recipes[:3]:  # Show first 3
        print(f"\n{recipe.name} ({recipe.recipe_type.value}):")
        config = recipe.to_json()
        print(json.dumps(config, indent=2)[:500] + "...")
    print()

    # Step 5: Show Optimization Notes
    print("STEP 5: Optimization Analysis")
    print("-" * 70)
    if flow.recommendations:
        for rec in flow.recommendations:
            print(f"  [{rec.priority}] {rec.type}: {rec.message}")
    if flow.optimization_notes:
        for note in flow.optimization_notes:
            print(f"  📊 {note}")
    print()

    print("=" * 70)
    print("Demo complete!")
    print()
    print("To use with a real LLM provider:")
    print("  ANTHROPIC_API_KEY=your_key python -m py2dataiku.examples.llm_demo --provider anthropic")
    print("  OPENAI_API_KEY=your_key python -m py2dataiku.examples.llm_demo --provider openai")
    print("=" * 70)


if __name__ == "__main__":
    main()
