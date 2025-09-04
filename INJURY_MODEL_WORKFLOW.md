# RB Injury Risk Model - Complete Workflow

## Overview

This document describes the complete workflow for using the RB injury risk model system. The system uses a foundational linear-spline model with logistic regression to predict injury risk for NFL running backs based on key factors like age, workload, and injury history.

## System Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Data Sources  │───▶│  Injury Model    │───▶│  Predictions    │
│                 │    │                  │    │                 │
│ • Synthetic RB  │    │ • Linear Spline  │    │ • Risk Scores   │
│ • Real PFR Data │    │ • Logistic Reg   │    │ • Analysis      │
│ • Historical    │    │ • Feature Eng    │    │ • Reports       │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

## Quick Start

### 1. Generate Synthetic Data (for testing/demo)
```bash
python3 scripts/generate_rb_data.py
```
This creates realistic RB data for 2021-2024 seasons in `data/rb_synthetic_data.csv`

### 2. Train and Apply the Injury Model
```bash
python3 scripts/apply_injury_model.py
```
This trains the model on the data and generates predictions

### 3. Generate Analysis Report
```bash
python3 scripts/create_injury_report.py
```
This creates a comprehensive analysis report and visualizations

### 4. Use the Model for Predictions
```bash
python3 scripts/injury_model_usage_example.py
```
This demonstrates how to use the model for real-world predictions

## Data Requirements

The injury model expects the following features:

| Feature | Description | Range | Example |
|---------|-------------|-------|---------|
| `age` | Player age in years | 21-35 | 27 |
| `games_played` | Expected games in season | 1-18 | 15 |
| `touches_per_game` | Expected touches per game | 1-30 | 18 |
| `yards_per_touch` | Expected yards per touch | 2-8 | 4.5 |
| `injury_history` | Previous injury (0/1) | 0 or 1 | 1 |

## Model Features

### Core Features
- **Age Splines**: Captures U-shaped relationship between age and injury risk
- **Touch Splines**: Handles non-linear workload effects
- **Injury History**: Binary indicator for previous injuries
- **Position**: Currently focused on RBs

### Spline Implementation
The model automatically creates spline features for:
- Age (3 knots at 25th, 50th, 75th percentiles)
- Touches per game (3 knots for workload effects)

## Model Performance

### Current Performance (Synthetic Data)
- **Accuracy**: ~65%
- **ROC AUC**: ~0.57
- **Precision**: ~67%
- **Recall**: ~21%

### Strengths
- Good at identifying low-risk players
- Handles non-linear relationships
- Provides interpretable risk scores
- Actionable recommendations

### Areas for Improvement
- Better injury prediction for high-risk players
- More training data needed
- Feature engineering could be enhanced

## Usage Examples

### Example 1: High-Risk Veteran
```python
veteran_rb = {
    'name': 'Derrick Henry',
    'age': 30,
    'games_played': 16,
    'touches_per_game': 22,
    'yards_per_touch': 4.5,
    'injury_history': 1,
    'position': 'RB'
}

# Predicted Risk: 57.7% (HIGH)
# Recommendation: Implement injury prevention protocols
```

### Example 2: Low-Risk Young Backup
```python
young_backup = {
    'name': 'Bijan Robinson',
    'age': 22,
    'games_played': 14,
    'touches_per_game': 12,
    'yards_per_touch': 4.8,
    'injury_history': 0,
    'position': 'RB'
}

# Predicted Risk: 45.9% (MEDIUM)
# Recommendation: Consider load management
```

## Risk Levels and Recommendations

| Risk Level | Range | Recommendation |
|------------|-------|----------------|
| **LOW** | 0-30% | Monitor workload, low injury concern |
| **MEDIUM** | 30-50% | Moderate risk, consider load management |
| **HIGH** | 50-70% | High risk, implement prevention protocols |
| **VERY HIGH** | 70%+ | Very high risk, consider reduced role |

## Integration with Real Data

### When Real PFR Data is Available

1. **Scrape Weekly Statistics**
   ```bash
   python3 scripts/scrape_pfr_weeklies_curl.py --season 2024 --players_csv data/rbs_2024_fixed.csv
   ```

2. **Join with Schedule Data**
   ```bash
   python3 scripts/join_weekly_with_schedule.py
   ```

3. **Build Season Features**
   ```bash
   python3 scripts/build_rb_seasons.py
   ```

4. **Apply Injury Model**
   ```bash
   python3 scripts/apply_injury_model.py
   ```

### Data Pipeline
```
PFR Player Lists → Weekly Stats → Schedule Join → Season Features → Injury Model
```

## Output Files

### Generated Files
- `data/rb_synthetic_data.csv` - Synthetic RB data for testing
- `data/rb_injury_predictions.csv` - Model predictions
- `data/rb_injury_analysis_report.txt` - Detailed analysis report
- `data/rb_injury_dashboard.png` - Visualization dashboard

### Key Metrics
- Injury risk scores (0-100%)
- Risk level classifications
- Specific recommendations
- Performance metrics

## Customization

### Adding New Features
1. Modify `prepare_features()` in `RBInjuryModel`
2. Add feature engineering logic
3. Update spline creation if needed
4. Retrain model

### Model Tuning
1. Adjust spline knot positions
2. Modify regularization parameters
3. Try different algorithms (Random Forest, XGBoost)
4. Ensemble multiple models

## Best Practices

### For Production Use
1. **Validate with Real Data**: Test predictions against actual outcomes
2. **Regular Updates**: Retrain model with new season data
3. **Medical Input**: Combine with medical staff assessments
4. **Monitoring**: Track prediction accuracy over time

### For Development
1. **Start with Synthetic Data**: Test workflow before real data
2. **Iterate on Features**: Experiment with different predictors
3. **Cross-Validation**: Use proper validation techniques
4. **Documentation**: Keep track of model changes

## Troubleshooting

### Common Issues

**Import Errors**
```bash
# Fix Python path issues
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
```

**Data Not Found**
```bash
# Ensure data files exist
ls -la data/
# Generate synthetic data if needed
python3 scripts/generate_rb_data.py
```

**Model Performance Issues**
- Check data quality and distributions
- Verify feature engineering
- Consider more training data
- Try different model parameters

## Future Enhancements

### Planned Improvements
1. **More Features**: Add conditioning, team factors, playing surface
2. **Better Models**: Implement ensemble methods, deep learning
3. **Real-time Updates**: Live injury risk monitoring
4. **API Integration**: REST API for easy access

### Research Opportunities
1. **Injury Types**: Predict specific injury types
2. **Recovery Time**: Estimate return-to-play timelines
3. **Prevention Strategies**: Recommend specific interventions
4. **Team Impact**: Analyze injury effects on team performance

## Support and Resources

### Documentation
- `injury_model.py` - Core model implementation
- `scripts/` - Utility scripts and examples
- `data/` - Sample data and outputs

### Dependencies
- pandas, numpy, scikit-learn
- matplotlib, seaborn
- requests, beautifulsoup4 (for scraping)

### Getting Help
1. Check script outputs for error messages
2. Verify data file existence and format
3. Review model performance metrics
4. Test with synthetic data first

---

**Note**: This system is designed for research and demonstration purposes. For production use in professional sports, additional validation, medical expertise, and regulatory compliance may be required.

