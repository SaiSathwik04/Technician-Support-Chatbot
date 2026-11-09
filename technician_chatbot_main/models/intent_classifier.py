import json
import logging
import os
import pickle

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics import accuracy_score
from sklearn.model_selection import train_test_split
from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import Pipeline

logger = logging.getLogger(__name__)


class IntentClassifier:
    """Intent classification system for routing user queries"""

    def __init__(self, model_path="models/intent_classifier.pkl"):
        self.model_path = model_path
        self.pipeline = None
        self.intent_labels = []

        # Load existing model if available
        if os.path.exists(model_path):
            self._load_model()
        else:
            self._create_model()

    def _create_model(self):
        """Create a new intent classification model"""
        self.pipeline = Pipeline(
            [
                (
                    "tfidf",
                    TfidfVectorizer(
                        max_features=5000,
                        ngram_range=(1, 2),
                        stop_words="english",
                        lowercase=True,
                        strip_accents="ascii",
                    ),
                ),
                ("classifier", MultinomialNB(alpha=0.1)),
            ]
        )
        logger.info("Created new intent classifier")

    def train(self, training_data_path="data/training_intents.json"):
        """Train the intent classifier"""
        try:
            # Load training data
            if not os.path.exists(training_data_path):
                self._create_training_data(training_data_path)

            with open(training_data_path, "r") as f:
                training_data = json.load(f)

            # Prepare training data
            texts = []
            labels = []

            for intent, examples in training_data.items():
                for example in examples:
                    texts.append(example.lower().strip())
                    labels.append(intent)

            self.intent_labels = list(training_data.keys())

            # Split data
            X_train, X_test, y_train, y_test = train_test_split(
                texts, labels, test_size=0.2, random_state=42, stratify=labels
            )

            # Train model
            self.pipeline.fit(X_train, y_train)

            # Evaluate model
            y_pred = self.pipeline.predict(X_test)
            accuracy = accuracy_score(y_test, y_pred)

            logger.info(f"Intent classifier trained with {accuracy:.3f} accuracy")
            logger.info(f"Training samples: {len(texts)}")
            logger.info(f"Intent categories: {len(self.intent_labels)}")

            # Save model
            self._save_model()

            return True

        except Exception as e:
            logger.error(f"Error training intent classifier: {str(e)}")
            return False

    def classify(self, text):
        """Classify user input and return intent with confidence"""
        if not self.pipeline:
            return {"intent": "unclear", "confidence": 0.0, "route": "rule_based"}

        try:
            # Clean input
            clean_text = text.lower().strip()

            # Get prediction probabilities
            probabilities = self.pipeline.predict_proba([clean_text])[0]
            max_prob_idx = np.argmax(probabilities)
            max_probability = probabilities[max_prob_idx]
            predicted_intent = self.pipeline.classes_[max_prob_idx]

            # Determine routing based on intent and confidence
            route = self._determine_route(predicted_intent, max_probability, clean_text)

            return {
                "intent": predicted_intent,
                "confidence": float(max_probability),
                "route": route,
                "all_probabilities": {
                    intent: float(prob)
                    for intent, prob in zip(self.pipeline.classes_, probabilities)
                },
            }

        except Exception as e:
            logger.error(f"Error classifying intent: {str(e)}")
            return {"intent": "unclear", "confidence": 0.0, "route": "rule_based"}

    def _determine_route(self, intent, confidence, text):
        """Determine whether to use rule-based or LLM routing"""

        # High confidence simple intents go to rule-based
        simple_intents = [
            "greeting",
            "goodbye",
            "help",
            "simple_troubleshooting",
            "safety_query",
        ]
        if intent in simple_intents and confidence > 0.7:
            return "rule_based"

        # Complex technical queries go to LLM
        complex_intents = [
            "complex_troubleshooting",
            "technical_explanation",
            "equipment_specific",
        ]
        if intent in complex_intents:
            return "llm"

        # Medium confidence or unclear intents
        if confidence < 0.5:
            return "rule_based"  # Safe fallback

        # Check for technical keywords that might need LLM
        technical_keywords = [
            "analyze",
            "diagnose",
            "explain why",
            "root cause",
            "theory",
            "principle",
            "mechanism",
            "detailed",
            "comprehensive",
            "complex",
        ]

        if any(keyword in text for keyword in technical_keywords):
            return "llm"

        # Default to rule-based for reliability
        return "rule_based"

    def _create_training_data(self, file_path):
        """Create default training data"""
        training_data = {
            "greeting": [
                "hello",
                "hi",
                "hey",
                "good morning",
                "good afternoon",
                "good evening",
                "greetings",
                "howdy",
                "what's up",
                "how are you",
                "nice to meet you",
                "hello there",
                "hi there",
                "hey there",
                "good day",
                "salutations",
            ],
            "goodbye": [
                "bye",
                "goodbye",
                "see you later",
                "farewell",
                "take care",
                "catch you later",
                "see you",
                "until next time",
                "bye bye",
                "so long",
                "have a good day",
                "thanks goodbye",
                "that's all",
                "end chat",
                "exit",
                "quit",
            ],
            "help": [
                "what can you do",
                "what are your capabilities",
                "how do you work",
                "what is your purpose",
                "help me understand",
                "explain yourself",
                "what kind of help can you provide",
                "what topics can you help with",
                "tell me about yourself",
                "what are you",
                "how can you help me",
            ],
            "simple_troubleshooting": [
                "motor won't start",
                "pump not working",
                "no power",
                "machine stopped",
                "equipment down",
                "system offline",
                "won't turn on",
                "not responding",
                "basic problem",
                "simple fix",
                "quick help",
                "easy solution",
                "motor problem",
                "pump issue",
                "electrical problem",
                "mechanical issue",
            ],
            "complex_troubleshooting": [
                "intermittent failure",
                "complex diagnostic",
                "multiple symptoms",
                "advanced troubleshooting",
                "detailed analysis needed",
                "root cause analysis",
                "system integration issue",
                "performance degradation",
                "unusual behavior",
                "sophisticated problem",
                "in-depth investigation",
                "comprehensive diagnosis",
            ],
            "safety_query": [
                "safety procedure",
                "lockout tagout",
                "hazard identification",
                "personal protective equipment",
                "emergency procedure",
                "safety check",
                "risk assessment",
                "safety protocol",
                "LOTO procedure",
                "PPE requirements",
                "safety guidelines",
                "hazard control",
                "accident prevention",
            ],
            "maintenance_planning": [
                "maintenance schedule",
                "preventive maintenance",
                "when to service",
                "maintenance frequency",
                "service interval",
                "maintenance checklist",
                "planning maintenance",
                "scheduled maintenance",
                "routine maintenance",
            ],
            "equipment_specific": [
                "HVAC system",
                "conveyor belt",
                "hydraulic pump",
                "electrical motor",
                "pneumatic valve",
                "control panel",
                "sensor calibration",
                "compressor",
                "specific equipment model",
                "manufacturer specifications",
            ],
            "unclear": [
                "I don't know",
                "not sure",
                "unclear question",
                "confusing",
                "can't understand",
                "what do you mean",
                "huh",
                "random text",
                "unclear",
                "ambiguous",
                "vague",
                "uncertain",
            ],
        }

        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, "w") as f:
            json.dump(training_data, f, indent=2)

        logger.info(f"Created training data at {file_path}")

    def _save_model(self):
        """Save the trained model to disk"""
        try:
            model_data = {
                "pipeline": self.pipeline,
                "intent_labels": self.intent_labels,
            }

            os.makedirs(os.path.dirname(self.model_path), exist_ok=True)
            with open(self.model_path, "wb") as f:
                pickle.dump(model_data, f)

            logger.info(f"Model saved to {self.model_path}")
        except Exception as e:
            logger.error(f"Error saving model: {str(e)}")

    def _load_model(self):
        """Load the trained model from disk"""
        try:
            with open(self.model_path, "rb") as f:
                model_data = pickle.load(f)

            self.pipeline = model_data["pipeline"]
            self.intent_labels = model_data["intent_labels"]

            logger.info(f"Model loaded from {self.model_path}")
        except Exception as e:
            logger.error(f"Error loading model: {str(e)}")
            self._create_model()

    def get_model_info(self):
        """Get information about the model"""
        return {
            "model_type": "Multinomial Naive Bayes with TF-IDF",
            "intent_categories": len(self.intent_labels),
            "intents": self.intent_labels,
            "model_exists": self.pipeline is not None,
            "model_path": self.model_path,
        }
