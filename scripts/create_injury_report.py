#!/usr/bin/env python3
"""
Create a comprehensive injury analysis report from the model predictions.
This generates insights about RB injury patterns and model performance.
"""
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.metrics import classification_report, confusion_matrix, roc_auc_score

def create_injury_report():
    """Create a comprehensive injury analysis report."""
    
    print("Creating RB Injury Analysis Report")
    print("=" * 50)
    
    # Load the predictions
    try:
        predictions = pd.read_csv('data/rb_injury_predictions.csv')
        print(f"✓ Loaded predictions: {len(predictions)} records")
    except FileNotFoundError:
        print("❌ Error: rb_injury_predictions.csv not found!")
        print("Please run scripts/apply_injury_model.py first.")
        return
    
    # Load the original data for comparison
    try:
        original_data = pd.read_csv('data/rb_synthetic_data.csv')
        print(f"✓ Loaded original data: {len(original_data)} records")
    except FileNotFoundError:
        print("❌ Error: rb_synthetic_data.csv not found!")
        return
    
    # Model Performance Analysis
    print(f"\nModel Performance Analysis:")
    print("-" * 50)
    
    y_true = predictions['actual_injury']
    y_pred = predictions['predicted_injury']
    y_proba = predictions['predicted_risk']
    
    accuracy = (y_true == y_pred).mean()
    roc_auc = roc_auc_score(y_true, y_proba)
    
    print(f"Accuracy: {accuracy:.3f}")
    print(f"ROC AUC: {roc_auc:.3f}")
    
    # Confusion Matrix
    cm = confusion_matrix(y_true, y_pred)
    print(f"\nConfusion Matrix:")
    print(f"                Predicted")
    print(f"                No Injury  Injury")
    print(f"Actual No Injury    {cm[0,0]:>8}    {cm[0,1]:>6}")
    print(f"      Injury        {cm[1,0]:>8}    {cm[1,1]:>6}")
    
    # Calculate additional metrics
    tn, fp, fn, tp = cm.ravel()
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0
    f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0
    
    print(f"\nDetailed Metrics:")
    print(f"Precision: {precision:.3f}")
    print(f"Recall: {recall:.3f}")
    print(f"F1-Score: {f1:.3f}")
    
    # Injury Patterns by Season
    print(f"\nInjury Patterns by Season:")
    print("-" * 50)
    
    season_analysis = predictions.groupby('season').agg({
        'actual_injury': ['count', 'mean'],
        'predicted_risk': 'mean',
        'age': 'mean',
        'touches_per_game': 'mean'
    }).round(3)
    
    season_analysis.columns = ['Players', 'Actual_Injury_Rate', 'Avg_Predicted_Risk', 'Avg_Age', 'Avg_Touches']
    print(season_analysis)
    
    # Age-based Analysis
    print(f"\nAge-based Injury Analysis:")
    print("-" * 50)
    
    # Create age groups
    predictions['age_group'] = pd.cut(predictions['age'], 
                                    bins=[20, 25, 30, 35], 
                                    labels=['Young (21-25)', 'Prime (26-30)', 'Veteran (31-35)'])
    
    age_analysis = predictions.groupby('age_group').agg({
        'actual_injury': ['count', 'mean'],
        'predicted_risk': 'mean',
        'touches_per_game': 'mean'
    }).round(3)
    
    age_analysis.columns = ['Players', 'Injury_Rate', 'Avg_Predicted_Risk', 'Avg_Touches']
    print(age_analysis)
    
    # Touch-based Analysis
    print(f"\nTouch-based Injury Analysis:")
    print("-" * 50)
    
    # Create touch groups
    predictions['touch_group'] = pd.cut(predictions['touches_per_game'], 
                                      bins=[0, 10, 15, 20, 30], 
                                      labels=['Low (0-10)', 'Medium (11-15)', 'High (16-20)', 'Very High (21+)'])
    
    touch_analysis = predictions.groupby('touch_group').agg({
        'actual_injury': ['count', 'mean'],
        'predicted_risk': 'mean',
        'age': 'mean'
    }).round(3)
    
    touch_analysis.columns = ['Players', 'Injury_Rate', 'Avg_Predicted_Risk', 'Avg_Age']
    print(touch_analysis)
    
    # Risk Score Analysis
    print(f"\nRisk Score Analysis:")
    print("-" * 50)
    
    # Create risk groups
    predictions['risk_group'] = pd.cut(predictions['predicted_risk'], 
                                     bins=[0, 0.3, 0.5, 0.7, 1.0], 
                                     labels=['Low (0-0.3)', 'Medium (0.3-0.5)', 'High (0.5-0.7)', 'Very High (0.7+)'])
    
    risk_analysis = predictions.groupby('risk_group').agg({
        'actual_injury': ['count', 'mean'],
        'age': 'mean',
        'touches_per_game': 'mean'
    }).round(3)
    
    risk_analysis.columns = ['Players', 'Actual_Injury_Rate', 'Avg_Age', 'Avg_Touches']
    print(risk_analysis)
    
    # Top 10 Highest Risk Players
    print(f"\nTop 10 Highest Risk Players:")
    print("-" * 50)
    
    high_risk = predictions.nlargest(10, 'predicted_risk')[['player', 'age', 'touches_per_game', 'injury_history', 'predicted_risk', 'actual_injury']]
    print(high_risk.to_string(index=False))
    
    # Top 10 Lowest Risk Players
    print(f"\nTop 10 Lowest Risk Players:")
    print("-" * 50)
    
    low_risk = predictions.nsmallest(10, 'predicted_risk')[['player', 'age', 'touches_per_game', 'injury_history', 'predicted_risk', 'actual_injury']]
    print(low_risk.to_string(index=False))
    
    # Model Calibration Analysis
    print(f"\nModel Calibration Analysis:")
    print("-" * 50)
    
    # Group by predicted risk ranges and compare with actual injury rates
    risk_ranges = [(0, 0.2), (0.2, 0.4), (0.4, 0.6), (0.6, 0.8), (0.8, 1.0)]
    
    for low, high in risk_ranges:
        mask = (predictions['predicted_risk'] >= low) & (predictions['predicted_risk'] < high)
        if mask.sum() > 0:
            subset = predictions[mask]
            actual_rate = subset['actual_injury'].mean()
            predicted_rate = subset['predicted_risk'].mean()
            count = len(subset)
            print(f"Risk {low:.1f}-{high:.1f}: {count:>2} players, Predicted: {predicted_rate:.3f}, Actual: {actual_rate:.3f}")
    
    # Save detailed report
    report_file = 'data/rb_injury_analysis_report.txt'
    
    with open(report_file, 'w') as f:
        f.write("RB Injury Analysis Report\n")
        f.write("=" * 50 + "\n\n")
        
        f.write(f"Model Performance:\n")
        f.write(f"Accuracy: {accuracy:.3f}\n")
        f.write(f"ROC AUC: {roc_auc:.3f}\n")
        f.write(f"Precision: {precision:.3f}\n")
        f.write(f"Recall: {recall:.3f}\n")
        f.write(f"F1-Score: {f1:.3f}\n\n")
        
        f.write("Season Analysis:\n")
        f.write(season_analysis.to_string() + "\n\n")
        
        f.write("Age Analysis:\n")
        f.write(age_analysis.to_string() + "\n\n")
        
        f.write("Touch Analysis:\n")
        f.write(touch_analysis.to_string() + "\n\n")
        
        f.write("Risk Analysis:\n")
        f.write(risk_analysis.to_string() + "\n\n")
        
        f.write("High Risk Players:\n")
        f.write(high_risk.to_string() + "\n\n")
        
        f.write("Low Risk Players:\n")
        f.write(low_risk.to_string() + "\n")
    
    print(f"\n✓ Detailed report saved to: {report_file}")
    
    # Create visualizations
    print(f"\nGenerating visualizations...")
    
    # Set up the plotting style
    plt.style.use('default')
    sns.set_palette("Set2")
    
    # Create a comprehensive dashboard
    fig, axes = plt.subplots(2, 3, figsize=(18, 12))
    fig.suptitle('RB Injury Risk Analysis Dashboard', fontsize=16, fontweight='bold')
    
    # 1. Injury Rate by Season
    ax1 = axes[0, 0]
    season_injuries = predictions.groupby('season')['actual_injury'].mean()
    ax1.bar(season_injuries.index, season_injuries.values, color=['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4'])
    ax1.set_title('Injury Rate by Season')
    ax1.set_xlabel('Season')
    ax1.set_ylabel('Injury Rate')
    ax1.set_ylim(0, 0.6)
    
    # 2. Age vs Injury Rate
    ax2 = axes[0, 1]
    age_injuries = predictions.groupby('age_group')['actual_injury'].mean()
    ax2.bar(range(len(age_injuries)), age_injuries.values, color=['#FF6B6B', '#4ECDC4', '#45B7D1'])
    ax2.set_title('Injury Rate by Age Group')
    ax2.set_xlabel('Age Group')
    ax2.set_ylabel('Injury Rate')
    ax2.set_xticks(range(len(age_injuries)))
    ax2.set_xticklabels(age_injuries.index, rotation=45)
    
    # 3. Touches vs Injury Rate
    ax3 = axes[0, 2]
    touch_injuries = predictions.groupby('touch_group')['actual_injury'].mean()
    ax3.bar(range(len(touch_injuries)), touch_injuries.values, color=['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4'])
    ax3.set_title('Injury Rate by Touch Volume')
    ax3.set_xlabel('Touch Volume')
    ax3.set_ylabel('Injury Rate')
    ax3.set_xticks(range(len(touch_injuries)))
    ax3.set_xticklabels(touch_injuries.index, rotation=45)
    
    # 4. Predicted vs Actual Risk
    ax4 = axes[1, 0]
    ax4.scatter(predictions['predicted_risk'], predictions['actual_injury'], alpha=0.6)
    ax4.plot([0, 1], [0, 1], 'r--', alpha=0.8)
    ax4.set_title('Predicted vs Actual Injury Risk')
    ax4.set_xlabel('Predicted Risk')
    ax4.set_ylabel('Actual Injury (0/1)')
    
    # 5. Age vs Predicted Risk
    ax5 = axes[1, 1]
    ax5.scatter(predictions['age'], predictions['predicted_risk'], alpha=0.6)
    ax5.set_title('Age vs Predicted Injury Risk')
    ax5.set_xlabel('Age')
    ax5.set_ylabel('Predicted Risk')
    
    # 6. Touches vs Predicted Risk
    ax6 = axes[1, 2]
    ax6.scatter(predictions['touches_per_game'], predictions['predicted_risk'], alpha=0.6)
    ax6.set_title('Touches per Game vs Predicted Risk')
    ax6.set_xlabel('Touches per Game')
    ax6.set_ylabel('Predicted Risk')
    
    plt.tight_layout()
    plt.savefig('data/rb_injury_dashboard.png', dpi=300, bbox_inches='tight')
    print(f"✓ Dashboard saved to: data/rb_injury_dashboard.png")
    
    print(f"\nReport generation complete!")

if __name__ == "__main__":
    create_injury_report()

