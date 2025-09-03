"""
Train and save an injury risk model for running backs.
Input: Season-level CSV with features
Output: Trained model saved as pickle file
"""
import argparse
import pickle
import pandas as pd
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import classification_report, roc_auc_score
from sklearn.pipeline import Pipeline
import warnings
warnings.filterwarnings('ignore')

class RBInjuryModel:
    """
    Injury risk prediction model for NFL running backs.
    """
    
    def __init__(self):
        self.model = None
        self.scaler = StandardScaler()
        self.feature_names = []
        
    def prepare_features(self, data):
        """
        Prepare features for modeling.
        """
        # Select features for modeling
        feature_cols = ['age', 'touches_per_game', 'yards_per_touch', 'multiweek_absences']
        X = data[feature_cols].copy()
        
        # Handle missing values
        X = X.fillna(X.median())
        
        # Create target variable (injury = 1 if multiweek absences > 0)
        y = (data['multiweek_absences'] > 0).astype(int)
        
        self.feature_names = X.columns.tolist()
        return X, y
    
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
        
        # Cross-validation
        cv_scores = cross_val_score(self.model, X, y, cv=5)
        print(f"\nCross-validation scores: {cv_scores}")
        print(f"CV mean: {cv_scores.mean():.3f} (+/- {cv_scores.std() * 2:.3f})")
        
        return X_train, X_test, y_train, y_test, y_pred, y_pred_proba
    
    def save_model(self, filepath):
        """
        Save the trained model to a pickle file.
        """
        if self.model is None:
            raise ValueError("Model not trained yet!")
        
        model_data = {
            'model': self.model,
            'feature_names': self.feature_names,
            'scaler': self.scaler
        }
        
        with open(filepath, 'wb') as f:
            pickle.dump(model_data, f)
        
        print(f"Model saved to {filepath}")

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", required=True, help="Input CSV with season features")
    ap.add_argument("--out", required=True, help="Output pickle file for trained model")
    args = ap.parse_args()
    
    print("RB Injury Risk Model Training")
    print("=" * 50)
    
    # Load data
    print(f"Loading data from {args.in}")
    data = pd.read_csv(args.in)
    print(f"Loaded {len(data)} season records")
    
    # Initialize model
    model = RBInjuryModel()
    
    # Prepare features
    print("Preparing features...")
    X, y = model.prepare_features(data)
    
    print(f"Number of features: {X.shape[1]}")
    print(f"Feature names: {model.feature_names}")
    print(f"Target distribution: {y.value_counts().to_dict()}")
    
    # Train model
    print("\nTraining model...")
    X_train, X_test, y_train, y_test, y_pred, y_pred_proba = model.train(X, y)
    
    # Save model
    print(f"\nSaving model to {args.out}")
    model.save_model(args.out)
    
    print("\nModel training complete!")

if __name__ == "__main__":
    main()

