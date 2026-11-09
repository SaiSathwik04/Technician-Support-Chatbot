#!/usr/bin/env python3
"""
Technician Support Chatbot - Application Runner
"""

import os

from app import create_app

if __name__ == "__main__":
    app = create_app()

    # Get configuration from environment
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", 5000))
    debug = os.getenv("DEBUG", "True").lower() == "true"

    print("🔧 Starting Technician Support Chatbot...")
    print(f"📡 Server: http://{host}:{port}")
    print(f"🔧 Chatbot: http://{host}:{port}")
    print(f"👨‍💼 Admin: http://{host}:{port}/admin")
    print("=" * 50)

    app.run(host=host, port=port, debug=debug)
