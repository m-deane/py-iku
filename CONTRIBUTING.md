# Contributing to py2dataiku

Thank you for your interest in contributing to py2dataiku! This document provides guidelines and instructions for contributing.

## Development Setup

1. **Fork and clone the repository**
   ```bash
   git clone https://github.com/YOUR_USERNAME/py2dataiku.git
   cd py2dataiku
   ```

2. **Create a virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install development dependencies**
   ```bash
   pip install -e ".[all]"
   # or
   pip install -r requirements-dev.txt
   ```

4. **Run tests to verify setup**
   ```bash
   pytest tests/ -v
   ```

## Development Workflow

### Making Changes

1. Create a new branch for your feature or fix:
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. Make your changes, following the code style guidelines below.

3. Add tests for any new functionality.

4. Run the test suite:
   ```bash
   pytest tests/ -v
   ```

5. Run code quality checks:
   ```bash
   black py2dataiku tests
   isort py2dataiku tests
   ruff check py2dataiku tests
   mypy py2dataiku
   ```

### Code Style

- Follow PEP 8 guidelines
- Use Black for code formatting (line length: 88)
- Use isort for import sorting
- Write docstrings for all public functions and classes
- Add type hints where possible

### Commit Messages

- Use clear, descriptive commit messages
- Start with a verb in present tense (e.g., "Add", "Fix", "Update")
- Keep the first line under 72 characters
- Reference issues when applicable (e.g., "Fix #123")

Example:
```
Add support for Window recipe mapping

- Implement rolling window detection in AST analyzer
- Add WindowRecipe model with proper configuration
- Include tests for rolling mean, sum, and custom windows
```

## Adding New Features

### Adding a New Dataiku Recipe Type

1. Add the recipe type to `py2dataiku/models/dataiku_recipe.py`:
   ```python
   class RecipeType(Enum):
       # ... existing types
       NEW_RECIPE = "new_recipe"
   ```

2. Add pattern detection in `py2dataiku/parser/pattern_matcher.py` or update LLM schemas in `py2dataiku/llm/schemas.py`.

3. Implement the recipe generator in `py2dataiku/generators/recipe_generator.py`.

4. Add tests in `tests/test_py2dataiku/`.

### Adding a New Prepare Processor

1. Add the processor type to `py2dataiku/models/prepare_step.py`:
   ```python
   class ProcessorType(Enum):
       # ... existing types
       NEW_PROCESSOR = "NewProcessor"
   ```

2. Add the factory method:
   ```python
   @classmethod
   def new_processor(cls, column: str, **kwargs) -> "PrepareStep":
       return cls(
           processor_type=ProcessorType.NEW_PROCESSOR,
           column=column,
           params=kwargs
       )
   ```

3. Add pattern mapping in `py2dataiku/mappings/pandas_mappings.py`.

4. Add tests.

### Adding a New LLM Provider

1. Create a new provider class in `py2dataiku/llm/providers.py`:
   ```python
   class NewProvider(LLMProvider):
       def __init__(self, api_key: str = None, model: str = "default-model"):
           # Initialize

       def complete(self, prompt: str, system_prompt: str = None) -> LLMResponse:
           # Implement

       def complete_json(self, prompt: str, system_prompt: str = None) -> Dict:
           # Implement
   ```

2. Register in `get_provider()` function.

3. Add tests using MockProvider as reference.

## Testing Guidelines

- Write tests for all new functionality
- Use pytest fixtures for common test data
- Test both success and error cases
- Use MockProvider for LLM tests (no API calls in tests)

Example test:
```python
def test_new_feature():
    """Test description."""
    # Arrange
    input_data = ...

    # Act
    result = function_under_test(input_data)

    # Assert
    assert result.expected_property == expected_value
```

## Pull Request Process

1. Update the README.md if you've added new features
2. Add yourself to CONTRIBUTORS.md (if it exists)
3. Ensure all tests pass
4. Request review from maintainers
5. Address any feedback

## Questions?

Feel free to open an issue for any questions or discussions about contributions.
