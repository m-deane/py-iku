# Prompt: Generate Interactive Bayesian Regression and Time Series Forecasting Course for Commodities Trading

You are an expert in Bayesian statistics, time series analysis, and commodities trading. Create a comprehensive, interactive course titled "Bayesian Regression and Time Series Forecasting for Commodities Trading" that takes learners from fundamentals to practical trading applications.

## COURSE GENERATION REQUIREMENTS

### Overall Structure
Generate a complete course with:
- **10 progressive modules** (fundamentals → advanced applications)
- **Format**: Jupyter notebooks with markdown explanations and executable code
- **Duration**: ~40 hours of content (4 hours per module)
- **Prerequisites**: Basic Python, pandas, and undergraduate statistics

### Technical Stack
All code implementations must use:
- **Core Libraries**: PyMC (v5+), ArviZ, pandas, numpy, matplotlib, seaborn
- **Data Sources**: yfinance, FRED API, Quandl for real commodities data
- **Additional**: scipy, statsmodels, scikit-learn for comparisons
- **Deployment**: Jupyter notebooks with clear dependency lists

## MODULE SPECIFICATIONS

### Module 1: Foundations of Bayesian Thinking for Trading
**Learning Objectives:**
- Understand Bayesian vs Frequentist paradigms in financial context
- Apply Bayes' theorem to trading scenarios
- Interpret probability as degree of belief about market movements

**Content Requirements:**
```python
# Include implementations of:
- Bayes theorem calculator for trading signals
- Prior/posterior visualization for price predictions
- Comparison with frequentist confidence intervals
- Monte Carlo simulation of trading outcomes
```

**Exercises:**
1. Calculate posterior probability of trend reversal given technical indicators
2. Build Bayesian coin flip model for bid/ask imbalance
3. Quiz: 10 conceptual questions on Bayesian interpretation

### Module 2: Prior Selection and Market Knowledge Encoding
**Learning Objectives:**
- Encode market expertise into prior distributions
- Understand conjugate priors for computational efficiency
- Perform prior predictive checks for commodities

**Content Requirements:**
```python
# Implement:
- Prior elicitation from historical volatility
- Weakly informative priors for commodity returns
- Prior sensitivity analysis
- Expert knowledge encoding (e.g., seasonal patterns)
```

**Practical Dataset**: Crude oil (WTI) spot prices 2010-present

### Module 3: MCMC and Computational Inference
**Learning Objectives:**
- Implement MCMC sampling for posterior inference
- Diagnose convergence and sampling issues
- Optimize sampling for large-scale models

**Content Requirements:**
```python
# Cover:
- Metropolis-Hastings from scratch
- NUTS sampler in PyMC
- Convergence diagnostics (R-hat, ESS, trace plots)
- Posterior predictive checks
```

**Interactive Elements:**
- Widget to adjust sampler parameters and see convergence impact
- Exercise: Debug a poorly sampling model

### Module 4: Time Series Fundamentals for Commodities
**Learning Objectives:**
- Test and handle stationarity in commodity prices
- Decompose seasonal patterns in agricultural commodities
- Model autocorrelation structures

**Content Requirements:**
```python
# Implement:
- ADF and KPSS tests
- STL decomposition for wheat/corn prices
- ACF/PACF analysis and interpretation
- Differencing and detrending strategies
```

**Datasets**: Agricultural futures (corn, soybeans, wheat)

### Module 5: Bayesian Linear Regression for Price Prediction
**Learning Objectives:**
- Build Bayesian linear models with PyMC
- Incorporate economic indicators as predictors
- Quantify prediction uncertainty

**Content Requirements:**
```python
# Build progressively complex models:
1. Simple linear regression (price ~ time)
2. Multiple regression (price ~ supply + demand + USD_index)
3. Polynomial and basis function regression
4. Robust regression with Student-t likelihood

# Include:
- Posterior predictive distributions
- Credible intervals vs confidence intervals
- Model comparison using WAIC/LOO
```

**Case Study**: Natural gas prices with weather data

### Module 6: Bayesian Structural Time Series (BSTS)
**Learning Objectives:**
- Decompose time series into interpretable components
- Model trends, seasonality, and external regressors
- Generate probabilistic forecasts

**Content Requirements:**
```python
# Implement BSTS with:
- Local level model
- Local linear trend
- Seasonal components (daily, weekly, annual)
- Regression component for external factors
- Dynamic regression with time-varying coefficients
```

**Project**: Build BSTS model for gold prices with USD and inflation data

### Module 7: Hierarchical Models for Multiple Commodities
**Learning Objectives:**
- Model multiple related commodity series simultaneously
- Share information across similar markets
- Handle partial pooling for rare events

**Content Requirements:**
```python
# Develop:
- Hierarchical model for energy complex (WTI, Brent, Natural Gas)
- Varying intercepts and slopes by commodity
- Cross-commodity correlation structures
- Shrinkage and regularization in Bayesian context
```

**Exercise**: Model agricultural commodities with shared weather impacts

### Module 8: Gaussian Processes for Non-Linear Forecasting
**Learning Objectives:**
- Apply GP regression to capture non-linear patterns
- Select appropriate kernel functions for commodities
- Combine GPs with parametric components

**Content Requirements:**
```python
# Implement:
- GP with RBF kernel for smooth trends
- Periodic kernels for seasonality
- Matérn kernels for rough price movements
- Composite kernels (trend + seasonal + noise)
- Sparse GPs for computational efficiency
```

**Advanced**: GP with exogenous variables for copper prices

### Module 9: Volatility Modeling and Uncertainty Quantification
**Learning Objectives:**
- Model time-varying volatility (stochastic volatility)
- Distinguish aleatory vs epistemic uncertainty
- Generate prediction intervals for risk management

**Content Requirements:**
```python
# Build:
- GARCH models in Bayesian framework
- Stochastic volatility models
- Realized volatility using high-frequency data
- VaR and CVaR from posterior predictive
```

**Application**: Options pricing using Bayesian volatility estimates

### Module 10: Backtesting, Evaluation, and Trading Strategies
**Learning Objectives:**
- Properly backtest Bayesian forecasting models
- Avoid look-ahead bias and overfitting
- Translate forecasts into trading signals

**Content Requirements:**
```python
# Comprehensive backtesting framework:
- Walk-forward analysis
- Probabilistic Sharpe ratio
- Bayesian performance attribution
- Kelly criterion with parameter uncertainty

# Trading strategies:
- Mean reversion with uncertainty bands
- Trend following with regime switching
- Pairs trading with cointegration
- Portfolio optimization with Bayesian returns
```

**Capstone Project**: Complete trading system for energy portfolio

## PEDAGOGICAL REQUIREMENTS

### For Each Module, Include:

1. **Opening Hook**: Real trading scenario or market anomaly that motivates the topic
2. **Learning Path**:
   - Intuitive explanation with visualizations
   - Mathematical formulation (gradual complexity)
   - Code implementation (commented, step-by-step)
   - Trading application with real data

3. **Visual Elements**:
   - Interactive plots using plotly/bokeh
   - Posterior distribution animations
   - Before/after model comparisons
   - Trading signal visualizations

4. **Knowledge Checks**:
   - 5 multiple-choice questions per module (with explanations)
   - 3 coding exercises (easy/medium/hard)
   - 1 mini-project applying concepts

5. **Common Pitfalls Section**:
   - "Don't do this" examples with consequences
   - Debugging guides for common errors
   - Best practices checklist

### Interactive Features

1. **Code Exercises Format**:
```python
# EXERCISE: Fill in the missing parts
def calculate_posterior(prior, likelihood, evidence):
    """Calculate posterior using Bayes theorem"""
    # TODO: Your code here
    posterior = ___________
    return posterior

# SOLUTION (hidden by default)
def calculate_posterior(prior, likelihood, evidence):
    posterior = (likelihood * prior) / evidence
    return posterior
```

2. **Parameter Exploration Widgets**:
```python
# Use ipywidgets for interactive exploration
@interact(prior_mean=(-2, 2, 0.1), prior_std=(0.1, 3, 0.1))
def explore_prior_impact(prior_mean, prior_std):
    # Show how prior affects posterior
    pass
```

3. **Self-Assessment Quizzes**:
- Immediate feedback with explanations
- Adaptive difficulty based on performance
- Progress tracking across modules

## DATA REQUIREMENTS

### Primary Datasets to Include:
1. **Energy**: WTI Crude, Brent Crude, Natural Gas, RBOB Gasoline
2. **Metals**: Gold, Silver, Copper, Aluminum
3. **Agriculture**: Corn, Soybeans, Wheat, Coffee, Sugar
4. **Economic**: USD Index, Inflation, Interest Rates

### Data Preprocessing Templates:
```python
def prepare_commodity_data(ticker, start_date, end_date):
    """
    Standardized data preparation pipeline:
    1. Download from yfinance/FRED
    2. Handle missing values
    3. Calculate returns
    4. Add technical indicators
    5. Merge with economic data
    """
    pass
```

## DELIVERABLE SPECIFICATIONS

### File Structure:
```
bayesian-commodities-course/
├── requirements.txt
├── README.md
├── datasets/
│   ├── download_data.py
│   └── cached_data/
├── modules/
│   ├── 01_bayesian_foundations/
│   │   ├── notebook.ipynb
│   │   ├── exercises.ipynb
│   │   ├── solutions.ipynb
│   │   └── quiz.json
│   ├── 02_prior_selection/
│   │   └── ...
│   └── 10_trading_strategies/
├── projects/
│   ├── mid_course_project.ipynb
│   └── capstone_project.ipynb
├── utils/
│   ├── plotting.py
│   ├── metrics.py
│   └── backtesting.py
└── tests/
    └── test_solutions.py
```

### Quality Criteria:
1. **Code Quality**:
   - All code must run without errors in Python 3.9+
   - Type hints for all functions
   - Docstrings with examples
   - Unit tests for utility functions

2. **Educational Quality**:
   - Learning objectives measurably achieved
   - Progressive difficulty curve
   - At least 3 worked examples per concept
   - Clear connection to trading applications

3. **Practical Relevance**:
   - Use recent data (within last 2 years)
   - Include transaction costs and slippage
   - Address market microstructure issues
   - Discuss regulatory considerations

## ADVANCED TOPICS (Bonus Modules)

### Optional Module 11: Deep Learning Integration
- Bayesian neural networks for price prediction
- Uncertainty in LSTM forecasts
- Variational autoencoders for regime identification

### Optional Module 12: Alternative Data Sources
- Satellite data for agricultural commodities
- Weather data integration
- News sentiment with uncertainty
- Supply chain indicators

## ASSESSMENT AND CERTIFICATION

### Course Completion Requirements:
1. Complete 80% of exercises (auto-graded)
2. Pass module quizzes (70% threshold)
3. Submit mid-course project (peer-reviewed)
4. Complete capstone project with:
   - Working forecasting system
   - Backtesting report
   - Risk analysis
   - 5-page writeup

### Capstone Project Rubric:
- **Technical Implementation** (40%): Code quality, model sophistication
- **Performance** (30%): Backtest metrics, proper evaluation
- **Risk Management** (20%): Uncertainty quantification, position sizing
- **Documentation** (10%): Clear explanation, reproducibility

## MAINTENANCE AND UPDATES

Include instructions for:
1. Updating data feeds when sources change
2. Refreshing examples with recent market events
3. Adding new commodities or markets
4. Incorporating new PyMC features
5. Community contribution guidelines

## SUCCESS METRICS

The course should achieve:
- Learner can implement Bayesian models for any commodity
- Portfolio Sharpe ratio improvement of >0.2 vs baseline
- 90% completion rate for engaged learners
- Practical skills directly applicable to trading roles

---

**EXECUTION INSTRUCTIONS**: Generate this complete course as a series of Jupyter notebooks with all code functional and tested. Include sample outputs, visualizations, and ensure all data downloads work with fallback options. Make the course self-contained so learners can run everything locally with minimal setup. Begin with Module 1 and progressively build complexity while maintaining practical trading focus throughout.