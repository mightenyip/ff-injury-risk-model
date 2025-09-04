#!/usr/bin/env python3
"""
Example usage of the RB injury model for real-world applications.
This demonstrates how to use the trained model to predict injury risk for new players.
"""
import pandas as pd
import numpy as np
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from scripts.apply_injury_model import RBInjuryModel

def load_trained_model():
    """Load and return a trained injury model."""
    
    # Load the synthetic data
    data = pd.read_csv('data/rb_synthetic_data.csv')
    
    # Initialize and train the model
    model = RBInjuryModel()
    X = model.prepare_features(data)
    y = data['injury']
    
    # Train the model
    print("Training injury model...")
    model.train(X, y)
    
    return model

def predict_injury_risk_for_player(model, player_data):
    """Predict injury risk for a specific player."""
    
    # Create a DataFrame with the player data
    player_df = pd.DataFrame([player_data])
    
    # Make prediction
    risk = model.predict_injury_risk(player_df)
    
    return risk[0]

def analyze_player_risk(player_data, risk_score):
    """Analyze and interpret the injury risk for a player."""
    
    print(f"\nInjury Risk Analysis for {player_data['name']}:")
    print("-" * 50)
    print(f"Age: {player_data['age']}")
    print(f"Expected Games: {player_data['games_played']}")
    print(f"Expected Touches/Game: {player_data['touches_per_game']}")
    print(f"Previous Injury History: {'Yes' if player_data['injury_history'] else 'No'}")
    print(f"Predicted Injury Risk: {risk_score:.1%}")
    
    # Risk interpretation
    if risk_score < 0.3:
        risk_level = "LOW"
        recommendation = "Monitor workload, but low injury concern"
    elif risk_score < 0.5:
        risk_level = "MEDIUM"
        recommendation = "Moderate injury risk, consider load management"
    elif risk_score < 0.7:
        risk_level = "HIGH"
        recommendation = "High injury risk, implement injury prevention protocols"
    else:
        risk_level = "VERY HIGH"
        recommendation = "Very high injury risk, consider reduced role or special monitoring"
    
    print(f"Risk Level: {risk_level}")
    print(f"Recommendation: {recommendation}")
    
    # Specific recommendations based on factors
    print(f"\nSpecific Recommendations:")
    
    if player_data['age'] > 30:
        print(f"  • Age factor: Consider reduced workload for veteran RB")
    
    if player_data['touches_per_game'] > 20:
        print(f"  • Touch volume: High touch count increases injury risk")
    
    if player_data['injury_history']:
        print(f"  • Injury history: Previous injuries increase future risk")
    
    if player_data['age'] <= 25 and player_data['touches_per_game'] < 15:
        print(f"  • Young backup: Low risk profile, good for depth")

def main():
    """Main function demonstrating injury model usage."""
    
    print("RB Injury Risk Model - Usage Example")
    print("=" * 50)
    
    # Load the trained model
    model = load_trained_model()
    
    print(f"\nModel loaded successfully!")
    print(f"Features used: {model.feature_names}")
    
    # Example 1: High-risk veteran RB
    print(f"\n" + "="*60)
    print("EXAMPLE 1: High-Risk Veteran RB")
    print("="*60)
    
    veteran_rb = {
        'name': 'Derrick Henry',
        'age': 30,
        'games_played': 16,
        'touches_per_game': 22,
        'yards_per_touch': 4.5,
        'injury_history': 1,
        'position': 'RB'
    }
    
    risk = predict_injury_risk_for_player(model, veteran_rb)
    analyze_player_risk(veteran_rb, risk)
    
    # Example 2: Low-risk young backup
    print(f"\n" + "="*60)
    print("EXAMPLE 2: Low-Risk Young Backup")
    print("="*60)
    
    young_backup = {
        'name': 'Bijan Robinson',
        'age': 22,
        'games_played': 14,
        'touches_per_game': 12,
        'yards_per_touch': 4.8,
        'injury_history': 0,
        'position': 'RB'
    }
    
    risk = predict_injury_risk_for_player(model, young_backup)
    analyze_player_risk(young_backup, risk)
    
    # Example 3: Medium-risk starter
    print(f"\n" + "="*60)
    print("EXAMPLE 3: Medium-Risk Starter")
    print("="*60)
    
    starter_rb = {
        'name': 'Saquon Barkley',
        'age': 27,
        'games_played': 15,
        'touches_per_game': 18,
        'yards_per_touch': 4.2,
        'injury_history': 1,
        'position': 'RB'
    }
    
    risk = predict_injury_risk_for_player(model, starter_rb)
    analyze_player_risk(starter_rb, risk)
    
    # Example 4: Custom player analysis
    print(f"\n" + "="*60)
    print("CUSTOM PLAYER ANALYSIS")
    print("="*60)
    
    print("Enter player details for custom analysis:")
    
    try:
        name = input("Player name: ").strip() or "Custom Player"
        age = int(input("Age (21-35): ") or "25")
        games = int(input("Expected games played (1-18): ") or "15")
        touches = float(input("Expected touches per game (1-30): ") or "15")
        yards = float(input("Expected yards per touch (2-8): ") or "4.5")
        history = int(input("Previous injury history (0=No, 1=Yes): ") or "0")
        
        custom_player = {
            'name': name,
            'age': age,
            'games_played': games,
            'touches_per_game': touches,
            'yards_per_touch': yards,
            'injury_history': history,
            'position': 'RB'
        }
        
        risk = predict_injury_risk_for_player(model, custom_player)
        analyze_player_risk(custom_player, risk)
        
    except (ValueError, KeyboardInterrupt):
        print("\nCustom analysis skipped.")
    
    # Summary of model capabilities
    print(f"\n" + "="*60)
    print("MODEL CAPABILITIES SUMMARY")
    print("="*60)
    
    print("This injury risk model can:")
    print("  • Predict injury probability for any RB based on key factors")
    print("  • Handle non-linear relationships using spline features")
    print("  • Account for age, workload, and injury history")
    print("  • Provide actionable recommendations for injury prevention")
    
    print(f"\nKey Factors Considered:")
    print("  • Age (with U-shaped risk curve)")
    print("  • Touches per game (workload)")
    print("  • Previous injury history")
    print("  • Games played (durability)")
    print("  • Yards per touch (efficiency)")
    
    print(f"\nModel Performance:")
    print("  • Accuracy: ~65% on test data")
    print("  • ROC AUC: ~0.57")
    print("  • Best at identifying low-risk players")
    print("  • Can be improved with more training data")
    
    print(f"\nUsage Recommendations:")
    print("  • Use as part of a broader injury prevention strategy")
    print("  • Combine with medical staff assessments")
    print("  • Monitor predictions vs. actual outcomes")
    print("  • Update model with new data regularly")
    
    print(f"\nInjury model demonstration complete!")

if __name__ == "__main__":
    main()
