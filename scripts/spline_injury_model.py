#!/usr/bin/env python3
"""
NFL Injury Risk Model using Logistic Regression with Spline Terms
Based on the original injury_model.py design.
"""

import pandas as pd
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import classification_report, confusion_matrix, roc_auc_score
from scipy.interpolate import UnivariateSpline
import warnings
warnings.filterwarnings('ignore')

def create_spline_features(df, feature_name, n_knots=3):
    """Create spline features for a given variable."""
    # Remove NaN values for spline fitting
    valid_data = df[feature_name].dropna()
    if len(valid_data) < 10:  # Need enough data for splines
        return df[feature_name].fillna(0)
    
    # Create knots
    knots = np.linspace(valid_data.min(), valid_data.max(), n_knots + 2)[1:-1]
    
    # Create spline features
    spline_features = []
    for i, knot in enumerate(knots):
        # Create basis function: max(0, x - knot)
        basis = np.maximum(0, df[feature_name].fillna(0) - knot)
        spline_features.append(basis)
    
    return spline_features

def prepare_spline_features(df):
    """Prepare features with spline terms for the injury model."""
    print("Creating spline features...")
    
    # Select key features for spline modeling
    key_features = [
        'Att', 'Yds', 'touches_prev', 'career_touches_prior', 
        'prior_multiweek_prev', 'touches_per_game', 'age'
    ]
    
    # Filter to available features
    available_features = [col for col in key_features if col in df.columns]
    print(f"  Using features: {available_features}")
    
    # Create spline features
    spline_data = {}
    
    for feature in available_features:
        if feature in df.columns:
            # Original feature
            spline_data[feature] = df[feature].fillna(0)
            
            # Spline features (3 knots)
            spline_basis = create_spline_features(df, feature, n_knots=3)
            for i, basis in enumerate(spline_basis):
                spline_data[f'{feature}_spline_{i}'] = basis
    
    # Add other important features without splines
    other_features = ['TD', 'Rec', 'Y/A', 'late_season', 'games_played']
    for feature in other_features:
        if feature in df.columns:
            spline_data[feature] = df[feature].fillna(0)
    
    return pd.DataFrame(spline_data)

def train_spline_model(X_train, y_train, X_test, y_test):
    """Train logistic regression with spline features."""
    print("Training Logistic Regression with Spline Features...")
    
    # Scale the features
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)
    
    # Train logistic regression
    model = LogisticRegression(
        random_state=42, 
        class_weight='balanced', 
        max_iter=1000,
        C=1.0  # Regularization parameter
    )
    
    model.fit(X_train_scaled, y_train)
    
    # Make predictions
    y_pred = model.predict(X_test_scaled)
    y_pred_proba = model.predict_proba(X_test_scaled)[:, 1]
    
    # Calculate metrics
    auc_score = roc_auc_score(y_test, y_pred_proba)
    accuracy = (y_pred == y_test).mean()
    
    # Cross-validation score
    cv_scores = cross_val_score(model, X_train_scaled, y_train, cv=5, scoring='roc_auc')
    
    print(f"  AUC Score: {auc_score:.3f}")
    print(f"  Accuracy: {accuracy:.3f}")
    print(f"  Cross-Validation AUC: {cv_scores.mean():.3f} ± {cv_scores.std():.3f}")
    
    return model, scaler, {
        'auc_score': auc_score,
        'accuracy': accuracy,
        'cv_mean': cv_scores.mean(),
        'cv_std': cv_scores.std(),
        'y_pred': y_pred,
        'y_pred_proba': y_pred_proba
    }

def evaluate_spline_model(model, scaler, results, y_test, feature_names):
    """Evaluate the spline model performance."""
    print("\nSpline Model Performance:")
    print("=" * 50)
    
    print(f"AUC Score: {results['auc_score']:.3f}")
    print(f"Accuracy: {results['accuracy']:.3f}")
    print(f"Cross-Validation AUC: {results['cv_mean']:.3f} ± {results['cv_std']:.3f}")
    
    # Classification report
    print(f"\nClassification Report:")
    print(classification_report(y_test, results['y_pred']))
    
    # Confusion matrix
    print(f"\nConfusion Matrix:")
    cm = confusion_matrix(y_test, results['y_pred'])
    print(cm)
    
    # Feature importance (coefficients)
    print(f"\nTop 10 Most Important Features:")
    feature_importance = pd.DataFrame({
        'feature': feature_names,
        'coefficient': model.coef_[0]
    }).sort_values('coefficient', key=abs, ascending=False)
    
    print(feature_importance.head(10).to_string(index=False))
    
    return feature_importance

def test_with_known_player_spline(df, model, scaler, feature_names, player_id='chubni00'):
    """Test the spline model with a known player."""
    print(f"\nTesting Spline Model with known player: {player_id}")
    print("=" * 50)
    
    # Get player data
    player_data = df[df['player_id'] == player_id].copy()
    
    if len(player_data) == 0:
        print(f"  ❌ No data found for player {player_id}")
        return
    
    # Prepare spline features
    player_spline_features = prepare_spline_features(player_data)
    
    # Ensure all features are present
    for feature in feature_names:
        if feature not in player_spline_features.columns:
            player_spline_features[feature] = 0
    
    # Reorder columns to match training data
    X_player = player_spline_features[feature_names]
    y_player = player_data['injured']
    
    # Scale features
    X_player_scaled = scaler.transform(X_player)
    
    # Make predictions
    injury_prob = model.predict_proba(X_player_scaled)[:, 1]
    injury_pred = model.predict(X_player_scaled)
    
    # Add predictions to player data
    player_data['injury_probability'] = injury_prob
    player_data['injury_prediction'] = injury_pred
    
    # Show results
    print(f"  Total games: {len(player_data)}")
    print(f"  Actual injuries: {y_player.sum()}")
    print(f"  Predicted injuries: {injury_pred.sum()}")
    print(f"  Average injury probability: {injury_prob.mean():.3f}")
    print(f"  Max injury probability: {injury_prob.max():.3f}")
    
    # Show games with highest injury risk
    high_risk_games = player_data[player_data['injury_probability'] > 0.3].sort_values('injury_probability', ascending=False)
    if len(high_risk_games) > 0:
        print(f"\n  Games with highest injury risk (>30%):")
        display_cols = ['season', 'Week', 'Date', 'Team', 'Opp', 'Att', 'Yds', 'injured', 'injury_probability']
        available_cols = [col for col in display_cols if col in high_risk_games.columns]
        print(high_risk_games[available_cols].head(5).to_string(index=False))
    
    return player_data

def test_with_new_player_spline(model, scaler, feature_names):
    """Test the spline model with a new player (simulated data)."""
    print(f"\nTesting Spline Model with new player (simulated data)")
    print("=" * 50)
    
    # Create simulated data for a new player
    np.random.seed(42)
    n_games = 17
    
    # Simulate a high-risk player
    new_player_data = {
        'Att': np.random.normal(20, 5, n_games),
        'Yds': np.random.normal(100, 30, n_games),
        'TD': np.random.poisson(1, n_games),
        'Rec': np.random.normal(5, 2, n_games),
        'Y/A': np.random.normal(4.5, 0.5, n_games),
        'touches_prev': np.random.normal(20, 5, n_games),
        'career_touches_prior': np.cumsum(np.random.normal(20, 5, n_games)),
        'prior_multiweek_prev': np.random.poisson(1, n_games),
        'touches_per_game': np.random.normal(25, 5, n_games),
        'late_season': [0] * 12 + [1] * 5,
        'games_played': range(1, n_games + 1),
        'age': np.ones(n_games) * 22
    }
    
    new_player_df = pd.DataFrame(new_player_data)
    
    print(f"  Simulated {n_games} games for new player")
    print(f"  Average touches per game: {new_player_df['touches_per_game'].mean():.1f}")
    print(f"  Average career touches: {new_player_df['career_touches_prior'].mean():.1f}")
    
    # Prepare spline features
    new_player_spline_features = prepare_spline_features(new_player_df)
    
    # Ensure all features are present
    for feature in feature_names:
        if feature not in new_player_spline_features.columns:
            new_player_spline_features[feature] = 0
    
    # Reorder columns to match training data
    X_new = new_player_spline_features[feature_names]
    
    # Scale features
    X_new_scaled = scaler.transform(X_new)
    
    # Make predictions
    injury_prob = model.predict_proba(X_new_scaled)[:, 1]
    injury_pred = model.predict(X_new_scaled)
    
    # Add predictions to dataframe
    new_player_df['injury_probability'] = injury_prob
    new_player_df['injury_prediction'] = injury_pred
    
    # Show results
    print(f"  Predicted injuries: {injury_pred.sum()}")
    print(f"  Average injury probability: {injury_prob.mean():.3f}")
    print(f"  Max injury probability: {injury_prob.max():.3f}")
    
    # Show games with highest injury risk
    high_risk_games = new_player_df[new_player_df['injury_probability'] > 0.3].sort_values('injury_probability', ascending=False)
    if len(high_risk_games) > 0:
        print(f"\n  Games with highest injury risk (>30%):")
        display_cols = ['touches_per_game', 'Att', 'Yds', 'injury_probability', 'injury_prediction']
        available_cols = [col for col in display_cols if col in high_risk_games.columns]
        print(high_risk_games[available_cols].head(5).to_string(index=False))
    
    return new_player_df

def main():
    """Main function to build and test the spline-based injury risk model."""
    print("Building NFL Injury Risk Model with Spline Terms")
    print("=" * 60)
    
    # Load the cleaned dataset
    print("Loading cleaned dataset...")
    df = pd.read_csv("data/multi_season_final/cleaned_three_season_injury_data.csv")
    print(f"  ✅ Loaded {len(df)} games from {df['player_id'].nunique()} players")
    
    # Create simple additional features
    print("Creating additional features...")
    df['touches_per_game'] = df['Att'] + df['Rec']
    df['late_season'] = (df['Week'] > 12).astype(int)
    df['games_played'] = df.groupby('player_id').cumcount() + 1
    
    # Prepare spline features
    X_spline = prepare_spline_features(df)
    y = df['injured']
    
    print(f"  ✅ Created {X_spline.shape[1]} features (including spline terms)")
    
    # Split the data
    X_train, X_test, y_train, y_test = train_test_split(X_spline, y, test_size=0.2, random_state=42, stratify=y)
    
    print(f"  Training set: {len(X_train)} games")
    print(f"  Test set: {len(X_test)} games")
    print(f"  Injury rate in training: {y_train.mean():.3f}")
    print(f"  Injury rate in test: {y_test.mean():.3f}")
    
    # Train spline model
    model, scaler, results = train_spline_model(X_train, y_train, X_test, y_test)
    
    # Evaluate performance
    feature_importance = evaluate_spline_model(model, scaler, results, y_test, X_spline.columns.tolist())
    
    # Test with known player
    known_player_results = test_with_known_player_spline(df, model, scaler, X_spline.columns.tolist(), 'chubni00')
    
    # Test with new player
    new_player_results = test_with_new_player_spline(model, scaler, X_spline.columns.tolist())
    
    print(f"\n🎯 SPLINE INJURY RISK MODEL COMPLETE!")
    print(f"Model type: Logistic Regression with Spline Terms")
    print(f"Model performance: AUC = {results['auc_score']:.3f}")
    print(f"Ready for real-world injury risk prediction!")

if __name__ == "__main__":
    main()
