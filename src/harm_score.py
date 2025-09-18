import os
import pandas as pd
import numpy as np
import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification
import json
from sklearn.preprocessing import MinMaxScaler
import warnings
from pathlib import Path
warnings.filterwarnings("ignore")

class EnhancedHarmfulnessScorer:
    """
    Enhanced Rumor Harmfulness Scoring System
    Uses both sentiment and stance detection models as described in RSK-T5 paper
    """
    
    def __init__(self,
                 sentiment_model_path: str = None,
                 stance_model_path: str = None):
        """Initialize with trained sentiment and stance models

        If paths are not provided, resolve to repository 'models/' directory
        (assumes this file is in src/ under the repo root).
        """
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        print(f"Using device: {self.device}")

        # Resolve default model paths relative to repository root (two levels up from src/)
        repo_root = Path(__file__).resolve().parents[1]
        if sentiment_model_path is None:
            sentiment_model_path = repo_root / 'models' / 'sentiment_model_3050'
        if stance_model_path is None:
            stance_model_path = repo_root / 'models' / 'stance_model_3050'

        sentiment_model_path = Path(sentiment_model_path)
        stance_model_path = Path(stance_model_path)

        # Load sentiment model
        self.sentiment_model = None
        if sentiment_model_path.exists():
            print(f"Loading sentiment model from: {sentiment_model_path}")
            try:
                self.sentiment_tokenizer = AutoTokenizer.from_pretrained(str(sentiment_model_path))
                self.sentiment_model = AutoModelForSequenceClassification.from_pretrained(str(sentiment_model_path)).to(self.device)
                self.sentiment_model.eval()
                self.id_to_sentiment = {int(k): v for k, v in self.sentiment_model.config.id2label.items()}
                print(f"[OK] Sentiment model loaded: {list(self.id_to_sentiment.values())}")
            except Exception as e:
                print(f"[ERROR] Error loading sentiment model: {e}")
                try:
                    files = list(sentiment_model_path.iterdir())
                    print("Model directory contents:")
                    for f in files:
                        print(f" - {f.name}")
                    if any(f.name.endswith('.safetensors') for f in files):
                        print("Note: model weights are in .safetensors format. Ensure the 'safetensors' package is installed (pip install safetensors).")
                except Exception:
                    pass
                self.sentiment_model = None

        # Load stance model
        self.stance_model = None
        if stance_model_path.exists():
            print(f"Loading stance model from: {stance_model_path}")
            try:
                self.stance_tokenizer = AutoTokenizer.from_pretrained(str(stance_model_path))
                self.stance_model = AutoModelForSequenceClassification.from_pretrained(str(stance_model_path)).to(self.device)
                self.stance_model.eval()

                # Load stance label mappings
                label_file = stance_model_path / 'label_mappings.json'
                if label_file.exists():
                    with open(label_file, 'r') as f:
                        label_info = json.load(f)
                        self.id_to_stance = {int(k): v for k, v in label_info['id_to_label'].items()}
                else:
                    self.id_to_stance = {int(k): v for k, v in self.stance_model.config.id2label.items()}

                self.id_to_stance = {int(k): v for k, v in self.stance_model.config.id2label.items()}
                print(f"[OK] Stance model loaded: {list(self.id_to_stance.values())}")
            except Exception as e:
                print(f"[ERROR] Error loading stance model: {e}")
                try:
                    files = list(stance_model_path.iterdir())
                    print("Model directory contents:")
                    for f in files:
                        print(f" - {f.name}")
                    if any(f.name.endswith('.safetensors') for f in files):
                        print("Note: model weights are in .safetensors format. Ensure the 'safetensors' package is installed (pip install safetensors).")
                except Exception:
                    pass
                self.stance_model = None

        # Fallback to rule-based methods if models not available
        if self.sentiment_model is None:
            print("[WARN] Using VADER sentiment analysis as fallback")
            from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
            self.vader_analyzer = SentimentIntensityAnalyzer()

        if self.stance_model is None:
            print("[WARN] Using rule-based stance detection as fallback")
    
    def predict_sentiment(self, texts):
        """Predict sentiment using trained model or VADER fallback"""
        if isinstance(texts, str):
            texts = [texts]
        
        if self.sentiment_model is not None:
            try:
                inputs = self.sentiment_tokenizer(
                    texts, 
                    padding=True, 
                    truncation=True, 
                    max_length=256, 
                    return_tensors='pt'
                ).to(self.device)
                
                with torch.no_grad():
                    logits = self.sentiment_model(**inputs).logits
                
                predictions = logits.argmax(dim=-1).cpu().numpy()
                return [self.id_to_sentiment[int(pred)] for pred in predictions]
            except Exception as e:
                print(f"Error in sentiment prediction: {e}")
                return ['neutral'] * len(texts)
        else:
            # VADER fallback
            sentiments = []
            for text in texts:
                if pd.isna(text) or not isinstance(text, str):
                    sentiments.append('neutral')
                    continue
                
                scores = self.vader_analyzer.polarity_scores(text)
                compound = scores['compound']
                
                if compound >= 0.05:
                    sentiments.append('positive')
                elif compound <= -0.05:
                    sentiments.append('negative')
                else:
                    sentiments.append('neutral')
            
            return sentiments
    
    def predict_stance(self, texts):
        """Predict stance using trained model or rule-based fallback"""
        if isinstance(texts, str):
            texts = [texts]
        
        if self.stance_model is not None:
            try:
                inputs = self.stance_tokenizer(
                    texts,
                    padding=True,
                    truncation=True,
                    max_length=256,
                    return_tensors='pt'
                ).to(self.device)
                
                with torch.no_grad():
                    logits = self.stance_model(**inputs).logits
                
                predictions = logits.argmax(dim=-1).cpu().numpy()
                return [self.id_to_stance[int(pred)] for pred in predictions]
            except Exception as e:
                print(f"Error in stance prediction: {e}")
                return ['comment'] * len(texts)
        else:
            # Rule-based fallback
            stances = []
            for text in texts:
                if pd.isna(text) or not isinstance(text, str):
                    stances.append('comment')
                    continue
                
                text_lower = text.lower()
                
                # Simple rule-based stance detection
                if any(word in text_lower for word in ['agree', 'true', 'correct', 'support', 'yes', 'definitely']):
                    stances.append('support')
                elif any(word in text_lower for word in ['disagree', 'false', 'wrong', 'fake', 'no', 'deny']):
                    stances.append('deny')
                elif any(word in text_lower for word in ['?', 'question', 'verify', 'confirm', 'sure', 'really']):
                    stances.append('query')
                else:
                    stances.append('comment')
            
            return stances
    
    def calculate_rumor_sentimentality(self, sentiments):
        """Calculate R_c: intensity of negative emotions"""
        sentiment_counts = pd.Series(sentiments).value_counts()
        
        negative_count = sentiment_counts.get('negative', 0)
        positive_count = sentiment_counts.get('positive', 0)
        total_emotional = negative_count + positive_count
        
        if total_emotional == 0:
            return 0.0
        
        # Higher score = more negative sentiment (more harmful)
        R_c = negative_count / total_emotional
        return R_c
    
    def calculate_rumor_approval(self, stances):
        """Calculate R_r: support level for rumor"""
        stance_counts = pd.Series(stances).value_counts()
        
        support_count = stance_counts.get('support', 0)
        deny_count = stance_counts.get('deny', 0)
        query_count = stance_counts.get('query', 0)
        
        total_stance = support_count + deny_count + query_count
        
        if total_stance == 0:
            return 0.0
        
        # Higher score = more support (potentially more harmful)
        R_r = support_count / total_stance
        return R_r
    
    def calculate_organization_score(self, comments_df):
        """Calculate R_o: organization/coordination level"""
        if len(comments_df) < 2:
            return 0.0
        
        # User activity concentration
        if 'user.handle' in comments_df.columns:
            user_activity = comments_df['user.handle'].value_counts()
            unique_users = len(user_activity)
            total_comments = len(comments_df)
            
            # Engagement intensity
            engagement_intensity = total_comments / unique_users
            
            # Top user dominance
            top_user_ratio = user_activity.iloc[0] / total_comments if len(user_activity) > 0 else 0
            
            # Combined organization score
            R_o = min((top_user_ratio * 0.6) + (min(engagement_intensity / 5.0, 1.0) * 0.4), 1.0)
        else:
            # Fallback: assume moderate organization
            R_o = 0.3
        
        return R_o
    
    def calculate_propagation_metrics(self, comments_df, sentiments, stances):
        """Calculate additional propagation and engagement metrics"""
        metrics = {}
        
        # Basic counts
        metrics['total_comments'] = len(comments_df)
        metrics['unique_users'] = comments_df['user.handle'].nunique() if 'user.handle' in comments_df.columns else len(comments_df)
        
        # Engagement metrics
        metrics['engagement_intensity'] = metrics['total_comments'] / max(metrics['unique_users'], 1)
        
        # Diversity metrics (entropy)
        sentiment_counts = pd.Series(sentiments).value_counts()
        stance_counts = pd.Series(stances).value_counts()
        
        metrics['sentiment_entropy'] = self._calculate_entropy(sentiment_counts)
        metrics['stance_entropy'] = self._calculate_entropy(stance_counts)
        
        # Controversy indicators
        metrics['sentiment_diversity'] = len(sentiment_counts)
        metrics['stance_diversity'] = len(stance_counts)
        
        # Emotional intensity
        negative_ratio = sentiment_counts.get('negative', 0) / len(sentiments)
        positive_ratio = sentiment_counts.get('positive', 0) / len(sentiments)
        metrics['emotional_intensity'] = negative_ratio + positive_ratio  # Non-neutral emotions
        
        # Opposition ratio
        support_ratio = stance_counts.get('support', 0) / len(stances)
        deny_ratio = stance_counts.get('deny', 0) / len(stances)
        metrics['opposition_balance'] = min(support_ratio, deny_ratio) * 2  # Balanced = more controversial
        
        return metrics
    
    def _calculate_entropy(self, counts):
        """Calculate entropy for diversity measurement"""
        if len(counts) == 0 or counts.sum() == 0:
            return 0.0
        
        probabilities = counts / counts.sum()
        entropy = -np.sum(probabilities * np.log2(probabilities + 1e-10))
        return entropy
    
    def calculate_harmfulness_score(self, rumor_text, comments_df):
        """
        Calculate comprehensive harmfulness score using RSK-T5 methodology
        
        Args:
            rumor_text (str): Original rumor text
            comments_df (pd.DataFrame): Comments dataframe
            
        Returns:
            dict: Detailed harmfulness analysis
        """
        # Validation
        if len(comments_df) == 0:
            return {
                'harmfulness_score': 0.0,
                'harmfulness_score_normalized': 0.0,
                'components': {},
                'comment_count': 0,
                'interpretation': 'No comments to analyze'
            }
        
        # Clean data
        comments_df = comments_df.dropna(subset=['text']).copy()
        texts = comments_df['text'].tolist()
        
        print(f"Analyzing {len(texts)} comments for harmfulness...")
        
        # Predict sentiment and stance using trained models
        print("Predicting sentiments...")
        sentiments = self.predict_sentiment(texts)
        
        print("Predicting stances...")
        stances = self.predict_stance(texts)
        
        # Add predictions to dataframe
        comments_df['sentiment_pred'] = sentiments
        comments_df['stance_pred'] = stances
        
        # Calculate core RSK-T5 components
        print("Calculating harmfulness components...")
        
        # R_c: Rumor sentimentality (negative emotion intensity)
        R_c = self.calculate_rumor_sentimentality(sentiments)
        
        # R_r: Rumor approval (support level)
        R_r = self.calculate_rumor_approval(stances)
        
        # R_o: Organization score
        R_o = self.calculate_organization_score(comments_df)
        
        # Additional propagation metrics
        prop_metrics = self.calculate_propagation_metrics(comments_df, sentiments, stances)
        
        # Normalize additional metrics to [0,1] scale
        engagement_score = min(prop_metrics['engagement_intensity'] / 5.0, 1.0)
        controversy_score = min((prop_metrics['sentiment_entropy'] + prop_metrics['stance_entropy']) / 4.0, 1.0)
        emotional_intensity_score = prop_metrics['emotional_intensity']
        opposition_score = prop_metrics['opposition_balance']
        
        # Component weights (based on RSK-T5 paper and empirical importance)
        weights = {
            'sentimentality': 0.25,      # Negative emotions (R_c)
            'approval': 0.25,            # Support for rumor (R_r)  
            'organization': 0.20,        # Coordinated spreading (R_o)
            'engagement': 0.10,          # Engagement intensity
            'controversy': 0.10,         # Diverse reactions (indicates debate)
            'emotional_intensity': 0.05, # Overall emotional response
            'opposition': 0.05           # Balanced opposition (controversial)
        }
        
        # Calculate weighted harmfulness score
        harmfulness_components = {
            'rumor_sentimentality_R_c': R_c,
            'rumor_approval_R_r': R_r,
            'organization_score_R_o': R_o,
            'engagement_score': engagement_score,
            'controversy_score': controversy_score,
            'emotional_intensity_score': emotional_intensity_score,
            'opposition_score': opposition_score,
            'total_comments': len(comments_df),
            'unique_users': prop_metrics['unique_users'],
            'sentiment_distribution': pd.Series(sentiments).value_counts().to_dict(),
            'stance_distribution': pd.Series(stances).value_counts().to_dict()
        }
        
        # Final weighted score
        final_score = (
            weights['sentimentality'] * R_c +
            weights['approval'] * R_r +
            weights['organization'] * R_o +
            weights['engagement'] * engagement_score +
            weights['controversy'] * controversy_score +
            weights['emotional_intensity'] * emotional_intensity_score +
            weights['opposition'] * opposition_score
        )
        
        # Normalize to 0-100 scale for interpretability
        harmfulness_score_normalized = final_score * 100
        
        return {
            'harmfulness_score': final_score,
            'harmfulness_score_normalized': harmfulness_score_normalized,
            'components': harmfulness_components,
            'comment_count': len(comments_df),
            'interpretation': self._interpret_score(harmfulness_score_normalized),
            'model_info': {
                'sentiment_model_available': self.sentiment_model is not None,
                'stance_model_available': self.stance_model is not None
            }
        }
    
    def _interpret_score(self, normalized_score):
        """Interpret harmfulness score with detailed explanation"""
        if normalized_score < 15:
            return "Very Low (0-15): Minimal harm potential. Limited negative impact expected."
        elif normalized_score < 30:
            return "Low (15-30): Some concern warranted. Monitor for escalation."
        elif normalized_score < 45:
            return "Moderate (30-45): Significant potential for harm. Consider intervention."
        elif normalized_score < 60:
            return "High (45-60): High harm potential. Active monitoring recommended."
        elif normalized_score < 75:
            return "Very High (60-75): Serious threat. Immediate attention needed."
        else:
            return "Critical (75-100): Extreme harm potential. Urgent intervention required."
    
    def analyze_conversation_thread(self, conversation_data, topic_name="unknown"):
        """Analyze complete conversation thread"""
        if isinstance(conversation_data, list):
            df = pd.DataFrame(conversation_data)
        elif isinstance(conversation_data, pd.DataFrame):
            df = conversation_data.copy()
        else:
            raise ValueError("conversation_data must be list or DataFrame")
        
        if len(df) == 0:
            return {"error": "No valid conversation data provided"}
        
        # Find source rumor
        source_rumor = ""
        if 'is_source_rumor' in df.columns:
            source_posts = df[df['is_source_rumor'] == True]
            if len(source_posts) > 0:
                source_rumor = source_posts.iloc[0]['text']
        
        if not source_rumor and len(df) > 0:
            source_rumor = df.iloc[0]['text']
        
        # Calculate harmfulness
        result = self.calculate_harmfulness_score(source_rumor, df)
        result['topic'] = topic_name
        result['source_rumor'] = source_rumor[:200] + "..." if len(source_rumor) > 200 else source_rumor
        
        return result

def test_enhanced_harmfulness_system():
    """Test the enhanced harmfulness scoring system"""
    
    print("Testing Enhanced Harmfulness Scoring System")
    print("=" * 60)
    
    # Initialize scorer
    scorer = EnhancedHarmfulnessScorer()
    
    # Test conversation with various stances and sentiments
    test_conversation = [
        {
            'text': 'BREAKING: Major chemical spill at downtown facility, evacuate immediately!',
            'user.handle': 'AlertCitizen',
            'is_source_rumor': True
        },
        {
            'text': 'Oh my god this is terrifying! Everyone needs to get out now!',
            'user.handle': 'PanickedResident',
        },
        {
            'text': 'I agree, this looks very serious. Stay safe everyone.',
            'user.handle': 'ConcernedNeighbor',
        },
        {
            'text': 'This is completely fake news! No official sources confirm this.',
            'user.handle': 'SkepticalCitizen',
        },
        {
            'text': 'STOP spreading panic! This is misinformation!',
            'user.handle': 'TruthSeeker',
        },
        {
            'text': 'Can someone verify this with local authorities?',
            'user.handle': 'ResponsiblePerson',
        },
        {
            'text': 'I heard sirens but not sure if related. Anyone else notice?',
            'user.handle': 'LocalResident',
        },
        {
            'text': 'This makes me so angry! Why spread false alarms?',
            'user.handle': 'AngryPerson',
        }
    ]
    
    # Analyze the conversation
    result = scorer.analyze_conversation_thread(test_conversation, "chemical_spill_alert")
    
    print(f"Topic: {result['topic']}")
    print(f"Source Rumor: {result['source_rumor']}")
    print(f"\nHARMFULNESS ANALYSIS:")
    print(f"Raw Score: {result['harmfulness_score']:.3f}")
    print(f"Normalized Score: {result['harmfulness_score_normalized']:.1f}/100")
    print(f"Interpretation: {result['interpretation']}")
    print(f"Total Comments: {result['comment_count']}")
    
    print(f"\nCOMPONENT BREAKDOWN:")
    components = result['components']
    print(f"• Sentimentality (R_c): {components['rumor_sentimentality_R_c']:.3f}")
    print(f"• Approval (R_r): {components['rumor_approval_R_r']:.3f}")
    print(f"• Organization (R_o): {components['organization_score_R_o']:.3f}")
    print(f"• Engagement: {components['engagement_score']:.3f}")
    print(f"• Controversy: {components['controversy_score']:.3f}")
    
    print(f"\nDISTRIBUTIONS:")
    print(f"Sentiments: {components['sentiment_distribution']}")
    print(f"Stances: {components['stance_distribution']}")
    
    print(f"\nMODEL STATUS:")
    model_info = result['model_info']
    print(f"Sentiment Model: {'✅ Available' if model_info['sentiment_model_available'] else '❌ Using fallback'}")
    print(f"Stance Model: {'✅ Available' if model_info['stance_model_available'] else '❌ Using fallback'}")
    
    return result

if __name__ == "__main__":
    test_enhanced_harmfulness_system()