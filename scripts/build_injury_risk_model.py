#!/usr/bin/env python3
"""
Build and test an injury risk model using the cleaned three-season dataset.
"""

import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import classification_report, confusion_matrix, roc_auc_score, roc_curve
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

def load_and_prepare_data():
    """Load and prepare the cleaned dataset for modeling."""
    print("Loading and preparing data for injury risk modeling...")
    
    # Load the cleaned dataset
    df = pd.read_csv("data/multi_season_final/cleaned_three_season_injury_data.csv")
    print(f"  ✅ Loaded {len(df)} games from {df['player_id'].nunique()} players")
    
    # Create additional features for modeling
    print("Creating additional features...")
    
    # Workload features
    df['touches_per_game'] = df['Att'] + df['Rec']
    df['yards_per_touch'] = df['Yds'] / (df['touches_per_game'] + 1)  # +1 to avoid division by zero
    df['touchdown_rate'] = df['TD'] / (df['touches_per_game'] + 1)
    
    # Recent workload (last 3 games)
    df['recent_touches_avg'] = df.groupby('player_id')['touches_per_game'].rolling(3, min_periods=1).mean().shift(1).fillna(0)
    df['recent_yards_avg'] = df.groupby('player_id')['Yds'].rolling(3, min_periods=1).mean().shift(1).fillna(0)
    
    # Workload trends
    df['touches_trend'] = df.groupby('player_id')['touches_per_game'].rolling(3, min_periods=1).apply(lambda x: np.polyfit(range(len(x)), x, 1)[0] if len(x) > 1 else 0).shift(1).fillna(0)
    
    # Season progression
    df['week_in_season'] = df['Week']
    df['late_season'] = (df['Week'] > 12).astype(int)
    
    # Player experience
    df['games_played'] = df.groupby('player_id').cumcount() + 1
    df['season_experience'] = df.groupby('player_id')['season'].rank(method='dense')
    
    # Injury history features
    df['injury_rate_prior'] = df.groupby('player_id')['injured'].expanding().mean().shift(1).fillna(0)
    df['days_since_last_injury'] = df.groupby('player_id')['injured'].apply(lambda x: (x == 1).cumsum().shift(1).fillna(0))
    
    print(f"  ✅ Created {len(df.columns)} total features")
    
    return df

def select_features(df):
    """Select features for the injury risk model."""
    print("Selecting features for modeling...")
    
    # Define feature columns
    feature_columns = [
        # Basic game stats
        'Att', 'Yds', 'TD', 'Rec', 'Y/A', 'Tgt', 'Y/R', 'Ctch%',
        
        # Workload features
        'touches_per_game', 'yards_per_touch', 'touchdown_rate',
        'touches_prev', 'touches_prev_2', 'touches_prev_3',
        'recent_touches_avg', 'recent_yards_avg', 'touches_trend',
        
        # Career features
        'career_touches_prior', 'games_played', 'season_experience',
        
        # Injury history
        'injury_rate_prior', 'prior_multiweek_prev', 'days_since_last_injury',
        
        # Season/context features
        'week_in_season', 'late_season', 'age'
    ]
    
    # Filter to only include columns that exist in the dataframe
    available_features = [col for col in feature_columns if col in df.columns]
    print(f"  ✅ Using {len(available_features)} features: {available_features}")
    
    return available_features

def train_models(X_train, y_train, X_test, y_test):
    """Train multiple models and compare performance."""
    print("Training multiple models...")
    
    models = {
        'Random Forest': RandomForestClassifier(n_estimators=100, random_state=42, class_weight='balanced'),
        'Gradient Boosting': GradientBoostingClassifier(n_estimators=100, random_state=42),
        'Logistic Regression': LogisticRegression(random_state=42, class_weight='balanced', max_iter=1000)
    }
    
    results = {}
    
    for name, model in models.items():
        print(f"  Training {name}...")
        
        # Train the model
        model.fit(X_train, y_train)
        
        # Make predictions
        y_pred = model.predict(X_test)
        y_pred_proba = model.predict_proba(X_test)[:, 1]
        
        # Calculate metrics
        auc_score = roc_auc_score(y_test, y_pred_proba)
        accuracy = (y_pred == y_test).mean()
        
        # Cross-validation score
        cv_scores = cross_val_score(model, X_train, y_train, cv=5, scoring='roc_auc')
        
        results[name] = {
            'model': model,
            'auc_score': auc_score,
            'accuracy': accuracy,
            'cv_mean': cv_scores.mean(),
            'cv_std': cv_scores.std(),
            'y_pred': y_pred,
            'y_pred_proba': y_pred_proba
        }
        
        print(f"    AUC: {auc_score:.3f}, Accuracy: {accuracy:.3f}, CV AUC: {cv_scores.mean():.3f} ± {cv_scores.std():.3f}")
    
    return results

def evaluate_model_performance(results, y_test):
    """Evaluate and compare model performance."""
    print("\nModel Performance Comparison:")
    print("=" * 50)
    
    # Find best model
    best_model_name = max(results.keys(), key=lambda x: results[x]['auc_score'])
    best_model = results[best_model_name]
    
    print(f"Best Model: {best_model_name}")
    print(f"AUC Score: {best_model['auc_score']:.3f}")
    print(f"Accuracy: {best_model['accuracy']:.3f}")
    print(f"Cross-Validation AUC: {best_model['cv_mean']:.3f} ± {best_model['cv_std']:.3f}")
    
    # Classification report
    print(f"\nClassification Report for {best_model_name}:")
    print(classification_report(y_test, best_model['y_pred']))
    
    # Confusion matrix
    print(f"\nConfusion Matrix for {best_model_name}:")
    cm = confusion_matrix(y_test, best_model['y_pred'])
    print(cm)
    
    return best_model_name, best_model

def test_with_known_player(df, model, feature_columns, player_id='chubni00'):
    """Test the model with a known player from the training data."""
    print(f"\nTesting with known player: {player_id}")
    print("=" * 50)
    
    # Get player data
    player_data = df[df['player_id'] == player_id].copy()
    
    if len(player_data) == 0:
        print(f"  ❌ No data found for player {player_id}")
        return
    
    # Prepare features
    X_player = player_data[feature_columns].fillna(0)
    y_player = player_data['injured']
    
    # Make predictions
    injury_prob = model.predict_proba(X_player)[:, 1]
    injury_pred = model.predict(X_player)
    
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

def test_with_new_player():
    """Test the model with a new player (simulated data)."""
    print(f"\nTesting with new player (simulated data)")
    print("=" * 50)
    
    # Create simulated data for a new player
    np.random.seed(42)
    n_games = 17
    
    # Simulate a high-risk player (high workload, recent injuries)
    new_player_data = {
        'Att': np.random.normal(20, 5, n_games),  # High rushing attempts
        'Yds': np.random.normal(100, 30, n_games),  # High yards
        'TD': np.random.poisson(1, n_games),  # Touchdowns
        'Rec': np.random.normal(5, 2, n_games),  # Receptions
        'Y/A': np.random.normal(4.5, 0.5, n_games),  # Yards per attempt
        'Tgt': np.random.normal(6, 2, n_games),  # Targets
        'Y/R': np.random.normal(8, 2, n_games),  # Yards per reception
        'Ctch%': np.random.normal(80, 10, n_games),  # Catch percentage
        'touches_per_game': np.random.normal(25, 5, n_games),  # High touches
        'yards_per_touch': np.random.normal(4, 0.5, n_games),
        'touchdown_rate': np.random.normal(0.05, 0.02, n_games),
        'touches_prev': np.random.normal(20, 5, n_games),
        'touches_prev_2': np.random.normal(22, 5, n_games),
        'touches_prev_3': np.random.normal(18, 5, n_games),
        'recent_touches_avg': np.random.normal(20, 3, n_games),
        'recent_yards_avg': np.random.normal(95, 20, n_games),
        'touches_trend': np.random.normal(0, 1, n_games),
        'career_touches_prior': np.cumsum(np.random.normal(20, 5, n_games)),
        'games_played': range(1, n_games + 1),
        'season_experience': np.ones(n_games),  # Rookie season
        'injury_rate_prior': np.random.normal(0.15, 0.05, n_games),  # High injury rate
        'prior_multiweek_prev': np.random.poisson(1, n_games),  # Recent injuries
        'days_since_last_injury': np.random.exponential(30, n_games),  # Recent injury
        'week_in_season': range(1, n_games + 1),
        'late_season': [0] * 12 + [1] * 5,  # Late season games
        'age': np.ones(n_games) * 22  # Young player
    }
    
    new_player_df = pd.DataFrame(new_player_data)
    
    print(f"  Simulated {n_games} games for new player")
    print(f"  Average touches per game: {new_player_df['touches_per_game'].mean():.1f}")
    print(f"  Average injury rate prior: {new_player_df['injury_rate_prior'].mean():.3f}")
    print(f"  Recent injuries: {new_player_df['prior_multiweek_prev'].sum()}")
    
    return new_player_df

def make_predictions_for_new_player(model, feature_columns, new_player_df):
    """Make injury risk predictions for the new player."""
    print(f"\nMaking injury risk predictions for new player...")
    
    # Prepare features
    X_new = new_player_df[feature_columns].fillna(0)
    
    # Make predictions
    injury_prob = model.predict_proba(X_new)[:, 1]
    injury_pred = model.predict(X_new)
    
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
        display_cols = ['week_in_season', 'touches_per_game', 'Att', 'Yds', 'injury_probability', 'injury_prediction']
        available_cols = [col for col in display_cols if col in high_risk_games.columns]
        print(high_risk_games[available_cols].head(5).to_string(index=False))
    
    return new_player_df

def main():
    """Main function to build and test the injury risk model."""
    print("Building NFL Injury Risk Model")
    print("=" * 50)
    
    # Load and prepare data
    df = load_and_prepare_data()
    
    # Select features
    feature_columns = select_features(df)
    
    # Prepare training data
    print("Preparing training data...")
    X = df[feature_columns].fillna(0)
    y = df['injured']
    
    # Split the data
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)
    
    print(f"  Training set: {len(X_train)} games")
    print(f"  Test set: {len(X_test)} games")
    print(f"  Injury rate in training: {y_train.mean():.3f}")
    print(f"  Injury rate in test: {y_test.mean():.3f}")
    
    # Train models
    results = train_models(X_train, y_train, X_test, y_test)
    
    # Evaluate performance
    best_model_name, best_model = evaluate_model_performance(results, y_test)
    
    # Test with known player
    known_player_results = test_with_known_player(df, best_model['model'], feature_columns, 'chubni00')
    
    # Test with new player
    new_player_df = test_with_new_player()
    new_player_results = make_predictions_for_new_player(best_model['model'], feature_columns, new_player_df)
    
    print(f"\n🎯 INJURY RISK MODEL COMPLETE!")
    print(f"Best model: {best_model_name}")
    print(f"Model performance: AUC = {best_model['auc_score']:.3f}")
    print(f"Ready for real-world injury risk prediction!")

if __name__ == "__main__":
    main()
