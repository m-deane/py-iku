"""Tests for NumPy operation support in py2dataiku."""

import pytest

from py2dataiku import convert
from py2dataiku.parser.ast_analyzer import CodeAnalyzer
from py2dataiku.models.transformation import TransformationType


class TestNumPyMathOperations:
    """Tests for NumPy mathematical operations."""

    def test_numpy_log(self):
        """Test np.log conversion creates transformation."""
        code = """
import numpy as np
import pandas as pd
df = pd.read_csv('data.csv')
df['log_value'] = np.log(df['value'])
"""
        analyzer = CodeAnalyzer()
        transformations = analyzer.analyze(code)
        # Should detect at least the read and log operations
        assert len(transformations) >= 2
        numeric_ops = [t for t in transformations if t.transformation_type == TransformationType.NUMERIC_TRANSFORM]
        assert len(numeric_ops) >= 1

    def test_numpy_log10(self):
        """Test np.log10 conversion creates transformation."""
        code = """
import numpy as np
import pandas as pd
df = pd.read_csv('data.csv')
df['log10_value'] = np.log10(df['value'])
"""
        analyzer = CodeAnalyzer()
        transformations = analyzer.analyze(code)
        assert len(transformations) >= 2
        numeric_ops = [t for t in transformations if t.transformation_type == TransformationType.NUMERIC_TRANSFORM]
        assert len(numeric_ops) >= 1

    def test_numpy_log1p(self):
        """Test np.log1p conversion creates transformation."""
        code = """
import numpy as np
import pandas as pd
df = pd.read_csv('data.csv')
df['log1p_value'] = np.log1p(df['value'])
"""
        analyzer = CodeAnalyzer()
        transformations = analyzer.analyze(code)
        assert len(transformations) >= 2
        numeric_ops = [t for t in transformations if t.transformation_type == TransformationType.NUMERIC_TRANSFORM]
        assert len(numeric_ops) >= 1

    def test_numpy_exp(self):
        """Test np.exp conversion creates transformation."""
        code = """
import numpy as np
import pandas as pd
df = pd.read_csv('data.csv')
df['exp_value'] = np.exp(df['value'])
"""
        analyzer = CodeAnalyzer()
        transformations = analyzer.analyze(code)
        assert len(transformations) >= 2
        numeric_ops = [t for t in transformations if t.transformation_type == TransformationType.NUMERIC_TRANSFORM]
        assert len(numeric_ops) >= 1

    def test_numpy_expm1(self):
        """Test np.expm1 conversion creates transformation."""
        code = """
import numpy as np
import pandas as pd
df = pd.read_csv('data.csv')
df['expm1_value'] = np.expm1(df['value'])
"""
        analyzer = CodeAnalyzer()
        transformations = analyzer.analyze(code)
        assert len(transformations) >= 2
        numeric_ops = [t for t in transformations if t.transformation_type == TransformationType.NUMERIC_TRANSFORM]
        assert len(numeric_ops) >= 1

    def test_numpy_sqrt(self):
        """Test np.sqrt conversion creates transformation."""
        code = """
import numpy as np
import pandas as pd
df = pd.read_csv('data.csv')
df['sqrt_value'] = np.sqrt(df['value'])
"""
        analyzer = CodeAnalyzer()
        transformations = analyzer.analyze(code)
        assert len(transformations) >= 2
        numeric_ops = [t for t in transformations if t.transformation_type == TransformationType.NUMERIC_TRANSFORM]
        assert len(numeric_ops) >= 1

    def test_numpy_power(self):
        """Test np.power conversion creates transformation."""
        code = """
import numpy as np
import pandas as pd
df = pd.read_csv('data.csv')
df['squared'] = np.power(df['value'], 2)
"""
        analyzer = CodeAnalyzer()
        transformations = analyzer.analyze(code)
        assert len(transformations) >= 2
        numeric_ops = [t for t in transformations if t.transformation_type == TransformationType.NUMERIC_TRANSFORM]
        assert len(numeric_ops) >= 1

    def test_numpy_square(self):
        """Test np.square conversion creates transformation."""
        code = """
import numpy as np
import pandas as pd
df = pd.read_csv('data.csv')
df['squared'] = np.square(df['value'])
"""
        analyzer = CodeAnalyzer()
        transformations = analyzer.analyze(code)
        assert len(transformations) >= 2
        numeric_ops = [t for t in transformations if t.transformation_type == TransformationType.NUMERIC_TRANSFORM]
        assert len(numeric_ops) >= 1

    def test_numpy_abs(self):
        """Test np.abs conversion creates transformation."""
        code = """
import numpy as np
import pandas as pd
df = pd.read_csv('data.csv')
df['abs_value'] = np.abs(df['value'])
"""
        analyzer = CodeAnalyzer()
        transformations = analyzer.analyze(code)
        assert len(transformations) >= 2
        numeric_ops = [t for t in transformations if t.transformation_type == TransformationType.NUMERIC_TRANSFORM]
        assert len(numeric_ops) >= 1

    def test_numpy_absolute(self):
        """Test np.absolute conversion creates transformation."""
        code = """
import numpy as np
import pandas as pd
df = pd.read_csv('data.csv')
df['abs_value'] = np.absolute(df['value'])
"""
        analyzer = CodeAnalyzer()
        transformations = analyzer.analyze(code)
        # absolute falls through to CUSTOM_FUNCTION since it's not explicitly mapped
        assert len(transformations) >= 2

    def test_numpy_round(self):
        """Test np.round conversion creates transformation."""
        code = """
import numpy as np
import pandas as pd
df = pd.read_csv('data.csv')
df['rounded'] = np.round(df['value'], 2)
"""
        analyzer = CodeAnalyzer()
        transformations = analyzer.analyze(code)
        assert len(transformations) >= 2

    def test_numpy_around(self):
        """Test np.around conversion creates transformation."""
        code = """
import numpy as np
import pandas as pd
df = pd.read_csv('data.csv')
df['rounded'] = np.around(df['value'], 2)
"""
        analyzer = CodeAnalyzer()
        transformations = analyzer.analyze(code)
        assert len(transformations) >= 2


class TestNumPyClipOperations:
    """Tests for NumPy clip operations."""

    def test_numpy_clip(self):
        """Test np.clip conversion creates transformation."""
        code = """
import numpy as np
import pandas as pd
df = pd.read_csv('data.csv')
df['clipped'] = np.clip(df['value'], 0, 100)
"""
        analyzer = CodeAnalyzer()
        transformations = analyzer.analyze(code)
        assert len(transformations) >= 2
        clip_ops = [t for t in transformations if "clip" in str(t.parameters).lower()]
        assert len(clip_ops) >= 1

    def test_numpy_clip_with_none(self):
        """Test np.clip with None bounds."""
        code = """
import numpy as np
import pandas as pd
df = pd.read_csv('data.csv')
df['clipped_min'] = np.clip(df['value'], 0, None)
"""
        analyzer = CodeAnalyzer()
        transformations = analyzer.analyze(code)
        assert len(transformations) >= 2


class TestNumPyConditionalOperations:
    """Tests for NumPy conditional operations."""

    def test_numpy_where(self):
        """Test np.where conversion creates transformation."""
        code = """
import numpy as np
import pandas as pd
df = pd.read_csv('data.csv')
df['result'] = np.where(df['value'] > 0, 'positive', 'non-positive')
"""
        analyzer = CodeAnalyzer()
        transformations = analyzer.analyze(code)
        assert len(transformations) >= 2
        # np.where creates a COLUMN_CREATE transformation
        column_create_ops = [t for t in transformations if t.transformation_type == TransformationType.COLUMN_CREATE]
        assert len(column_create_ops) >= 1

    def test_numpy_isnan(self):
        """Test np.isnan conversion creates transformation."""
        code = """
import numpy as np
import pandas as pd
df = pd.read_csv('data.csv')
df['is_nan'] = np.isnan(df['value'])
"""
        analyzer = CodeAnalyzer()
        transformations = analyzer.analyze(code)
        assert len(transformations) >= 2

    def test_numpy_isinf(self):
        """Test np.isinf conversion creates transformation."""
        code = """
import numpy as np
import pandas as pd
df = pd.read_csv('data.csv')
df['is_inf'] = np.isinf(df['value'])
"""
        analyzer = CodeAnalyzer()
        transformations = analyzer.analyze(code)
        assert len(transformations) >= 2

    def test_numpy_isfinite(self):
        """Test np.isfinite conversion creates transformation."""
        code = """
import numpy as np
import pandas as pd
df = pd.read_csv('data.csv')
df['is_finite'] = np.isfinite(df['value'])
"""
        analyzer = CodeAnalyzer()
        transformations = analyzer.analyze(code)
        assert len(transformations) >= 2

    def test_numpy_nan_to_num(self):
        """Test np.nan_to_num conversion creates transformation."""
        code = """
import numpy as np
import pandas as pd
df = pd.read_csv('data.csv')
df['cleaned'] = np.nan_to_num(df['value'])
"""
        flow = convert(code)
        assert len(flow.recipes) >= 1


class TestNumPyAggregationOperations:
    """Tests for NumPy aggregation operations."""

    def test_numpy_sum(self):
        """Test np.sum conversion."""
        code = """
import numpy as np
import pandas as pd
df = pd.read_csv('data.csv')
total = np.sum(df['value'])
"""
        flow = convert(code)
        # Aggregations may or may not create recipes
        assert flow is not None

    def test_numpy_mean(self):
        """Test np.mean conversion."""
        code = """
import numpy as np
import pandas as pd
df = pd.read_csv('data.csv')
avg = np.mean(df['value'])
"""
        flow = convert(code)
        assert flow is not None

    def test_numpy_std(self):
        """Test np.std conversion."""
        code = """
import numpy as np
import pandas as pd
df = pd.read_csv('data.csv')
std_dev = np.std(df['value'])
"""
        flow = convert(code)
        assert flow is not None

    def test_numpy_var(self):
        """Test np.var conversion."""
        code = """
import numpy as np
import pandas as pd
df = pd.read_csv('data.csv')
variance = np.var(df['value'])
"""
        flow = convert(code)
        assert flow is not None

    def test_numpy_min(self):
        """Test np.min conversion."""
        code = """
import numpy as np
import pandas as pd
df = pd.read_csv('data.csv')
min_val = np.min(df['value'])
"""
        flow = convert(code)
        assert flow is not None

    def test_numpy_max(self):
        """Test np.max conversion."""
        code = """
import numpy as np
import pandas as pd
df = pd.read_csv('data.csv')
max_val = np.max(df['value'])
"""
        flow = convert(code)
        assert flow is not None

    def test_numpy_median(self):
        """Test np.median conversion."""
        code = """
import numpy as np
import pandas as pd
df = pd.read_csv('data.csv')
med = np.median(df['value'])
"""
        flow = convert(code)
        assert flow is not None

    def test_numpy_percentile(self):
        """Test np.percentile conversion."""
        code = """
import numpy as np
import pandas as pd
df = pd.read_csv('data.csv')
p75 = np.percentile(df['value'], 75)
"""
        flow = convert(code)
        assert flow is not None


class TestNumPyArrayOperations:
    """Tests for NumPy array operations."""

    def test_numpy_concatenate(self):
        """Test np.concatenate conversion."""
        code = """
import numpy as np
import pandas as pd
df1 = pd.read_csv('data1.csv')
df2 = pd.read_csv('data2.csv')
combined = np.concatenate([df1['value'].values, df2['value'].values])
"""
        flow = convert(code)
        assert flow is not None

    def test_numpy_vstack(self):
        """Test np.vstack conversion."""
        code = """
import numpy as np
import pandas as pd
df1 = pd.read_csv('data1.csv')
df2 = pd.read_csv('data2.csv')
stacked = np.vstack([df1.values, df2.values])
"""
        flow = convert(code)
        assert flow is not None

    def test_numpy_hstack(self):
        """Test np.hstack conversion."""
        code = """
import numpy as np
import pandas as pd
df1 = pd.read_csv('data1.csv')
df2 = pd.read_csv('data2.csv')
stacked = np.hstack([df1.values, df2.values])
"""
        flow = convert(code)
        assert flow is not None

    def test_numpy_sort(self):
        """Test np.sort conversion."""
        code = """
import numpy as np
import pandas as pd
df = pd.read_csv('data.csv')
sorted_arr = np.sort(df['value'].values)
"""
        flow = convert(code)
        assert flow is not None

    def test_numpy_unique(self):
        """Test np.unique conversion."""
        code = """
import numpy as np
import pandas as pd
df = pd.read_csv('data.csv')
unique_vals = np.unique(df['category'].values)
"""
        flow = convert(code)
        assert flow is not None


class TestNumPyReshapeOperations:
    """Tests for NumPy reshaping operations."""

    def test_numpy_reshape(self):
        """Test np.reshape conversion."""
        code = """
import numpy as np
import pandas as pd
df = pd.read_csv('data.csv')
reshaped = np.reshape(df['value'].values, (-1, 1))
"""
        flow = convert(code)
        assert flow is not None

    def test_numpy_flatten(self):
        """Test np.flatten conversion."""
        code = """
import numpy as np
arr = np.array([[1, 2], [3, 4]])
flat = arr.flatten()
"""
        flow = convert(code)
        assert flow is not None

    def test_numpy_ravel(self):
        """Test np.ravel conversion."""
        code = """
import numpy as np
arr = np.array([[1, 2], [3, 4]])
raveled = np.ravel(arr)
"""
        flow = convert(code)
        assert flow is not None

    def test_numpy_transpose(self):
        """Test np.transpose conversion."""
        code = """
import numpy as np
arr = np.array([[1, 2, 3], [4, 5, 6]])
transposed = np.transpose(arr)
"""
        flow = convert(code)
        assert flow is not None


class TestNumPyCreationOperations:
    """Tests for NumPy array creation operations."""

    def test_numpy_zeros(self):
        """Test np.zeros conversion."""
        code = """
import numpy as np
zeros_arr = np.zeros((10, 5))
"""
        flow = convert(code)
        assert flow is not None

    def test_numpy_ones(self):
        """Test np.ones conversion."""
        code = """
import numpy as np
ones_arr = np.ones((10, 5))
"""
        flow = convert(code)
        assert flow is not None

    def test_numpy_full(self):
        """Test np.full conversion."""
        code = """
import numpy as np
full_arr = np.full((10, 5), 42)
"""
        flow = convert(code)
        assert flow is not None

    def test_numpy_empty(self):
        """Test np.empty conversion."""
        code = """
import numpy as np
empty_arr = np.empty((10, 5))
"""
        flow = convert(code)
        assert flow is not None

    def test_numpy_arange(self):
        """Test np.arange conversion."""
        code = """
import numpy as np
arr = np.arange(0, 100, 10)
"""
        flow = convert(code)
        assert flow is not None

    def test_numpy_linspace(self):
        """Test np.linspace conversion."""
        code = """
import numpy as np
arr = np.linspace(0, 1, 50)
"""
        flow = convert(code)
        assert flow is not None


class TestNumPyIntegration:
    """Integration tests for NumPy with pandas."""

    def test_numpy_pandas_pipeline(self):
        """Test a pipeline combining NumPy and pandas operations."""
        code = """
import numpy as np
import pandas as pd

df = pd.read_csv('data.csv')

# NumPy operations
df['log_value'] = np.log1p(df['value'])
df['clipped'] = np.clip(df['score'], 0, 100)
df['abs_diff'] = np.abs(df['actual'] - df['predicted'])

# Conditional
df['category'] = np.where(df['value'] > 100, 'high', 'low')

# Clean NaN
df['cleaned'] = np.nan_to_num(df['ratio'], nan=0.0)

df.to_csv('processed.csv', index=False)
"""
        flow = convert(code)
        assert len(flow.datasets) >= 2
        assert len(flow.recipes) >= 1

    def test_numpy_full_transformation_pipeline(self):
        """Test full transformation pipeline with NumPy."""
        code = """
import numpy as np
import pandas as pd

df = pd.read_csv('raw_data.csv')

# Math transformations
df['value_log'] = np.log(df['value'])
df['value_sqrt'] = np.sqrt(df['value'])
df['value_exp'] = np.exp(df['rate'])

# Rounding and clipping
df['rounded'] = np.round(df['score'], 2)
df['clipped'] = np.clip(df['pct'], 0, 1)

# Aggregation
total = np.sum(df['value'])
average = np.mean(df['value'])

# Save
df.to_csv('transformed.csv', index=False)
"""
        flow = convert(code)
        assert len(flow.recipes) >= 1

    def test_numpy_feature_engineering(self):
        """Test NumPy for feature engineering."""
        code = """
import numpy as np
import pandas as pd

df = pd.read_csv('features.csv')

# Normalize features
df['norm_value'] = (df['value'] - np.mean(df['value'])) / np.std(df['value'])

# Handle special values
df['clean_ratio'] = np.nan_to_num(df['ratio'], nan=0, posinf=1, neginf=-1)
df['is_valid'] = np.isfinite(df['score']).astype(int)

# Categorical encoding with where
df['high_flag'] = np.where(df['amount'] > 1000, 1, 0)

df.to_csv('engineered_features.csv', index=False)
"""
        flow = convert(code)
        assert len(flow.recipes) >= 1


class TestCodeAnalyzerNumPy:
    """Tests for CodeAnalyzer NumPy handling."""

    def test_analyzer_detects_numpy_import(self):
        """Test that analyzer correctly detects numpy import."""
        code = """
import numpy as np
import pandas as pd
df = pd.read_csv('data.csv')
df['log'] = np.log(df['value'])
"""
        analyzer = CodeAnalyzer()
        transformations = analyzer.analyze(code)
        # Should have at least the read operation and the numpy operation
        assert len(transformations) >= 2
        numeric_ops = [t for t in transformations if t.transformation_type == TransformationType.NUMERIC_TRANSFORM]
        assert len(numeric_ops) >= 1

    def test_analyzer_handles_numpy_alias(self):
        """Test that analyzer handles 'numpy' as alias (not just 'np')."""
        code = """
import numpy
import pandas as pd
df = pd.read_csv('data.csv')
df['log'] = numpy.log(df['value'])
"""
        analyzer = CodeAnalyzer()
        transformations = analyzer.analyze(code)
        # Should detect both read and numpy operations
        assert len(transformations) >= 2

    def test_analyzer_multiple_numpy_operations(self):
        """Test multiple NumPy operations in sequence."""
        code = """
import numpy as np
import pandas as pd
df = pd.read_csv('data.csv')
df['a'] = np.log(df['x'])
df['b'] = np.exp(df['y'])
df['c'] = np.sqrt(df['z'])
df['d'] = np.abs(df['w'])
"""
        analyzer = CodeAnalyzer()
        transformations = analyzer.analyze(code)
        # Should detect read + 4 numpy operations = at least 5
        assert len(transformations) >= 5
        numeric_ops = [t for t in transformations if t.transformation_type == TransformationType.NUMERIC_TRANSFORM]
        assert len(numeric_ops) >= 4


class TestNumPyEdgeCases:
    """Edge case tests for NumPy support."""

    def test_numpy_with_constants(self):
        """Test NumPy operations with constant values."""
        code = """
import numpy as np
pi_values = np.full((10,), np.pi)
e_values = np.full((10,), np.e)
"""
        flow = convert(code)
        assert flow is not None

    def test_numpy_chained_operations(self):
        """Test chained NumPy operations."""
        code = """
import numpy as np
import pandas as pd
df = pd.read_csv('data.csv')
df['result'] = np.round(np.abs(np.log1p(df['value'])), 2)
"""
        flow = convert(code)
        assert flow is not None

    def test_numpy_with_broadcasting(self):
        """Test NumPy broadcasting behavior."""
        code = """
import numpy as np
import pandas as pd
df = pd.read_csv('data.csv')
df['scaled'] = df['value'] * np.sqrt(2)
"""
        flow = convert(code)
        assert flow is not None

    def test_empty_numpy_code(self):
        """Test code that only imports numpy."""
        code = """
import numpy as np
"""
        flow = convert(code)
        assert flow is not None
        assert len(flow.datasets) == 0
