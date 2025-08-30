# Digital Twin System for Rumor Threat Analysis
### 1. Project Objective

This project aims to develop an intelligent system capable of automatically assessing the potential threat of online rumors and misinformation. The core objective is to move beyond simple true/false detection and create a model that can provide a nuanced, quantitative harmfulness score for a given rumor. This score helps to prioritize moderation efforts, understand public reaction, and mitigate the real-world impact of fake news.

The methodology is directly inspired by the research paper: "Harmfulness metrics in digital twins of social network rumors detection in cloud computing environment" by Li et al. (2024). We replicate the paper's novel two-stage training process to build a highly effective threat analysis model.

The ultimate vision is to integrate this model into a Digital Twin of a social network environment. This would allow for real-time monitoring and simulation, enabling platform managers to predict the trajectory and potential damage of a rumor before it spreads widely.
### 2. Project Roadmap & Current Status

This project is divided into three distinct phases. We have successfully completed all data preparation and are currently in the model training phase.
Phase 1: Data Preparation & Preprocessing (✅ Complete)

This foundational phase focused on transforming the raw PHEME dataset into a structured format suitable for our advanced two-stage training methodology.

    [✅] Step 1.1: Dataset Acquisition: The PHEME dataset, containing real-world rumor conversations, was acquired and loaded.

    [✅] Step 1.2: Stance Label Standardization: Comment annotations were standardized into four distinct categories: support, deny, query, and comment.

    [✅] Step 1.3: Sentiment Analysis Annotation: Each comment was analyzed to attach a positive, negative, or neutral sentiment label using the VADER library.

    [✅] Step 1.4: Conversation Structuring: The flat list of posts was organized into distinct conversation threads based on their root topic.

    [✅] Step 1.5: Harmfulness Score Calculation: A final, normalized harmfulness score was calculated for each source rumor, based on the sentiment, stance, and propagation characteristics of its comment thread. This created the target label for our final model.

Phase 2: Model Training (⏳ In Progress)

This is the core machine learning phase where we build and train our prediction model.

    [⏳] Step 2.1: Domain-Specific Pre-training: We are currently here. A google/flan-t5-small model is being pre-trained on the tasks of stance detection and sentiment analysis using all the prepared comment data. The goal is to create a model that understands the specific language and reaction patterns associated with rumors (i.e., "rumor propagation knowledge").

    [🔜] Step 2.2: Fine-tuning for Harmfulness Prediction: Once pre-training is complete, the knowledgeable model will be fine-tuned on the final, specific task: predicting the harmfulness_score for the source rumors.

Phase 3: Integration & Application (Future Work)

    [⬜] Step 3.1: Model Inference Pipeline: Develop a script or API endpoint that can take new, unseen rumor text and use the trained model to output a harmfulness score.

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

    pip install pandas vaderSentiment scipy torch scikit-learn transformers sentencepiece datasets

3.2. Running the Code

The project scripts should be run in the following order:

    Data Preparation (If needed): Run the sequence of data processing notebooks/scripts to generate the final training files.

    Stage 1 - Pre-training: Run the model pre-training script. This will generate the rumor_knowledge_model.

    python stage_1_pretraining.py

    Stage 2 - Fine-tuning (Coming soon): Run the fine-tuning script to train the final harmfulness prediction model.

### 4. Key Technologies

    Programming Language: Python

    Data Manipulation: Pandas

    Machine Learning: PyTorch, Scikit-learn

    NLP Model: Hugging Face Transformers (T5)

    Libraries: VADER, SciPy, SentencePiece, Datasets

### 5. Citation

This project's methodology is based on the findings from the following academic paper:

    Li, H., Yang, W., Wang, W. et al. Harmfulness metrics in digital twins of social network rumors detection in cloud computing environment. J Cloud Comp 13, 36 (2024). https://doi.org/10.1186/s13677-024-00596-x
