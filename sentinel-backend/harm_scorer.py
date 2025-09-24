"""
Fixed Enhanced Rumor Harmfulness Scoring System with proper model path resolution
"""
import os
import pandas as pd
import numpy as np
import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification
import json
from pathlib import Path
import warnings
warnings.filterwarnings("ignore")

class EnhancedHarmfulnessScorer:
    """
    Enhanced Rumor Harmfulness Scoring System based on RSK-T5 methodology
    Uses both sentiment and stance detection models
    """
    
    def __init__(self, sentiment_model_path=None, stance_model_path=None):
        """Initialize with trained sentiment and stance models"""
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        print(f"Using device: {self.device}")
        
        # Resolve model paths
        self.sentiment_path = self._resolve_model_path(sentiment_model_path, 'sentiment_model_3050')
        self.stance_path = self._resolve_model_path(stance_model_path, 'stance_model_3050')
        
        print(f"Initializing HarmfulnessScorer with:")
        print(f"- Sentiment model path: {self.sentiment_path}")
        print(f"- Stance model path: {self.stance_path}")
        
        # Load models
        self._load_sentiment_model()
        self._load_stance_model()
        
        # Initialize fallbacks if models fail to load
        if self.sentiment_model is None:
            print("⚠️ Using VADER sentiment analysis as fallback")
            try:
                from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
                self.vader_analyzer = SentimentIntensityAnalyzer()
            except ImportError:
                print("❌ VADER not available, using rule-based sentiment")
                self.vader_analyzer = None
        
        if self.stance_model is None:
            print("⚠️ Using rule-based stance detection as fallback")
    
    def _resolve_model_path(self, provided_path, model_name):
        """Resolve model path with multiple fallback strategies"""
        
        # Strategy 1: Use provided path if it exists
        if provided_path and os.path.exists(provided_path):
            return provided_path
        
        # Strategy 2: Check environment variables
        env_key = 'STANCE_MODEL_PATH' if 'stance' in model_name else 'SENTIMENT_MODEL_PATH'
        env_path = os.getenv(env_key)
        if env_path and os.path.exists(env_path):
            return env_path
        
        # Strategy 3: Look in common locations relative to this file
        current_dir = Path(__file__).parent
        
        # Check relative to backend directory
        possible_paths = [
            current_dir / '..' / 'models' / model_name,
            current_dir / 'models' / model_name,
            current_dir / '..' / '..' / 'models' / model_name,
            Path(model_name),  # If it's already a full path
        ]
        
        for path in possible_paths:
            if path.exists() and path.is_dir():
                return str(path.absolute())
        
        # Strategy 4: Search in system paths
        for search_dir in ['/app/models', '/models', os.path.expanduser('~/models')]:
            candidate = Path(search_dir) / model_name
            if candidate.exists():
                return str(candidate)
        
        print(f"❌ Could not find model directory: {model_name}")
        print(f"Searched paths: {[str(p) for p in possible_paths]}")
        return None
    
    def _load_sentiment_model(self):
        """Load sentiment analysis model"""
        self.sentiment_model = None
        self.sentiment_tokenizer = None
        self.id_to_sentiment = {}
        
        if not self.sentiment_path or not os.path.exists(self.sentiment_path):
            print(f"❌ Sentiment model path not found: {self.sentiment_path}")
            return
        
        try:
            print(f"Loading sentiment model from: {self.sentiment_path}")
            self.sentiment_tokenizer = AutoTokenizer.from_pretrained(self.sentiment_path)
            self.sentiment_model = AutoModelForSequenceClassification.from_pretrained(
                self.sentiment_path
            ).to(self.device)
            self.sentiment_model.eval()
            
            # Load label mappings
            if hasattr(self.sentiment_model.config, 'id2label'):
                self.id_to_sentiment = {
                    int(k): v for k, v in self.sentiment_model.config.id2label.items()
                }
            else:
                # Default mapping if not available
                self.id_to_sentiment = {0: 'negative', 1: 'neutral', 2: 'positive'}
            
            print(f"✅ Sentiment model loaded successfully")
            print(f"   Labels: {list(self.id_to_sentiment.values())}")
            
        except Exception as e:
            print(f"❌ Error loading sentiment model: {str(e)}")
            self.sentiment_model = None
            self.sentiment_tokenizer = None
    
    def _load_stance_model(self):
        """Load stance detection model"""
        self.stance_model = None
        self.stance_tokenizer = None
        self.id_to_stance = {}
        
        if not self.stance_path or not os.path.exists(self.stance_path):
            print(f"❌ Stance model path not found: {self.stance_path}")
            return
        
        try:
            print(f"Loading stance model from: {self.stance_path}")
            self.stance_tokenizer = AutoTokenizer.from_pretrained(self.stance_path)
            self.stance_model = AutoModelForSequenceClassification.from_pretrained(
                self.stance_path
            ).to(self.device)
            self.stance_model.eval()
            
            # Try to load label mappings from multiple sources
            label_sources = [
                os.path.join(self.stance_path, 'label_mappings.json'),
                os.path.join(self.stance_path, 'config.json')
            ]
            
            labels_loaded = False
            for label_file in label_sources:
                if os.path.exists(label_file):
                    try:
                        with open(label_file, 'r') as f:
                            label_info = json.load(f)
                            if 'id_to_label' in label_info:
                                self.id_to_stance = {
                                    int(k): v for k, v in label_info['id_to_label'].items()
                                }
                                labels_loaded = True
                                break
                    except Exception as e:
                        continue
            
            if not labels_loaded:
                # Try model config
                if hasattr(self.stance_model.config, 'id2label'):
                    self.id_to_stance = {
                        int(k): v for k, v in self.stance_model.config.id2label.items()
                    }
                    labels_loaded = True
            
            if not labels_loaded:
                # Default SDQC mapping
                self.id_to_stance = {
                    0: 'support', 1: 'deny', 2: 'query', 3: 'comment'
                }
                print("⚠️ Using default SDQC label mapping")
            
            print(f"✅ Stance model loaded successfully")
            print(f"   Labels: {list(self.id_to_stance.values())}")
            
        except Exception as e:
            print(f"❌ Error loading stance model: {str(e)}")
            self.stance_model = None
            self.stance_tokenizer = None
    
    def predict_sentiment(self, texts):
        """Predict sentiment using trained model or fallback methods"""
        if isinstance(texts, str):
            texts = [texts]
        
        # Try trained model first
        if self.sentiment_model is not None and self.sentiment_tokenizer is not None:
            try:
                inputs = self.sentiment_tokenizer(
                    texts, 
                    padding=True, 
                    truncation=True, 
                    max_length=512, 
                    return_tensors='pt'
                ).to(self.device)
                
                with torch.no_grad():
                    logits = self.sentiment_model(**inputs).logits
                
                predictions = logits.argmax(dim=-1).cpu().numpy()
                return [self.id_to_sentiment.get(int(pred), 'neutral') for pred in predictions]
                
            except Exception as e:
                print(f"Error in sentiment model prediction: {e}")
                # Fall through to fallback methods
        
        # VADER fallback
        if hasattr(self, 'vader_analyzer') and self.vader_analyzer is not None:
            sentiments = []
            for text in texts:
                if pd.isna(text) or not isinstance(text, str) or not text.strip():
                    sentiments.append('neutral')
                    continue
                
                try:
                    scores = self.vader_analyzer.polarity_scores(text)
                    compound = scores['compound']
                    
                    if compound >= 0.05:
                        sentiments.append('positive')
                    elif compound <= -0.05:
                        sentiments.append('negative')
                    else:
                        sentiments.append('neutral')
                except Exception:
                    sentiments.append('neutral')
            
            return sentiments
        
        # Rule-based fallback
        return self._rule_based_sentiment(texts)
    
    def _rule_based_sentiment(self, texts):
        """Rule-based sentiment analysis fallback"""
        positive_words = {
            'good', 'great', 'excellent', 'amazing', 'wonderful', 'fantastic', 'awesome',
            'love', 'like', 'happy', 'joy', 'pleased', 'glad', 'excited', 'thrilled',
            'perfect', 'brilliant', 'outstanding', 'superb', 'magnificent', 'incredible'
        }
        
        negative_words = {
            'bad', 'terrible', 'awful', 'horrible', 'disgusting', 'hate', 'dislike',
            'angry', 'mad', 'furious', 'sad', 'depressed', 'worried', 'concerned',
            'dangerous', 'threat', 'crisis', 'disaster', 'tragic', 'devastating',
            'fake', 'false', 'lie', 'wrong', 'stupid', 'ridiculous'
        }
        
        sentiments = []
        for text in texts:
            if pd.isna(text) or not isinstance(text, str):
                sentiments.append('neutral')
                continue
            
            words = text.lower().split()
            pos_count = sum(1 for word in words if word in positive_words)
            neg_count = sum(1 for word in words if word in negative_words)
            
            if pos_count > neg_count + 1:
                sentiments.append('positive')
            elif neg_count > pos_count + 1:
                sentiments.append('negative')
            else:
                sentiments.append('neutral')
        
        return sentiments
    
    def predict_stance(self, texts):
        """Predict stance using trained model or fallback methods"""
        if isinstance(texts, str):
            texts = [texts]
        
        # Try trained model first
        if self.stance_model is not None and self.stance_tokenizer is not None:
            try:
                inputs = self.stance_tokenizer(
                    texts,
                    padding=True,
                    truncation=True,
                    max_length=512,
                    return_tensors='pt'
                ).to(self.device)
                
                with torch.no_grad():
                    logits = self.stance_model(**inputs).logits
                
                predictions = logits.argmax(dim=-1).cpu().numpy()
                return [self.id_to_stance.get(int(pred), 'comment') for pred in predictions]
                
            except Exception as e:
                print(f"Error in stance model prediction: {e}")
                # Fall through to fallback
        
        # Rule-based fallback
        return self._rule_based_stance(texts)
    
    def _rule_based_stance(self, texts):
        """Rule-based stance detection fallback"""
        support_patterns = [
            'agree', 'true', 'correct', 'right', 'absolutely', 'exactly', 'definitely',
            'support', 'yes', 'confirmed', 'verify', 'validate', 'accurate'
        ]
        
        deny_patterns = [
            'disagree', 'false', 'wrong', 'fake', 'lie', 'bullshit', 'nonsense',
            'deny', 'no', 'incorrect', 'untrue', 'bogus', 'debunked', 'misinformation'
        ]
        
        question_patterns = [
            '?', 'question', 'doubt', 'sure', 'really', 'verify', 'confirm',
            'source', 'evidence', 'proof', 'uncertain', 'skeptical', 'wonder'
        ]
        
        stances = []
        for text in texts:
            if pd.isna(text) or not isinstance(text, str):
                stances.append('comment')
                continue
            
            text_lower = text.lower()
            
            support_count = sum(1 for pattern in support_patterns if pattern in text_lower)
            deny_count = sum(1 for pattern in deny_patterns if pattern in text_lower)
            question_count = sum(1 for pattern in question_patterns if pattern in text_lower)
            
            if support_count > max(deny_count, question_count):
                stances.append('support')
            elif deny_count > max(support_count, question_count):
                stances.append('deny')
            elif question_count > 0 or '?' in text:
                stances.append('query')
            else:
                stances.append('comment')
        
        return stances
    
    def calculate_rumor_sentimentality(self, sentiments):
        """Calculate R_c: intensity of negative emotions (RSK-T5 methodology)"""
        if not sentiments:
            return 0.0
        
        sentiment_counts = pd.Series(sentiments).value_counts()
        negative_count = sentiment_counts.get('negative', 0)
        positive_count = sentiment_counts.get('positive', 0)
        total_emotional = negative_count + positive_count
        
        if total_emotional == 0:
            return 0.0
        
        # R_c = negative emotions / total emotional reactions
        R_c = negative_count / total_emotional
        return float(R_c)
    
    def calculate_rumor_approval(self, stances):
        """Calculate R_r: support level for rumor (RSK-T5 methodology)"""
        if not stances:
            return 0.0
        
        stance_counts = pd.Series(stances).value_counts()
        support_count = stance_counts.get('support', 0)
        deny_count = stance_counts.get('deny', 0)
        query_count = stance_counts.get('query', 0)
        
        total_stance = support_count + deny_count + query_count
        
        if total_stance == 0:
            return 0.0
        
        # R_r = support / (support + deny + query)
        R_r = support_count / total_stance
        return float(R_r)
    
    def calculate_organization_score(self, comments_df):
        """Calculate R_o: organization/coordination level (RSK-T5 methodology)"""
        if len(comments_df) < 2:
            return 0.0
        
        try:
            # User activity analysis
            if 'user.handle' in comments_df.columns:
                user_activity = comments_df['user.handle'].value_counts()
                unique_users = len(user_activity)
                total_comments = len(comments_df)
                
                if unique_users == 0:
                    return 0.0
                
                # Engagement intensity
                engagement_intensity = total_comments / unique_users
                
                # Top user dominance (Gini-like coefficient)
                if len(user_activity) > 0:
                    top_user_ratio = user_activity.iloc[0] / total_comments
                    
                    # Skewness calculation (simplified)
                    activity_values = user_activity.values
                    mean_activity = np.mean(activity_values)
                    if mean_activity > 0:
                        skewness = np.sum((activity_values - mean_activity) ** 3) / (len(activity_values) * (np.std(activity_values) ** 3 + 1e-6))
                        skewness = abs(skewness)  # Take absolute value
                    else:
                        skewness = 0
                    
                    # Combined organization score
                    R_o = min((top_user_ratio * 0.4) + (min(engagement_intensity / 5.0, 1.0) * 0.3) + (min(skewness / 2.0, 1.0) * 0.3), 1.0)
                else:
                    R_o = 0.1
            else:
                # Fallback when no user info available
                R_o = min(len(comments_df) / 20.0, 0.5)  # Proxy based on comment count
            
            return float(R_o)
        
        except Exception as e:
            print(f"Error calculating organization score: {e}")
            return 0.3  # Default moderate score
    
    def calculate_propagation_metrics(self, comments_df, sentiments, stances):
        """Calculate additional propagation and engagement metrics"""
        metrics = {}
        
        try:
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
            emotional_comments = sentiment_counts.get('negative', 0) + sentiment_counts.get('positive', 0)
            metrics['emotional_intensity'] = emotional_comments / max(len(sentiments), 1)
            
            # Opposition ratio (balanced opposition indicates controversy)
            support_ratio = stance_counts.get('support', 0) / max(len(stances), 1)
            deny_ratio = stance_counts.get('deny', 0) / max(len(stances), 1)
            metrics['opposition_balance'] = min(support_ratio, deny_ratio) * 2  # Balanced = more controversial
            
        except Exception as e:
            print(f"Error calculating propagation metrics: {e}")
            # Set safe defaults
            metrics = {
                'total_comments': len(comments_df) if hasattr(comments_df, '__len__') else 0,
                'unique_users': 1,
                'engagement_intensity': 1.0,
                'sentiment_entropy': 0.0,
                'stance_entropy': 0.0,
                'sentiment_diversity': 1,
                'stance_diversity': 1,
                'emotional_intensity': 0.5,
                'opposition_balance': 0.0
            }
        
        return metrics
    
    def _calculate_entropy(self, counts):
        """Calculate entropy for diversity measurement"""
        if len(counts) == 0 or counts.sum() == 0:
            return 0.0
        
        try:
            probabilities = counts / counts.sum()
            # Add small epsilon to avoid log(0)
            probabilities = probabilities + 1e-10
            entropy = -np.sum(probabilities * np.log2(probabilities))
            return float(entropy)
        except Exception:
            return 0.0
    
    def calculate_harmfulness_score(self, rumor_text, comments_df):
        """
        Calculate comprehensive harmfulness score using RSK-T5 methodology
        
        Args:
            rumor_text (str): Original rumor text
            comments_df (pd.DataFrame): Comments dataframe
            
        Returns:
            dict: Detailed harmfulness analysis
        """
        try:
            # Validation
            if len(comments_df) == 0:
                return {
                    'harmfulness_score': 0.0,
                    'harmfulness_score_normalized': 0.0,
                    'components': {
                        'rumor_sentimentality_R_c': 0.0,
                        'rumor_approval_R_r': 0.0,
                        'organization_score_R_o': 0.0,
                        'engagement_score': 0.0,
                        'controversy_score': 0.0,
                        'emotional_intensity_score': 0.0,
                        'opposition_score': 0.0,
                        'total_comments': 0,
                        'unique_users': 0,
                        'sentiment_distribution': {},
                        'stance_distribution': {}
                    },
                    'comment_count': 0,
                    'interpretation': 'No comments to analyze',
                    'model_info': {
                        'sentiment_model_available': self.sentiment_model is not None,
                        'stance_model_available': self.stance_model is not None
                    }
                }
            
            # Clean data and extract texts
            comments_df = comments_df.dropna(subset=['text']).copy()
            if len(comments_df) == 0:
                return self.calculate_harmfulness_score(rumor_text, pd.DataFrame())
            
            texts = comments_df['text'].tolist()
            
            print(f"Analyzing {len(texts)} comments for harmfulness...")
            
            # Predict sentiment and stance using trained models
            print("Predicting sentiments...")
            sentiments = self.predict_sentiment(texts)
            
            print("Predicting stances...")
            stances = self.predict_stance(texts)
            
            # Add predictions to dataframe for reference
            comments_df['sentiment_pred'] = sentiments
            comments_df['stance_pred'] = stances
            
            # Calculate core RSK-T5 components
            print("Calculating RSK-T5 harmfulness components...")
            
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
            
            # Component weights based on RSK-T5 paper and empirical importance
            weights = {
                'sentimentality': 0.25,      # Negative emotions (R_c)
                'approval': 0.25,            # Support for rumor (R_r)  
                'organization': 0.20,        # Coordinated spreading (R_o)
                'engagement': 0.10,          # Engagement intensity
                'controversy': 0.10,         # Diverse reactions (debate indicator)
                'emotional_intensity': 0.05, # Overall emotional response
                'opposition': 0.05           # Balanced opposition (controversial)
            }
            
            # Calculate weighted harmfulness score
            final_score = (
                weights['sentimentality'] * R_c +
                weights['approval'] * R_r +
                weights['organization'] * R_o +
                weights['engagement'] * engagement_score +
                weights['controversy'] * controversy_score +
                weights['emotional_intensity'] * emotional_intensity_score +
                weights['opposition'] * opposition_score
            )
            
            # Ensure score is in [0,1] range
            final_score = max(0.0, min(1.0, final_score))
            
            # Build component breakdown
            harmfulness_components = {
                'rumor_sentimentality_R_c': float(R_c),
                'rumor_approval_R_r': float(R_r),
                'organization_score_R_o': float(R_o),
                'engagement_score': float(engagement_score),
                'controversy_score': float(controversy_score),
                'emotional_intensity_score': float(emotional_intensity_score),
                'opposition_score': float(opposition_score),
                'total_comments': len(comments_df),
                'unique_users': prop_metrics['unique_users'],
                'sentiment_distribution': pd.Series(sentiments).value_counts().to_dict(),
                'stance_distribution': pd.Series(stances).value_counts().to_dict()
            }
            
            # Normalize to 0-100 scale for interpretability
            harmfulness_score_normalized = final_score * 100
            
            result = {
                'harmfulness_score': float(final_score),
                'harmfulness_score_normalized': float(harmfulness_score_normalized),
                'components': harmfulness_components,
                'comment_count': len(comments_df),
                'interpretation': self._interpret_score(harmfulness_score_normalized),
                'model_info': {
                    'sentiment_model_available': self.sentiment_model is not None,
                    'stance_model_available': self.stance_model is not None
                }
            }
            
            print(f"Harmfulness analysis complete. Score: {final_score:.3f}")
            return result
            
        except Exception as e:
            print(f"Error in calculate_harmfulness_score: {str(e)}")
            import traceback
            traceback.print_exc()
            
            # Return safe fallback
            return {
                'harmfulness_score': 0.0,
                'harmfulness_score_normalized': 0.0,
                'components': {},
                'comment_count': 0,
                'interpretation': 'Error in analysis',
                'error': str(e),
                'model_info': {
                    'sentiment_model_available': False,
                    'stance_model_available': False
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
        try:
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
            
        except Exception as e:
            print(f"Error in analyze_conversation_thread: {str(e)}")
            return {"error": f"Analysis failed: {str(e)}"}