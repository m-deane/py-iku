# Bayesian Regression and Time Series Forecasting for Commodities Trading
## Comprehensive Course Research Summary

**Research Date:** 2025-12-02
**Research Scope:** 135+ sources analyzed across GitHub, academic publications, documentation, and technical blogs

---

## Executive Summary

This research compiles authoritative technical resources for developing an educational course on Bayesian time series forecasting applied to commodities trading. The analysis covers modern Bayesian libraries (PyMC, Stan, NumPyro, TensorFlow Probability), specialized time series models (BSTS, BVAR, GPs, state-space), commodities market dynamics, and practical implementation considerations including evaluation metrics (CRPS), backtesting frameworks, and uncertainty quantification for trading decisions.

**Key Finding:** Bayesian methods excel for commodities forecasting due to their ability to (1) quantify uncertainty explicitly, (2) incorporate domain knowledge through priors, (3) handle small datasets via regularization, and (4) enable sequential updating as new data arrives.

---

## Module 1: Bayesian Fundamentals for Time Series

### Core Concepts

**Priors vs Posteriors:**
- Priors encode domain knowledge before observing data
- Critical for AR models: broad uniform priors can cause forecast instability
- Best practice: Use informative priors that enforce stationarity (|phi| < 1 for AR coefficients)

**MCMC vs Variational Inference:**

| Method | Speed | Accuracy | When to Use |
|--------|-------|----------|-------------|
| MCMC (NUTS) | Baseline (1x) | Unbiased, exact | Small/medium data, need precision |
| Variational Inference (ADVI) | 10,000x faster | Slight bias, underestimates uncertainty | Large datasets, need speed |

**Decision Criteria:**
- Use MCMC when you have time and value precision
- Use VI for large-scale problems or rapid prototyping
- Always validate VI results against MCMC on subset

### Recommended Libraries

**PyMC (Primary Recommendation):**
- User-friendly API with extensive documentation
- NUTS sampler (state-of-art MCMC) and ADVI built-in
- Active community and regular updates
- Best for: Education, rapid development, general Bayesian modeling

**Stan/PyStan:**
- Own autodiff library, proven at scale
- Excellent error/warning messages (auto-detects divergences)
- Best for: Production systems, rigorous statistical analysis
- Limitation: Cannot sample discrete variables, requires learning Stan language

**NumPyro:**
- JAX-based for JIT compilation to GPU/TPU/CPU
- Fastest sampling, especially with GPU
- Best for: Large-scale problems, researchers, GPU users
- Performance: Outperforms PyStan on medium/large datasets

**TensorFlow Probability:**
- Most modular, allows custom algorithms
- Deep learning integration
- Best for: Researchers developing new methods, deep probabilistic models
- Limitation: More verbose API

### Key Resources

1. [Bayesian Modeling and Computation in Python - Chapter 6: Time Series](https://bayesiancomputationbook.com/markdown/chp_06.html)
2. [PyMC Tutorial at PyData London 2025](https://cfp.pydata.org/london2025/talk/T9KEHN/)
3. [Comparison of Python PPLs](https://www.nelsontang.com/blog/python_ppls_compared/python-ppls-compared.html)

---

## Module 2: Bayesian Time Series Models

### 1. Bayesian Structural Time Series (BSTS)

**Description:** Decompose time series into trend + seasonality + regression components with Bayesian inference

**Advantages over ARIMA:**
- Transparent (no differencing/lags to interpret)
- Visual component inspection
- Quantify uncertainty of each component
- Natural framework for causal impact analysis

**Python Libraries:**

| Library | Method | Strengths | Limitations |
|---------|--------|-----------|-------------|
| TensorFlow Probability | `tfp.sts` module | Convenient helpers, mature | Requires TF knowledge |
| pybuc | Gibbs sampling | Fast, follows R's bsts | Python ≥3.9, no spike-and-slab prior |
| pydlm | Dynamic Linear Models | Well-documented | Limited to linear Gaussian |
| PyFlux | Easy interface | User-friendly | Less actively maintained |

**Applications:** Demand forecasting, anomaly detection, nowcasting, causal inference

### 2. Bayesian Vector Autoregression (BVAR)

**Key Innovation:** Parameters treated as random variables with priors (vs fixed in classical VAR)

**Minnesota Prior:** Standard prior assuming random walk for each variable, shrinks unrestricted model toward parsimonious benchmark

**Hierarchical Extension:** Estimate BVAR across multiple commodities (e.g., countries/regions) with shared parameters

**Python Implementation:**
- PyMC: Full BVAR with impulse response, hierarchical priors
- pybvar: Dedicated package (early stage)
- Statsmodels: TVP-VAR (time-varying parameters) with MCMC

**Use Cases for Commodities:**
- Model crude oil, gasoline, heating oil jointly (related products)
- Analyze spillover effects between energy markets
- Forecast multiple commodity prices with shared information

### 3. Gaussian Processes (GP)

**Advantages:**
- Non-parametric (flexible functional form)
- Probabilistic predictions with uncertainty
- Capture complex patterns via kernel choice

**Challenges:**
- O(n³) computational cost
- Can get stuck in local optima
- Poor kernel choice → flat forecasts

**Python Libraries:**
- GPflow: TensorFlow-based, GPU acceleration, state-of-art (Variational Fourier Features)
- PyMC: GP priors in Bayesian models
- scikit-learn: Basic GP regression

**Resources:**
- [Juan Camilo Orduz - GP Time Series with PyMC3](https://juanitorduz.github.io/gp_ts_pymc3/)
- [PyData Berlin 2019 Tutorial](https://juanitorduz.github.io/gaussian_process_time_series/)

### 4. Hierarchical Models

**Description:** Multilevel models sharing information across related time series

**Key Benefit:** Partial pooling - balance between complete pooling (ignore differences) and no pooling (separate models)

**Commodities Applications:**
- Regional commodity prices with global trend
- Related products (heating oil, diesel, gasoline) with shared seasonality
- Demand across product grades

**Case Study:** PyMC Labs forecasted 308 Australian tourism time series (1998-2016) by state/region/purpose using hierarchical model

**Libraries:**
- PyMC: Native support, non-centered parameterization
- Bambi: Built on PyMC, formula-based like R's lme4

### 5. State Space Models

**Description:** Observed time series as function of unobserved latent states

**Inference:** Kalman filter (linear Gaussian) or particle filter (nonlinear/non-Gaussian)

**Advantages:**
- Handle missing observations elegantly
- Integrate external regressors
- Separate observation noise from process noise

**Python Support:**
- pymc-extras.statespace: Official PyMC state space (formerly pymc_statespace)
- statsmodels.tsa.statespace: Kalman filter with Bayesian MCMC parameter estimation

**Upcoming Tutorial:** [PyData Berlin 2025 - Beginner's Guide to State Space Modeling](https://cfp.pydata.org/berlin2025/talk/GRZ3RG/)

### 6. Prophet

**Bayesian Foundation:** Uses Stan for MAP optimization, optional full sampling

**Components:**
- Piecewise linear/logistic trend with automatic changepoints
- Fourier series for seasonality (yearly, weekly, daily)
- Holiday effects with custom calendars

**Commodities Application:**
- Study on raw materials forecasting: MAPE 5.14% for glass fiber, resin, metal, energy, paint
- Faster than custom Bayesian models but rarely beats on accuracy

**Alternative:** pm-prophet (Prophet-like in PyMC3 with more flexibility)

**Comparison Study:** Bayesian Symbolic Regression vs Prophet for 56 commodity spot prices

---

## Module 3: Commodities Trading Applications

### Commodity Types and Characteristics

| Category | Examples | Key Characteristics | Mean Reversion |
|----------|----------|---------------------|----------------|
| **Energy** | Crude oil, natural gas, gasoline, heating oil | Geopolitical, seasonal (heating/cooling), speculative | Low - trend following works better |
| **Precious Metals** | Gold, silver, platinum, palladium | Store of value, inflation hedge | Moderate |
| **Industrial Metals** | Copper, aluminum, zinc, nickel | Tied to manufacturing, construction | Moderate |
| **Agriculture/Grains** | Corn, wheat, soybeans, rice | Planting/harvest cycles, weather-dependent | Higher than energy |
| **Softs** | Coffee, cocoa, sugar, cotton, orange juice | Perishable, harvest-based, weather shocks | Variable |
| **Livestock** | Live cattle, lean hogs | Feed costs (corn/soy), consumer demand | Moderate |

### Data Sources

**Free Sources:**

1. **TurtleTrader:**
   - Historical futures from 1970s
   - Format: ASCII/CSV with OHLCV + Open Interest
   - Commodities: Crude, Gold, Corn, Cotton, Soybeans, Sugar, Wheat, etc.
   - URL: https://www.turtletrader.com/hpd/

2. **Quandl (Nasdaq Data Link):**
   - Daily futures, some from 1950s
   - API: Python, R, Excel, MATLAB
   - Note: CHRIS continuous futures discontinued Aug 2024
   - Requires free API key

3. **World Bank Pink Sheet:**
   - Monthly prices since 1960 for 100+ commodities
   - Source: IMF data

4. **Yahoo Finance (via yfinance):**
   - Recent futures: CL=F (Crude), GC=F (Gold), NG=F (Natural Gas)
   - Limitation: Limited historical depth

**Paid Sources:**

1. **Databento:** Real-time/historical tick, order book, 1-min bars; Python/C++/Rust APIs
2. **FirstRate Data:** 1-min to daily from 2007 for 130+ contracts
3. **Bloomberg Terminal:** Professional-grade (~$25k/year)

### Seasonality Patterns

**Key Drivers:**
- Weather (heating/cooling demand for energy)
- Planting/harvest seasons (agriculture)
- Holiday demand (gold in India, sugar)
- Production cycles (livestock)

**Examples:**
- Natural gas: Higher in winter (heating) and summer (cooling)
- Crude oil: Summer driving season demand
- Corn/wheat: Prices rise during planting, fall at harvest
- Gold: Spikes during Indian wedding season

**Statistical Models:**
- SARIMA: Captures seasonal patterns better than non-seasonal ETS
- Data requirement: 5-10 years minimum for reliable seasonal indexes
- Technique: Divide each month's average by year's average

**Caution:** Past seasonality doesn't guarantee future patterns; external factors (weather, politics) can override

**Resources:**
- [Forecaster - Seasonality in Financial Markets](https://forecaster.biz/seasonality/)
- [FasterCapital - Seasonality in Commodities](https://fastercapital.com/content/Seasonality-in-Commodities--Capitalizing-on-Cyclical-Trends.html)

### Mean Reversion vs Momentum

**Critical Insight:** Commodities are LESS mean-reverting than stocks; trend following often works better

| Strategy | Best Horizon | Works Better In | Commodities Performance |
|----------|--------------|-----------------|------------------------|
| Mean Reversion | < 3 months | Spot markets | Poor for commodities |
| Momentum | 3-12 months | Futures markets | Excellent for commodities |

**Combined Strategy:**
- Double-sort (momentum + reversal): 20.24% annual return
- Momentum-only: 11.14% annual return
- Outperformance related to global funding liquidity

**Mean Reversion Techniques:**
- Statistical arbitrage
- Pairs trading
- Bollinger bands

**Resources:**
- [ScienceDirect - Momentum and mean-reversion in commodity markets](https://www.sciencedirect.com/science/article/abs/pii/S2405851315300416)
- [QuantInsti - Mean Reversion Strategies](https://blog.quantinsti.com/mean-reversion-strategies-introduction-building-blocks/)

### Spread Trading and Cointegration

**Concept:** Trade price differential between related commodities expecting convergence

**Statistical Foundation:** Cointegration = long-term equilibrium between non-stationary series

**Methodology:**
1. Test cointegration (ADF test via statsmodels.tsa.stattools.coint)
2. Estimate hedge ratio via linear regression (beta coefficient)
3. Calculate spread = linear combination of two assets
4. Compute z-score of spread
5. Trade when z-score exceeds thresholds (e.g., ±2)
6. Exit when spread reverts to mean

**Commodities Example:**
- Crude oil and gasoline (production linkage)
- Natural gas and heating oil (substitutes)
- Corn and ethanol (input-output relationship)

**Pitfall:** Multiple comparisons bias
- Testing 100 random pairs → expect 5 false positives at p<0.05
- **Solution:** Start with economic rationale for cointegration

**Resources:**
- [PyQuant News - Pairs Trading Strategy](https://www.pyquantnews.com/the-pyquant-newsletter/build-a-pairs-trading-strategy-python)
- [Medium - Cointegration and Spread Monitoring](https://medium.com/@mburakbedir/understanding-cointegration-and-how-to-monitor-spread-between-prices-with-python-518c66c39ee4)

### Contango and Backwardation

| Term | Definition | Roll Yield | Cause | Example |
|------|------------|------------|-------|---------|
| **Contango** | Futures > Spot (upward curve) | Negative (lose money) | Storage + financing costs | Gold |
| **Backwardation** | Futures < Spot (downward curve) | Positive (gain money) | Supply disruptions, high demand | Crude during shortage |

**Impact on Investors:**
- Commodity ETFs using futures: Contango erodes returns, backwardation enhances
- Prices converge to spot as expiration approaches
- 2020 oil crash: Steep contango → significant negative roll yields

**Resources:**
- [Fidelity - Commodity ETFs: Contango/Backwardation](https://www.fidelity.com/learning-center/investment-products/etf/commodity-etfs-contango-backwardation)
- [CME Group - What is Contango and Backwardation](https://www.cmegroup.com/education/courses/introduction-to-ferrous-metals/what-is-contango-and-backwardation.html)

---

## Module 4: Practical Implementation

### Data Preprocessing

**Missing Data:**
- Forward fill for infrequent trading
- Interpolation for systematic gaps
- State space models handle missing naturally (Kalman filter)
- Multiple imputation for uncertainty quantification

**Outliers:**
- Detection: Z-score, IQR, domain knowledge
- Handling: Robust loss functions (Huber, Student-t), Winsorization, mixture models

**Structural Breaks:**
- Examples: Regime changes, policy shifts
- Detection: Changepoint detection, CUSUM tests
- Modeling: Automatic (Prophet, BSTS) or explicit (Markov switching)

### Feature Engineering

**Lagged Features:**
- Past values as predictors (assumption: past informs future)
- Example: Lag 1, 7, 30 days for daily data

**Rolling Statistics:**
- Moving averages, standard deviations over sliding window
- Benefits: Smooth noise, highlight trends, capture volatility
- Example: 20-day MA, 60-day rolling std, Bollinger bands

**Calendar Features:**
- Temporal: Day of week, month, quarter
- Cyclical encoding: Sin/cos for continuity (Dec → Jan)
- Holidays: Custom calendars for commodities

**External Variables:**

| Type | Examples | Use Case |
|------|----------|----------|
| Weather | Temperature, precipitation, HDD/CDD | Energy demand, agriculture |
| Inventory | EIA crude stocks, USDA grain stocks | Fundamental supply indicator |
| Macro | GDP, inflation, interest rates, USD index | Economic conditions |
| Domain-specific | Crack spread, crush spread | Commodity-specific margins |

**Resources:**
- [Analytics Vidhya - 6 Powerful Feature Engineering Techniques](https://www.analyticsvidhya.com/blog/2019/12/6-powerful-feature-engineering-techniques-time-series/)
- [Microsoft - Feature Engineering for Time Series](https://medium.com/data-science-at-microsoft/introduction-to-feature-engineering-for-time-series-forecasting-620aa55fcab0)

### Backtesting

**Time Series Considerations:**
- NO random splits (would train on future, predict past)
- Use chronological train/test split
- Walk-forward validation (expanding or rolling window)
- Avoid look-ahead bias

**Python Libraries:**

| Library | Features | Use Case |
|---------|----------|----------|
| Orbit | BackTester class for rolling validation | Bayesian forecasting with hyperparameter tuning |
| PyBats | One-step-ahead with parameter updating | True out-of-sample Bayesian predictions |
| PyAlgoTrade | Mature framework, paper/live trading | Algorithm trading strategies |
| bt | Portfolio strategy testing | Asset weighting, rebalancing |

**Walk-Forward Example:**
- Train: 5-year rolling window
- Test: 1 month ahead
- Refit: Monthly (retrain on most recent 5 years)
- Note: Computationally expensive for Bayesian MCMC

### Evaluation Metrics

**Probabilistic Metrics (Critical for Bayesian):**

**CRPS (Continuous Ranked Probability Score):**
- Generalizes MAE to probability distributions
- Formula: CRPS(F, y) = ∫(F(x) - 1_{x≥y})² dx
- Lower is better
- Evaluates both sharpness (narrow intervals) and calibration (accuracy)
- Reduces to MAE for point forecasts
- **Proper scoring rule** (cannot be gamed)

**Python Libraries:**
- properscoring: 20x speedup with numba
- CRPS package: crps, fcrps (fair), acrps (adjusted)
- PyTorch-Metrics: Deep learning integration
- Skforecast: Works with bootstrap ensembles

**Other Probabilistic Metrics:**
- Log-likelihood: Direct probabilistic fit
- Calibration: 90% intervals should have 90% coverage
- Sharpness: Width of prediction intervals (narrower better, given calibration)

**Point Forecast Metrics:**
- MAE: Interpretable in original units
- RMSE: Penalizes large errors more
- MAPE: Scale-independent (but undefined for zeros)

**Trading Metrics:**
- Sharpe ratio, maximum drawdown, hit rate, profit factor

**Resources:**
- [Skforecast - CRPS Guide](https://skforecast.org/0.15.0/faq/probabilistic-forecasting-crps-score.html)
- [Medium - Essential Guide to CRPS](https://medium.com/data-science/essential-guide-to-continuous-ranked-probability-score-crps-for-forecasting-ac0a55dcb30d)

---

## Module 5: Advanced Topics

### Regime-Switching Models

**Markov Switching Models:**
- Parameters switch between k regimes following Markov process
- Examples: Bull vs bear, high vs low volatility, contango vs backwardation

**Python (statsmodels):**
- `MarkovRegression`: First-order k-regime switching
- `MarkovAutoregression`: Hamilton (1989) model
- Parameters: k_regimes, trend, switching_variance, exog_tvtp
- Estimation: Hamilton filter + Kim smoother
- Tip: Use search_reps=20 to find global optimum (many local maxima)

**Resources:**
- [Statsmodels - Markov Regression](https://www.statsmodels.org/stable/examples/notebooks/generated/markov_regression.html)

### Incorporating Fundamental Data

**Data Types:**

| Category | Sources | Examples |
|----------|---------|----------|
| Inventory | EIA, USDA | Crude stocks, grain stocks, crop production |
| Production | Baker Hughes, OPEC, mining reports | Rig counts, mine output, smelter production |
| Demand | PMI, construction, exports | Refinery utilization, industrial production, export data |
| Weather | NOAA | HDD/CDD, precipitation, temperature |

**Bayesian Advantage:**
- Natural framework to combine price signals with fundamental priors
- Example: Use inventory levels to inform prior on price direction
- Hierarchical models share information between fundamentals and prices

### Multi-Output Forecasting

**Approaches:**
- Bayesian VAR: Capture cross-commodity dynamics (e.g., crude oil + gasoline + heating oil)
- Hierarchical models: Share information across commodities with common structure
- Copula models: Model marginal distributions separately, join with copula

**Benefits:**
- Improved forecasts via information sharing
- Consistent multi-asset scenarios for portfolio optimization
- Capture spillover effects

### Real-Time Updating

**Sequential Bayesian Inference:**
- Today's posterior → tomorrow's prior
- Incremental updates without full retraining
- Requires conjugate priors for closed-form (fast)

**Challenges:**
- Model drift (non-stationarity)
- Full MCMC too slow for high-frequency updates
- Solution: Variational inference or conjugate models

### Uncertainty Quantification for Trading

**Applications:**

| Use Case | Bayesian Approach | Benefit |
|----------|-------------------|---------|
| Position sizing | Kelly criterion with posterior distribution | Account for forecast uncertainty |
| Value-at-Risk | Estimate from posterior predictive | Better tail risk estimates |
| Optimal stopping | Bayesian decision theory | When to exit based on updated beliefs |
| Portfolio optimization | Account for parameter uncertainty | More robust allocations |

**Epistemic vs Aleatoric Uncertainty:**
- Epistemic: Model/parameter uncertainty (reducible with data) → Posterior spread
- Aleatoric: Inherent randomness (irreducible) → Likelihood variance
- Importance: Distinguish for better risk management
- Methods: Deep Ensembles, Bayesian Neural Networks

**Frameworks:**
- UAMDP (Uncertainty-Aware MDP): Bayesian forecasting + RL + CVaR constraint
- Applications: High-frequency trading, inventory control

**Resources:**
- [INFORMS - Decisions Under Uncertainty](https://pubsonline.informs.org/doi/10.1287/mnsc.2023.00265)
- [Wiley - Financial Time Series Uncertainty](https://onlinelibrary.wiley.com/doi/10.1111/joes.70018)

---

## Common Pitfalls and Solutions

| Pitfall | Solution |
|---------|----------|
| Overly broad uniform priors → unstable forecasts | Use informative priors; enforce stationarity in AR coefficients |
| Non-stationary data without differencing | Test for unit roots (ADF); difference or use integrated models |
| Look-ahead bias in features/preprocessing | Strictly chronological splits; no global scaling with future data |
| Ignoring uncertainty (point forecasts only) | Always report full posterior predictive; evaluate with CRPS |
| Overfitting to noise (complex model, short series) | Informative priors as regularization; prefer simpler models |
| Ignoring MCMC diagnostics | Check R-hat, ESS, divergences; reparameterize if needed |
| Multiple comparisons (testing many pairs) | Start with economic rationale; adjust p-values or use Bayesian selection |
| Assuming stationarity during regime changes | Use regime-switching or changepoint detection |
| Full MCMC on huge dataset | Start with subset; use ADVI; consider NumPyro + GPU |
| VI underestimating uncertainty | Validate against MCMC on subset; or switch to MCMC |

---

## Best Practices

### Bayesian Workflow (Gelman et al. 2020)

1. Prior predictive checks (simulate from prior to ensure sensible)
2. Fit model to data
3. Posterior diagnostics (R-hat, ESS, trace plots)
4. Posterior predictive checks (does model reproduce data features?)
5. Model comparison (WAIC, LOO)
6. Iterate and refine

### Model Development

- Start simple (Bayesian linear regression), add complexity incrementally
- Prefer interpretable models (easier to debug and explain)
- Incorporate domain knowledge in priors and features
- Validate assumptions (check residuals for autocorrelation, heteroskedasticity)

### Production Deployment

- Model versioning (track priors, hyperparameters)
- Monitor forecast performance over time
- Decide retraining frequency based on market dynamics
- Have fallback simpler model if complex model fails

### Communication

- Visualize uncertainty (prediction intervals, not just point forecasts)
- Translate Bayesian concepts to business language
- Highlight model limitations and when assumptions may break

---

## Recommended Course Structure

### Module 1: Bayesian Foundations (2 weeks)
- Bayesian inference fundamentals
- MCMC and variational inference
- PyMC/Stan basics
- Prior specification and sensitivity
- Posterior diagnostics

**Labs:**
- Bayesian linear regression for commodity prices
- Compare MCMC vs ADVI
- Prior predictive checks for time series

### Module 2: Bayesian Time Series Models (4 weeks)
- ARIMA and Bayesian ARIMA
- State space models and Kalman filtering
- BSTS and decomposition
- Prophet
- Gaussian processes

**Labs:**
- Forecast crude oil with Bayesian ARIMA
- Custom Prophet-like model in PyMC
- BSTS for natural gas seasonality

### Module 3: Commodities Market Dynamics (2 weeks)
- Commodity types and futures markets
- Seasonality and calendar effects
- Contango, backwardation, roll yield
- Mean reversion vs momentum
- Fundamental drivers

**Labs:**
- Seasonality in agricultural futures
- Crude-gasoline spread with cointegration
- Regime switching in volatility

### Module 4: Hierarchical and Multivariate Models (3 weeks)
- Hierarchical Bayesian models
- Bayesian VAR
- Cointegration and error correction
- Copula models

**Labs:**
- Hierarchical model for regional grain prices
- BVAR for energy complex
- Pairs trading with Bayesian spreads

### Module 5: Advanced Topics and Production (3 weeks)
- Markov switching
- Incorporating fundamental data
- Real-time updating
- Uncertainty quantification for risk management
- CRPS and calibration
- Deployment and backtesting

**Labs:**
- Regime-switching for crude volatility
- Real-time Bayesian updating
- Trading system with uncertainty-based sizing
- Walk-forward backtest with probabilistic evaluation

### Capstone Project
- Forecast 3-5 commodities with appropriate Bayesian models
- Incorporate seasonality, fundamentals, regime switching
- Proper backtesting with probabilistic metrics
- Uncertainty quantification for risk management
- Deploy with real-time updates
- Written report with Bayesian workflow

---

## Essential Python Libraries

### Core Bayesian
- **pymc** (≥5.0): Primary PPL, NUTS + ADVI
- **arviz**: Posterior analysis, diagnostics, model comparison
- **bambi**: High-level hierarchical models on PyMC

### Alternative PPLs
- **stan/pystan**: Production-grade, robust warnings
- **numpyro**: JAX-based, GPU acceleration, fastest

### Time Series
- **prophet**: Baseline additive model
- **statsmodels**: ARIMA, state space, Markov switching
- **orbit**: Bayesian forecasting with backtesting (Uber)
- **pydlm**: Dynamic linear models

### Data & Features
- **pandas**: Time series manipulation
- **yfinance**: Yahoo Finance downloader
- **investpy**: Investing.com commodity data
- **featuretools**: Automated feature engineering

### Backtesting & Evaluation
- **properscoring**: CRPS and proper scoring rules
- **pyalgotrade**: Algorithm backtesting
- **bt**: Portfolio backtesting

### Visualization
- **matplotlib**, **seaborn**: Basic plots
- **plotly**: Interactive forecasts
- **arviz**: Bayesian-specific (trace, posterior, pair plots)

---

## Suggested Datasets

### Beginner
- **TurtleTrader**: Free continuous futures (1970s+) - Corn, Crude, Gold, Natural Gas
- **Yahoo Finance**: Easy Python access via yfinance - CL=F, GC=F, NG=F, ZC=F

### Intermediate
- **Quandl**: Long history via API (requires free key)
- **World Bank Pink Sheet**: Monthly prices 1960+ for 100+ commodities
- **EIA**: Energy fundamentals (inventories, production)
- **USDA**: Agriculture fundamentals (grain stocks, crop production)

### Advanced/Capstone
- **Databento**: Tick, order book, 1-min bars (professional-grade, free credits)
- **FirstRate Data**: 1-min to daily from 2007 for 130+ contracts

### Supplementary
- **NOAA**: Weather data (temperature, precipitation, HDD/CDD)
- **FRED**: Macro indicators via pandas_datareader (GDP, CPI, rates, USD)
- **CFTC**: Commitments of Traders (positioning/sentiment)

---

## Authoritative References

### Books
1. Bayesian Modeling and Computation in Python (Martin et al., 2021) - https://bayesiancomputationbook.com/
2. Forecasting: Principles and Practice, 3rd ed (Hyndman & Athanasopoulos, 2021) - https://otexts.com/fpp3/
3. Time Series Analysis by State Space Methods (Durbin & Koopman, 2012)

### Papers
1. Taylor & Letham (2018) - Forecasting at Scale (Prophet), The American Statistician
2. Chad Fulton (2022) - Bayesian Estimation and Forecasting in statsmodels, SciPy 2022
3. Scott & Varian (2014) - Predicting the Present with BSTS, IJMMNO

### Online Resources
1. PyMC Example Gallery - Time Series: https://www.pymc.io/projects/examples/en/latest/blog/tag/time-series.html
2. PyMC Labs Blog: https://www.pymc-labs.com/blog-posts/
3. Dr. Juan Camilo Orduz Blog: https://juanitorduz.github.io/
4. Chad Fulton's Blog: http://www.chadfulton.com/

### Documentation
1. PyMC: https://www.pymc.io/
2. ArviZ: https://arviz-devs.github.io/arviz/
3. Statsmodels TSA: https://www.statsmodels.org/stable/tsa.html
4. Prophet: https://facebook.github.io/prophet/

---

## Key Takeaways

1. **Bayesian methods are ideal for commodities** due to uncertainty quantification, domain knowledge incorporation, and handling of limited data

2. **Choose the right tool:**
   - PyMC for education and rapid development
   - Stan for production and rigorous analysis
   - NumPyro for large-scale + GPU
   - TF Probability for custom algorithms

3. **BSTS and hierarchical models** are particularly powerful for commodities due to seasonal decomposition and information sharing

4. **Commodities differ from stocks:** Less mean-reverting, momentum works better, understand contango/backwardation

5. **Proper evaluation is critical:** Use CRPS for probabilistic forecasts, not just RMSE/MAE

6. **Bayesian workflow matters:** Prior/posterior predictive checks, diagnostics, and iteration are essential

7. **Start simple, add complexity:** Build from Bayesian linear regression → ARIMA → BSTS → hierarchical

8. **Uncertainty for trading:** Use full posterior distribution for position sizing, risk management, and decision-making

---

**Full detailed research with 48 citations available in:** `bayesian_commodities_course_research.json`
