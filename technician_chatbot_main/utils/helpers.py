import html
import logging
import re
import unicodedata
from datetime import datetime

logger = logging.getLogger(__name__)


def sanitize_input(text, max_length=1000):
    """Sanitize user input to prevent XSS and other attacks"""
    if not text or not isinstance(text, str):
        return ""

    # Remove null bytes and other control characters
    text = text.replace("\x00", "")

    # Normalize unicode
    text = unicodedata.normalize("NFKC", text)

    # Escape HTML
    text = html.escape(text)

    # Remove excessive whitespace
    text = re.sub(r"\s+", " ", text).strip()

    # Limit length
    if len(text) > max_length:
        text = text[:max_length]

    return text


def calculate_similarity(text1, text2):
    """Calculate simple word-based similarity between two texts"""
    if not text1 or not text2:
        return 0.0

    words1 = set(text1.lower().split())
    words2 = set(text2.lower().split())

    if not words1 or not words2:
        return 0.0

    intersection = words1.intersection(words2)
    union = words1.union(words2)

    return len(intersection) / len(union) if union else 0.0


def format_response_time(response_time):
    """Format response time for display"""
    if response_time < 1:
        return f"{int(response_time * 1000)}ms"
    else:
        return f"{response_time:.2f}s"


def truncate_text(text, max_length=100, suffix="..."):
    """Truncate text to specified length"""
    if not text or len(text) <= max_length:
        return text

    return text[: max_length - len(suffix)] + suffix


def extract_keywords(text, min_length=3):
    """Extract keywords from text"""
    if not text:
        return []

    # Simple keyword extraction
    words = re.findall(r"\b[a-zA-Z]{" + str(min_length) + ",}\b", text.lower())

    # Remove common stop words
    stop_words = {
        "the",
        "and",
        "but",
        "for",
        "are",
        "with",
        "this",
        "that",
        "from",
        "they",
        "know",
        "want",
        "been",
        "good",
        "much",
        "some",
        "time",
        "very",
        "when",
        "come",
        "here",
        "just",
        "like",
        "long",
        "make",
        "many",
        "over",
        "such",
        "take",
        "than",
        "them",
        "well",
        "were",
    }

    keywords = [word for word in words if word not in stop_words]

    return list(set(keywords))  # Remove duplicates


def validate_rating(rating):
    """Validate feedback rating"""
    try:
        rating = int(rating)
        return 1 <= rating <= 5
    except (ValueError, TypeError):
        return False


def format_timestamp(timestamp, format_str="%Y-%m-%d %H:%M:%S"):
    """Format timestamp for display"""
    if isinstance(timestamp, str):
        try:
            timestamp = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
        except ValueError:
            return timestamp

    if isinstance(timestamp, datetime):
        return timestamp.strftime(format_str)

    return str(timestamp)


def is_safe_filename(filename):
    """Check if filename is safe"""
    if not filename or not isinstance(filename, str):
        return False

    # Check for dangerous patterns
    dangerous_patterns = [
        r"\.\.",
        r"/",
        r"\\",
        r":",
        r"\*",
        r"\?",
        r'"',
        r"<",
        r">",
        r"\|",
    ]

    for pattern in dangerous_patterns:
        if re.search(pattern, filename):
            return False

    return True


def rate_limit_key(request):
    """Generate rate limiting key from request"""
    # Use IP address as key
    return request.environ.get("REMOTE_ADDR", "unknown")


def log_performance(func):
    """Decorator to log function performance"""

    def wrapper(*args, **kwargs):
        start_time = datetime.utcnow()
        try:
            result = func(*args, **kwargs)
            end_time = datetime.utcnow()
            duration = (end_time - start_time).total_seconds()
            logger.debug(f"{func.__name__} executed in {duration:.3f}s")
            return result
        except Exception as e:
            end_time = datetime.utcnow()
            duration = (end_time - start_time).total_seconds()
            logger.error(f"{func.__name__} failed after {duration:.3f}s: {str(e)}")
            raise

    return wrapper


def clean_whitespace(text):
    """Clean excessive whitespace from text"""
    if not text:
        return ""

    # Replace multiple whitespaces with single space
    text = re.sub(r"\s+", " ", text)

    # Remove whitespace at beginning and end of lines
    text = "\n".join(line.strip() for line in text.split("\n"))

    # Remove excessive line breaks
    text = re.sub(r"\n\s*\n\s*\n", "\n\n", text)

    return text.strip()


def mask_sensitive_data(text, patterns=None):
    """Mask sensitive data in text"""
    if not text:
        return text

    default_patterns = [
        (
            r"\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b",
            "XXXX-XXXX-XXXX-XXXX",
        ),  # Credit cards
        (r"\b\d{3}-\d{2}-\d{4}\b", "XXX-XX-XXXX"),  # SSN
        (
            r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",
            "user@domain.com",
        ),  # Email
    ]

    patterns = patterns or default_patterns

    for pattern, replacement in patterns:
        text = re.sub(pattern, replacement, text)

    return text


class TextProcessor:
    """Advanced text processing utility"""

    @staticmethod
    def extract_technical_terms(text):
        """Extract technical terms from text"""
        technical_patterns = [
            r"\b\d+\s*(hp|kw|volts?|amps?|rpm|psi|gpm|cfm)\b",  # Units
            r"\b[A-Z]{2,}\s*\d+[A-Z]?\b",  # Model numbers
            r"\b\d+\.\d+\s*(inches?|mm|cm|feet|meters?)\b",  # Measurements
        ]

        terms = []
        for pattern in technical_patterns:
            terms.extend(re.findall(pattern, text, re.IGNORECASE))

        return terms

    @staticmethod
    def highlight_keywords(text, keywords, css_class="highlight"):
        """Highlight keywords in text with HTML"""
        if not keywords:
            return text

        for keyword in keywords:
            pattern = re.escape(keyword)
            replacement = f'<span class="{css_class}">{keyword}</span>'
            text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)

        return text

    @staticmethod
    def split_into_sentences(text):
        """Split text into sentences"""
        # Simple sentence splitting
        sentences = re.split(r"[.!?]+", text)
        return [s.strip() for s in sentences if s.strip()]


def create_response_metadata(response_data, processing_time=None):
    """Create metadata for API responses"""
    metadata = {
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0",
        "service": "technician_chatbot",
    }

    if processing_time:
        metadata["processing_time"] = processing_time

    if isinstance(response_data, dict):
        metadata.update(
            {
                "response_length": len(str(response_data.get("response", ""))),
                "source": response_data.get("source", "unknown"),
                "confidence": response_data.get("confidence", 0.0),
            }
        )

    return metadata


# Error handling utilities
class ChatbotError(Exception):
    """Base exception for chatbot errors"""

    pass


class InvalidInputError(ChatbotError):
    """Raised when input validation fails"""

    pass


class ProcessingError(ChatbotError):
    """Raised when processing fails"""

    pass


class ExternalServiceError(ChatbotError):
    """Raised when external service fails"""

    pass


def handle_error(error, context=""):
    """Standard error handling"""
    error_id = datetime.utcnow().strftime("%Y%m%d_%H%M%S")

    logger.error(f"Error {error_id}: {str(error)} | Context: {context}")

    return {
        "error_id": error_id,
        "message": "An error occurred processing your request",
        "timestamp": datetime.utcnow().isoformat(),
        "context": context,
    }


# Configuration helpers
def get_config_value(key, default=None, cast_type=None):
    """Get configuration value with type casting"""
    import os

    value = os.getenv(key, default)

    if cast_type and value is not None:
        try:
            if cast_type == bool:
                return str(value).lower() in ("true", "1", "yes", "on")
            else:
                return cast_type(value)
        except (ValueError, TypeError):
            logger.warning(f"Failed to cast config {key}={value} to {cast_type}")
            return default

    return value
