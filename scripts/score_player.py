"""
Score individual players using a trained injury risk model.
Input: Player features as JSON
Output: Injury risk probability
"""
import argparse
import json
import pickle
import pandas as pd
import numpy as np

def load_model(model_path):
    """Load a trained model from pickle file."""
    with open(model_path, 'rb') as f:
        model = pickle.load(f)
    return model

def prepare_player_features(player_data):
    """
    Prepare player features for prediction.
    
    Args:
        player_data: dict with player features
        
    Returns:
        DataFrame with prepared features
    """
    # Convert to DataFrame
    df = pd.DataFrame([player_data])
    
    # Ensure all required features are present
    required_features = ['age', 'touches_prev', 'career_touches_prior', 'prior_multiweek_prev']
    
    for feature in required_features:
        if feature not in df.columns:
            raise ValueError(f"Missing required feature: {feature}")
    
    # Add any additional features the model might expect
    # These could be derived features or defaults
    if 'position_RB' not in df.columns:
        df['position_RB'] = 1  # Default to RB for this script
    
    if 'yards_per_touch' not in df.columns:
        df['yards_per_touch'] = 4.5  # Default value
    
    if 'injury_history' not in df.columns:
        df['injury_history'] = 0  # Default value
    
    return df

def predict_injury_risk(model, player_features):
    """
    Predict injury risk for a player.
    
    Args:
        model: Trained injury risk model
        player_features: DataFrame with player features
        
    Returns:
        float: Injury risk probability (0-1)
    """
    try:
        # Make prediction
        risk_probability = model.predict_proba(player_features)[:, 1]
        return float(risk_probability[0])
    except Exception as e:
        raise RuntimeError(f"Prediction failed: {e}")

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--type", choices=['rb', 'wr'], default='rb', help="Player type")
    ap.add_argument("--model", required=True, help="Path to trained model (.pkl)")
    ap.add_argument("--player", required=True, help="Player features as JSON string")
    args = ap.parse_args()
    
    try:
        # Load model
        print(f"Loading model from {args.model}")
        model = load_model(args.model)
        
        # Parse player data
        print("Parsing player data...")
        player_data = json.loads(args.player)
        
        # Prepare features
        print("Preparing features...")
        player_features = prepare_player_features(player_data)
        
        # Make prediction
        print("Making prediction...")
        injury_risk = predict_injury_risk(model, player_features)
        
        # Output results
        print("\n" + "="*50)
        print("INJURY RISK PREDICTION")
        print("="*50)
        print(f"Player Type: {args.type.upper()}")
        print(f"Age: {player_data.get('age', 'N/A')}")
        print(f"Previous Season Touches: {player_data.get('touches_prev', 'N/A')}")
        print(f"Career Touches Prior: {player_data.get('career_touches_prior', 'N/A')}")
        print(f"Prior Multi-week Absences: {player_data.get('prior_multiweek_prev', 'N/A')}")
        print(f"Injury Risk Probability: {injury_risk:.3f} ({injury_risk*100:.1f}%)")
        
        # Risk level interpretation
        if injury_risk < 0.3:
            risk_level = "LOW"
        elif injury_risk < 0.6:
            risk_level = "MEDIUM"
        else:
            risk_level = "HIGH"
        
        print(f"Risk Level: {risk_level}")
        print("="*50)
        
    except Exception as e:
        print(f"Error: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())

