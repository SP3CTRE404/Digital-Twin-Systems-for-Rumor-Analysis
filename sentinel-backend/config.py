from __future__ import annotations

import os
from pathlib import Path
from dotenv import load_dotenv

def validate_env():
    """Validate and load environment variables."""
    # Load .env file
    env_path = Path(__file__).parent / '.env'
    load_dotenv(env_path)
    
    # Validate required model paths
    stance_path = Path(os.getenv('STANCE_MODEL_PATH', ''))
    sentiment_path = Path(os.getenv('SENTIMENT_MODEL_PATH', ''))
    
    if not stance_path.exists():
        raise EnvironmentError(f"Stance model path not found: {stance_path}")
    if not sentiment_path.exists():
        raise EnvironmentError(f"Sentiment model path not found: {sentiment_path}")
        
    # Validate API key
    api_key = os.getenv('GOOGLE_FACTCHECK_API_KEY')
    if not api_key or api_key == 'your_api_key_here':
        raise EnvironmentError("Google Factcheck API key not configured")
        
    # Validate CORS origin
    cors_origin = os.getenv('CORS_ORIGIN')
    if not cors_origin:
        raise EnvironmentError("CORS_ORIGIN not configured")
        
    # Validate simulation parameters
    sim_params = {
        'DT_GRAPH_N': int,
        'DT_GRAPH_M': int,
        'DT_COMMUNITY_FRAC': float,
        'DT_SEED': int
    }
    
    for param, type_func in sim_params.items():
        value = os.getenv(param)
        if not value:
            raise EnvironmentError(f"{param} not configured")
        try:
            type_func(value)
        except ValueError:
            raise EnvironmentError(f"{param} has invalid value: {value}")
            
    return True