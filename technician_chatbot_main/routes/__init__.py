from .admin_routes import admin_bp
from .auth_routes import auth_bp
from .chat_routes import chat_bp

__all__ = ["chat_bp", "admin_bp", "auth_bp"]
