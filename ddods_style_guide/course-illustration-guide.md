# Course Illustration & Visual Enhancement Guide

A reusable reference for enhancing technical courses and textbooks with professional diagrams and inline example plots. Extracted from the py-tidymodels textbook project, which uses Daily Dose of Data Science (DDODS) as the visual design benchmark.

---

## Part 1: The DDODS Visual Design Language

### What Makes DDODS Diagrams Effective

Daily Dose of Data Science (dailydoseofds.com) by Avi Chawla has established a distinctive visual language for explaining ML/DS concepts. The diagrams succeed because they follow consistent design principles:

### 1.1 Two Core Visual Styles

**Style A: Hand-Drawn Whiteboard Diagrams**
- White or near-white background with rounded-corner container boxes
- Hand-drawn aesthetic (slightly imperfect lines, handwritten-style fonts)
- Colored icons/shapes representing data points (pastel squares, circles)
- Gray directional arrows showing data flow
- Bold, large title text (underlined or decorative)
- Minimal axis labels --- the shape of the diagram IS the explanation
- Examples: Bagging overview, Boosting overview, PCA transformation, Bayesian optimization concept

**Style B: Gradient-Background Presentation Slides**
- Purple/pink gradient backgrounds (characteristic DDODS branding)
- White text for labels and annotations
- Embedded code snippets with dark terminal-style boxes (macOS traffic light dots)
- Side-by-side comparisons (before/after, good/bad, simple/complex)
- Curving white arrows connecting elements
- Examples: Decision Tree vs Random Forest variance, Linear Regression fit, XGBoost concept

### 1.2 Diagram Category Taxonomy

| Category | Purpose | DDODS Examples |
|----------|---------|----------------|
| **Algorithm Flow** | Show step-by-step process | Bagging (data -> bootstrap -> models), Boosting (sequential correction) |
| **Concept Comparison** | Side-by-side contrast | Decision Tree vs Random Forest variance, Single model vs Ensemble (sticks analogy) |
| **Transformation** | Input -> Process -> Output | PCA (X -> X_transformed), Hyperparameter search (space -> model -> best) |
| **Problem Illustration** | Visualize the issue | Curse of dimensionality (2D dense -> high-D sparse), R-squared can be misleading |
| **Code + Visual** | Show what code produces | Linear regression fit (code block + scatter plot) |
| **Analogy/Metaphor** | Physical-world parallel | Single stick vs bundle of sticks (ensemble strength) |

### 1.3 Color Palette

DDODS uses a consistent, limited palette:

| Color | Hex (approx) | Usage |
|-------|-------------|-------|
| Light blue | `#B3D9FF` | Data points, prediction boxes, neutral elements |
| Green | `#4CAF50` | Correct predictions, positive outcomes, "good" |
| Red/Coral | `#E57373` | Incorrect predictions, errors, "bad", warnings |
| Teal/Cyan | `#00BCD4` | Model icons (brain/circuit icon), process nodes |
| Purple gradient | `#9C27B0` to `#E91E63` | Background for Style B slides |
| Orange/Yellow | `#FFA726` | Accents, highlighted elements |
| White | `#FFFFFF` | Background (Style A), text (Style B) |
| Dark gray | `#424242` | Arrows, borders, labels (Style A) |

### 1.4 Key Design Principles

1. **One concept per diagram**: Each image explains exactly ONE thing. Bagging is separate from Boosting. PCA is separate from the curse of dimensionality.

2. **Progressive disclosure**: Complex algorithms are shown as left-to-right or top-to-bottom flows with clear stages. The reader's eye follows a natural path.

3. **Color as semantics**: Colors encode meaning consistently. Green = correct/good, Red = incorrect/bad, Blue = data/neutral. This is never arbitrary.

4. **Minimal text**: Labels are 1-3 words. Explanation lives in the surrounding article text, not crammed into the diagram.

5. **Concrete over abstract**: Uses specific examples (colored data points, tree diagrams, actual scatter plots) rather than abstract notation. The "sticks" analogy for ensembles is a physical metaphor.

6. **Whitespace is structural**: Generous spacing between elements creates visual groupings. The empty space IS part of the layout.

7. **Handwritten feel builds trust**: The slightly imperfect hand-drawn style makes complex topics feel approachable rather than intimidating. This is deliberate --- not "unfinished."

---

## Part 2: Embedding Patterns for Technical Textbooks

### 2.1 Placement Rules

**Concept diagrams (DDODS-style) go BEFORE the text they illustrate:**
```markdown
## Section Title

![Descriptive alt text](../assets/images/ddods/diagram-name.png)

*Source: [Attribution](https://source-url.com) --- one-sentence context connecting diagram to section.*

The detailed explanation text follows here...
```

**Example output plots go AFTER the code that produces them:**
```markdown
```python
# Code example
results = model.evaluate(test_data)
print(results)
`` `

![What the output looks like](../assets/images/examples/ch09-metric-comparison.png)

*Caption describing what the reader should notice in the plot.*
```

### 2.2 Two-Layer Visual Strategy

Every chapter should have TWO types of visuals working together:

| Layer | Purpose | Source | Placement |
|-------|---------|--------|-----------|
| **Concept diagrams** | Explain the "what" and "why" | DDODS-style hand-drawn or custom | Before code, near section intro |
| **Example plots** | Show the "how" and "result" | matplotlib/plotly from synthetic data | After code blocks |

This mirrors how effective teaching works: concept first (diagram), then implementation (code), then verification (output plot).

### 2.3 Attribution Format

For third-party diagrams:
```markdown
![Alt text describing the concept](../assets/images/ddods/filename.png)

*Source: [Daily Dose of Data Science](https://www.dailydoseofds.com/) --- brief connecting statement.*
```

For self-generated plots:
```markdown
![Alt text describing what's shown](../assets/images/examples/chNN-description.png)

*Caption: what the reader should observe or learn from this plot.*
```

### 2.4 Density Guidelines

| Chapter Type | Concept Diagrams | Example Plots | Total Images |
|-------------|-----------------|---------------|-------------|
| Introductory concept (Ch1-3) | 1-2 | 0-1 | 1-3 |
| Core technique (Ch4-15) | 1-2 | 2-4 | 3-5 |
| Advanced topic (Ch16-25) | 1 | 2-3 | 3-4 |
| Applied/tools (Ch26-32) | 0-1 | 3-5 | 3-5 |

---

## Part 3: Generating Example Plots with matplotlib

### 3.1 Style Configuration

```python
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend for CI/server environments
import matplotlib.pyplot as plt
import numpy as np

# Consistent style for all textbook plots
plt.rcParams.update({
    'figure.figsize': (10, 6),
    'figure.dpi': 150,
    'figure.facecolor': 'white',
    'axes.facecolor': 'white',
    'axes.grid': True,
    'axes.grid.which': 'major',
    'grid.alpha': 0.3,
    'grid.color': '#cccccc',
    'font.size': 12,
    'axes.titlesize': 16,
    'axes.titleweight': 'bold',
    'axes.labelsize': 13,
    'legend.fontsize': 11,
    'legend.framealpha': 0.9,
    'savefig.bbox': 'tight',
    'savefig.pad_inches': 0.2,
})

# Color palette matching DDODS aesthetic
COLORS = {
    'primary': '#2ECB71',      # Emerald green (primary data)
    'secondary': '#E74C3C',    # Red (comparison/error)
    'accent': '#9B59B6',       # Purple (highlights)
    'neutral': '#3498DB',      # Blue (secondary data)
    'warning': '#F39C12',      # Orange (warnings/thresholds)
    'light_fill': '#2ECB7133', # Semi-transparent green
    'light_red': '#E74C3C33',  # Semi-transparent red
}
```

### 3.2 Plot Type Templates

**Scatter with Reference Line (Actual vs Predicted)**
```python
def plot_actual_vs_predicted(actuals, predictions, save_path):
    fig, ax = plt.subplots(figsize=(8, 8))
    ax.scatter(actuals, predictions, alpha=0.5, color=COLORS['primary'], s=30)
    lims = [min(actuals.min(), predictions.min()), max(actuals.max(), predictions.max())]
    ax.plot(lims, lims, '--', color=COLORS['secondary'], linewidth=2, label='Perfect prediction')
    ax.set_xlabel('Actual')
    ax.set_ylabel('Predicted')
    ax.set_title('Actual vs. Predicted')
    ax.legend()
    fig.savefig(save_path)
    plt.close(fig)
```

**Dual-Line Comparison (Train vs Test, Bias-Variance)**
```python
def plot_bias_variance(complexity, train_error, test_error, save_path):
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.plot(complexity, train_error, 'o--', color=COLORS['primary'],
            linewidth=2, markersize=8, label='Train RMSE')
    ax.plot(complexity, test_error, 's-', color=COLORS['secondary'],
            linewidth=2, markersize=8, label='Test RMSE')
    # Annotate optimal point
    best_idx = np.argmin(test_error)
    ax.axvline(complexity[best_idx], color='gray', linestyle=':', alpha=0.5)
    ax.annotate('Optimal\ncomplexity', xy=(complexity[best_idx], test_error[best_idx]),
                fontsize=11, ha='center', va='bottom')
    ax.set_xlabel('Model Complexity')
    ax.set_ylabel('RMSE')
    ax.set_title('Bias-Variance Tradeoff')
    ax.legend()
    fig.savefig(save_path)
    plt.close(fig)
```

**Horizontal Bar Chart (Model Comparison / Feature Importance)**
```python
def plot_model_comparison(names, scores, metric_name, save_path):
    fig, ax = plt.subplots(figsize=(10, max(4, len(names) * 0.6)))
    colors = [COLORS['primary'] if s == min(scores) else COLORS['neutral'] for s in scores]
    bars = ax.barh(names, scores, color=colors, edgecolor='white', height=0.6)
    ax.set_xlabel(metric_name)
    ax.set_title(f'Model Comparison: {metric_name}')
    ax.invert_yaxis()
    for bar, score in zip(bars, scores):
        ax.text(bar.get_width() + max(scores) * 0.01, bar.get_y() + bar.get_height()/2,
                f'{score:.4f}', va='center', fontsize=11)
    fig.savefig(save_path)
    plt.close(fig)
```

**Architecture/Flow Diagram (Stacking, Pipeline)**
```python
def plot_pipeline_diagram(stages, save_path):
    """Draw a left-to-right pipeline diagram using matplotlib patches."""
    fig, ax = plt.subplots(figsize=(12, 4))
    ax.set_xlim(0, len(stages) * 2.5)
    ax.set_ylim(0, 2)
    ax.axis('off')

    box_colors = [COLORS['neutral'], COLORS['primary'], COLORS['accent'], COLORS['warning']]
    for i, (label, sublabel) in enumerate(stages):
        x = i * 2.5 + 0.5
        rect = plt.Rectangle((x, 0.5), 1.8, 1.0, facecolor=box_colors[i % len(box_colors)],
                              edgecolor='white', linewidth=2, alpha=0.85, zorder=2)
        ax.add_patch(rect)
        ax.text(x + 0.9, 1.0, label, ha='center', va='center',
                fontsize=13, fontweight='bold', color='white', zorder=3)
        if sublabel:
            ax.text(x + 0.9, 0.7, sublabel, ha='center', va='center',
                    fontsize=10, color='white', alpha=0.9, zorder=3)
        if i < len(stages) - 1:
            ax.annotate('', xy=(x + 2.3, 1.0), xytext=(x + 1.9, 1.0),
                        arrowprops=dict(arrowstyle='->', color='gray', lw=2))

    ax.set_title('Pipeline Architecture', fontsize=16, fontweight='bold', pad=20)
    fig.savefig(save_path)
    plt.close(fig)
```

**Time Series CV Folds**
```python
def plot_ts_cv_folds(n_folds, n_total, save_path):
    fig, ax = plt.subplots(figsize=(10, n_folds * 0.8 + 1))
    for i in range(n_folds):
        train_end = int(n_total * (0.5 + i * 0.1))
        test_end = train_end + int(n_total * 0.1)
        ax.barh(i, train_end, color=COLORS['primary'], height=0.6, label='Training' if i == 0 else '')
        ax.barh(i, test_end - train_end, left=train_end, color=COLORS['accent'],
                height=0.6, label='Assessment' if i == 0 else '')
        ax.barh(i, n_total - test_end, left=test_end, color='#eeeeee',
                height=0.6, label='Unused' if i == 0 else '')
    ax.set_yticks(range(n_folds))
    ax.set_yticklabels([f'Fold {i+1}' for i in range(n_folds)])
    ax.set_xlabel('Time')
    ax.set_title('Time Series Cross-Validation (Expanding Window)')
    ax.legend(loc='lower right')
    fig.savefig(save_path)
    plt.close(fig)
```

### 3.3 Synthetic Data Generation

Always generate deterministic synthetic data for reproducible plots:

```python
rng = np.random.default_rng(42)  # Reproducible, local RNG

# Regression data
n = 200
x = rng.uniform(0, 10, n)
y = 3 * x + 2 + rng.normal(0, 2, n)

# Classification data
from sklearn.datasets import make_classification
X, y = make_classification(n_samples=300, n_features=5, n_informative=3, random_state=42)

# Time series data
dates = pd.date_range('2020-01-01', periods=365, freq='D')
trend = np.linspace(100, 150, 365)
seasonal = 10 * np.sin(2 * np.pi * np.arange(365) / 365)
noise = rng.normal(0, 3, 365)
ts = pd.DataFrame({'date': dates, 'value': trend + seasonal + noise})
```

### 3.4 Image Specifications

| Property | Specification |
|----------|--------------|
| Format | PNG (universal compatibility) |
| DPI | 150 (crisp on screens, reasonable file size) |
| Max width | 800px rendered (figsize 10 at 150 DPI = 1500px, but renders at ~800px in docs) |
| Background | White (`#FFFFFF`) |
| File naming | `chNN-description-in-kebab-case.png` |
| File size target | 30-150KB per image |
| Backend | `matplotlib.use('Agg')` for headless generation |

---

## Part 4: Topic-to-Diagram Mapping Reference

### 4.1 ML/DS Concept Coverage

This maps common course topics to the type of diagram that explains them best:

| Topic | Diagram Type | Key Visual Elements |
|-------|-------------|-------------------|
| Linear Regression | Code + scatter + fit line | Gradient bg, terminal code block, scatter with trend |
| Regularization (L1/L2) | Comparison diagram | Coefficient shrinkage paths, constraint regions |
| Overfitting | Dual-line plot | Train loss (decreasing) vs validation loss (U-shape) |
| Bias-Variance Tradeoff | Dual-line plot | Complexity axis, optimal point annotation |
| Cross-Validation | Fold diagram | Horizontal bars: train (green), test (purple), unused (gray) |
| Bagging | Algorithm flow | Data -> bootstrap samples -> independent models -> aggregate |
| Boosting | Algorithm flow | Sequential models, weighted data, correct/incorrect split |
| Stacking | Architecture diagram | Base models -> OOF predictions -> meta-learner -> final |
| PCA | Transformation diagram | Matrix X -> PCA arrow -> X_transformed |
| Curse of Dimensionality | Problem illustration | 2D (dense points) -> 3D -> high-D (sparse, arrows outward) |
| SHAP Values | Waterfall chart | Base value + per-feature contributions = prediction |
| Conformal Prediction | Problem + solution | Grid of predictions + "I know 5% are wrong but not which" |
| Bayesian Optimization | Process diagram | Parameter space -> surrogate model -> select best -> iterate |
| Decision Boundaries | Comparison | High-variance (jagged) vs low-variance (smooth) regions |
| Ensemble Strength | Physical metaphor | Single stick (fragile) vs bundle of sticks (strong) |
| Model Interpretability | Spectrum diagram | Simple (interpretable) <-> Complex (accurate) |
| R-squared Limitations | Counter-example | High R-squared but clearly wrong model fit |
| Hyperparameter Tuning | Heatmap / surface | 2D parameter grid colored by metric value |
| Feature Importance | Horizontal bar chart | Features ranked by importance score |
| Prediction Intervals | Time series + bands | Point predictions with widening confidence bands |

### 4.2 DDODS Article-to-Topic Index

These DDODS article topics have free-preview diagrams usable for educational content:

| DDODS Article Topic | Usable Diagrams | Best For Course Chapter |
|--------------------|-----------------|----------------------|
| Bagging explained | Algorithm flow (whiteboard style) | Ensemble methods, Random Forest |
| Boosting explained | Sequential flow (whiteboard style) | Gradient Boosting, XGBoost |
| Decision Tree vs Random Forest | Variance comparison (gradient bg) | Tree models, overfitting |
| Overfitting with polynomials | Polynomial degree progression | Model complexity, regularization |
| Linear regression assumptions | Code + fit + residuals (gradient bg) | Linear models, diagnostics |
| R-squared is flawed | Counter-example (gradient bg) | Model evaluation metrics |
| PCA overview | Matrix transformation (whiteboard) | Dimensionality reduction |
| Curse of dimensionality | 2D/3D/high-D point density | Feature engineering, PCA motivation |
| Bayesian optimization | Hyperparameter space search | Hyperparameter tuning |
| Conformal prediction | Prediction uncertainty | Prediction intervals, trust |
| Model interpretability | MRI -> model -> prediction | SHAP, model explanation |
| Regularization (L1/L2) | Eggshells analogy (Bayesian) | Ridge, Lasso, Elastic Net |
| XGBoost intuition | Sticks analogy (ensemble) | Gradient boosting |
| MLE and linear fit | Code + probability vis | Model fitting theory |
| GLM assumptions | Assumption validation plots | Generalized linear models |
| Homoscedasticity | Before/after residual patterns | Residual diagnostics |

---

## Part 5: Implementation Workflow

### 5.1 For a New Course/Textbook

1. **Audit chapters**: Read each chapter and identify:
   - Concepts that benefit from a visual overview (-> concept diagram)
   - Code blocks that produce visual output (-> example plot)
   - Complex processes with multiple steps (-> flow diagram)

2. **Map to diagram types**: Use the Topic-to-Diagram Mapping (Section 4.1) to decide what kind of diagram each concept needs.

3. **Source concept diagrams**: Either:
   - Use DDODS free-preview diagrams with attribution (easiest)
   - Create custom diagrams following the DDODS design principles (Section 1)
   - Use a tool like Excalidraw for the hand-drawn whiteboard style
   - Use Canva/Figma for the gradient-background presentation style

4. **Generate example plots**: Use the matplotlib templates (Section 3.2) with synthetic data to create output visualizations for code examples.

5. **Embed following placement rules**: Concept diagrams before text, example plots after code (Section 2.1).

### 5.2 Agent Team Prompt Template

For automating the plot generation across chapters with an agent team:

```
TASK: Generate inline example plots for [COURSE NAME] chapters [N-M].

CONTEXT:
- Chapters are at: [PATH TO CHAPTERS]
- Save images to: [PATH TO IMAGES]
- Virtualenv: [ACTIVATION COMMAND]

WORKFLOW per chapter:
1. Read the chapter markdown to find code blocks producing visual/tabular output
2. Write a Python script that generates representative plots with SYNTHETIC data
3. Run the script to produce PNG files
4. Edit the chapter markdown to embed images after the relevant code blocks

STYLE:
- Use matplotlib with Agg backend (no display needed)
- White background, 150 DPI, max 800px rendered width
- Color palette: emerald green (#2ECB71), red (#E74C3C), purple (#9B59B6), blue (#3498DB)
- File naming: chNN-description.png
- Alt text: descriptive of what's shown
- Caption: what the reader should notice

PRIORITIES:
- Quality over quantity: 2-4 well-placed images per chapter
- Focus on: scatter plots, comparison charts, diagnostic panels, architecture diagrams
- Skip: trivial outputs (single numbers, short DataFrames unless they illustrate structure)
```

### 5.3 Quality Checklist

Before publishing, verify each image:

- [ ] Alt text is descriptive (not just "Figure 1")
- [ ] Caption explains what to look for
- [ ] Concept diagrams appear BEFORE the text they explain
- [ ] Example plots appear AFTER the code that would produce them
- [ ] Colors are consistent across all plots in the same chapter
- [ ] File size is under 200KB (optimize PNGs if needed)
- [ ] No broken image links (build the docs site and check)
- [ ] Maximum 1-2 DDODS diagrams per chapter (avoid over-reliance on one source)
- [ ] Attribution is present for all third-party images

---

## Part 6: Tools and Resources

### Diagram Creation Tools

| Tool | Best For | Cost |
|------|----------|------|
| [Excalidraw](https://excalidraw.com) | Hand-drawn whiteboard diagrams (DDODS Style A) | Free |
| [tldraw](https://tldraw.com) | Quick sketches and flow diagrams | Free |
| Canva | Gradient-background slides (DDODS Style B) | Free tier |
| Figma | Precise vector diagrams | Free tier |
| matplotlib | Data plots, charts, statistical visualizations | Free |
| [Mermaid](https://mermaid.js.org) | Flowcharts, sequence diagrams (in markdown) | Free |
| draw.io / diagrams.net | Architecture and pipeline diagrams | Free |

### Image Optimization

```bash
# Optimize PNGs without quality loss
pip install Pillow
python -c "
from PIL import Image
import glob
for f in glob.glob('docs/assets/images/examples/*.png'):
    img = Image.open(f)
    img.save(f, optimize=True)
"

# Or use optipng (brew install optipng / apt install optipng)
optipng -o2 docs/assets/images/examples/*.png
```

### DDODS Access Notes

- DDODS uses Ghost CMS; most articles are behind a paywall
- However, CDN-hosted images from Ghost are publicly accessible via their direct URL
- Free-preview images are visible on article pages before the paywall cutoff
- Always attribute: `*Source: [Daily Dose of Data Science](https://www.dailydoseofds.com/)*`
- The "Classical ML and Deep Learning" course section has the most relevant diagrams for ML textbooks

---

## Appendix: Image Inventory from py-tidymodels Textbook

### DDODS Diagrams (23 images)

| Filename | Topic | Chapters Used |
|----------|-------|--------------|
| ddods-bagging-overview.jpg | Bagging algorithm flow | Ch20 |
| ddods-boosting-overview.jpg | Boosting algorithm flow | Ch20 |
| ddods-bayesian-opt-concept.png | Hyperparameter space search | Ch14 |
| ddods-bayesian-opt-exploration.png | Exploration vs exploitation | Ch14 |
| ddods-conformal-concept.png | Prediction uncertainty | Ch19 |
| ddods-conformal-intervals.png | Conformal intervals | (available) |
| ddods-curse-dimensionality.png | High-D point sparsity | Ch16 |
| ddods-curse-dimensionality-2.png | Alternative curse-of-dim visual | (available) |
| ddods-dtree-vs-rf-variance.png | Variance comparison | (available) |
| ddods-glm-lr-assumptions.png | GLM assumption validation | (available) |
| ddods-heteroscedasticity.jpeg | Bad residual pattern | (available) |
| ddods-homoscedasticity.jpeg | Good residual pattern | (available) |
| ddods-interpretability-overview.png | Model -> prediction pipeline | Ch18 |
| ddods-linear-regression-assumptions.png | Code + scatter + fit | Ch6 |
| ddods-mle-linear-fit.jpg | MLE probability visualization | (available) |
| ddods-overfitting-polynomial.png | Polynomial degree progression | Ch12 |
| ddods-pca-overview.png | Matrix transformation | Ch16 |
| ddods-pca-variance.png | Variance preservation | (available) |
| ddods-r-squared-flawed.jpg | R-squared counter-example | Ch9 |
| ddods-regression-types.jpg | Regression type comparison | (available) |
| ddods-regularization-l1-l2.png | Bayesian regularization analogy | (available) |
| ddods-regularization-overview.png | Regularization overview | (available) |
| ddods-xgboost-concept.png | Ensemble strength (sticks) | (available) |

### Generated Example Plots (85 images)

Chapters 4-32, 2-9 images per chapter. Full listing available in the textbook-site docs/assets/images/examples/ directory.
