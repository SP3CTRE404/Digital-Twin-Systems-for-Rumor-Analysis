"""Test API-based comment generation"""
from simulation.comment_generator import APICommentGenerator
import os

def main():
    # Ensure we have an API key for testing
    if not os.getenv('OPENAI_API_KEY'):
        print("⚠️ No OpenAI API key found. Set OPENAI_API_KEY environment variable for API testing.")
        print("Will use template-based generation instead.")
    
    # Initialize the comment generator
    generator = APICommentGenerator()
    
    # Test rumor
    test_rumor = "Breaking: Scientists discover a new variant of COVID-19 that spreads through digital devices!"
    
    # Test different user types and stances
    test_cases = [
        ('influencer', 'support'),
        ('skeptic', 'deny'),
        ('regular', 'query'),
        ('amplifier', 'neutral')
    ]
    
    print("\nTesting Comment Generation:")
    print("-" * 50)
    
    for user_type, stance in test_cases:
        print(f"\nGenerating comment for {user_type} user with {stance} stance:")
        comment = generator.generate_comment(user_type, stance, test_rumor)
        print(f"Generated Text: {comment['text']}")
        print(f"Generation Method: {comment['user']['generated_by']}")
        print("-" * 50)

if __name__ == "__main__":
    main()