import logging
from functools import lru_cache

import torch
from transformers import AutoModelForSequenceClassification, AutoTokenizer

from app.core.sentiment.base import SentimentAnalyzer, SentimentResult

logger = logging.getLogger(__name__)

MODEL_NAME = "ProsusAI/finbert"


@lru_cache(maxsize=1)
def _load_model():
    """Load FinBERT model and tokenizer (cached - loaded once)."""
    logger.info(f"Loading FinBERT model: {MODEL_NAME}")
    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
    model = AutoModelForSequenceClassification.from_pretrained(MODEL_NAME)
    model.eval()
    logger.info("FinBERT model loaded successfully")
    return tokenizer, model


class FinBERTAnalyzer(SentimentAnalyzer):
    """Financial sentiment analysis using FinBERT (ProsusAI/finbert).

    Runs locally on CPU. ~50ms per article.
    Labels: positive, negative, neutral
    """

    def __init__(self):
        self.tokenizer, self.model = _load_model()
        self.labels = ["positive", "negative", "neutral"]

    async def analyze(self, text: str) -> SentimentResult:
        """Analyze sentiment of a single financial text."""
        inputs = self.tokenizer(
            text,
            return_tensors="pt",
            padding=True,
            truncation=True,
            max_length=512,
        )

        with torch.no_grad():
            outputs = self.model(**inputs)
            probs = torch.nn.functional.softmax(outputs.logits, dim=-1)

        probs = probs[0].tolist()
        positive = probs[0]
        negative = probs[1]
        neutral = probs[2]

        # Composite score: -1 (very negative) to +1 (very positive)
        composite = positive - negative

        return SentimentResult(
            positive=positive,
            negative=negative,
            neutral=neutral,
            composite_score=composite,
            text=text[:200],
        )

    async def analyze_batch(self, texts: list[str]) -> list[SentimentResult]:
        """Analyze sentiment of multiple texts efficiently."""
        if not texts:
            return []

        inputs = self.tokenizer(
            texts,
            return_tensors="pt",
            padding=True,
            truncation=True,
            max_length=512,
        )

        with torch.no_grad():
            outputs = self.model(**inputs)
            probs = torch.nn.functional.softmax(outputs.logits, dim=-1)

        results = []
        for i, text in enumerate(texts):
            p = probs[i].tolist()
            results.append(
                SentimentResult(
                    positive=p[0],
                    negative=p[1],
                    neutral=p[2],
                    composite_score=p[0] - p[1],
                    text=text[:200],
                )
            )

        return results
