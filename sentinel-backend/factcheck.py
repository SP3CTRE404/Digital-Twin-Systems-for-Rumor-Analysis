"""
Fixed factcheck.py with correct ClaimBuster API endpoints
The API structure has changed - we need to use the correct endpoints
"""
from __future__ import annotations

import os
import json
from typing import Optional, Dict, List
from collections import Counter
import requests
import numpy as np

# Updated ClaimBuster API endpoints - the API structure has changed
CLAIMBUSTER_BASE_URL = "https://idir.uta.edu/claimbuster/api"
CLAIMBUSTER_SCORE_API = f"{CLAIMBUSTER_BASE_URL}/score/text"
CLAIMBUSTER_CHECK_API = f"{CLAIMBUSTER_BASE_URL}/factcheck"

def analyze_thread_veracity(rumor_text: str, comments: List[Dict] = None, api_key: Optional[str] = None) -> Dict:
    """
    Analyze the veracity of a rumor text (and optionally comments).
    """
    print(f"🔍 Starting fact-check analysis for: '{rumor_text[:100]}...'")
    
    # Analyze the main rumor text
    rumor_analysis = get_veracity_score(rumor_text, api_key)
    
    # If comments provided, analyze them too
    comment_analyses = []
    if comments:
        print(f"📝 Analyzing {len(comments)} comments...")
        for i, comment in enumerate(comments):
            if comment.get('text', '').strip():
                print(f"   - Comment {i+1}: '{comment['text'][:50]}...'")
                analysis = get_veracity_score(comment['text'], api_key)
                comment_analyses.append(analysis)
    
    # Combine analyses - weight rumor more heavily than comments
    if comment_analyses:
        comment_scores = [a['score'] for a in comment_analyses if a['confidence'] > 0]
        if comment_scores:
            avg_comment_score = np.mean(comment_scores)
            # Weight: 70% rumor, 30% comments
            combined_score = 0.7 * rumor_analysis['score'] + 0.3 * avg_comment_score
            combined_confidence = max(rumor_analysis['confidence'], np.mean([a['confidence'] for a in comment_analyses]))
        else:
            combined_score = rumor_analysis['score']
            combined_confidence = rumor_analysis['confidence']
    else:
        combined_score = rumor_analysis['score']
        combined_confidence = rumor_analysis['confidence']
    
    # Collect all sources
    all_sources = set(rumor_analysis['sources'])
    for analysis in comment_analyses:
        all_sources.update(analysis['sources'])
    
    result = {
        'rumor_veracity': {
            'score': float(combined_score),
            'confidence': float(combined_confidence),
        },
        'rumor_analysis': rumor_analysis,
        'comment_analyses': comment_analyses,
        'sources': list(all_sources),
        'analysis_summary': {
            'total_fact_checks': len([a for a in [rumor_analysis] + comment_analyses if a['confidence'] > 0]),
            'avg_confidence': float(combined_confidence)
        }
    }
    
    print(f"✅ Fact-check complete. Veracity score: {combined_score:.3f}, Confidence: {combined_confidence:.3f}")
    return result


def get_veracity_score(claim: str, api_key: Optional[str] = None, timeout_s: float = 15.0) -> Dict:
    """Get veracity score for a single claim using corrected ClaimBuster API"""
    
    if not claim or not claim.strip():
        print("⚠️ Empty claim provided")
        return _default_response("Empty claim")

    # Get API key from parameter or environment
    key = api_key or os.getenv("CLAIMBUSTER_API_KEY")
    
    if not key or key == "your_api_key_here":
        print("❌ ClaimBuster API key not configured")
        return _default_response("No API key configured")

    print(f"🔑 Using API key: {key[:8]}..." if len(key) > 8 else f"🔑 Using API key: {key}")
    
    headers = {
        'x-api-key': key,
        'Content-Type': 'application/json'
    }
    
    try:
        print(f"📡 Step 1: Getting claim score for '{claim[:100]}...'")
        
        # Method 1: Try POST request with JSON body (newer API format)
        score_payload = {
            'text': claim,
            'cid': '1'  # Channel ID - may be required
        }
        
        print(f"   Trying POST to: {CLAIMBUSTER_SCORE_API}")
        score_resp = requests.post(
            CLAIMBUSTER_SCORE_API,
            headers=headers,
            json=score_payload,
            timeout=timeout_s
        )
        
        print(f"   Status: {score_resp.status_code}")
        
        # If POST fails, try GET method (older API format)
        if score_resp.status_code == 404:
            print("   POST failed, trying GET method...")
            
            # Try alternative URLs
            alternative_urls = [
                f"https://idir.uta.edu/claimbuster/score/text/{requests.utils.quote(claim)}",
                f"https://idir.uta.edu/claimbuster/api/v2/score/text/{requests.utils.quote(claim)}",
                f"https://claimbuster.org/api/v2/score/text/{requests.utils.quote(claim)}"
            ]
            
            for url in alternative_urls:
                print(f"   Trying: {url}")
                try:
                    score_resp = requests.get(url, headers=headers, timeout=timeout_s)
                    print(f"   Status: {score_resp.status_code}")
                    if score_resp.status_code == 200:
                        break
                except Exception as e:
                    print(f"   Failed: {e}")
                    continue
        
        if score_resp.status_code == 401:
            print("❌ Authentication failed - check your API key")
            return _default_response("Authentication failed")
        elif score_resp.status_code == 429:
            print("❌ Rate limit exceeded")
            return _default_response("Rate limit exceeded")
        elif score_resp.status_code != 200:
            print(f"❌ Score API error: {score_resp.status_code}")
            print(f"   Response: {score_resp.text[:200]}...")
            # Fallback to keyword-based scoring
            return _keyword_based_fallback(claim)
        
        try:
            score_data = score_resp.json()
        except json.JSONDecodeError as e:
            print(f"❌ Failed to parse response as JSON: {e}")
            return _keyword_based_fallback(claim)
        
        print(f"   Response keys: {list(score_data.keys())}")
        
        # Parse the response - handle different API response formats
        claim_scores = []
        
        if 'results' in score_data and score_data['results']:
            for result in score_data['results']:
                if 'score' in result:
                    claim_scores.append(float(result['score']))
        elif 'score' in score_data:
            # Direct score response
            claim_scores.append(float(score_data['score']))
        elif isinstance(score_data, list):
            # Array response
            for item in score_data:
                if isinstance(item, dict) and 'score' in item:
                    claim_scores.append(float(item['score']))
        
        if not claim_scores:
            print("⚠️ No valid claim scores found in response")
            return _keyword_based_fallback(claim)
        
        avg_claim_score = np.mean(claim_scores)
        print(f"   Claim scores: {claim_scores}, Average: {avg_claim_score:.3f}")
        
        # For now, use claim score as final score since fact-check API might also be unavailable
        # In a production system, you'd also try to get fact-check results here
        
        final_score = min(1.0, avg_claim_score)
        confidence = min(0.8, avg_claim_score) if avg_claim_score > 0.1 else 0.2
        
        print(f"   Final score: {final_score:.3f}, Confidence: {confidence:.3f}")
        
        return {
            'score': float(final_score),
            'confidence': float(confidence),
            'sources': [],  # No fact-check sources available
            'stance_analysis': {},
            'threat_indicators': {
                'score': 1.0 - final_score,
                'factors': ['Based on claim analysis only']
            },
            'raw_data': {
                'claim_scores': claim_scores,
                'fact_check_ratings': [],
                'num_fact_checks': 0,
                'api_method': 'claim_score_only'
            }
        }
        
    except requests.exceptions.Timeout:
        print(f"❌ Request timeout after {timeout_s} seconds")
        return _keyword_based_fallback(claim)
    except requests.exceptions.ConnectionError:
        print("❌ Connection error - using fallback scoring")
        return _keyword_based_fallback(claim)
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return _keyword_based_fallback(claim)


def _keyword_based_fallback(claim: str) -> Dict:
    """Fallback keyword-based veracity scoring when API is unavailable"""
    print("🔄 Using keyword-based fallback scoring...")
    
    claim_lower = claim.lower()
    
    # High confidence false indicators
    false_keywords = [
        'microchip', 'microchips', '5g causes', 'vaccine magnet', 'plandemic',
        'flat earth', 'chemtrails', 'lizard people', 'fake moon landing',
        'covid hoax', 'bill gates control', 'depopulation agenda'
    ]
    
    # High confidence true indicators  
    true_keywords = [
        'vaccine effective', 'masks reduce transmission', 'earth is round',
        'climate change real', 'evolution scientific fact'
    ]
    
    # Neutral/uncertain indicators
    uncertain_keywords = [
        'might', 'could', 'possibly', 'allegedly', 'reportedly', 'claims',
        'unconfirmed', 'developing story'
    ]
    
    false_count = sum(1 for keyword in false_keywords if keyword in claim_lower)
    true_count = sum(1 for keyword in true_keywords if keyword in claim_lower)
    uncertain_count = sum(1 for keyword in uncertain_keywords if keyword in claim_lower)
    
    if false_count > 0:
        score = 0.1 + (false_count * 0.05)  # Very low veracity
        confidence = 0.7
        factors = ['Contains known misinformation patterns']
    elif true_count > 0:
        score = 0.8 + (true_count * 0.05)  # High veracity
        confidence = 0.7
        factors = ['Contains established factual patterns']
    elif uncertain_count > 0:
        score = 0.4  # Uncertain
        confidence = 0.3
        factors = ['Contains uncertainty indicators']
    else:
        # Default neutral for unknown claims
        score = 0.5
        confidence = 0.2
        factors = ['No clear indicators found']
    
    score = max(0.0, min(1.0, score))
    
    print(f"   Fallback score: {score:.3f}, Confidence: {confidence:.3f}")
    
    return {
        'score': float(score),
        'confidence': float(confidence),
        'sources': [],
        'stance_analysis': {},
        'threat_indicators': {
            'score': 1.0 - score,
            'factors': factors
        },
        'raw_data': {
            'claim_scores': [score],
            'fact_check_ratings': [],
            'num_fact_checks': 0,
            'api_method': 'keyword_fallback',
            'keyword_matches': {
                'false_indicators': false_count,
                'true_indicators': true_count, 
                'uncertain_indicators': uncertain_count
            }
        }
    }


def _default_response(reason: str) -> Dict:
    """Return default response when fact-checking fails"""
    return {
        'score': 0.5,
        'confidence': 0.0,
        'sources': [],
        'stance_analysis': {},
        'threat_indicators': {
            'score': 0.5,
            'factors': [reason]
        },
        'raw_data': {
            'claim_scores': [],
            'fact_check_ratings': [],
            'num_fact_checks': 0,
            'api_method': 'fallback'
        }
    }


def test_factcheck_api():
    """Test the fact-checking with different claims"""
    print("🧪 Testing ClaimBuster API with fallback...")
    
    test_claims = [
        "The sky is blue",
        "COVID vaccines contain microchips", 
        "The earth is flat",
        "I love eating ice cream"
    ]
    
    for claim in test_claims:
        print(f"\n--- Testing: '{claim}' ---")
        result = get_veracity_score(claim)
        print(f"Score: {result['score']:.3f}")
        print(f"Confidence: {result['confidence']:.3f}")
        print(f"Method: {result['raw_data'].get('api_method', 'unknown')}")


if __name__ == "__main__":
    test_factcheck_api()