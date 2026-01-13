"""Command-line interface for py2dataiku.

Usage:
    py2dataiku convert script.py                    # Rule-based conversion
    py2dataiku convert script.py --llm              # LLM-based conversion
    py2dataiku convert script.py -o flow.json       # Output to JSON
    py2dataiku convert script.py --format yaml      # Output as YAML
    py2dataiku visualize script.py                  # Generate visualization
    py2dataiku visualize script.py --format svg     # Generate SVG
    py2dataiku analyze script.py                    # Show analysis only
"""

import argparse
import os
import sys
from typing import Optional

from py2dataiku import (
    convert,
    DataikuFlow,
    CodeAnalyzer,
)


def create_parser() -> argparse.ArgumentParser:
    """Create the argument parser for the CLI."""
    parser = argparse.ArgumentParser(
        prog="py2dataiku",
        description="Convert Python data processing code to Dataiku DSS flows",
        epilog="For more information, visit: https://github.com/m-deane/py-iku",
    )
    parser.add_argument(
        "--version",
        action="version",
        version="%(prog)s 0.3.0",
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Convert command
    convert_parser = subparsers.add_parser(
        "convert",
        help="Convert Python code to Dataiku flow",
        description="Parse Python code and generate Dataiku DSS flow configuration",
    )
    convert_parser.add_argument(
        "input",
        help="Input Python file or '-' for stdin",
    )
    convert_parser.add_argument(
        "-o", "--output",
        help="Output file (default: stdout)",
        default=None,
    )
    convert_parser.add_argument(
        "-f", "--format",
        choices=["json", "yaml", "dict", "summary"],
        default="json",
        help="Output format (default: json)",
    )
    convert_parser.add_argument(
        "--llm",
        action="store_true",
        help="Use LLM-based analysis (requires API key)",
    )
    convert_parser.add_argument(
        "--provider",
        choices=["anthropic", "openai"],
        default="anthropic",
        help="LLM provider (default: anthropic)",
    )
    convert_parser.add_argument(
        "--api-key",
        help="API key (or use environment variable)",
        default=None,
    )
    convert_parser.add_argument(
        "--model",
        help="Model name override",
        default=None,
    )
    convert_parser.add_argument(
        "--no-optimize",
        action="store_true",
        help="Disable flow optimization",
    )
    convert_parser.add_argument(
        "--name",
        help="Name for the generated flow",
        default="converted_flow",
    )
    convert_parser.add_argument(
        "-q", "--quiet",
        action="store_true",
        help="Suppress informational messages",
    )

    # Visualize command
    viz_parser = subparsers.add_parser(
        "visualize",
        aliases=["viz"],
        help="Generate flow visualization",
        description="Generate visual diagrams of the converted flow",
    )
    viz_parser.add_argument(
        "input",
        help="Input Python file or '-' for stdin",
    )
    viz_parser.add_argument(
        "-o", "--output",
        help="Output file (default: stdout)",
        default=None,
    )
    viz_parser.add_argument(
        "-f", "--format",
        choices=["svg", "html", "ascii", "plantuml", "mermaid"],
        default="ascii",
        help="Visualization format (default: ascii)",
    )
    viz_parser.add_argument(
        "--llm",
        action="store_true",
        help="Use LLM-based analysis",
    )
    viz_parser.add_argument(
        "--provider",
        choices=["anthropic", "openai"],
        default="anthropic",
        help="LLM provider (default: anthropic)",
    )
    viz_parser.add_argument(
        "--api-key",
        help="API key (or use environment variable)",
        default=None,
    )
    viz_parser.add_argument(
        "--theme",
        choices=["light", "dark"],
        default="light",
        help="Color theme (default: light)",
    )
    viz_parser.add_argument(
        "--no-optimize",
        action="store_true",
        help="Disable flow optimization",
    )
    viz_parser.add_argument(
        "-q", "--quiet",
        action="store_true",
        help="Suppress informational messages",
    )

    # Analyze command
    analyze_parser = subparsers.add_parser(
        "analyze",
        help="Analyze Python code without converting",
        description="Analyze and display detected transformations",
    )
    analyze_parser.add_argument(
        "input",
        help="Input Python file or '-' for stdin",
    )
    analyze_parser.add_argument(
        "-o", "--output",
        help="Output file (default: stdout)",
        default=None,
    )
    analyze_parser.add_argument(
        "-f", "--format",
        choices=["text", "json", "yaml"],
        default="text",
        help="Output format (default: text)",
    )
    analyze_parser.add_argument(
        "--llm",
        action="store_true",
        help="Use LLM-based analysis",
    )
    analyze_parser.add_argument(
        "--provider",
        choices=["anthropic", "openai"],
        default="anthropic",
        help="LLM provider (default: anthropic)",
    )
    analyze_parser.add_argument(
        "--api-key",
        help="API key (or use environment variable)",
        default=None,
    )
    analyze_parser.add_argument(
        "-q", "--quiet",
        action="store_true",
        help="Suppress informational messages",
    )

    return parser


def read_input(input_path: str) -> str:
    """Read input from file or stdin."""
    if input_path == "-":
        return sys.stdin.read()

    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Input file not found: {input_path}")

    with open(input_path, "r", encoding="utf-8") as f:
        return f.read()


def write_output(content: str, output_path: Optional[str]) -> None:
    """Write output to file or stdout."""
    if output_path:
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(content)
    else:
        print(content)


def log(message: str, quiet: bool = False) -> None:
    """Log a message to stderr."""
    if not quiet:
        print(message, file=sys.stderr)


def convert_code(
    code: str,
    use_llm: bool = False,
    provider: str = "anthropic",
    api_key: Optional[str] = None,
    model: Optional[str] = None,
    optimize: bool = True,
    flow_name: str = "converted_flow",
) -> DataikuFlow:
    """Convert Python code to a Dataiku flow."""
    if use_llm:
        try:
            from py2dataiku import convert_with_llm
            return convert_with_llm(
                code,
                provider=provider,
                api_key=api_key,
                model=model,
                optimize=optimize,
                flow_name=flow_name,
            )
        except ImportError as e:
            raise ImportError(
                f"LLM dependencies not installed. Install with: pip install py-iku[llm]\n"
                f"Error: {e}"
            )
    else:
        return convert(code, optimize=optimize)


def format_flow(flow: DataikuFlow, fmt: str) -> str:
    """Format a flow for output."""
    if fmt == "json":
        return flow.to_json(indent=2)
    elif fmt == "yaml":
        return flow.to_yaml()
    elif fmt == "dict":
        import json
        return json.dumps(flow.to_dict(), indent=2)
    elif fmt == "summary":
        return flow.get_summary()
    else:
        raise ValueError(f"Unknown format: {fmt}")


def cmd_convert(args: argparse.Namespace) -> int:
    """Handle the convert command."""
    try:
        log(f"Reading input from: {args.input}", args.quiet)
        code = read_input(args.input)

        log("Converting code to Dataiku flow...", args.quiet)
        flow = convert_code(
            code,
            use_llm=args.llm,
            provider=args.provider,
            api_key=args.api_key,
            model=args.model,
            optimize=not args.no_optimize,
            flow_name=args.name,
        )

        log(f"Generated flow with {len(flow.recipes)} recipes", args.quiet)

        output = format_flow(flow, args.format)
        write_output(output, args.output)

        if args.output:
            log(f"Output written to: {args.output}", args.quiet)

        return 0

    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    except SyntaxError as e:
        print(f"Syntax error in input: {e}", file=sys.stderr)
        return 1
    except ImportError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


def cmd_visualize(args: argparse.Namespace) -> int:
    """Handle the visualize command."""
    try:
        log(f"Reading input from: {args.input}", args.quiet)
        code = read_input(args.input)

        log("Converting code to Dataiku flow...", args.quiet)
        flow = convert_code(
            code,
            use_llm=args.llm,
            provider=args.provider,
            api_key=args.api_key,
            optimize=not args.no_optimize,
        )

        log(f"Generating {args.format} visualization...", args.quiet)

        # Get theme
        theme = None
        if args.format in ("svg", "html"):
            from py2dataiku.visualizers import DATAIKU_LIGHT, DATAIKU_DARK
            theme = DATAIKU_DARK if args.theme == "dark" else DATAIKU_LIGHT

        if args.format == "mermaid":
            from py2dataiku.generators.diagram_generator import DiagramGenerator
            gen = DiagramGenerator()
            output = gen.to_mermaid(flow)
        else:
            output = flow.visualize(format=args.format, theme=theme)

        write_output(output, args.output)

        if args.output:
            log(f"Visualization written to: {args.output}", args.quiet)

        return 0

    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    except SyntaxError as e:
        print(f"Syntax error in input: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


def cmd_analyze(args: argparse.Namespace) -> int:
    """Handle the analyze command."""
    try:
        log(f"Reading input from: {args.input}", args.quiet)
        code = read_input(args.input)

        log("Analyzing code...", args.quiet)

        if args.llm:
            try:
                from py2dataiku import LLMCodeAnalyzer, get_provider
                provider = get_provider(args.provider, args.api_key)
                analyzer = LLMCodeAnalyzer(provider=provider)
                result = analyzer.analyze(code)

                if args.format == "text":
                    output = format_llm_analysis(result)
                elif args.format == "json":
                    import json
                    output = json.dumps(result.to_dict(), indent=2)
                elif args.format == "yaml":
                    import yaml
                    output = yaml.dump(result.to_dict(), default_flow_style=False)
                else:
                    raise ValueError(f"Unknown format: {args.format}")

            except ImportError as e:
                print(f"LLM dependencies not installed. Error: {e}", file=sys.stderr)
                return 1
        else:
            analyzer = CodeAnalyzer()
            transformations = analyzer.analyze(code)

            if args.format == "text":
                output = format_transformations(transformations)
            elif args.format == "json":
                import json
                output = json.dumps(
                    [t.to_dict() for t in transformations],
                    indent=2
                )
            elif args.format == "yaml":
                import yaml
                output = yaml.dump(
                    [t.to_dict() for t in transformations],
                    default_flow_style=False
                )
            else:
                raise ValueError(f"Unknown format: {args.format}")

        write_output(output, args.output)

        if args.output:
            log(f"Analysis written to: {args.output}", args.quiet)

        return 0

    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    except SyntaxError as e:
        print(f"Syntax error in input: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


def format_transformations(transformations) -> str:
    """Format transformations for text output."""
    if not transformations:
        return "No transformations detected."

    lines = [
        f"Detected {len(transformations)} transformation(s):",
        "",
    ]

    for i, t in enumerate(transformations, 1):
        lines.append(f"{i}. {t.transformation_type.value}")
        if t.source_dataframe:
            lines.append(f"   Source: {t.source_dataframe}")
        if t.target_dataframe:
            lines.append(f"   Target: {t.target_dataframe}")
        if t.columns:
            lines.append(f"   Columns: {', '.join(t.columns)}")
        if t.suggested_recipe:
            lines.append(f"   Suggested Recipe: {t.suggested_recipe}")
        if t.suggested_processor:
            lines.append(f"   Suggested Processor: {t.suggested_processor}")
        if t.source_line:
            lines.append(f"   Line: {t.source_line}")
        if t.notes:
            for note in t.notes:
                lines.append(f"   Note: {note}")
        lines.append("")

    return "\n".join(lines)


def format_llm_analysis(result) -> str:
    """Format LLM analysis result for text output."""
    lines = [
        "LLM Analysis Result",
        "=" * 50,
        "",
    ]

    if hasattr(result, 'summary') and result.summary:
        lines.extend([
            "Summary:",
            result.summary,
            "",
        ])

    if hasattr(result, 'steps') and result.steps:
        lines.append(f"Detected {len(result.steps)} step(s):")
        lines.append("")

        for i, step in enumerate(result.steps, 1):
            lines.append(f"{i}. {step.operation.value if hasattr(step.operation, 'value') else step.operation}")
            if hasattr(step, 'description') and step.description:
                lines.append(f"   Description: {step.description}")
            if hasattr(step, 'inputs') and step.inputs:
                lines.append(f"   Inputs: {', '.join(step.inputs)}")
            if hasattr(step, 'outputs') and step.outputs:
                lines.append(f"   Outputs: {', '.join(step.outputs)}")
            if hasattr(step, 'recipe_type') and step.recipe_type:
                lines.append(f"   Recipe Type: {step.recipe_type}")
            lines.append("")

    return "\n".join(lines)


def main(argv=None) -> int:
    """Main entry point for the CLI."""
    parser = create_parser()
    args = parser.parse_args(argv)

    if args.command is None:
        parser.print_help()
        return 0

    if args.command == "convert":
        return cmd_convert(args)
    elif args.command in ("visualize", "viz"):
        return cmd_visualize(args)
    elif args.command == "analyze":
        return cmd_analyze(args)
    else:
        parser.print_help()
        return 1


if __name__ == "__main__":
    sys.exit(main())
