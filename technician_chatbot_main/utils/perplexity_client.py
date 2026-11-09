import logging
import os
import time

import requests

logger = logging.getLogger(__name__)


class PerplexityClient:
    """Client for Perplexity Pro API"""

    def __init__(self):
        self.api_key = os.getenv("PERPLEXITY_API_KEY")
        self.api_url = os.getenv(
            "PERPLEXITY_API_URL", "https://api.perplexity.ai/chat/completions"
        )
        self.model = os.getenv("PERPLEXITY_MODEL", "sonar-medium-online")
        self.max_tokens = int(os.getenv("MAX_RESPONSE_LENGTH", 500))
        self.timeout = 30

        if not self.api_key:
            logger.warning("Perplexity API key not configured")

    def query(self, user_message, context="", max_retries=3):
        """Query Perplexity API with user message and optional context"""
        logger.info(
            f"Sending request to Perplexity API: model={self.model}, user_message='{user_message[:50]}...'"
        )
        logger.debug(f"Context sent: {context[:100]}")
        if not self.api_key:
            return {
                "success": False,
                "error": "Perplexity API key not configured",
                "response": None,
            }

        # Build system message with technical focus and topic restrictions
        system_message = self._build_system_message(context)

        # Check if query is technical
        if not self._is_technical_query(user_message):
            return {
                "success": True,
                "response": "I can only assist with technical maintenance and equipment-related questions. Please ask about troubleshooting, repairs, maintenance procedures, or safety protocols.",
                "model": self.model,
                "tokens_used": 0,
                "response_time": 0.001,
            }

        # Prepare request
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_message},
                {"role": "user", "content": user_message},
            ],
            "max_tokens": self.max_tokens,
            "temperature": 0.2,  # Lower temperature for more consistent technical responses
            "top_p": 0.9,
            "stream": False,
        }

        # Make request with retries
        for attempt in range(max_retries):
            try:
                start_time = time.time()

                response = requests.post(
                    self.api_url, headers=headers, json=payload, timeout=self.timeout
                )

                response_time = time.time() - start_time

                if response.status_code == 200:
                    result = response.json()

                    if "choices" in result and len(result["choices"]) > 0:
                        response_text = result["choices"][0]["message"]["content"]

                        # Apply final topic filter
                        if self._contains_non_technical_content(response_text):
                            response_text = "I can only provide assistance with technical maintenance and equipment-related topics. Please ask about troubleshooting, repairs, or maintenance procedures."

                        return {
                            "success": True,
                            "response": response_text,
                            "model": result.get("model", self.model),
                            "tokens_used": result.get("usage", {}).get(
                                "total_tokens", 0
                            ),
                            "response_time": response_time,
                        }
                    else:
                        logger.error("Invalid response format from Perplexity API")
                        return {
                            "success": False,
                            "error": "Invalid response format",
                            "response": None,
                        }

                elif response.status_code == 401:
                    logger.error("Perplexity API authentication failed")
                    return {
                        "success": False,
                        "error": "Authentication failed - check API key",
                        "response": None,
                    }

                elif response.status_code == 429:
                    # Rate limit - wait and retry
                    wait_time = 2**attempt  # Exponential backoff
                    logger.warning(f"Rate limited, waiting {wait_time} seconds...")
                    time.sleep(wait_time)
                    continue

                else:
                    logger.error(
                        f"Perplexity API error: {response.status_code} - {response.text}"
                    )
                    return {
                        "success": False,
                        "error": f"API error: {response.status_code}",
                        "response": None,
                    }

            except requests.exceptions.Timeout:
                logger.warning(f"Perplexity API timeout (attempt {attempt + 1})")
                if attempt == max_retries - 1:
                    return {
                        "success": False,
                        "error": "Request timeout",
                        "response": None,
                    }

            except requests.exceptions.RequestException as e:
                logger.error(f"Perplexity API request error: {str(e)}")
                return {
                    "success": False,
                    "error": f"Request error: {str(e)}",
                    "response": None,
                }

            except Exception as e:
                logger.error(f"Unexpected error querying Perplexity API: {str(e)}")
                return {
                    "success": False,
                    "error": f"Unexpected error: {str(e)}",
                    "response": None,
                }

        return {"success": False, "error": "Max retries exceeded", "response": None}

    def _build_system_message(self, context=""):
        """Build system message with technical focus and context"""
        system_message = """You are a specialized technical support assistant for industrial maintenance technicians. 

STRICT GUIDELINES:
- ONLY answer questions about technical maintenance, equipment troubleshooting, repairs, and safety procedures
- Focus on motors, pumps, HVAC systems, electrical systems, mechanical equipment, engines and industrial machinery
- Provide practical, actionable advice with specific steps
- Always emphasize safety procedures and proper lockout/tagout when relevant
- If asked about non-technical topics, politely redirect to technical subjects

RESPONSE REQUIREMENTS:
- Keep responses under 400 words
- Use clear, structured formatting with bullet points or numbered steps
- Include relevant safety warnings
- Be specific and practical
- Cite equipment types, specifications, and procedures when helpful

TOPICS I CAN HELP WITH:
- Equipment troubleshooting (motors, pumps, compressors, etc.)
- Maintenance procedures and schedules  
- Safety protocols (LOTO, PPE, hazard assessment)
- Electrical systems and controls
- Mechanical systems diagnostics
- HVAC maintenance and repair
- Preventive maintenance planning

TOPICS I CANNOT HELP WITH:
- Non-technical subjects (sports, entertainment, politics, etc.)
- Personal advice unrelated to work
- Financial or business strategy
- General knowledge questions outside maintenance/technical scope"""

        if context:
            system_message += f"\n\nRELEVANT CONTEXT:\n{context}\n\nUse this context to provide more specific and accurate technical guidance."

        return system_message

    def _is_technical_query(self, query):
        """Check if query is technical/maintenance related"""
        technical_keywords = [
            # Equipment
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
            # Problems/Actions
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
            "inspect",
            "test",
            "measure",
            "malfunction",
            "failure",
            "broken",
            "noise",
            "vibration",
            "leak",
            "overheat",
            # Technical terms
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
            # Safety
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
        ]

        query_lower = query.lower()
        return any(keyword in query_lower for keyword in technical_keywords)

    def _contains_non_technical_content(self, response):
        """Check if response contains non-technical content"""
        non_technical_indicators = [
            "sports",
            "entertainment",
            "politics",
            "celebrity",
            "movie",
            "music",
            "food",
            "recipe",
            "weather",
            "news",
            "social media",
            "gaming",
            "personal relationship",
            "dating",
            "finance",
            "investment",
            "stock market",
        ]

        response_lower = response.lower()
        return any(
            indicator in response_lower for indicator in non_technical_indicators
        )

    def test_connection(self):
        """Test connection to Perplexity API"""
        test_result = self.query("What is a motor?")

        return {
            "connected": test_result["success"],
            "model": self.model,
            "api_configured": bool(self.api_key),
            "error": test_result.get("error") if not test_result["success"] else None,
        }
