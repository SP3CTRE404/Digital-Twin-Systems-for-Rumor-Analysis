"""
AI-Powered realistic comment section simulator for a digital twin system.
This module uses a large language model to generate an entire, coherent 
conversation thread based on an initial rumor.
"""
from typing import Dict, List
import os
import json
import requests

class AIConversationSimulator:
    """
    Generates a realistic, multi-comment conversation thread using a single,
    powerful API call to a large language model.
    """

    def __init__(self):
        """Initializes the AI Conversation Simulator."""
        self.api_key = os.getenv('OPENAI_API_KEY')
        self.api_url = "https://api.openai.com/v1/chat/completions"
        
        if not self.api_key:
            print("⚠️ WARNING: OPENAI_API_KEY environment variable not set.")
            print("The simulator will not be able to generate comments.")
        else:
            print("✅ AI Conversation Simulator initialized successfully.")

    def generate_thread(self, rumor_text: str, num_comments: int = 10, topic_context: str = "a breaking news event") -> List[Dict]:
        """
        Generates a full, realistic comment thread about a given rumor.

        Args:
            rumor_text (str): The initial rumor to seed the conversation.
            num_comments (int): The desired number of comments in the thread.
            topic_context (str): A brief description of the rumor's context 
                                 (e.g., 'celebrity gossip', 'political news').

        Returns:
            List[Dict]: A list of comment dictionaries, or an empty list if generation fails.
        """
        if not self.api_key:
            print("❌ Error: Cannot generate comments without an API key.")
            return []

        # The core prompt that instructs the AI to generate a full conversation.
        # It asks for a JSON output to ensure the response is structured and easy to parse.
        system_prompt = f"""
        You are an advanced simulator of social media conversations. Your task is to create a realistic comment thread in response to a rumor.

        RULES:
        1.  Generate a JSON array containing exactly {num_comments} comment objects.
        2.  The conversation should be dynamic and coherent. Comments should realistically reply to or reference the original rumor.
        3.  Simulate a variety of user personas: supporters, deniers, skeptics asking for proof, and neutral observers.
        4.  Each JSON object in the array MUST have the following keys: "username", "user_type" (e.g., 'supporter', 'denier', 'skeptic', 'neutral'), "comment_text", and "stance" ('support', 'deny', 'query', 'comment').
        5.  The tone should match the topic context: '{topic_context}'.
        """

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Generate the comment thread for this rumor: \"{rumor_text}\""}
        ]

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }

        # Requesting JSON mode from the API for reliable output
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
            
            if response.status_code == 200:
                print("✅ AI response received successfully.")
                response_data = response.json()
                # The actual content is a JSON string within the response, which we need to parse.
                content_string = response_data.get('choices', [{}])[0].get('message', {}).get('content', '{}')
                
                # The content might be inside a root key, like {"comments": [...]}. We need to find the list.
                parsed_content = json.loads(content_string)
                
                if isinstance(parsed_content, dict):
                    # Find the key that holds the list of comments
                    for key, value in parsed_content.items():
                        if isinstance(value, list):
                            print(f"✅ Successfully parsed {len(value)} comments.")
                            return value
                
                print("❌ Error: Parsed JSON does not contain a list of comments.")
                return []

            else:
                print(f"❌ API Error: {response.status_code} - {response.text}")
                return []

        except requests.exceptions.RequestException as e:
            print(f"❌ Network Error: Failed to connect to API. {e}")
            return []
        except json.JSONDecodeError:
            print(f"❌ Error: Failed to decode the AI's JSON response. Response was: {content_string}")
            return []
        except Exception as e:
            print(f"❌ An unexpected error occurred: {e}")
            return []


# --- Example Usage ---
if __name__ == "__main__":
    # The rumor you want to generate a comment section for.
    input_rumor = "Sources are reporting that the city's main bridge will be closed for emergency repairs for the next three days, starting tomorrow at 5 AM."

    # Initialize the simulator.
    simulator = AIConversationSimulator()

    # Generate the conversation thread.
    comment_thread = simulator.generate_thread(
        rumor_text=input_rumor, 
        num_comments=8, 
        topic_context="a local city news announcement"
    )

    # Display the generated comment section.
    if comment_thread:
        print("\n--- 🤖 Generated Comment Section 🤖 ---\n")
        for i, comment in enumerate(comment_thread, 1):
            print(f"#{i} User: {comment.get('username', 'N/A')} ({comment.get('user_type', 'N/A')})")
            print(f"   Stance: {comment.get('stance', 'N/A')}")
            print(f"   Comment: {comment.get('comment_text', 'N/A')}\n")
    else:
        print("\nCould not generate the comment thread. Please check your API key and network connection.")
