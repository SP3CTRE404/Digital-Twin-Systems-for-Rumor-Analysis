# Digital Twin System for Rumor Threat Analysis
### 1. Project Objective

This project aims to develop an intelligent system capable of automatically assessing the potential threat of online rumors and misinformation. The core objective is to move beyond simple true/false detection and create a model that can provide a nuanced, quantitative harmfulness score for a given rumor. This score helps to prioritize moderation efforts, understand public reaction, and mitigate the real-world impact of fake news.

The methodology is directly inspired by the research paper: "Harmfulness metrics in digital twins of social network rumors detection in cloud computing environment" by Li et al. (2024). We replicate the paper's novel two-stage training process to build a highly effective threat analysis model.

The ultimate vision is to integrate this model into a Digital Twin of a social network environment. This would allow for real-time monitoring and simulation, enabling platform managers to predict the trajectory and potential damage of a rumor before it spreads widely.
### 2. Project Roadmap & Current Status

This project is divided into three distinct phases. We have successfully completed all data preparation and are currently in the model training phase.
Phase 1: Data Preparation & Preprocessing (✅ Completed)

This foundational phase focused on transforming the raw PHEME dataset into a structured format suitable for our advanced two-stage training methodology.

    [✅] Step 1.1: Dataset Acquisition: The PHEME dataset, containing real-world rumor conversations, was acquired and loaded.

    [✅] Step 1.2: Stance Label Standardization: Comment annotations were standardized into four distinct categories: support, deny, query, and comment.

    [✅] Step 1.3: Sentiment Analysis Annotation: Each comment was analyzed to attach a positive, negative, or neutral sentiment label using the VADER library.

    [✅] Step 1.4: Conversation Structuring: The flat list of posts was organized into distinct conversation threads based on their root topic.

    [✅] Step 1.5: Harmfulness Score Calculation: A final, normalized harmfulness score was calculated for each source rumor, based on the sentiment, stance, and propagation characteristics of its comment thread. This created the target label for our final model.

Phase 2: Model Training (✅ Completed)

This is the core machine learning phase where we build and train our prediction model.

    [✅] Step 2.1: Domain-Specific Pre-training: A `google/flan-t5-small` model was pre-trained on the tasks of stance detection and sentiment analysis using all the prepared comment data. This created a model that understands the specific language and reaction patterns associated with rumors (i.e., "rumor propagation knowledge").

    [✅] Step 2.2: Fine-tuning for Harmfulness Prediction: The pre-trained model was then fine-tuned on the final, specific task: predicting the `harmfulness_score` for the source rumors. This resulted in our final threat analysis model.

Phase 3: Integration & Application (⏳ In Progress)

    [✅] Step 3.1: Model Inference Pipeline: A script has been developed that takes new, unseen rumor text and its associated comments to output a detailed harmfulness score and analysis.

    Related output:-
    Testing Enhanced Harmfulness Scoring System
    ============================================================
    Using device: cuda
    Loading sentiment model from: models\sentiment_model
    [OK] Sentiment model loaded: ['negative', 'neutral', 'positive']
    Loading stance model from: models\stance_model
    [OK] Stance model loaded: ['deny', 'support']
    Analyzing 8 comments for harmfulness...
    Predicting sentiments...
    Predicting stances...
    Calculating harmfulness components...
    Topic: chemical_spill_alert
    Source Rumor: BREAKING: Major chemical spill at downtown facility, evacuate immediately!
    
    HARMFULNESS ANALYSIS:
    Raw Score: 0.568
    Normalized Score: 56.8/100
    Interpretation: High (45-60): High harm potential. Active monitoring recommended.
    Total Comments: 8
    
    COMPONENT BREAKDOWN:
    • Sentimentality (R_c): 0.857
    • Approval (R_r): 0.750
    • Organization (R_o): 0.155
    • Engagement: 0.200
    • Controversy: 0.468
    
    DISTRIBUTIONS:
    Sentiments: {'negative': 6, 'positive': 1, 'neutral': 1}
    Stances: {'support': 6, 'deny': 2}
    
    MODEL STATUS:
    Sentiment Model: ✅ Available
    Stance Model: ✅ Available

    [⬜] Step 3.2: Digital Twin Integration: Integrate the inference pipeline into a dashboard or simulation environment to monitor rumor threats in real-time.

### 3. How to Use This Repository
3.1. Setup

    Clone the repository:

    git clone [https://github.com/SP3CTRE404/Digital-Twin-Systems-for-Rumor-Analysis.git](https://github.com/SP3CTRE404/Digital-Twin-Systems-for-Rumor-Analysis.git)
    cd Digital-Twin-Systems-for-Rumor-Analysis

    Create a virtual environment:

    python -m venv rumorenv
    source rumorenv/bin/activate  # On Windows, use `rumorenv\Scripts\activate`

    Install dependencies:

    pip install pandas vaderSentiment scipy torch scikit-learn transformers sentencepiece datasets accelerate

3.2. Running the Code

The project scripts should be run in the following order:

    Data Preparation (If needed): Run the sequence of data processing notebooks/scripts to generate the final training files.

    Stage 1 - Pre-training: Run the model pre-training script. This will generate the rumor_knowledge_model.

    python stage_1_pretraining.py

    Harmfulness Analysis: Run the inference script to analyze a rumor.

    python run_harmfulness_analysis.py

    Stage 2 - Fine-tuning (Coming soon): Run the fine-tuning script to train the final harmfulness prediction model.

3.3. Sentiment Classification (Supervised)

This repo includes a supervised sentiment classifier to predict the `sentiment` column in `datasets/final_rumor_dataset_for_training.csv`.

Train:

```bash
python -m src.sentiment_training \\
  --dataset datasets/final_rumor_dataset_for_training.csv \\
  --text_col text \\
  --label_col sentiment \\
  --model distilbert \\
  --epochs 3 \\
  --batch_size 16 \\
  --lr 5e-5 \\
  --max_length 256 \\
  --output_dir models/sentiment_model
```

Evaluation metrics (accuracy, macro-F1) are printed and the model/tokenizer are saved to `models/sentiment_model` along with a `label_mapping.json`.

Inference example:

```python
from transformers import AutoTokenizer, AutoModelForSequenceClassification
import torch

model_dir = "models/sentiment_model"
tokenizer = AutoTokenizer.from_pretrained(model_dir)
model = AutoModelForSequenceClassification.from_pretrained(model_dir)

texts = ["I love this!", "This is terrible.", "It's okay, I guess."]
enc = tokenizer(texts, padding=True, truncation=True, max_length=256, return_tensors="pt")
with torch.no_grad():
    logits = model(**enc).logits
pred = logits.argmax(dim=-1).cpu().numpy()
id_to_label = {int(k): v for k, v in model.config.id2label.items()}
print([id_to_label[int(i)] for i in pred])
```

Note: The script infers label mapping from dataset values (e.g., `positive/neutral/negative`). Ensure the dataset has `text` and `sentiment` columns.

### 4. Key Technologies

    - Programming Language: Python

    Data Manipulation: Pandas

    Machine Learning: PyTorch, Scikit-learn

    NLP Model: Hugging Face Transformers (DistilBERT)

    Libraries: VADER, SciPy, SentencePiece, Datasets

### 5. Citation

This project's methodology is based on the findings from the following academic paper:

    Li, H., Yang, W., Wang, W. et al. Harmfulness metrics in digital twins of social network rumors detection in cloud computing environment. J Cloud Comp 13, 36 (2024). https://doi.org/10.1186/s13677-024-00596-x
