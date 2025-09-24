"""
Advanced, AI-Powered realistic comment section simulator for a digital twin system.
This module uses a large language model to generate an entire, coherent 
conversation thread based on an initial rumor using a single API call.
"""
from typing import Dict, List
import os
import json
import requests

class AdvancedSimulator:
    """
    Generates a realistic, multi-comment conversation thread using a single,
    powerful API call to a large language model.
    """

    def __init__(self):
        """Initializes the Advanced AI Conversation Simulator."""
        self.api_key = os.getenv('OPENAI_API_KEY')
        self.api_url = "https://api.openai.com/v1/chat/completions"
        
        if not self.api_key:
            print("⚠️ WARNING: OPENAI_API_KEY environment variable not set.")
            print("The simulator will not be able to generate comments.")
        else:
            print("✅ Advanced AI Simulator initialized successfully.")

    def generate_thread(self, rumor_text: str, num_comments: int = 10, topic_context: str = "a breaking news event") -> List[Dict]:
        """
        Generates a full, realistic comment thread about a given rumor.

        Args:
            rumor_text (str): The initial rumor to seed the conversation.
            num_comments (int): The desired number of comments in the thread.
            topic_context (str): A brief description of the rumor's context.

        Returns:
            List[Dict]: A list of comment dictionaries, or an empty list if generation fails.
        """
        if not self.api_key:
            print("❌ Error: Cannot generate comments without an API key.")
            return []

        system_prompt = f"""
        You are an advanced simulator of social media conversations. Your task is to create a realistic comment thread in response to a rumor.

        RULES:
        1.  Your entire response MUST be a single JSON object.
        2.  The JSON object must have a single root key named "comments".
        3.  The value of "comments" must be a JSON array containing exactly {num_comments} comment objects.
        4.  The conversation should be dynamic and coherent. Comments should realistically react to the original rumor or each other.
        5.  Simulate a variety of user personas: supporters, deniers, skeptics asking for proof, and neutral observers.
        6.  Each comment object in the array MUST have the following keys: "username", "user_type" (e.g., 'supporter', 'denier', 'skeptic', 'neutral'), "comment_text", and "stance" ('support', 'deny', 'query', 'comment').
        7.  The tone should match the topic context: '{topic_context}'.
        """

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Generate the comment thread for this rumor: \"{rumor_text}\""}
        ]

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }

        payload = {
            "model": "gpt-4o",
            "messages": messages,
            "response_format": {"type": "json_object"},
            "temperature": 0.8,
            "max_tokens": 2048,
        }

        print(f"\n🚀 Sending request to AI for a thread of {num_comments} comments...")

        try:
            response = requests.post(self.api_url, headers=headers, json=payload, timeout=90)
            response.raise_for_status()  # Will raise an HTTPError for bad responses (4xx or 5xx)

            print("✅ AI response received successfully.")
            response_data = response.json()
            content_string = response_data.get('choices', [{}])[0].get('message', {}).get('content', '{}')
            
            parsed_content = json.loads(content_string)
            
            # Directly access the "comments" key as requested in the prompt
            comment_list = parsed_content.get("comments")

            if comment_list and isinstance(comment_list, list):
                print(f"✅ Successfully parsed {len(comment_list)} comments.")
                return comment_list
            else:
                print("❌ Error: Parsed JSON does not contain a 'comments' list.")
                print(f"   Received content: {content_string}")
                return []

        except requests.exceptions.HTTPError as e:
            print(f"❌ API Error: {e.response.status_code} - {e.response.text}")
            return []
        except requests.exceptions.RequestException as e:
            print(f"❌ Network Error: Failed to connect to API. {e}")
            return []
        except json.JSONDecodeError:
            print(f"❌ Error: Failed to decode the AI's JSON response. Raw response was: {content_string}")
            return []
        except Exception as e:
            print(f"❌ An unexpected error occurred: {e}")
            return []

# --- Example Usage ---
if __name__ == "__main__":
    input_rumor = "Breaking: Scientists have discovered a new species of glowing mushrooms in the Amazon that can power a small lightbulb for over a week."

    simulator = AdvancedSimulator()

    comment_thread = simulator.generate_thread(
        rumor_text=input_rumor, 
        num_comments=8, 
        topic_context="a surprising scientific discovery"
    )

    if comment_thread:
        print("\n--- 🤖 Generated Comment Section 🤖 ---\n")
        for i, comment in enumerate(comment_thread, 1):
            print(f"#{i} User: {comment.get('username', 'N/A')} ({comment.get('user_type', 'N/A')})")
            print(f"   Stance: {comment.get('stance', 'N/A')}")
            print(f"   Comment: {comment.get('comment_text', 'N/A')}\n")
    else:
        print("\nCould not generate the comment thread. Please check your API key and network connection.")
