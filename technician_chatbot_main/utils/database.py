import csv
import logging
import os
from datetime import datetime, timedelta
from io import StringIO

from bson.objectid import ObjectId
from pymongo import DESCENDING, MongoClient

logger = logging.getLogger(__name__)

# Global database connection
_db_client = None
_database = None


def get_database():
    """Get database connection"""
    global _db_client, _database

    if _database is None:
        try:
            mongo_uri = os.getenv("MONGO_URI", "mongodb://localhost:27017/")
            db_name = os.getenv("MONGO_DB_NAME", "technician_chatbot")

            _db_client = MongoClient(mongo_uri)
            _database = _db_client[db_name]

            # Test connection
            _db_client.admin.command("ismaster")
            logger.info(f"Connected to MongoDB: {db_name}")

        except Exception as e:
            logger.error(f"Failed to connect to MongoDB: {str(e)}")
            raise

    return _database


def init_db():
    """Initialize database collections and indexes"""
    try:
        db = get_database()

        # Create collections if they don't exist
        collections = ["chat_logs", "feedback", "admin_users"]

        for collection in collections:
            if collection not in db.list_collection_names():
                db.create_collection(collection)
                logger.info(f"Created collection: {collection}")

        # Create indexes
        db.chat_logs.create_index([("timestamp", DESCENDING)])
        db.chat_logs.create_index([("intent", 1)])
        db.chat_logs.create_index([("response_source", 1)])
        db.feedback.create_index([("chat_log_id", 1)])

        logger.info("Database initialized successfully")
        return True

    except Exception as e:
        logger.error(f"Error initializing database: {str(e)}")
        return False


def get_user_by_id(user_id):
    """Get user by ID for Flask-Login"""
    if user_id == "admin":
        from routes.auth_routes import AdminUser

        return AdminUser(user_id="admin", username="admin")
    return None


def log_chat_interaction(
    user_query, intent, confidence, response, response_source, response_time
):
    """Log a chat interaction to database"""
    try:
        db = get_database()

        chat_log = {
            "timestamp": datetime.utcnow(),
            "user_query": user_query,
            "intent": intent,
            "confidence": float(confidence),
            "response": response,
            "response_source": response_source,
            "response_time": float(response_time),
            "feedback_rating": None,
            "feedback_comment": None,
        }

        result = db.chat_logs.insert_one(chat_log)
        logger.debug(f"Chat interaction logged: {result.inserted_id}")

        return str(result.inserted_id)

    except Exception as e:
        logger.error(f"Error logging chat interaction: {str(e)}")
        return None


def save_feedback(chat_log_id, rating, comment):
    """Save user feedback for a chat interaction"""
    try:
        db = get_database()

        # Update the chat log with feedback
        result = db.chat_logs.update_one(
            {"_id": ObjectId(chat_log_id)},
            {
                "$set": {
                    "feedback_rating": int(rating),
                    "feedback_comment": comment,
                    "feedback_timestamp": datetime.utcnow(),
                }
            },
        )

        if result.modified_count > 0:
            logger.info(f"Feedback saved for chat log: {chat_log_id}")
            return True
        else:
            logger.warning(f"Chat log not found for feedback: {chat_log_id}")
            return False

    except Exception as e:
        logger.error(f"Error saving feedback: {str(e)}")
        return False


def get_dashboard_metrics():
    """Get dashboard metrics"""
    try:
        db = get_database()

        # Total interactions
        total_interactions = db.chat_logs.count_documents({})

        # Recent interactions (last 24 hours)
        yesterday = datetime.utcnow() - timedelta(days=1)
        recent_interactions = db.chat_logs.count_documents(
            {"timestamp": {"$gte": yesterday}}
        )

        # Average confidence
        pipeline = [
            {"$group": {"_id": None, "avg_confidence": {"$avg": "$confidence"}}}
        ]
        confidence_result = list(db.chat_logs.aggregate(pipeline))
        avg_confidence = (
            confidence_result[0]["avg_confidence"] if confidence_result else 0
        )

        # Average rating
        pipeline = [
            {"$match": {"feedback_rating": {"$exists": True, "$ne": None}}},
            {"$group": {"_id": None, "avg_rating": {"$avg": "$feedback_rating"}}},
        ]
        rating_result = list(db.chat_logs.aggregate(pipeline))
        avg_rating = rating_result[0]["avg_rating"] if rating_result else 0

        return {
            "total_interactions": total_interactions,
            "recent_interactions": recent_interactions,
            "avg_confidence": avg_confidence,
            "avg_rating": avg_rating,
        }

    except Exception as e:
        logger.error(f"Error getting dashboard metrics: {str(e)}")
        return {}


def get_recent_chat_logs(limit=10):
    """Get recent chat logs"""
    try:
        db = get_database()

        cursor = db.chat_logs.find().sort("timestamp", DESCENDING).limit(limit)
        chat_logs = list(cursor)

        return chat_logs

    except Exception as e:
        logger.error(f"Error getting recent chat logs: {str(e)}")
        return []


def get_intent_distribution(limit=10):
    """Get distribution of intents"""
    try:
        db = get_database()

        pipeline = [
            {"$group": {"_id": "$intent", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}},
            {"$limit": limit},
        ]

        result = list(db.chat_logs.aggregate(pipeline))
        return result

    except Exception as e:
        logger.error(f"Error getting intent distribution: {str(e)}")
        return []


def get_response_time_stats():
    """Get response time statistics"""
    try:
        db = get_database()

        pipeline = [
            {
                "$group": {
                    "_id": None,
                    "avg_response_time": {"$avg": "$response_time"},
                    "min_response_time": {"$min": "$response_time"},
                    "max_response_time": {"$max": "$response_time"},
                }
            }
        ]

        result = list(db.chat_logs.aggregate(pipeline))
        return result[0] if result else {}

    except Exception as e:
        logger.error(f"Error getting response time stats: {str(e)}")
        return {}


def get_daily_interaction_stats(days=30):
    """Get daily interaction statistics"""
    try:
        db = get_database()

        # Get start date
        start_date = datetime.utcnow() - timedelta(days=days)

        pipeline = [
            {"$match": {"timestamp": {"$gte": start_date}}},
            {
                "$group": {
                    "_id": {
                        "$dateToString": {"format": "%Y-%m-%d", "date": "$timestamp"}
                    },
                    "count": {"$sum": 1},
                }
            },
            {"$sort": {"_id": 1}},
        ]

        result = list(db.chat_logs.aggregate(pipeline))
        return result

    except Exception as e:
        logger.error(f"Error getting daily stats: {str(e)}")
        return []


def get_source_distribution():
    """Get response source distribution"""
    try:
        db = get_database()

        pipeline = [
            {"$group": {"_id": "$response_source", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}},
        ]

        result = list(db.chat_logs.aggregate(pipeline))
        return result

    except Exception as e:
        logger.error(f"Error getting source distribution: {str(e)}")
        return []


def get_confidence_distribution():
    """Get confidence score distribution"""
    try:
        db = get_database()

        pipeline = [
            {
                "$bucket": {
                    "groupBy": "$confidence",
                    "boundaries": [0, 0.2, 0.4, 0.6, 0.8, 1.0],
                    "default": "Other",
                    "output": {"count": {"$sum": 1}},
                }
            }
        ]

        result = list(db.chat_logs.aggregate(pipeline))
        return result

    except Exception as e:
        logger.error(f"Error getting confidence distribution: {str(e)}")
        return []


def get_feedback_distribution():
    """Get feedback rating distribution"""
    try:
        db = get_database()

        pipeline = [
            {"$match": {"feedback_rating": {"$exists": True, "$ne": None}}},
            {"$group": {"_id": "$feedback_rating", "count": {"$sum": 1}}},
            {"$sort": {"_id": 1}},
        ]

        result = list(db.chat_logs.aggregate(pipeline))
        return result

    except Exception as e:
        logger.error(f"Error getting feedback distribution: {str(e)}")
        return []


def get_chat_logs(page=1, per_page=50, filters=None):
    """Get paginated chat logs with optional filters"""
    try:
        db = get_database()

        # Build query
        query = {}
        if filters:
            if "intent" in filters:
                query["intent"] = filters["intent"]
            if "response_source" in filters:
                query["response_source"] = filters["response_source"]
            if "date_from" in filters or "date_to" in filters:
                query["timestamp"] = {}
                if "date_from" in filters:
                    query["timestamp"]["$gte"] = filters["date_from"]
                if "date_to" in filters:
                    query["timestamp"]["$lte"] = filters["date_to"]

        # Get total count
        total_count = db.chat_logs.count_documents(query)

        # Get paginated results
        skip = (page - 1) * per_page
        cursor = (
            db.chat_logs.find(query)
            .sort("timestamp", DESCENDING)
            .skip(skip)
            .limit(per_page)
        )
        chat_logs = list(cursor)

        return chat_logs, total_count

    except Exception as e:
        logger.error(f"Error getting chat logs: {str(e)}")
        return [], 0


def export_chat_logs_csv(date_from=None):
    """Export chat logs as CSV"""
    try:
        db = get_database()

        # Build query
        query = {}
        if date_from:
            query["timestamp"] = {"$gte": date_from}

        # Get data
        cursor = db.chat_logs.find(query).sort("timestamp", DESCENDING)

        # Create CSV
        output = StringIO()
        writer = csv.writer(output)

        # Write header
        writer.writerow(
            [
                "Timestamp",
                "User Query",
                "Intent",
                "Confidence",
                "Response Source",
                "Response Time",
                "Feedback Rating",
                "Feedback Comment",
            ]
        )

        # Write data
        for log in cursor:
            writer.writerow(
                [
                    log.get("timestamp", ""),
                    log.get("user_query", ""),
                    log.get("intent", ""),
                    log.get("confidence", ""),
                    log.get("response_source", ""),
                    log.get("response_time", ""),
                    log.get("feedback_rating", ""),
                    log.get("feedback_comment", ""),
                ]
            )

        return output.getvalue()

    except Exception as e:
        logger.error(f"Error exporting chat logs: {str(e)}")
        return ""


def get_detailed_metrics():
    """Get detailed metrics for admin dashboard"""
    try:
        db = get_database()

        # Get basic metrics
        basic_metrics = get_dashboard_metrics()

        # Get intent distribution
        intent_dist = get_intent_distribution()

        # Additional metrics can be added here
        return {**basic_metrics, "intent_distribution": intent_dist}

    except Exception as e:
        logger.error(f"Error getting detailed metrics: {str(e)}")
        return {}


def get_chart_data(chart_type, days=30):
    """Get data for charts"""
    try:
        if chart_type == "daily_interactions":
            return get_daily_interaction_stats(days)
        elif chart_type == "intent_distribution":
            return get_intent_distribution()
        elif chart_type == "source_distribution":
            return get_source_distribution()
        else:
            return []

    except Exception as e:
        logger.error(f"Error getting chart data: {str(e)}")
        return []
