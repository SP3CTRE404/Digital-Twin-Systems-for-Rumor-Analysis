from __future__ import annotations

from typing import Any, Dict, Tuple

import os
import torch
from transformers import (
    AutoTokenizer,
    AutoModelForSequenceClassification,
    AutoModelForSeq2SeqLM,
    AutoConfig,
)


def _resolve_model_path(model_name_env: str | None) -> str:
    # Priority: explicit env path → provided name → fallback hardcoded path
    explicit_path = os.getenv("MODEL_LOCAL_PATH")
    if explicit_path:
        return explicit_path
    if model_name_env:
        return model_name_env
    # User-specified local path (with spaces handled). Update if needed.
    return r"C:\Users\harsh\OneDrive\Desktop\New folder\models"


def load_model(model_name: str | None) -> Dict[str, Any]:
    """Load tokenizer and sequence classification model from a local directory.

    Expects the directory to contain Hugging Face files like config.json, tokenizer.json, etc.
    """
    model_path = _resolve_model_path(model_name)
    try:
        # Preferred: load everything from the local folder
        cfg = AutoConfig.from_pretrained(model_path)
        tokenizer = AutoTokenizer.from_pretrained(model_path, use_fast=True)
        if getattr(cfg, "is_encoder_decoder", False) or cfg.model_type in {"t5", "bart", "mbart"}:
            model = AutoModelForSeq2SeqLM.from_pretrained(model_path, config=cfg)
        else:
            model = AutoModelForSequenceClassification.from_pretrained(model_path, config=cfg)
    except Exception as primary_exc:
        # Fallback: use a base model name for config/tokenizer, then load local weights
        try:
            base_name = os.getenv("MODEL_BASE_NAME")  # e.g., "bert-base-uncased", "xlm-roberta-base"
            if not base_name:
                raise primary_exc
            cfg = AutoConfig.from_pretrained(base_name)
            tokenizer = AutoTokenizer.from_pretrained(base_name, use_fast=True)
            if getattr(cfg, "is_encoder_decoder", False) or cfg.model_type in {"t5", "bart", "mbart"}:
                model = AutoModelForSeq2SeqLM.from_pretrained(model_path, config=cfg, local_files_only=True)
            else:
                model = AutoModelForSequenceClassification.from_pretrained(model_path, config=cfg, local_files_only=True)
        except Exception:
            return {
                "model_path": model_path,
                "error": f"Failed to load model from {model_path}: {primary_exc}",
                "loaded": False,
            }

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model.to(device)
    model.eval()

    return {
        "model_path": model_path,
        "tokenizer": tokenizer,
        "model": model,
        "device": device,
        "id2label": getattr(model.config, "id2label", {}),
        "loaded": True,
    }


def _predict_label_and_confidence(text: str, handle: Dict[str, Any]) -> Tuple[str, float]:
    if not handle or not handle.get("loaded"):
        # Safe fallback: return neutral prediction
        return "unknown", 0.5

    tokenizer: AutoTokenizer = handle["tokenizer"]
    model = handle["model"]
    device: torch.device = handle["device"]
    id2label: Dict[int, str] = handle.get("id2label", {})

    # Prefix for seq2seq-style tasks (e.g., T5 stance generation)
    text_input = text
    if hasattr(model, "generate"):
        prefix = os.getenv("T5_PREFIX", "stance: ")
        # Avoid double prefix if already present
        if not text.strip().lower().startswith(prefix.strip().lower()):
            text_input = f"{prefix}{text}"
    inputs = tokenizer(text_input, return_tensors="pt", truncation=True, padding=True)
    inputs = {k: v.to(device) for k, v in inputs.items()}
    with torch.no_grad():
        if hasattr(model, "generate"):
            # Seq2Seq path (e.g., T5) – generate a text label and normalize to expected classes
            outputs = model.generate(**inputs, max_length=10)
            generated_raw = tokenizer.decode(outputs[0], skip_special_tokens=True)
            generated = generated_raw.strip().lower()

            # strip potential prompt echoes
            for p in ("stance:", "label:"):
                if generated.startswith(p):
                    generated = generated[len(p):].strip()

            # Map common variants/synonyms to canonical labels
            valid = {"support", "deny", "question", "comment"}
            alias_map = {
                "support": {"support", "supports", "agree", "agreement", "true", "yes"},
                "deny": {"deny", "denies", "false", "no", "refute", "refutes", "disagree"},
                "question": {"question", "query", "unsure", "uncertain", "doubt", "doubts"},
                "comment": {"comment", "neutral", "other", "statement"},
            }

            label = "unknown"
            # direct match
            if generated in valid:
                label = generated
            else:
                # alias contains/startswith matching
                for canonical, variants in alias_map.items():
                    if generated in variants:
                        label = canonical
                        break
                if label == "unknown":
                    for canonical, variants in alias_map.items():
                        if any(generated.startswith(v) or v in generated for v in variants):
                            label = canonical
                            break

            # Confidence is not directly available from generate; return neutral proxy
            return label, 0.5
        else:
            # Classification path
            outputs = model(**inputs)
            probs = torch.nn.functional.softmax(outputs.logits, dim=-1)
            predicted_id = int(torch.argmax(probs, dim=1).item())
            confidence = float(probs[0][predicted_id].item())
            label = id2label.get(predicted_id, str(predicted_id))
            return label, confidence


def analyze_text(text: str, model: Dict[str, Any]) -> Dict[str, Any]:
    label, confidence = _predict_label_and_confidence(text, model)
    return {
        "model_path": model.get("model_path"),
        "text": text,
        "prediction": {
            "label": label,
            "confidence": round(confidence, 4),
        },
        "model_loaded": bool(model.get("loaded")),
        "model_error": model.get("error"),
    }


def predict_stance_sentiment(text: str, model: Dict[str, Any]) -> Tuple[str, float]:
    """Public helper to mirror user snippet: returns (label, confidence)."""
    return _predict_label_and_confidence(text, model)


