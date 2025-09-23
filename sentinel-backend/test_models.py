import os
import sys

# Add the parent directory to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

from harm_scorer import EnhancedHarmfulnessScorer

def test_model_loading():
    base_dir = os.path.dirname(current_dir)
    sentiment_path = os.path.join(base_dir, "models", "sentiment_model_3050")
    stance_path = os.path.join(base_dir, "models", "stance_model_3050")
    
    print(f"Testing model paths:")
    print(f"Base directory: {base_dir}")
    print(f"Sentiment model path: {sentiment_path}")
    print(f"Stance model path: {stance_path}")
    print(f"Sentiment model exists: {os.path.exists(sentiment_path)}")
    print(f"Stance model exists: {os.path.exists(stance_path)}")
    
    try:
        scorer = EnhancedHarmfulnessScorer(
            sentiment_model_path=sentiment_path,
            stance_model_path=stance_path
        )
        print("Successfully loaded models!")
        return scorer
    except Exception as e:
        print(f"Failed to load models: {str(e)}")
        return None

if __name__ == "__main__":
    scorer = test_model_loading()
    if scorer:
        # Test with a sample text
        result = scorer.analyze_text("This is a test rumor")
        print("\nTest analysis result:")
        print(result)