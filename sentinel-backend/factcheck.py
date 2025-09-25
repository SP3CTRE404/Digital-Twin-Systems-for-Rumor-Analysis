from __future__ import annotations

import os
import json
from typing import Optional, Dict, List
from collections import Counter
import requests
import numpy as np

# ClaimBuster API endpoints
CLAIMBUSTER_BASE_URL = "https://idir.uta.edu/claimbuster"
CLAIMBUSTER_SCORE_API = f"{CLAIMBUSTER_BASE_URL}/score/text/"
CLAIMBUSTER_CHECK_API = f"{CLAIMBUSTER_BASE_URL}/factcheck/text/"

def analyze_thread_veracity(thread: List[Dict], api_key: Optional[str] = None) -> Dict:
    """Analyze the veracity of a thread of comments.
    
    Args:
        thread (List[Dict]): List of comment objects. Each comment should have 'text' key.
        api_key (Optional[str], optional): ClaimBuster API key. Defaults to None.
    
    Returns:
        Dict: Contains aggregated veracity analysis with:
            - overall_score: float [0,1] for thread veracity
            - confidence: float [0,1] for analysis confidence
            - claims: list of analyzed claims with scores
            - sources: set of fact-check sources
            - stance_distribution: distribution of stances across claims
            - threat_assessment: aggregated threat indicators
    """
    # Default response for empty thread
    if not thread:
        return {
            'overall_score': 0.5,
            'confidence': 0.0,
            'claims': [],
            'sources': set(),
            'stance_distribution': {},
            'threat_assessment': {
                'score': 0.0,
                'factors': ['Empty thread']
            }
        }
    
    # Analyze each comment
    claim_analyses = []
    all_sources = set()
    all_stances = Counter()
    all_threat_factors = []
    max_threat_score = 0.0
    
    for comment in thread:
        # Skip empty comments
        if not comment.get('text', '').strip():
            continue
            
        # Analyze comment text
        analysis = get_veracity_score(comment['text'], api_key)
        
        # Track sources and stances
        all_sources.update(analysis['sources'])
        for stance, weight in analysis['stance_analysis'].items():
            all_stances[stance] += weight
            
        # Track threat factors and max threat score
        threat_score = analysis['threat_indicators']['score']
        max_threat_score = max(max_threat_score, threat_score)
        
        if threat_score > 0.5:  # Only track significant threats
            all_threat_factors.extend(analysis['threat_indicators']['factors'])
        
        # Store analysis if it has non-zero confidence
        if analysis['confidence'] > 0:
            claim_analyses.append({
                'text': comment['text'],
                'score': analysis['score'],
                'confidence': analysis['confidence']
            })
    
    # Calculate aggregate scores
    if claim_analyses:
        # Weight scores by confidence
        weighted_scores = [a['score'] * a['confidence'] for a in claim_analyses]
        total_confidence = sum(a['confidence'] for a in claim_analyses)
        
        if total_confidence > 0:
            overall_score = sum(weighted_scores) / total_confidence
            # Scale confidence by number of claims analyzed
            confidence = min(1.0, total_confidence / len(thread))
        else:
            overall_score = 0.5
            confidence = 0.0
    else:
        overall_score = 0.5
        confidence = 0.0
    
    # Normalize stance distribution
    total_stance_weight = sum(all_stances.values())
    stance_distribution = {
        stance: count/total_stance_weight 
        for stance, count in all_stances.items()
    } if total_stance_weight > 0 else {}
    
    # Aggregate threat assessment
    thread_threat_score = max_threat_score  # Use max threat seen in thread
    
    # Deduplicate and prioritize threat factors
    unique_factors = list(dict.fromkeys(all_threat_factors))  # Preserve order
    
    return {
        'overall_score': float(overall_score),
        'confidence': float(confidence),
        'claims': claim_analyses,
        'sources': list(all_sources),
        'stance_distribution': stance_distribution,
        'threat_assessment': {
            'score': float(thread_threat_score),
            'factors': unique_factors[:5]  # Limit to top 5 factors
        }
    }


def get_veracity_score(claim: str, api_key: Optional[str] = None, timeout_s: float = 6.0) -> Dict:
    if not claim or not claim.strip():
        return {
            'score': 0.5,
            'confidence': 0.0,
            'sources': [],
            'stance_analysis': {},
            'threat_indicators': {'score': 0.0, 'factors': []}
        }

    # Read from function arg or environment variable
    key = api_key or os.getenv("CLAIMBUSTER_API_KEY")
    if not key or key == "your_api_key_here":
        print("Warning: ClaimBuster API key not configured")
        return {
            'score': 0.5,
            'confidence': 0.0,
            'sources': [],
            'stance_analysis': {},
            'threat_indicators': {'score': 0.0, 'factors': ['No fact-checking API configured']}
        }

    headers = {'x-api-key': key}
    
    try:
        # First get claim score
        score_resp = requests.get(
            CLAIMBUSTER_SCORE_API + claim,
            headers=headers,
            timeout=timeout_s
        )
        
        if score_resp.status_code != 200:
            return {
                'score': 0.5,
                'confidence': 0.0,
                'sources': [],
                'stance_analysis': {},
                'threat_indicators': {'score': 0.0, 'factors': ['API error']}
            }
        
        score_data = score_resp.json()
        if not score_data or 'results' not in score_data:
            return {
                'score': 0.5,
                'confidence': 0.0,
                'sources': [],
                'stance_analysis': {},
                'threat_indicators': {'score': 0.0, 'factors': ['No claim score available']}
            }
        
        # Get claim score
        claim_scores = [result['score'] for result in score_data['results']]
        if not claim_scores:
            return {
                'score': 0.5,
                'confidence': 0.0,
                'sources': [],
                'stance_analysis': {},
                'threat_indicators': {'score': 0.0, 'factors': ['No claim scores found']}
            }
            
        avg_claim_score = np.mean(claim_scores)
        
        # Get fact checks
        check_resp = requests.get(
            CLAIMBUSTER_CHECK_API + claim,
            headers=headers,
            timeout=timeout_s
        )
        
        if check_resp.status_code != 200:
            # Fallback to using claim score
            normalized_score = min(1.0, avg_claim_score)
            return {
                'score': normalized_score,
                'confidence': min(1.0, avg_claim_score),
                'sources': [],
                'stance_analysis': {'claim_based': 1.0},
                'threat_indicators': {
                    'score': 1.0 - normalized_score,
                    'factors': ['Based only on claim analysis']
                }
            }
        
        check_data = check_resp.json()
        if not check_data or 'results' not in check_data or not check_data['results']:
            # Fallback to using claim score
            normalized_score = min(1.0, avg_claim_score)
            return {
                'score': normalized_score,
                'confidence': min(1.0, avg_claim_score),
                'sources': [],
                'stance_analysis': {'claim_based': 1.0},
                'threat_indicators': {
                    'score': 1.0 - normalized_score,
                    'factors': ['No fact-checks found']
                }
            }
            
        # Extract ratings and sources
        ratings = []
        sources = set()
        stances = Counter()
        
        for fact_check in check_data['results']:
            rating = str(fact_check.get('rating', '')).lower()
            source = fact_check.get('source', {}).get('name', 'Unknown')
            sources.add(source)
            
            # Convert rating to numeric score
            if any(word in rating for word in ['true', 'correct', 'accurate']):
                ratings.append(1.0)
                stances['support'] += 1
            elif any(word in rating for word in ['false', 'fake', 'incorrect']):
                ratings.append(0.0)
                stances['deny'] += 1
            elif any(word in rating for word in ['mixed', 'partial']):
                ratings.append(0.5)
                stances['neutral'] += 1
            else:
                ratings.append(0.5)
                stances['unclear'] += 1
                
        # Calculate aggregate score using both claim score and fact-check ratings
        if ratings:
            fact_check_score = np.mean(ratings)
            # Weight fact-check score higher than claim score
            score = 0.7 * fact_check_score + 0.3 * min(1.0, avg_claim_score)
        else:
            score = min(1.0, avg_claim_score)
        
        # Calculate confidence based on number of fact checks and claim score strength
        fact_check_confidence = len(ratings) / 5.0  # Normalize by expected number of reviews
        claim_confidence = min(1.0, avg_claim_score)
        confidence = 0.7 * fact_check_confidence + 0.3 * claim_confidence
        confidence = min(confidence, 1.0)  # Cap at 1.0
        
        # Analyze stance distribution
        total_stances = sum(stances.values())
        stance_analysis = {
            stance: count/total_stances 
            for stance, count in stances.items()
        } if total_stances > 0 else {'claim_based': 1.0}
        
        # Calculate threat indicators
        threat_score = 0.0
        threat_factors = []
        
        # Factor 1: Conflicting fact-checks
        if len(set(ratings)) > 1:
            threat_score += 0.3
            threat_factors.append("Conflicting fact-check results")
            
        # Factor 2: High false rating ratio
        false_ratio = ratings.count(0.0) / len(ratings) if ratings else 0
        if false_ratio > 0.5:
            threat_score += 0.3
            threat_factors.append("Multiple false ratings")
            
        # Factor 3: Limited fact-checks but high claim score
        if len(ratings) < 3 and avg_claim_score > 0.7:
            threat_score += 0.2
            threat_factors.append("High claim score with limited fact-checking")
            
        # Factor 4: High stance diversity
        if len(stance_analysis) > 2:
            threat_score += 0.2
            threat_factors.append("High stance diversity in fact-checks")
        
        return {
            'score': float(score),
            'confidence': float(confidence),
            'sources': list(sources),
            'stance_analysis': stance_analysis,
            'threat_indicators': {
                'score': float(threat_score),
                'factors': threat_factors
            }
        }
        
    except requests.exceptions.RequestException as e:
        print(f"API request failed: {e}")
        return {
            'score': 0.5,
            'confidence': 0.0,
            'sources': [],
            'stance_analysis': {},
            'threat_indicators': {'score': 0.0, 'factors': ['API connection error']}
        }
    except Exception as e:
        print(f"Error processing fact check response: {e}")
        return {
            'score': 0.5,
            'confidence': 0.0,
            'sources': [],
            'stance_analysis': {},
            'threat_indicators': {'score': 0.0, 'factors': ['Internal processing error']}
        }