from typing import Dict, List
import os
import json
import requests
import random
from dotenv import load_dotenv
from pathlib import Path

dotenv_path = Path(__file__).resolve().parent.parent / '.env'
load_dotenv(dotenv_path)

class AdvancedSimulator:
    def __init__(self):
        self.api_key = os.getenv('GEMINI_API_KEY')
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY environment variable not set. This is required.")
       
        self.api_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-preview-05-20:generateContent?key={self.api_key}"

    def generate_thread(self, rumor_text: str, topic_context: str = "a breaking news event") -> List[Dict]:
        total_comments = 20

        num_supporters = random.randint(1, total_comments - 2)
        num_deniers = random.randint(1, total_comments - num_supporters - 1)
        num_skeptics = total_comments - num_supporters - num_deniers
        
        system_prompt = f"""
        You are an advanced simulator of a social media comment section. Your task is to create a realistic and coherent conversation thread based on a rumor.
        RULES:
        1.  Your entire output MUST be a single, valid JSON object that adheres to the provided schema.
        2.  The conversation must be dynamic. Comments should reply to the original post or to each other, creating a natural flow. Do not just list disconnected opinions.
        3.  You MUST simulate EXACTLY the following distribution of user stances:
            - **{num_supporters} people IN FAVOR of the rumor.** Their "user_type" should be 'supporter' and "stance" should be 'support'.
            - **{num_deniers} people AGAINST the rumor.** Their "user_type" should be 'denier' and "stance" should be 'deny'.
            - **{num_skeptics} NEUTRAL people asking for facts or sources.** Their "user_type" should be 'skeptic' and "stance" should be 'query'.
        4.  The tone of the conversation should match the topic context: '{topic_context}'.
        """ 
        user_prompt = f"Generate the comment thread for this rumor: \"{rumor_text}\""

        headers = { "Content-Type": "application/json" }

        json_schema = {
            "type": "OBJECT",
            "properties": {
                "comments": {
                    "type": "ARRAY",
                    "items": {
                        "type": "OBJECT",
                        "properties": {
                            "username": {"type": "STRING"},
                            "user_type": {"type": "STRING"},
                            "comment_text": {"type": "STRING"},
                            "stance": {"type": "STRING"}
                        },
                        "required": ["username", "user_type", "comment_text", "stance"]
                    }
                }
            },
            "required": ["comments"]
        }

        payload = {
            "contents": [{"parts": [{"text": user_prompt}]}],
            "systemInstruction": {"parts": [{"text": system_prompt}]},
            "generationConfig": {
                "responseMimeType": "application/json",
                "responseSchema": json_schema,
                "temperature": 0.9,
                "maxOutputTokens": 3000,
            }
        }

        print(f"\n🚀 Sending request to Gemini API for a thread of {total_comments} comments...")
        print(f"   Distribution: {num_supporters} supporters, {num_deniers} deniers, {num_skeptics} skeptics.")
        
        try:
            response = requests.post(self.api_url, headers=headers, json=payload, timeout=120)
            response.raise_for_status()

            print("✅ AI response received from Gemini.")
            # Updated response parsing for Gemini
            content_string = response.json()['candidates'][0]['content']['parts'][0]['text']
            comment_list = json.loads(content_string).get("comments", [])

            if isinstance(comment_list, list) and comment_list:
                print(f"✅ Successfully parsed {len(comment_list)} comments.")
                return comment_list
            else:
                print("❌ Warning: Gemini returned a valid but empty or malformed 'comments' list.")
                return []

        except requests.exceptions.HTTPError as e:
            print(f"❌ API Error: {e.response.status_code} - {e.response.text}")
        except requests.exceptions.RequestException as e:
            print(f"❌ Network Error: Failed to connect to API. {e}")
        except json.JSONDecodeError:
            print("❌ JSON Decode Error: Failed to parse the AI's response.")
        except (KeyError, IndexError):
            print("❌ Response Structure Error: Unexpected format from Gemini API.")
        return []