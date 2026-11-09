import logging
import os

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required, login_user, logout_user

logger = logging.getLogger(__name__)

auth_bp = Blueprint("auth", __name__)


class AdminUser:
    """Simple admin user class for Flask-Login"""

    def __init__(self, user_id, username):
        self.id = user_id
        self.username = username
        self.is_authenticated = True
        self.is_active = True
        self.is_anonymous = False

    def get_id(self):
        return str(self.id)


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    """Admin login page"""
    if current_user.is_authenticated:
        return redirect(url_for("admin.dashboard"))

    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        # Get admin credentials from environment
        admin_username = os.getenv("ADMIN_USERNAME", "admin")
        admin_password = os.getenv("ADMIN_PASSWORD", "admin123")

        if username == admin_username and password == admin_password:
            # Create admin user and log in
            admin_user = AdminUser(user_id="admin", username=username)
            login_user(admin_user, remember=True)

            logger.info(f"Admin login successful: {username}")
            flash("Login successful!", "success")

            # Redirect to next page or dashboard
            next_page = request.args.get("next")
            if next_page:
                return redirect(next_page)
            return redirect(url_for("admin.dashboard"))
        else:
            logger.warning(f"Failed admin login attempt: {username}")
            flash("Invalid username or password", "error")

    return render_template("admin/login.html")


@auth_bp.route("/logout")
@login_required
def logout():
    """Admin logout"""
    username = current_user.username if hasattr(current_user, "username") else "unknown"
    logout_user()

    logger.info(f"Admin logout: {username}")
    flash("You have been logged out", "info")

    return redirect(url_for("index"))
