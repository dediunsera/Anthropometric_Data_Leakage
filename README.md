# Anthropometric Data Leakage

This repository investigates the critical issue of **Data Leakage** in machine learning models that predict nutritional status (such as stunting, wasting, and underweight) using anthropometric measurements.

## 📌 Research Context
When developing predictive models for public health, researchers often inadvertently include raw anthropometric data (like height, weight, and age) as predictive features. However, because target variables (like Height-for-Age Z-scores or HAZ) are directly derived from these precise measurements, including them causes severe data leakage. This results in models that appear highly accurate during testing but are clinically useless and highly sensitive to measurement noise in the real world.

## 🎯 Objectives
- **Demonstrate Data Leakage:** Show how including leaky features artificially inflates model performance metrics (Accuracy, AUC).
- **Evaluate Measurement Uncertainty:** Analyze how small, common human errors in measuring child height/weight propagate into classification errors (label switching).
- **Develop Robust Frameworks:** Propose methodologies for building stunting prediction models that rely on robust socio-demographic, environmental, and health history features rather than leaky physical measurements.

## 📁 Repository Structure
*(Structure will be updated as scripts and data are added)*
- `scripts/`: Python codebase for modeling and simulations.
- `results/`: Outputs from experimental evaluations.
- `data/`: *(Private)* Confidential datasets used for the analysis.
