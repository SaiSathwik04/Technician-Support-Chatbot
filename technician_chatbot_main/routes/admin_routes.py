import logging
from datetime import datetime, timedelta

from flask import Blueprint, flash, jsonify, render_template, request
from flask_login import login_required

logger = logging.getLogger(__name__)

admin_bp = Blueprint("admin", __name__)


@admin_bp.route("/dashboard")
@login_required
def dashboard():
    """Main admin dashboard"""
    try:
        from utils.database import get_dashboard_metrics

        current_date = datetime.now()
        metrics = get_dashboard_metrics() or {}

        # Safely get values with fallback defaults
        total_interactions = metrics.get("total_interactions", 0) or 0
        recent_interactions = metrics.get("recent_interactions", 0) or 0
        avg_confidence = metrics.get("avg_confidence", 0) or 0.0
        avg_rating = metrics.get("avg_rating", 0) or 0.0

        recent_chats = _get_recent_chats() or []
        intent_distribution = _get_intent_distribution() or []
        response_time_stats = _get_response_time_stats() or {}

        return render_template(
            "admin/dashboard.html",
            total_interactions=total_interactions,
            recent_interactions=recent_interactions,
            avg_confidence=avg_confidence,
            avg_rating=avg_rating,
            recent_chats=recent_chats,
            intent_distribution=intent_distribution,
            response_time_stats=response_time_stats,
            current_date=current_date,
        )

    except Exception as e:
        logger.error(f"Error loading dashboard: {str(e)}")
        flash("Error loading dashboard data", "error")

        current_date = datetime.now()
        return render_template(
            "admin/dashboard.html",
            total_interactions=0,
            recent_interactions=0,
            avg_confidence=0.0,
            avg_rating=0.0,
            recent_chats=[],
            intent_distribution=[],
            response_time_stats={},
            current_date=current_date,
        )


@admin_bp.route("/metrics")
@login_required
def metrics():
    """Detailed metrics and analytics"""
    try:
        from utils.database import get_detailed_metrics

        # Get comprehensive metrics
        overview = get_detailed_metrics() or {}
        daily_stats = _get_daily_stats() or [{"_id": "Day 1", "count": 0}]
        source_distribution = _get_source_distribution() or [
            {"_id": "None", "count": 0}
        ]
        confidence_distribution = _get_confidence_distribution() or [
            {"_id": 0.0, "count": 0}
        ]
        feedback_distribution = _get_feedback_distribution() or [{"_id": 5, "count": 0}]

        return render_template(
            "admin/metrics.html",
            overview=overview,
            daily_stats=daily_stats,
            source_distribution=source_distribution,
            confidence_distribution=confidence_distribution,
            feedback_distribution=feedback_distribution,
        )

    except Exception as e:
        logger.error(f"Error loading metrics: {str(e)}")
        flash("Error loading metrics data", "error")
        # Also use safe non-empty defaults in the error case!
        return render_template(
            "admin/metrics.html",
            overview={},
            daily_stats=[{"_id": "Day 1", "count": 0}],
            source_distribution=[{"_id": "None", "count": 0}],
            confidence_distribution=[{"_id": 0.0, "count": 0}],
            feedback_distribution=[{"_id": 5, "count": 0}],
        )


@admin_bp.route("/chat_logs")
@login_required
def chat_logs():
    """View and search chat logs"""
    try:
        from utils.database import get_chat_logs

        # Get pagination parameters
        page = int(request.args.get("page", 1))
        per_page = int(request.args.get("per_page", 50))

        # Get filter parameters
        intent_filter = request.args.get("intent", "")
        source_filter = request.args.get("source", "")
        date_from = request.args.get("date_from", "")
        date_to = request.args.get("date_to", "")

        # Build filter dict
        filters = {}
        if intent_filter:
            filters["intent"] = intent_filter
        if source_filter:
            filters["response_source"] = source_filter
        if date_from:
            filters["date_from"] = datetime.fromisoformat(date_from)
        if date_to:
            filters["date_to"] = datetime.fromisoformat(date_to)

        # Get chat logs
        chat_logs, total_count = get_chat_logs(
            page=page, per_page=per_page, filters=filters
        )

        # Calculate pagination info
        total_pages = (total_count + per_page - 1) // per_page

        return render_template(
            "admin/chat_logs.html",
            chat_logs=chat_logs,
            page=page,
            per_page=per_page,
            total_count=total_count,
            total_pages=total_pages,
            filters=filters,
        )

    except Exception as e:
        logger.error(f"Error loading chat logs: {str(e)}")
        flash("Error loading chat logs", "error")
        return render_template(
            "admin/chat_logs.html",
            chat_logs=[],
            page=1,
            per_page=50,
            total_count=0,
            total_pages=0,
            filters={},
        )


@admin_bp.route("/api/metrics/chart_data")
@login_required
def chart_data():
    """API endpoint for chart data"""
    try:
        chart_type = request.args.get("type", "daily_interactions")
        days = int(request.args.get("days", 30))

        from utils.database import get_chart_data

        data = get_chart_data(chart_type, days)

        return jsonify(
            {"success": True, "data": data, "timestamp": datetime.utcnow().isoformat()}
        )

    except Exception as e:
        logger.error(f"Error getting chart data: {str(e)}")
        return jsonify(
            {
                "success": False,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat(),
            }
        ), 500


@admin_bp.route("/api/system/retrain", methods=["POST"])
@login_required
def retrain_models():
    """Retrain AI models"""
    try:
        from flask import current_app

        if not current_app.intent_classifier:
            return jsonify(
                {"success": False, "message": "Intent classifier not available"}
            ), 400

        # Retrain intent classifier
        success = current_app.intent_classifier.train()

        if success:
            logger.info("Models retrained successfully via admin interface")
            return jsonify(
                {
                    "success": True,
                    "message": "Models retrained successfully",
                    "timestamp": datetime.utcnow().isoformat(),
                }
            )
        else:
            return jsonify(
                {"success": False, "message": "Failed to retrain models"}
            ), 500

    except Exception as e:
        logger.error(f"Error retraining models: {str(e)}")
        return jsonify({"success": False, "message": f"Error: {str(e)}"}), 500


@admin_bp.route("/api/system/reindex", methods=["POST"])
@login_required
def reindex_knowledge_base():
    """Reindex knowledge base"""
    try:
        from flask import current_app

        if not current_app.rag_system:
            return jsonify(
                {"success": False, "message": "RAG system not available"}
            ), 400

        # Reindex documents
        success = current_app.rag_system.index_documents()

        if success:
            logger.info("Knowledge base reindexed successfully via admin interface")
            return jsonify(
                {
                    "success": True,
                    "message": "Knowledge base reindexed successfully",
                    "timestamp": datetime.utcnow().isoformat(),
                }
            )
        else:
            return jsonify(
                {"success": False, "message": "Failed to reindex knowledge base"}
            ), 500

    except Exception as e:
        logger.error(f"Error reindexing knowledge base: {str(e)}")
        return jsonify({"success": False, "message": f"Error: {str(e)}"}), 500


@admin_bp.route("/api/export/chat_logs")
@login_required
def export_chat_logs():
    """Export chat logs as CSV"""
    try:
        from flask import Response

        from utils.database import export_chat_logs_csv

        # Get date range
        days = int(request.args.get("days", 30))
        date_from = datetime.utcnow() - timedelta(days=days)

        csv_data = export_chat_logs_csv(date_from)

        return Response(
            csv_data,
            mimetype="text/csv",
            headers={
                "Content-Disposition": f"attachment; filename=chat_logs_{datetime.utcnow().strftime('%Y%m%d')}.csv"
            },
        )

    except Exception as e:
        logger.error(f"Error exporting chat logs: {str(e)}")
        return jsonify({"error": str(e)}), 500


def _get_recent_chats(limit=10):
    """Get recent chat interactions"""
    try:
        from utils.database import get_recent_chat_logs

        return get_recent_chat_logs(limit)
    except Exception as e:
        logger.error(f"Error getting recent chats: {str(e)}")
        return []


def _get_intent_distribution():
    """Get distribution of intents"""
    try:
        from utils.database import get_intent_distribution

        return get_intent_distribution()
    except Exception as e:
        logger.error(f"Error getting intent distribution: {str(e)}")
        return []


def _get_response_time_stats():
    """Get response time statistics"""
    try:
        from utils.database import get_response_time_stats

        return get_response_time_stats()
    except Exception as e:
        logger.error(f"Error getting response time stats: {str(e)}")
        return {}


def _get_daily_stats(days=30):
    """Get daily interaction statistics"""
    try:
        from utils.database import get_daily_interaction_stats

        return get_daily_interaction_stats(days)
    except Exception as e:
        logger.error(f"Error getting daily stats: {str(e)}")
        return []


def _get_source_distribution():
    """Get response source distribution"""
    try:
        from utils.database import get_source_distribution

        return get_source_distribution()
    except Exception as e:
        logger.error(f"Error getting source distribution: {str(e)}")
        return []


def _get_confidence_distribution():
    """Get confidence score distribution"""
    try:
        from utils.database import get_confidence_distribution

        return get_confidence_distribution()
    except Exception as e:
        logger.error(f"Error getting confidence distribution: {str(e)}")
        return []


def _get_feedback_distribution():
    """Get feedback rating distribution"""
    try:
        from utils.database import get_feedback_distribution

        return get_feedback_distribution()
    except Exception as e:
        logger.error(f"Error getting feedback distribution: {str(e)}")
        return []
