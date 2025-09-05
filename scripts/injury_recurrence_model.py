#!/usr/bin/env python3
"""
NFL Injury Recurrence Risk Model
Models the likelihood of additional missed time if a player missed time in previous seasons.
"""

import pandas as pd
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import classification_report, confusion_matrix, roc_auc_score
import matplotlib.pyplot as plt
import seaborn as sns
import warnings
warnings.filterwarnings('ignore')

def create_injury_history_features(df):
    """Create features that capture injury history patterns."""
    print("Creating injury history features...")
    
    # Sort by player and season for proper time series
    df = df.sort_values(['player_id', 'season', 'Week']).reset_index(drop=True)
    
    # Initialize new columns
    df['has_prior_injury_season'] = False
    df['injury_seasons_count'] = 0
    df['total_injury_games'] = 0
    df['injury_rate_prior_seasons'] = 0.0
    df['consecutive_injury_seasons'] = 0
    df['last_injury_season'] = 0
    df['seasons_since_last_injury'] = 0
    df['injury_severity_prior'] = 0.0  # Average games missed per injury season
    
    # Calculate injury history for each player
    for player_id in df['player_id'].unique():
        player_mask = df['player_id'] == player_id
        player_data = df[player_mask].copy()
        
        # Group by season to get injury patterns
        season_injuries = player_data.groupby('season').agg({
            'injured': ['sum', 'count', 'mean']
        }).round(3)
        
        season_injuries.columns = ['injury_games', 'total_games', 'injury_rate']
        season_injuries = season_injuries.reset_index()
        
        # Calculate cumulative injury history
        injury_seasons = season_injuries[season_injuries['injury_games'] > 0]['season'].tolist()
        total_injury_games = season_injuries['injury_games'].sum()
        
        # For each game, calculate prior injury history
        for idx, row in player_data.iterrows():
            current_season = row['season']
            
            # Prior seasons (before current season)
            prior_seasons = season_injuries[season_injuries['season'] < current_season]
            
            if len(prior_seasons) > 0:
                # Has player had injury seasons before?
                prior_injury_seasons = prior_seasons[prior_seasons['injury_games'] > 0]
                df.loc[idx, 'has_prior_injury_season'] = len(prior_injury_seasons) > 0
                df.loc[idx, 'injury_seasons_count'] = len(prior_injury_seasons)
                df.loc[idx, 'total_injury_games'] = prior_seasons['injury_games'].sum()
                df.loc[idx, 'injury_rate_prior_seasons'] = prior_seasons['injury_rate'].mean()
                
                # Consecutive injury seasons
                if len(prior_injury_seasons) > 0:
                    injury_seasons_list = sorted(prior_injury_seasons['season'].tolist())
                    consecutive_count = 0
                    for i in range(len(injury_seasons_list) - 1, -1, -1):
                        if i == len(injury_seasons_list) - 1 or injury_seasons_list[i] == injury_seasons_list[i+1] - 1:
                            consecutive_count += 1
                        else:
                            break
                    df.loc[idx, 'consecutive_injury_seasons'] = consecutive_count
                    
                    # Seasons since last injury
                    last_injury_season = max(injury_seasons_list)
                    df.loc[idx, 'last_injury_season'] = last_injury_season
                    df.loc[idx, 'seasons_since_last_injury'] = current_season - last_injury_season
                    
                    # Injury severity (average games missed per injury season)
                    df.loc[idx, 'injury_severity_prior'] = prior_injury_seasons['injury_games'].mean()
    
    print(f"  ✅ Created injury history features")
    return df

def create_recurrence_target(df):
    """Create target variable for injury recurrence."""
    print("Creating recurrence target variable...")
    
    # Sort by player and season
    df = df.sort_values(['player_id', 'season', 'Week']).reset_index(drop=True)
    
    # Initialize target
    df['injury_recurrence'] = False
    
    # For each player, identify if they have injury recurrence
    for player_id in df['player_id'].unique():
        player_mask = df['player_id'] == player_id
        player_data = df[player_mask].copy()
        
        # Group by season
        season_summary = player_data.groupby('season').agg({
            'injured': 'sum'
        }).reset_index()
        season_summary.columns = ['season', 'injury_games']
        
        # Identify seasons with injuries
        injury_seasons = season_summary[season_summary['injury_games'] > 0]['season'].tolist()
        
        # Mark recurrence: if player has injuries in multiple seasons
        if len(injury_seasons) > 1:
            # Mark all games in seasons after the first injury season as potential recurrence
            first_injury_season = min(injury_seasons)
            recurrence_mask = (df['player_id'] == player_id) & (df['season'] > first_injury_season)
            df.loc[recurrence_mask, 'injury_recurrence'] = True
    
    # Alternative definition: mark games where player is injured AND has prior injury history
    df['injury_recurrence_alt'] = df['injured'] & df['has_prior_injury_season']
    
    print(f"  ✅ Created recurrence target variables")
    print(f"  Recurrence rate (any season after first injury): {df['injury_recurrence'].mean():.3f}")
    print(f"  Recurrence rate (injured + prior history): {df['injury_recurrence_alt'].mean():.3f}")
    
    return df

def analyze_injury_patterns(df):
    """Analyze injury patterns and recurrence rates."""
    print("\nAnalyzing Injury Patterns:")
    print("=" * 50)
    
    # Overall injury rates
    print("Overall Injury Rates:")
    print(f"  Total games: {len(df)}")
    print(f"  Injured games: {df['injured'].sum()}")
    print(f"  Injury rate: {df['injured'].mean():.3f}")
    
    # Players with prior injury history
    prior_injury_games = df[df['has_prior_injury_season']]
    print(f"\nGames with Prior Injury History:")
    print(f"  Total games: {len(prior_injury_games)}")
    print(f"  Injured games: {prior_injury_games['injured'].sum()}")
    print(f"  Injury rate: {prior_injury_games['injured'].mean():.3f}")
    
    # Recurrence analysis
    print(f"\nInjury Recurrence Analysis:")
    recurrence_games = df[df['injury_recurrence']]
    print(f"  Potential recurrence games: {len(recurrence_games)}")
    print(f"  Actual injuries in recurrence games: {recurrence_games['injured'].sum()}")
    print(f"  Recurrence injury rate: {recurrence_games['injured'].mean():.3f}")
    
    # Compare injury rates
    no_prior_injury = df[~df['has_prior_injury_season']]
    print(f"\nInjury Rate Comparison:")
    print(f"  No prior injury history: {no_prior_injury['injured'].mean():.3f}")
    print(f"  With prior injury history: {prior_injury_games['injured'].mean():.3f}")
    print(f"  Risk ratio: {prior_injury_games['injured'].mean() / no_prior_injury['injured'].mean():.2f}x")
    
    # Player-level analysis
    print(f"\nPlayer-Level Injury Patterns:")
    player_summary = df.groupby('player_id').agg({
        'injured': 'sum',
        'has_prior_injury_season': 'any',
        'injury_seasons_count': 'max',
        'total_injury_games': 'max'
    }).round(2)
    player_summary.columns = ['Total_Injuries', 'Has_Prior_Injury', 'Injury_Seasons', 'Total_Injury_Games']
    player_summary = player_summary.sort_values('Total_Injuries', ascending=False)
    print(player_summary.head(10).to_string())

def train_recurrence_model(df):
    """Train model to predict injury recurrence."""
    print("\nTraining Injury Recurrence Model:")
    print("=" * 50)
    
    # Select features for recurrence modeling
    feature_columns = [
        # Current game features
        'Att', 'Yds', 'TD', 'Rec', 'touches_per_game', 'age',
        
        # Recent workload
        'touches_prev', 'touches_prev_2', 'touches_prev_3',
        
        # Injury history features
        'has_prior_injury_season', 'injury_seasons_count', 'total_injury_games',
        'injury_rate_prior_seasons', 'consecutive_injury_seasons',
        'seasons_since_last_injury', 'injury_severity_prior',
        
        # Context features
        'late_season', 'games_played'
    ]
    
    # Filter to available features
    available_features = [col for col in feature_columns if col in df.columns]
    print(f"Using features: {available_features}")
    
    # Prepare data
    X = df[available_features].fillna(0)
    
    # Use alternative recurrence definition (more specific)
    y = df['injury_recurrence_alt']
    
    print(f"Dataset shape: {X.shape}")
    print(f"Recurrence rate: {y.mean():.3f}")
    
    # Split data
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)
    
    # Train multiple models
    models = {
        'Logistic Regression': LogisticRegression(random_state=42, class_weight='balanced', max_iter=1000),
        'Random Forest': RandomForestClassifier(n_estimators=100, random_state=42, class_weight='balanced')
    }
    
    results = {}
    
    for name, model in models.items():
        print(f"\nTraining {name}...")
        
        # Train model
        model.fit(X_train, y_train)
        
        # Make predictions
        y_pred = model.predict(X_test)
        y_pred_proba = model.predict_proba(X_test)[:, 1]
        
        # Calculate metrics
        auc_score = roc_auc_score(y_test, y_pred_proba)
        accuracy = (y_pred == y_test).mean()
        
        # Cross-validation
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
        
        print(f"  AUC: {auc_score:.3f}")
        print(f"  Accuracy: {accuracy:.3f}")
        print(f"  CV AUC: {cv_scores.mean():.3f} ± {cv_scores.std():.3f}")
    
    return results, X_test, y_test, available_features

def evaluate_recurrence_model(results, X_test, y_test, feature_names):
    """Evaluate the recurrence model performance."""
    print("\nRecurrence Model Evaluation:")
    print("=" * 50)
    
    # Find best model
    best_model_name = max(results.keys(), key=lambda x: results[x]['auc_score'])
    best_model = results[best_model_name]
    
    print(f"Best Model: {best_model_name}")
    print(f"AUC Score: {best_model['auc_score']:.3f}")
    print(f"Accuracy: {best_model['accuracy']:.3f}")
    
    # Classification report
    print(f"\nClassification Report:")
    print(classification_report(y_test, best_model['y_pred']))
    
    # Feature importance
    if hasattr(best_model['model'], 'feature_importances_'):
        print(f"\nTop 10 Most Important Features:")
        feature_importance = pd.DataFrame({
            'feature': feature_names,
            'importance': best_model['model'].feature_importances_
        }).sort_values('importance', ascending=False)
        print(feature_importance.head(10).to_string(index=False))
    elif hasattr(best_model['model'], 'coef_'):
        print(f"\nTop 10 Most Important Features (Coefficients):")
        feature_importance = pd.DataFrame({
            'feature': feature_names,
            'coefficient': best_model['model'].coef_[0]
        }).sort_values('coefficient', key=abs, ascending=False)
        print(feature_importance.head(10).to_string(index=False))
    
    return best_model_name, best_model

def main():
    """Main function to build the injury recurrence model."""
    print("Building NFL Injury Recurrence Risk Model")
    print("=" * 60)
    
    # Load the cleaned dataset
    print("Loading cleaned dataset...")
    df = pd.read_csv("data/multi_season_final/cleaned_three_season_injury_data.csv")
    print(f"  ✅ Loaded {len(df)} games from {df['player_id'].nunique()} players")
    
    # Create additional features
    print("Creating additional features...")
    df['touches_per_game'] = df['Att'] + df['Rec']
    df['late_season'] = (df['Week'] > 12).astype(int)
    df['games_played'] = df.groupby('player_id').cumcount() + 1
    
    # Create injury history features
    df = create_injury_history_features(df)
    
    # Create recurrence target
    df = create_recurrence_target(df)
    
    # Analyze injury patterns
    analyze_injury_patterns(df)
    
    # Train recurrence model
    results, X_test, y_test, feature_names = train_recurrence_model(df)
    
    # Evaluate model
    best_model_name, best_model = evaluate_recurrence_model(results, X_test, y_test, feature_names)
    
    print(f"\n🎯 INJURY RECURRENCE MODEL COMPLETE!")
    print(f"Best model: {best_model_name}")
    print(f"Model performance: AUC = {best_model['auc_score']:.3f}")
    print(f"Ready to predict injury recurrence risk!")

if __name__ == "__main__":
    main()
