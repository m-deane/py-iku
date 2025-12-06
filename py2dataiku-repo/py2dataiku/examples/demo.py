"""
Demonstration of py2dataiku library converting Python pandas code
to Dataiku DSS recipes and flow diagrams.
"""

from py2dataiku.parser.ast_analyzer import CodeAnalyzer
from py2dataiku.generators.flow_generator import FlowGenerator
from py2dataiku.generators.diagram_generator import DiagramGenerator


def main():
    # Example Python data processing code
    python_code = '''
import pandas as pd

# Load customer and order data
customers = pd.read_csv('customers.csv')
orders = pd.read_csv('orders.csv')

# Clean customer data
customers['name'] = customers['name'].str.strip().str.title()
customers['email'] = customers['email'].str.lower()
customers = customers.dropna(subset=['customer_id'])
customers = customers.drop_duplicates(subset=['customer_id'])

# Join customers with orders
merged = pd.merge(customers, orders, on='customer_id', how='left')

# Aggregate by customer
summary = merged.groupby('customer_id').agg({
    'order_id': 'count',
    'amount': 'sum'
}).reset_index()

# Filter high-value customers
high_value = summary[summary['amount'] > 1000]

# Save results
high_value.to_csv('high_value_customers.csv')
'''

    print("=" * 70)
    print("py2dataiku - Python to Dataiku Converter Demo")
    print("=" * 70)
    print()
    print("INPUT: Python Code")
    print("-" * 70)
    print(python_code)
    print()

    # Step 1: Analyze the Python code
    print("STEP 1: Analyzing Python code...")
    print("-" * 70)
    analyzer = CodeAnalyzer()
    transformations = analyzer.analyze(python_code)

    print(f"Found {len(transformations)} transformations:")
    for i, trans in enumerate(transformations, 1):
        print(f"  {i}. {trans.transformation_type.value}: {trans.source_dataframe} -> {trans.target_dataframe}")
        if trans.suggested_recipe:
            print(f"      Suggested recipe: {trans.suggested_recipe}")
        if trans.suggested_processor:
            print(f"      Suggested processor: {trans.suggested_processor}")
    print()

    # Step 2: Generate Dataiku flow
    print("STEP 2: Generating Dataiku flow...")
    print("-" * 70)
    generator = FlowGenerator()
    flow = generator.generate(transformations, flow_name="customer_analysis_pipeline")

    print(flow.get_summary())
    print()

    # Step 3: Generate flow diagram
    print("STEP 3: Generating Mermaid diagram...")
    print("-" * 70)
    diagram_gen = DiagramGenerator()
    mermaid = diagram_gen.to_mermaid(flow)
    print("```mermaid")
    print(mermaid)
    print("```")
    print()

    # Step 4: Generate ASCII diagram
    print("STEP 4: Generating ASCII diagram...")
    print("-" * 70)
    ascii_diagram = diagram_gen.to_ascii(flow)
    print(ascii_diagram)
    print()

    # Step 5: Show recipe configurations
    print("STEP 5: Generated Recipe Configurations (JSON)")
    print("-" * 70)
    import json
    for recipe in flow.recipes:
        print(f"\n{recipe.name} ({recipe.recipe_type.value}):")
        config = recipe.to_json()
        print(json.dumps(config, indent=2))
    print()

    # Step 6: Show YAML summary
    print("STEP 6: Flow Summary (YAML)")
    print("-" * 70)
    print(flow.to_yaml())

    # Step 7: Show recommendations
    print("STEP 7: Optimization Recommendations")
    print("-" * 70)
    validation = flow.validate()
    if validation["warnings"]:
        for warning in validation["warnings"]:
            print(f"  ⚠️  {warning}")
    if flow.recommendations:
        for rec in flow.recommendations:
            print(f"  [{rec.priority}] {rec.type}: {rec.message}")
            if rec.action:
                print(f"      Action: {rec.action}")
    else:
        print("  ✓ No optimization issues found")
    print()

    print("=" * 70)
    print("Demo complete!")
    print("=" * 70)


if __name__ == "__main__":
    main()
