import logging
import re  # for filtering
import time
from datetime import datetime

from flask import Blueprint, current_app, jsonify, request

from utils.database import log_chat_interaction
from utils.preprocessing import preprocess_text

logger = logging.getLogger(__name__)

chat_bp = Blueprint("chat", __name__)


def _filter_references(text):
    """Remove [1], [2], etc."""
    return re.sub(r"\[\d+\]", "", text)


@chat_bp.route("/message", methods=["POST"])
def handle():
    try:
        data = request.get_json()
        if not data or "message" not in data:
            return jsonify({"error": "No message provided"}), 400
        user_msg = data["message"].strip()
        if not user_msg:
            return jsonify({"error": "Empty message"}), 400
        if len(user_msg) > 1000:
            return jsonify({"error": "Max length exceeded"}), 400

        # Check if query is in scope
        if not _is_technical_query(user_msg):
            return jsonify(
                {
                    "response": "I only handle technical maintenance/repair queries.",
                    "source": "filter",
                    "confidence": 1.0,
                    "response_time": 0.001,
                    "timestamp": datetime.utcnow().isoformat(),
                }
            )

        start_time = time.time()

        if current_app.intent_classifier:
            classification = current_app.intent_classifier.classify(user_msg)
            intent = classification["intent"]
            conf = classification["confidence"]
        else:
            intent = "general"
            conf = 0.0

        logger.info(f"Intent: {intent}, confidence: {conf:.3f}")

        # New routing based on confidence and retrieval
        response_source = None
        use_llm_direct = False
        context = ""

        if conf > 0.7:
            route = "rule_based"
        elif 0.3 <= conf <= 0.7:
            route = "rag"
        else:
            route = "llm"

        logger.info(f"Routing selected: {route}")

        if route == "rule_based" or not current_app.rag_system:
            # Preprocess input before rule-based matching
            proc_msg = preprocess_text(user_msg)
            if current_app.rule_based_bot:
                response_data = current_app.rule_based_bot.respond(proc_msg, intent)
                response_source = "rule_based"
            else:
                response_data = {"response": "System temporarily unavailable."}
                response_source = "fallback"

        elif route == "rag":
            # Retrieval Augmented Generation step
            try:
                context = current_app.rag_system.get_context_string(user_msg, k=5)
                # If no docs retrieved, fallback to pure LLM
                if not context.strip():
                    use_llm_direct = True
                else:
                    client = getattr(current_app, "perplexity_client", None)
                    if client is None:
                        from utils import perplexity_client

                        client = perplexity_client.PerplexityClient()
                        current_app.perplexity_client = client

                    llm_response = client.query(user_msg, context)

                    if llm_response.get("success"):
                        filtered_text = _filter_references(llm_response["response"])
                        response_data = {
                            "response": filtered_text,
                            "confidence": 0.75,
                            "source": "rag",
                            "context_used": True,
                            "model": llm_response.get("model", "unknown"),
                        }
                        response_source = "rag"
                    else:
                        if current_app.rule_based_bot:
                            proc_msg = preprocess_text(user_msg)
                            response_data = current_app.rule_based_bot.respond(
                                proc_msg, intent
                            )
                            response_source = "rule_based_fallback"
                        else:
                            response_data = {"response": "Unable to process request."}
                            response_source = "error"
            except Exception as e:
                logger.error(f"Exception during RAG processing: {e}")
                use_llm_direct = True

            if use_llm_direct:
                route = "llm"  # escalate to LLM fallback

        if route == "llm":
            # Pure LLM fallback
            try:
                client = getattr(current_app, "perplexity_client", None)
                if client is None:
                    from utils import perplexity_client

                    client = perplexity_client.PerplexityClient()
                    current_app.perplexity_client = client

                llm_response = client.query(user_msg, "")

                if llm_response.get("success"):
                    filtered_text = _filter_references(llm_response["response"])
                    response_data = {
                        "response": filtered_text,
                        "confidence": 0.6,
                        "source": "llm",
                        "context_used": False,
                        "model": llm_response.get("model", "unknown"),
                    }
                    response_source = "llm"
                else:
                    if current_app.rule_based_bot:
                        proc_msg = preprocess_text(user_msg)
                        response_data = current_app.rule_based_bot.respond(
                            proc_msg, intent
                        )
                        response_source = "rule_based_fallback"
                    else:
                        response_data = {"response": "Unable to process request."}
                        response_source = "error"
            except Exception as e:
                logger.error(f"Exception during LLM fallback: {e}")
                if current_app.rule_based_bot:
                    proc_msg = preprocess_text(user_msg)
                    response_data = current_app.rule_based_bot.respond(proc_msg, intent)
                    response_source = "rule_based_fallback"
                else:
                    response_data = {"response": "Unable to process request."}
                    response_source = "error"

        elapsed = time.time() - start_time

        if isinstance(response_data, dict):
            resp_text = response_data.get("response", "Sorry, no answer.")
            if response_source == "rule_based":
                resp_confidence = conf
            elif response_source == "rag":
                resp_confidence = 0.35
            elif response_source == "llm":
                resp_confidence = 0.10
            else:
                resp_confidence = conf
        else:
            resp_text = str(response_data)
            resp_confidence = conf

        try:
            chat_log_id = log_chat_interaction(
                user_msg,
                intent,
                resp_confidence,
                resp_text,
                response_source,
                elapsed,
            )
        except Exception as e:
            logger.error(f"Logging error: {e}")
            chat_log_id = None

        return jsonify(
            {
                "response": resp_text,
                "source": response_source,
                "intent": intent,
                "confidence": resp_confidence,
                "response_time": elapsed,
                "chat_log_id": chat_log_id,
                "timestamp": datetime.utcnow().isoformat(),
            }
        )

    except Exception as e:
        logger.error(f"Unhandled exception in chat handler: {e}")
        return jsonify({"error": "Internal server error"}), 500


def _is_technical_query(query):
    technical_indicators = [
        "motor",
        "pump",
        "valve",
        "sensor",
        "compressor",
        "generator",
        "turbine",
        "boiler",
        "chiller",
        "hvac",
        "conveyor",
        "bearing",
        "gearbox",
        "transformer",
        "actuator",
        "cylinder",
        "pneumatic",
        "hydraulic",
        "electrical",
        "mechanical",
        "troubleshoot",
        "repair",
        "fix",
        "maintain",
        "diagnose",
        "replace",
        "install",
        "calibrate",
        "adjust",
        "clean",
        "lubricate",
        "tighten",
        "test",
        "malfunction",
        "failure",
        "broken",
        "noise",
        "vibration",
        "leak",
        "overheat",
        "voltage",
        "current",
        "pressure",
        "temperature",
        "rpm",
        "flow",
        "torque",
        "efficiency",
        "capacity",
        "specification",
        "manual",
        "procedure",
        "protocol",
        "safety",
        "lockout",
        "tagout",
        "loto",
        "ppe",
        "hazard",
        "emergency",
        "protection",
        "preventive maintenance",
        "engine",
        "maintenance",
        "what can you do",
    ]
    ql = query.lower()
    return any(keyword in ql for keyword in technical_indicators)


@chat_bp.route("/feedback", methods=["POST"])
def handle_feedback():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400

        chat_log_id = data.get("chat_log_id")
        rating = data.get("rating")
        comment = data.get("comment", "")

        if not chat_log_id:
            return jsonify({"error": "Chat log ID required"}), 400
        if not isinstance(rating, int) or rating < 1 or rating > 5:
            return jsonify({"error": "Rating must be between 1 and 5"}), 400

        from utils import database

        success = database.save_feedback(chat_log_id, rating, comment)

        if success:
            return jsonify(
                {
                    "success": True,
                    "message": "Feedback saved successfully",
                    "timestamp": datetime.utcnow().isoformat(),
                }
            )
        else:
            return jsonify(
                {
                    "success": False,
                    "message": "Failed to save feedback",
                    "timestamp": datetime.utcnow().isoformat(),
                }
            )
    except Exception as e:
        logger.error(f"Error handling feedback: {e}")
        return jsonify({"error": "Failed to save feedback"}), 500
