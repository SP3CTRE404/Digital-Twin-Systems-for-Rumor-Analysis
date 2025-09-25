"""
Threat scoring module that combines harm and veracity analysis
"""
from typing import Dict, List
import numpy as np
from harm_scorer import EnhancedHarmfulnessScorer
from factcheck import analyze_thread_veracity

class ThreatScorer:
    """
    Analyzes the overall threat level of a rumor thread by combining:
    - Comment harmfulness analysis
    - Rumor veracity assessment
    - User interaction patterns
    - Propagation dynamics
    """
    
    def __init__(self, harm_scorer: EnhancedHarmfulnessScorer):
        """Initialize with a harmfulness scorer instance"""
        self.harm_scorer = harm_scorer
        
    def analyze_thread(self, 
                      rumor_text: str,
                      comments: List[Dict],
                      factcheck_api_key: str = None) -> Dict:
        """
        Analyze the complete threat profile of a rumor thread
        
        Args:
            rumor_text: The original rumor text
            comments: List of comment dictionaries
            factcheck_api_key: Optional API key for veracity checking
            
        Returns:
            Dict containing:
            - threat_score: Overall threat score [0,1]
            - threat_level: Categorical assessment
            - components: Detailed component scores
            - signals: List of threat signals detected
            - recommendations: Suggested actions
        """
        # Get harmfulness analysis
        harm_analysis = self.harm_scorer.analyze_conversation_thread(
            comments,
            topic_name=rumor_text[:50]
        )
        
        # Get veracity analysis
        veracity_analysis = analyze_thread_veracity(
            rumor_text,
            comments,
            factcheck_api_key
        )
        
        # Calculate component scores
        harm_score = harm_analysis['harmfulness_score']
        veracity_score = veracity_analysis['aggregate_scores']['threat_level']
        
        # Additional metrics from harm analysis
        engagement = harm_analysis['components'].get('engagement_score', 0.0)
        organization = harm_analysis['components'].get('organization_score_R_o', 0.0)
        emotional_intensity = harm_analysis['components'].get('emotional_intensity_score', 0.0)
        
        # Extract threat signals
        threat_signals = []
        
        # 1. Harmful and false content
        if harm_score > 0.6 and veracity_score > 0.6:
            threat_signals.append({
                'type': 'high_harm_false_content',
                'severity': 'critical',
                'description': 'Highly harmful content combined with likely false information'
            })
            
        # 2. Rapid amplification
        if engagement > 0.7:
            threat_signals.append({
                'type': 'rapid_amplification',
                'severity': 'high',
                'description': 'Content is being rapidly amplified and spread'
            })
            
        # 3. Coordinated behavior
        if organization > 0.7:
            threat_signals.append({
                'type': 'coordinated_behavior',
                'severity': 'high',
                'description': 'Potential coordinated behavior detected'
            })
            
        # 4. High emotional manipulation
        if emotional_intensity > 0.7:
            threat_signals.append({
                'type': 'emotional_manipulation',
                'severity': 'medium',
                'description': 'High level of emotional content and manipulation'
            })
            
        # Calculate overall threat score
        # Weights based on empirical importance
        weights = {
            'harm': 0.35,        # Direct harmful impact
            'veracity': 0.25,    # False information threat
            'engagement': 0.15,  # Spread potential
            'organization': 0.15, # Coordinated threat
            'emotion': 0.10      # Emotional manipulation
        }
        
        threat_score = (
            weights['harm'] * harm_score +
            weights['veracity'] * veracity_score +
            weights['engagement'] * engagement +
            weights['organization'] * organization +
            weights['emotion'] * emotional_intensity
        )
        
        # Ensure score is in [0,1]
        threat_score = max(0.0, min(1.0, threat_score))
        
        # Generate recommendations
        recommendations = self._generate_recommendations(
            threat_score,
            threat_signals,
            harm_analysis,
            veracity_analysis
        )
        
        return {
            'threat_score': float(threat_score),
            'threat_level': self._get_threat_level(threat_score),
            'components': {
                'harm_score': float(harm_score),
                'veracity_threat': float(veracity_score),
                'engagement_level': float(engagement),
                'coordination_level': float(organization),
                'emotional_intensity': float(emotional_intensity)
            },
            'signals': threat_signals,
            'recommendations': recommendations,
            'details': {
                'harm_analysis': harm_analysis,
                'veracity_analysis': veracity_analysis
            }
        }
    
    def _get_threat_level(self, score: float) -> str:
        """Convert numeric score to categorical threat level"""
        if score < 0.2:
            return "LOW"
        elif score < 0.4:
            return "MODERATE"
        elif score < 0.6:
            return "ELEVATED"
        elif score < 0.8:
            return "HIGH"
        else:
            return "CRITICAL"
            
    def _generate_recommendations(self,
                                threat_score: float,
                                signals: List[Dict],
                                harm_analysis: Dict,
                                veracity_analysis: Dict) -> List[Dict]:
        """Generate action recommendations based on threat analysis"""
        recommendations = []
        
        # High threat recommendations
        if threat_score > 0.7:
            recommendations.append({
                'priority': 'high',
                'action': 'immediate_intervention',
                'description': 'Immediate intervention required to contain threat',
                'details': [
                    'Monitor spread in real-time',
                    'Consider content removal',
                    'Alert relevant authorities if needed'
                ]
            })
            
        # Coordinated behavior response
        if any(s['type'] == 'coordinated_behavior' for s in signals):
            recommendations.append({
                'priority': 'high',
                'action': 'investigate_coordination',
                'description': 'Investigate potential coordinated behavior',
                'details': [
                    'Analyze user network patterns',
                    'Identify potential coordination hubs',
                    'Track similar narrative patterns'
                ]
            })
            
        # Emotional manipulation response
        if any(s['type'] == 'emotional_manipulation' for s in signals):
            recommendations.append({
                'priority': 'medium',
                'action': 'emotional_mitigation',
                'description': 'Address emotional manipulation',
                'details': [
                    'Deploy calming messaging',
                    'Promote factual discussion',
                    'Counter inflammatory content'
                ]
            })
            
        # Rapid spread response
        if any(s['type'] == 'rapid_amplification' for s in signals):
            recommendations.append({
                'priority': 'high',
                'action': 'contain_spread',
                'description': 'Contain rapid information spread',
                'details': [
                    'Implement sharing restrictions',
                    'Add friction to reshares',
                    'Deploy counter-narratives'
                ]
            })
            
        # False information response
        veracity_score = veracity_analysis['aggregate_scores']['overall_veracity']
        if veracity_score < 0.3:
            recommendations.append({
                'priority': 'medium',
                'action': 'fact_check_promotion',
                'description': 'Promote fact-checking information',
                'details': [
                    'Highlight fact-check results',
                    'Add warning labels',
                    'Provide authoritative sources'
                ]
            })
        
        return recommendations