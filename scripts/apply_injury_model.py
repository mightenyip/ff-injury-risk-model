#!/usr/bin/env python3
"""
Apply the injury model to RB data and generate predictions.
This demonstrates how to use the injury model with real-world data.
"""
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report, confusion_matrix, roc_auc_score, roc_curve
from sklearn.pipeline import Pipeline
import warnings
warnings.filterwarnings('ignore')

class RBInjuryModel:
    """
    RB-specific injury risk prediction model using the foundational injury model approach.
    """
    
    def __init__(self):
        self.model = None
        self.scaler = StandardScaler()
        self.feature_names = []
        
    def create_spline_features(self, X, feature_name, n_knots=3):
        """Create spline features for non-linear relationships."""
        feature_values = X[feature_name].values
        knots = np.percentile(feature_values, np.linspace(0, 100, n_knots + 2)[1:-1])
        
        spline_features = []
        for i in range(len(knots) - 1):
            # Create basis function for each spline segment
            basis = np.maximum(0, feature_values - knots[i]) - np.maximum(0, feature_values - knots[i+1])
            spline_features.append(basis)
        
        return np.column_stack(spline_features)
    
    def prepare_features(self, data):
        """Prepare features including spline terms for non-linear relationships."""
        # Select features for modeling
        feature_cols = ['age', 'games_played', 'touches_per_game', 'yards_per_touch', 'injury_history']
        X = data[feature_cols].copy()
        
        # Create spline features for age and touches_per_game
        age_splines = self.create_spline_features(X, 'age', n_knots=3)
        touches_splines = self.create_spline_features(X, 'touches_per_game', n_knots=3)
        
        # Add spline features to dataframe
        for i in range(age_splines.shape[1]):
            X[f'age_spline_{i}'] = age_splines[:, i]
        
        for i in range(touches_splines.shape[1]):
            X[f'touches_spline_{i}'] = touches_splines[:, i]
        
        self.feature_names = X.columns.tolist()
        return X
    
    def train(self, X, y):
        """Train the injury risk model."""
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y
        )
        
        # Create pipeline with scaling and logistic regression
        self.model = Pipeline([
            ('scaler', StandardScaler()),
            ('classifier', LogisticRegression(random_state=42, max_iter=1000))
        ])
        
        # Train model
        self.model.fit(X_train, y_train)
        
        # Evaluate model
        y_pred = self.model.predict(X_test)
        y_pred_proba = self.model.predict_proba(X_test)[:, 1]
        
        # Print results
        print("Model Performance:")
        print("-" * 50)
        print(f"Accuracy: {self.model.score(X_test, y_test):.3f}")
        print(f"ROC AUC: {roc_auc_score(y_test, y_pred_proba):.3f}")
        print("\nClassification Report:")
        print(classification_report(y_test, y_pred))
        
        return X_train, X_test, y_train, y_test, y_pred, y_pred_proba
    
    def predict_injury_risk(self, player_data):
        """Predict injury risk for given player data."""
        if self.model is None:
            print("Model not trained yet!")
            return None
        
        # Prepare features
        X = self.prepare_features(player_data)
        
        # Make prediction
        risk_probability = self.model.predict_proba(X)[:, 1]
        
        return risk_probability
    
    def plot_feature_importance(self, X):
        """Plot feature importance based on logistic regression coefficients."""
        if self.model is None:
            print("Model not trained yet!")
            return
        
        # Get coefficients
        coefficients = self.model.named_steps['classifier'].coef_[0]
        
        # Create feature importance dataframe
        importance_df = pd.DataFrame({
            'feature': self.feature_names,
            'coefficient': np.abs(coefficients)
        }).sort_values('coefficient', ascending=True)
        
        # Plot
        plt.figure(figsize=(10, 8))
        plt.barh(range(len(importance_df)), importance_df['coefficient'])
        plt.yticks(range(len(importance_df)), importance_df['feature'])
        plt.xlabel('Absolute Coefficient Value')
        plt.title('Feature Importance (Absolute Logistic Regression Coefficients)')
        plt.tight_layout()
        plt.show()
    
    def plot_roc_curve(self, y_test, y_pred_proba):
        """Plot ROC curve for model evaluation."""
        fpr, tpr, _ = roc_curve(y_test, y_pred_proba)
        auc = roc_auc_score(y_test, y_pred_proba)
        
        plt.figure(figsize=(8, 6))
        plt.plot(fpr, tpr, color='darkorange', lw=2, label=f'ROC curve (AUC = {auc:.3f})')
        plt.plot([0, 1], [0, 1], color='navy', lw=2, linestyle='--')
        plt.xlim([0.0, 1.0])
        plt.ylim([0.0, 1.05])
        plt.xlabel('False Positive Rate')
        plt.ylabel('True Positive Rate')
        plt.title('Receiver Operating Characteristic (ROC) Curve')
        plt.legend(loc="lower right")
        plt.grid(True)
        plt.show()

def analyze_rb_injuries_by_season(data):
    """Analyze injury patterns by season."""
    print("\nInjury Analysis by Season:")
    print("=" * 50)
    
    for season in sorted(data['season'].unique()):
        season_data = data[data['season'] == season]
        injury_rate = season_data['injury'].mean()
        avg_age = season_data['age'].mean()
        avg_touches = season_data['touches_per_game'].mean()
        
        print(f"\n{season} Season:")
        print(f"  Players: {len(season_data)}")
        print(f"  Injury Rate: {injury_rate:.1%}")
        print(f"  Average Age: {avg_age:.1f}")
        print(f"  Average Touches/Game: {avg_touches:.1f}")
        
        # Age vs Injury analysis
        young_rbs = season_data[season_data['age'] <= 25]
        veteran_rbs = season_data[season_data['age'] > 25]
        
        if len(young_rbs) > 0:
            young_injury_rate = young_rbs['injury'].mean()
            print(f"  Young RBs (≤25): {len(young_rbs)} players, {young_injury_rate:.1%} injury rate")
        
        if len(veteran_rbs) > 0:
            veteran_injury_rate = veteran_rbs['injury'].mean()
            print(f"  Veteran RBs (>25): {len(veteran_rbs)} players, {veteran_injury_rate:.1%} injury rate")

def main():
    """Main function to run RB injury analysis."""
    print("RB Injury Risk Analysis")
    print("=" * 50)
    
    # Load the synthetic RB data
    try:
        data = pd.read_csv('data/rb_synthetic_data.csv')
        print(f"✓ Loaded RB data: {len(data)} records")
    except FileNotFoundError:
        print("❌ Error: rb_synthetic_data.csv not found!")
        print("Please run scripts/generate_rb_data.py first.")
        return
    
    # Analyze the data
    print(f"\nDataset Overview:")
    print(f"  Seasons: {sorted(data['season'].unique())}")
    print(f"  Total Players: {len(data)}")
    print(f"  Overall Injury Rate: {data['injury'].mean():.1%}")
    
    # Analyze by season
    analyze_rb_injuries_by_season(data)
    
    # Initialize and train the injury model
    print(f"\nTraining Injury Model:")
    print("-" * 50)
    
    model = RBInjuryModel()
    
    # Prepare features
    X = model.prepare_features(data)
    y = data['injury']
    
    print(f"Features: {X.shape[1]}")
    print(f"Feature names: {model.feature_names}")
    
    # Train model
    X_train, X_test, y_train, y_test, y_pred, y_pred_proba = model.train(X, y)
    
    # Plot results
    print(f"\nGenerating visualizations...")
    model.plot_feature_importance(X)
    model.plot_roc_curve(y_test, y_pred_proba)
    
    # Make predictions on the test set
    test_predictions = model.predict_injury_risk(data.iloc[X_test.index])
    
    # Create results dataframe
    results_df = data.iloc[X_test.index].copy()
    results_df['predicted_injury'] = y_pred
    results_df['predicted_risk'] = test_predictions
    results_df['actual_injury'] = y_test
    
    # Show some example predictions
    print(f"\nExample Predictions:")
    print("-" * 50)
    sample_results = results_df.head(10)[['player', 'age', 'touches_per_game', 'injury_history', 'actual_injury', 'predicted_risk', 'predicted_injury']]
    print(sample_results.to_string(index=False))
    
    # Save results
    results_file = 'data/rb_injury_predictions.csv'
    results_df.to_csv(results_file, index=False)
    print(f"\n✓ Predictions saved to: {results_file}")
    
    # Summary statistics
    print(f"\nPrediction Summary:")
    print(f"  Test set size: {len(X_test)}")
    print(f"  Model accuracy: {model.model.score(X_test, y_test):.3f}")
    print(f"  ROC AUC: {roc_auc_score(y_test, y_pred_proba):.3f}")
    
    print(f"\nModel training and analysis complete!")

if __name__ == "__main__":
    main()

