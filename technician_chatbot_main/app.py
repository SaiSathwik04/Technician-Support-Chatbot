import logging
import os
from datetime import datetime

import click
from dotenv import load_dotenv
from flask import Flask, render_template
from flask_login import LoginManager

# Load environment variables
load_dotenv()


def create_app():
    app = Flask(__name__)

    # Configuration
    app.config["SECRET_KEY"] = os.getenv(
        "SECRET_KEY", "dev-secret-key-change-in-production"
    )
    app.config["DEBUG"] = os.getenv("DEBUG", "True").lower() == "true"
    app.config["MONGO_URI"] = os.getenv("MONGO_URI", "mongodb://localhost:27017/")
    app.config["MONGO_DB_NAME"] = os.getenv("MONGO_DB_NAME", "technician_chatbot")
    app.config["PERPLEXITY_API_KEY"] = os.getenv("PERPLEXITY_API_KEY")
    app.config["PERPLEXITY_API_URL"] = os.getenv(
        "PERPLEXITY_API_URL", "https://api.perplexity.ai/chat/completions"
    )
    app.config["PERPLEXITY_MODEL"] = os.getenv("PERPLEXITY_MODEL", "sonar")

    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[logging.FileHandler("logs/app.log"), logging.StreamHandler()],
    )

    # Create directories if they don't exist
    os.makedirs("logs", exist_ok=True)
    os.makedirs("knowledge_base/technician_manuals", exist_ok=True)
    os.makedirs("knowledge_base/vector_store", exist_ok=True)
    os.makedirs("data", exist_ok=True)

    # Initialize Login Manager
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = "auth.login"
    login_manager.login_message = "Please log in to access the admin panel."

    @login_manager.user_loader
    def load_user(user_id):
        from utils.database import get_user_by_id

        return get_user_by_id(user_id)

    # Initialize AI models
    try:
        from models.intent_classifier import IntentClassifier
        from models.rag_system import RAGSystem
        from models.rule_based_bot import RuleBasedBot

        app.intent_classifier = IntentClassifier()
        app.rule_based_bot = RuleBasedBot()
        app.rag_system = RAGSystem()

        logging.info("AI models initialized successfully")
    except Exception as e:
        logging.error(f"Error initializing AI models: {str(e)}")
        # Create dummy models to prevent crashes
        app.intent_classifier = None
        app.rule_based_bot = None
        app.rag_system = None

    # Register blueprints
    from routes.admin_routes import admin_bp
    from routes.auth_routes import auth_bp
    from routes.chat_routes import chat_bp

    app.register_blueprint(chat_bp, url_prefix="/api/chat")
    app.register_blueprint(admin_bp, url_prefix="/admin")
    app.register_blueprint(auth_bp, url_prefix="/auth")

    # Main route
    @app.route("/")
    def index():
        return render_template("index.html")

    # Health check
    @app.route("/health")
    def health():
        return {"status": "healthy", "message": "Technician Support Chatbot is running"}

    # CLI commands
    @app.cli.command("init-db-command")
    def init_db_command():
        """Initialize the database."""
        try:
            from utils.database import init_db

            init_db()
            click.echo("Database initialized successfully!")
        except Exception as e:
            click.echo(f"Error initializing database: {str(e)}")

    @app.cli.command("train-models")
    def train_models_command():
        """Train the AI models."""
        try:
            if app.intent_classifier:
                app.intent_classifier.train()
                click.echo("Models trained successfully!")
            else:
                click.echo("Intent classifier not available")
        except Exception as e:
            click.echo(f"Error training models: {str(e)}")

    @app.cli.command("index-documents")
    @click.argument("documents_path", default="knowledge_base/technician_manuals")
    def index_documents_command(documents_path):
        """Index documents for RAG system."""
        try:
            if app.rag_system:
                app.rag_system.index_documents(documents_path)
                click.echo("Documents indexed successfully!")
            else:
                click.echo("RAG system not available")
        except Exception as e:
            click.echo(f"Error indexing documents: {str(e)}")

    @app.context_processor
    def inject_now():
        return {"current_year": datetime.now().year}

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(debug=True, host="0.0.0.0", port=5000)
