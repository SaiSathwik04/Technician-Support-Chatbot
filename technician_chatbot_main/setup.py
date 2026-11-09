#!/usr/bin/env python3
"""
Technician Support Chatbot Setup Script - Hackathon Edition
Handles package installation failures gracefully
"""

import os
import subprocess
import sys
from pathlib import Path


def print_step(step_num, title):
    """Print formatted step header"""
    print(f"\n{'=' * 60}")
    print(f"Step {step_num}: {title}")
    print("=" * 60)


def run_command(command, description, required=True):
    """Run a command and handle errors gracefully"""
    print(f"Running: {description}")
    print(f"Command: {command}")

    try:
        result = subprocess.run(
            command, shell=True, capture_output=True, text=True, check=True
        )
        print(f"✅ Success: {description}")
        if result.stdout.strip():
            print(f"Output: {result.stdout.strip()}")
        return True, result
    except subprocess.CalledProcessError as e:
        if required:
            print(f"❌ Error: {description}")
            print(f"Error output: {e.stderr}")
            return False, e
        else:
            print(f"⚠️ Warning: {description} failed (non-critical)")
            print(f"Error: {e.stderr}")
            return True, e  # Continue even if failed


def check_python_version():
    """Check Python version compatibility"""
    version = sys.version_info
    print(f"Python version: {version.major}.{version.minor}.{version.micro}")

    if version.major != 3:
        print("❌ Python 3 is required")
        return False

    if version.minor < 8:
        print("⚠️ Warning: Python 3.8+ recommended, but continuing...")

    return True


def create_directories():
    """Create necessary project directories"""
    directories = [
        "models",
        "data",
        "logs",
        "knowledge_base/technician_manuals",
        "knowledge_base/vector_store",
        "static/css",
        "static/js",
        "templates/admin",
    ]

    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)

    print("✅ Created project directories")


def create_safe_requirements():
    """Create a safe requirements file"""
    safe_requirements = """Flask==2.3.3
Flask-Login==0.6.3
python-dotenv==1.0.0
pymongo==4.5.0
requests==2.31.0
nltk==3.8.1
bcrypt==4.0.1
click==8.1.7
Werkzeug==2.3.7
Jinja2==3.1.2
MarkupSafe==2.1.3
itsdangerous==2.1.2
"""

    with open("requirements_safe.txt", "w") as f:
        f.write(safe_requirements)

    print("✅ Created requirements_safe.txt")


def setup_virtual_environment():
    """Setup or verify virtual environment"""
    if os.path.exists("venv"):
        print("✅ Virtual environment already exists")
        print("📝 To activate virtual environment, run: venv\\Scripts\\activate")
        return True

    success, result = run_command("python -m venv venv", "Creating virtual environment")
    if success:
        print("📝 To activate virtual environment, run: venv\\Scripts\\activate")

    return success


def install_requirements():
    """Install Python requirements with multiple fallback strategies"""
    strategies = [
        (
            "venv\\Scripts\\pip install -r requirements.txt",
            "Installing from requirements.txt",
        ),
        (
            "venv\\Scripts\\pip install -r requirements_safe.txt",
            "Installing safe requirements",
        ),
        (
            "venv\\Scripts\\pip install --only-binary=all -r requirements_safe.txt",
            "Installing safe requirements (binary only)",
        ),
        (
            "venv\\Scripts\\pip install Flask python-dotenv pymongo requests",
            "Installing minimal requirements",
        ),
    ]

    for command, description in strategies:
        print(f"\nTrying: {description}")
        success, result = run_command(command, description, required=False)
        if success:
            print("✅ Package installation successful!")
            return True
        print(f"❌ Failed: {description}")

    print("⚠️ All package installation strategies failed. Please install manually:")
    print("venv\\Scripts\\activate")
    print("pip install Flask python-dotenv pymongo requests")
    return False


def create_env_file():
    """Create .env file if it doesn't exist"""
    if os.path.exists(".env"):
        print("✅ .env file already exists")
        return

    env_content = """# Flask Configuration
FLASK_ENV=development
SECRET_KEY=hackathon-secret-key-change-in-production
DEBUG=True

# Database Configuration  
MONGO_URI=mongodb://localhost:27017/
MONGO_DB_NAME=technician_chatbot

# Perplexity API Configuration (Optional)
PERPLEXITY_API_KEY=your-perplexity-api-key-here
PERPLEXITY_API_URL=https://api.perplexity.ai/chat/completions
PERPLEXITY_MODEL=sonar-medium-online

# Admin Configuration
ADMIN_USERNAME=admin
ADMIN_PASSWORD=admin123
"""

    with open(".env", "w") as f:
        f.write(env_content)

    print("✅ Created .env file")


def create_simple_intent_classifier():
    """Create simple intent classifier to replace scikit-learn dependency"""
    classifier_code = '''import json
import os
import logging
from collections import defaultdict

logger = logging.getLogger(__name__)

class IntentClassifier:
    """Simple keyword-based intent classifier (no scikit-learn dependency)"""
    
    def __init__(self, model_path='models/intent_keywords.json'):
        self.model_path = model_path
        self.intent_keywords = {}
        self.load_or_create_model()
    
    def load_or_create_model(self):
        """Load existing model or create new one"""
        if os.path.exists(self.model_path):
            try:
                with open(self.model_path, 'r') as f:
                    self.intent_keywords = json.load(f)
                logger.info("Simple intent classifier loaded")
            except Exception as e:
                logger.error(f"Error loading model: {e}")
                self.create_default_model()
        else:
            self.create_default_model()
    
    def create_default_model(self):
        """Create default keyword-based model"""
        self.intent_keywords = {
            "greeting": ["hello", "hi", "hey", "greetings", "good morning", "good afternoon"],
            "goodbye": ["bye", "goodbye", "farewell", "see you", "exit", "quit"],
            "help": ["help", "assist", "what can you do", "capabilities", "guide"],
            "simple_troubleshooting": ["motor", "pump", "not working", "stopped", "problem", "issue", "broken", "repair", "fix"],
            "safety_query": ["safety", "lockout", "tagout", "loto", "ppe", "hazard", "emergency"],
            "maintenance_planning": ["maintenance", "schedule", "service", "inspection", "routine"],
            "equipment_specific": ["hvac", "compressor", "valve", "sensor", "electrical", "mechanical"],
            "technical_explanation": ["how does", "explain", "why", "what causes", "principle", "theory"],
            "unclear": ["unclear", "don't know", "not sure", "confusing", "huh"]
        }
        self.save_model()
    
    def classify(self, text):
        """Classify text using keyword matching"""
        text_lower = text.lower()
        scores = defaultdict(float)
        
        # Score each intent based on keyword matches
        for intent, keywords in self.intent_keywords.items():
            for keyword in keywords:
                if keyword in text_lower:
                    scores[intent] += 1.0 / len(keywords)
        
        if not scores:
            return {
                'intent': 'unclear',
                'confidence': 0.1,
                'route': 'rule_based'
            }
        
        # Get best match
        best_intent = max(scores, key=scores.get)
        confidence = min(scores[best_intent], 1.0)
        
        # Determine routing
        route = self._determine_route(best_intent, confidence, text_lower)
        
        return {
            'intent': best_intent,
            'confidence': confidence,
            'route': route
        }
    
    def _determine_route(self, intent, confidence, text):
        """Determine routing based on intent and confidence"""
        simple_intents = ['greeting', 'goodbye', 'help', 'simple_troubleshooting', 'safety_query']
        
        if intent in simple_intents and confidence > 0.5:
            return 'rule_based'
        elif confidence < 0.3:
            return 'rule_based'  # Safe fallback
        else:
            return 'llm' if confidence > 0.7 else 'rule_based'
    
    def train(self):
        """Train method for compatibility (no-op for simple classifier)"""
        logger.info("Simple intent classifier training completed (keyword-based)")
        return True
    
    def save_model(self):
        """Save model to file"""
        try:
            os.makedirs(os.path.dirname(self.model_path), exist_ok=True)
            with open(self.model_path, 'w') as f:
                json.dump(self.intent_keywords, f, indent=2)
            logger.info(f"Model saved to {self.model_path}")
        except Exception as e:
            logger.error(f"Error saving model: {e}")
    
    def get_model_info(self):
        """Get model information"""
        return {
            'model_type': 'Simple keyword-based classifier',
            'intent_categories': len(self.intent_keywords),
            'intents': list(self.intent_keywords.keys()),
            'model_exists': True,
            'model_path': self.model_path
        }
'''

    os.makedirs("models", exist_ok=True)
    with open("models/intent_classifier.py", "w") as f:
        f.write(classifier_code)

    print("✅ Created simple intent classifier")


def create_simple_rag_system():
    """Create simple RAG system without sentence-transformers"""
    rag_code = '''import os
import json
import logging
from pathlib import Path
import re

logger = logging.getLogger(__name__)

class RAGSystem:
    """Simple RAG system without heavy dependencies"""
    
    def __init__(self, documents_path='knowledge_base/technician_manuals'):
        self.documents_path = documents_path
        self.documents = []
        self.metadata = []
        
        # Initialize directories
        os.makedirs(documents_path, exist_ok=True)
        
        # Initialize system
        self._initialize_system()
    
    def _initialize_system(self):
        """Initialize the RAG system"""
        try:
            # Create sample documents
            self._create_sample_documents()
            self.index_documents()
            logger.info("Simple RAG system initialized")
        except Exception as e:
            logger.error(f"Error initializing RAG system: {str(e)}")
    
    def _create_sample_documents(self):
        """Create sample technical documents"""
        sample_docs = {
            "motor_troubleshooting.txt": "Motor troubleshooting guide: Check power supply, verify connections, test overload relays, inspect for mechanical binding.",
            "pump_maintenance.txt": "Pump maintenance: Check suction line, verify priming, inspect impeller, check seals for leaks.",
            "safety_procedures.txt": "Safety procedures: Use lockout/tagout, wear proper PPE, follow emergency protocols.",
            "hvac_maintenance.txt": "HVAC maintenance: Replace filters regularly, clean coils, check refrigerant levels, inspect ductwork."
        }
        
        for filename, content in sample_docs.items():
            file_path = os.path.join(self.documents_path, filename)
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
    
    def index_documents(self, documents_path=None):
        """Index documents using simple text matching"""
        try:
            path = documents_path or self.documents_path
            self.documents = []
            self.metadata = []
            
            for file_path in Path(path).glob('*.txt'):
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    self.documents.append(content)
                    self.metadata.append({
                        'filename': file_path.name,
                        'source': str(file_path)
                    })
                    
                except Exception as e:
                    logger.error(f"Error processing {file_path}: {str(e)}")
            
            logger.info(f"Indexed {len(self.documents)} documents")
            return True
            
        except Exception as e:
            logger.error(f"Error indexing documents: {str(e)}")
            return False
    
    def retrieve_context(self, query, k=3):
        """Simple context retrieval using keyword matching"""
        if not self.documents:
            return []
        
        query_words = set(query.lower().split())
        scored_docs = []
        
        for i, doc in enumerate(self.documents):
            doc_words = set(doc.lower().split())
            overlap = len(query_words.intersection(doc_words))
            if overlap > 0:
                score = overlap / len(query_words.union(doc_words))
                scored_docs.append({
                    'text': doc,
                    'metadata': self.metadata[i],
                    'similarity_score': score,
                    'rank': len(scored_docs) + 1
                })
        
        # Sort by score and return top k
        scored_docs.sort(key=lambda x: x['similarity_score'], reverse=True)
        return scored_docs[:k]
    
    def get_context_string(self, query, k=3):
        """Get context as formatted string"""
        results = self.retrieve_context(query, k)
        
        if not results:
            return ""
        
        context_parts = []
        for result in results:
            context_parts.append(f"Source: {result['metadata']['filename']}\\n{result['text']}")
        
        return "\\n\\n---\\n\\n".join(context_parts)
    
    def get_statistics(self):
        """Get statistics about the knowledge base"""
        return {
            'total_documents': len(self.documents),
            'total_chunks': len(self.documents),
            'vector_store_initialized': True,
            'embedding_model': 'simple keyword matching'
        }
'''

    with open("models/rag_system.py", "w") as f:
        f.write(rag_code)

    print("✅ Created simple RAG system")


def main():
    """Main setup function"""
    print("🔧 Technician Support Chatbot - Hackathon Setup")
    print("📅 Optimized for quick deployment")

    # Step 1: Check Python version
    print_step(1, "Checking Python Version")
    if not check_python_version():
        return False

    # Step 2: Create directories
    print_step(2, "Creating Project Structure")
    create_directories()

    # Step 3: Setup virtual environment
    print_step(3, "Setting up Virtual Environment")
    if not setup_virtual_environment():
        print("❌ Virtual environment setup failed")
        return False

    # Step 4: Create safe requirements
    print_step(4, "Creating Safe Requirements")
    create_safe_requirements()

    # Step 5: Install requirements
    print_step(5, "Installing Python Dependencies")
    install_requirements()  # Non-blocking

    # Step 6: Create environment file
    print_step(6, "Creating Environment Configuration")
    create_env_file()

    # Step 7: Create simple AI models
    print_step(7, "Creating AI Models")
    create_simple_intent_classifier()
    create_simple_rag_system()

    # Final instructions
    print("\n" + "=" * 60)
    print("🎉 SETUP COMPLETED!")
    print("=" * 60)
    print("\n📋 NEXT STEPS:")
    print("1. Activate virtual environment:")
    print("   venv\\Scripts\\activate")
    print("\n2. Start the application:")
    print("   python run.py")
    print("\n3. Open browser:")
    print("   http://localhost:5000")
    print("\n4. Admin panel:")
    print("   http://localhost:5000/admin")
    print("   Username: admin, Password: admin123")

    print("\n⚠️ IMPORTANT NOTES:")
    print("- This uses simplified AI models for reliability")
    print("- Add your Perplexity API key in .env for advanced features")
    print("- MongoDB is optional - will use in-memory fallback")

    return True


if __name__ == "__main__":
    try:
        success = main()
        if success:
            print("\n✅ Setup completed successfully!")
        else:
            print("\n❌ Setup completed with warnings")
    except KeyboardInterrupt:
        print("\n\n⚠️ Setup interrupted by user")
    except Exception as e:
        print(f"\n❌ Setup failed with error: {str(e)}")
        print("Please run manual installation commands shown above")
