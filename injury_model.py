"""
NFL RB/WR Injury Risk Modeling with Logistic Regression and Spline Terms

This script implements injury risk prediction for NFL running backs and wide receivers
using logistic regression with spline terms to capture non-linear relationships.
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.preprocessing import StandardScaler, PolynomialFeatures
from sklearn.metrics import classification_report, confusion_matrix, roc_auc_score, roc_curve
from sklearn.pipeline import Pipeline
from scipy.interpolate import UnivariateSpline
import warnings
warnings.filterwarnings('ignore')

class InjuryRiskModel:
    """
    Injury risk prediction model for NFL RB/WR players using logistic regression with spline terms.
    """
    
    def __init__(self):
        self.model = None
        self.scaler = StandardScaler()
        self.feature_names = []
        
    def generate_sample_data(self, n_samples=1000):
        """
        Generate sample data for demonstration purposes.
        In a real scenario, this would be replaced with actual NFL data.
        """
        np.random.seed(42)
        
        # Generate features
        age = np.random.normal(25, 3, n_samples)
        games_played = np.random.poisson(12, n_samples)
        touches_per_game = np.random.normal(15, 5, n_samples)
        yards_per_touch = np.random.normal(5, 1.5, n_samples)
        injury_history = np.random.binomial(1, 0.3, n_samples)
        position = np.random.choice(['RB', 'WR'], n_samples)
        
        # Create non-linear relationships for injury risk
        # Age has a U-shaped relationship with injury risk
        age_risk = 0.1 * (age - 25)**2 / 25
        
        # Touches per game has increasing risk with diminishing returns
        touches_risk = 0.05 * np.log(1 + touches_per_game / 5)
        
        # Injury history increases risk
        history_risk = 0.3 * injury_history
        
        # Position-specific risk (RBs have higher injury risk)
        position_risk = 0.2 * (position == 'RB').astype(int)
        
        # Combine risks with some noise
        total_risk = age_risk + touches_risk + history_risk + position_risk + np.random.normal(0, 0.1, n_samples)
        
        # Convert to binary injury outcome
        injury = (total_risk > np.median(total_risk)).astype(int)
        
        # Create DataFrame
        data = pd.DataFrame({
            'age': age,
            'games_played': games_played,
            'touches_per_game': touches_per_game,
            'yards_per_touch': yards_per_touch,
            'injury_history': injury_history,
            'position': position,
            'injury': injury
        })
        
        return data
    
    def create_spline_features(self, X, feature_name, n_knots=3):
        """
        Create spline features for a given variable.
        """
        feature_values = X[feature_name].values
        knots = np.percentile(feature_values, np.linspace(0, 100, n_knots + 2)[1:-1])
        
        spline_features = []
        for i in range(len(knots) - 1):
            # Create basis function for each spline segment
            basis = np.maximum(0, feature_values - knots[i]) - np.maximum(0, feature_values - knots[i+1])
            spline_features.append(basis)
        
        return np.column_stack(spline_features)
    
    def prepare_features(self, data):
        """
        Prepare features including spline terms for non-linear relationships.
        """
        # Select features for modeling
        feature_cols = ['age', 'games_played', 'touches_per_game', 'yards_per_touch', 'injury_history']
        X = data[feature_cols].copy()
        
        # Add position as dummy variable
        X['position_RB'] = (data['position'] == 'RB').astype(int)
        
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
        """
        Train the injury risk model.
        """
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
    
    def plot_feature_importance(self, X):
        """
        Plot feature importance based on logistic regression coefficients.
        """
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
        """
        Plot ROC curve for model evaluation.
        """
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
    
    def predict_injury_risk(self, player_data):
        """
        Predict injury risk for a given player.
        """
        if self.model is None:
            print("Model not trained yet!")
            return None
        
        # Prepare features
        X = self.prepare_features(player_data)
        
        # Make prediction
        risk_probability = self.model.predict_proba(X)[:, 1]
        
        return risk_probability

def main():
    """
    Main function to run the injury risk modeling pipeline.
    """
    print("NFL RB/WR Injury Risk Modeling")
    print("=" * 50)
    
    # Initialize model
    model = InjuryRiskModel()
    
    # Generate sample data
    print("Generating sample data...")
    data = model.generate_sample_data(n_samples=1000)
    
    print(f"Dataset shape: {data.shape}")
    print(f"Injury rate: {data['injury'].mean():.3f}")
    print(f"Position distribution:\n{data['position'].value_counts()}")
    
    # Prepare features
    print("\nPreparing features...")
    X = model.prepare_features(data)
    y = data['injury']
    
    print(f"Number of features: {X.shape[1]}")
    print(f"Feature names: {model.feature_names}")
    
    # Train model
    print("\nTraining model...")
    X_train, X_test, y_train, y_test, y_pred, y_pred_proba = model.train(X, y)
    
    # Plot results
    print("\nGenerating plots...")
    model.plot_feature_importance(X)
    model.plot_roc_curve(y_test, y_pred_proba)
    
    # Example prediction
    print("\nExample prediction:")
    example_player = pd.DataFrame({
        'age': [28],
        'games_played': [14],
        'touches_per_game': [20],
        'yards_per_touch': [4.5],
        'injury_history': [1],
        'position': ['RB']
    })
    
    risk = model.predict_injury_risk(example_player)
    print(f"Example player injury risk: {risk[0]:.3f}")
    
    print("\nModel training complete!")

if __name__ == "__main__":
    main()
