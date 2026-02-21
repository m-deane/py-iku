# py-iku

**Convert Python data processing code to Dataiku DSS recipes and flows.**

py-iku analyzes your Python code (pandas, numpy, scikit-learn) and generates equivalent Dataiku DSS recipe configurations, flow structures, and visual diagrams.

## Two Analysis Modes

=== "LLM-based (Recommended)"

    Uses AI (Anthropic Claude or OpenAI GPT) to understand code semantics and produce accurate Dataiku mappings.

    ```python
    from py2dataiku import convert_with_llm

    flow = convert_with_llm("""
    import pandas as pd
    df = pd.read_csv('sales.csv')
    df = df.dropna(subset=['amount'])
    result = df.groupby('region').agg({'amount': 'sum'})
    result.to_csv('summary.csv')
    """, provider="anthropic")

    print(flow.visualize(format="ascii"))
    ```

=== "Rule-based (Offline)"

    Uses AST pattern matching for fast, deterministic conversion without API calls.

    ```python
    from py2dataiku import convert

    flow = convert("""
    import pandas as pd
    df = pd.read_csv('sales.csv')
    df = df.dropna(subset=['amount'])
    result = df.groupby('region').agg({'amount': 'sum'})
    result.to_csv('summary.csv')
    """)

    print(flow.visualize(format="ascii"))
    ```

## Features

- **37 recipe types** - Visual, code, ML, and plugin recipes
- **122 processor types** - Complete Dataiku Prepare recipe processor coverage
- **5 visualization formats** - SVG, HTML, ASCII, Mermaid, PlantUML
- **Round-trip serialization** - JSON, YAML, and dict export/import
- **DAG analysis** - Topological sort, cycle detection, column lineage
- **DSS project export** - Generate Dataiku-importable project bundles
- **Plugin system** - Extend with custom recipe/processor handlers
- **Scenario & metrics** - Automation triggers, data quality checks

## Quick Links

- [Installation](getting-started/installation.md)
- [Quick Start Guide](getting-started/quickstart.md)
- [API Reference](api/index.md)
- [GitHub Repository](https://github.com/m-deane/py-iku)
