import json
import logging
import os
import re

logger = logging.getLogger(__name__)


class RuleBasedBot:
    """Rule-based chatbot for handling common technician queries"""

    def __init__(self, rules_path="data/rules_db.json"):
        self.rules_path = rules_path
        self.rules = self._load_rules()

    def _load_rules(self):
        """Load rules database"""
        if os.path.exists(self.rules_path):
            try:
                with open(self.rules_path, "r") as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Error loading rules: {str(e)}")

        # Create default rules if file doesn't exist
        default_rules = self._create_default_rules()
        self._save_rules(default_rules)
        return default_rules

    def _create_default_rules(self):
        """Create default rule database"""
        return {
            "greetings": {
                "patterns": [
                    "hello",
                    "hi",
                    "hey",
                    "good morning",
                    "good afternoon",
                    "greetings",
                ],
                "responses": [
                    "Hello! I'm here to help you with technical and maintenance questions. What can I assist you with today?",
                    "Hi there! I'm your technical support assistant. How can I help you with your maintenance needs?",
                    "Good day! I'm ready to help with any technical or equipment-related questions you have.",
                ],
            },
            "goodbye": {
                "patterns": [
                    "bye",
                    "goodbye",
                    "see you",
                    "farewell",
                    "thanks goodbye",
                    "exit",
                ],
                "responses": [
                    "Goodbye! Feel free to return anytime you need technical assistance.",
                    "Take care! I'm here whenever you need help with maintenance or technical issues.",
                    "See you later! Stay safe and don't hesitate to ask if you have more questions.",
                ],
            },
            "motor_wont_start": {
                "patterns": [
                    "motor won't start",
                    "motor not starting",
                    "engine won't start",
                    "motor dead",
                    "motor problem",
                ],
                "responses": [
                    """Motor not starting? Here's a quick checklist:

🔍 **BASIC CHECKS:**
1. **Power Supply** - Verify voltage at motor terminals
2. **Overload Relays** - Reset if tripped  
3. **Motor Starter Contacts** - Check for burning or pitting
4. **Control Voltage** - Ensure proper voltage to starter coil
5. **Mechanical Binding** - Try turning shaft by hand
6. **Fuses/Breakers** - Verify all are in good condition

⚠️ **SAFETY FIRST**: Always use proper lockout/tagout procedures!

If these steps don't resolve the issue, you may need to test motor windings for continuity and insulation resistance."""
                ],
            },
            "pump_problems": {
                "patterns": [
                    "pump not working",
                    "pump failure",
                    "no flow",
                    "pump stopped",
                    "pump issue",
                ],
                "responses": [
                    """Pump troubleshooting steps:

💧 **SYSTEMATIC DIAGNOSIS:**
1. **Power & Motor Check** - Verify pump is getting power and motor is running
2. **Suction Line** - Check for blockages or air leaks
3. **Priming** - Ensure pump is properly primed
4. **Discharge Valve** - Verify it's open
5. **Cavitation Check** - Listen for unusual noise/vibration
6. **Impeller Inspection** - Look for damage or clogging
7. **System Pressure** - Verify it's not too high
8. **Seal Inspection** - Check for leakage

💡 **Pro Tip**: For centrifugal pumps, also verify rotation direction is correct."""
                ],
            },
            "no_power": {
                "patterns": [
                    "no power",
                    "power outage",
                    "electrical problem",
                    "no electricity",
                    "power issue",
                ],
                "responses": [
                    """No power troubleshooting:

⚡ **ELECTRICAL DIAGNOSTICS:**
1. **Main Breaker Panel** - Check for tripped breakers
2. **Power Source** - Use multimeter to verify voltage
3. **Fuse Inspection** - Check all fuses in the circuit
4. **Connection Check** - Look for loose or burned connections
5. **GFCI Outlets** - Test and reset if necessary
6. **Wiring Inspection** - Check for damaged wiring or conduit
7. **Transformer Check** - For low voltage systems

⚠️ **CRITICAL SAFETY**: Always use proper PPE and lockout/tagout procedures when working with electrical systems!

🔧 **Tools Needed**: Multimeter, voltage tester, insulated tools"""
                ],
            },
            "hvac_issues": {
                "patterns": [
                    "hvac problem",
                    "air conditioning",
                    "heating problem",
                    "ventilation issue",
                    "hvac",
                ],
                "responses": [
                    """HVAC system troubleshooting:

🌡️ **SYSTEMATIC APPROACH:**

**Basic Checks:**
1. **Thermostat** - Check settings and battery
2. **Air Filters** - Replace if dirty (check monthly)
3. **Power Supply** - Verify power to HVAC unit
4. **Circuit Breakers** - Check HVAC-specific breakers

**System Inspection:**
5. **Ductwork** - Look for leaks or blockages
6. **Condenser Coils** - Clean outdoor unit coils
7. **Refrigerant Levels** - Requires certified technician
8. **Blower Motor** - Check motor and belts
9. **Airflow** - Verify proper airflow at vents

🔄 **Maintenance Tip**: Regular maintenance prevents most HVAC issues!
📅 **Schedule**: Change filters monthly, professional service twice yearly"""
                ],
            },
            "safety_procedures": {
                "patterns": [
                    "safety",
                    "lockout tagout",
                    "loto",
                    "safety procedure",
                    "ppe",
                    "safety protocol",
                ],
                "responses": [
                    """Essential safety procedures:

🔒 **LOCKOUT/TAGOUT (LOTO):**
1. **Notification** - Inform affected personnel
2. **Proper Shutdown** - Follow equipment shutdown procedure
3. **Energy Isolation** - Isolate electrical, pneumatic, hydraulic sources
4. **Lock & Tag Application** - Apply personal locks and danger tags
5. **Verification** - Test to ensure complete energy isolation
6. **Work Completion** - Only lock owner removes their lock

🦺 **PPE Requirements:**
- Safety glasses/goggles
- Hard hat (overhead hazards)
- Work gloves (task-appropriate)
- Steel-toed boots
- Hearing protection (loud areas)
- Fall protection (above 6 feet)

⚠️ **Remember**: Always follow company-specific safety protocols!"""
                ],
            },
            "maintenance_schedule": {
                "patterns": [
                    "maintenance schedule",
                    "when to service",
                    "maintenance frequency",
                    "preventive maintenance",
                ],
                "responses": [
                    """General maintenance frequencies:

📅 **MAINTENANCE SCHEDULE:**

**DAILY CHECKS:**
- Visual inspections
- Operating parameter checks
- Lubrication points
- Safety device verification

**WEEKLY MAINTENANCE:**
- Detailed inspections
- Filter checks
- Belt tension verification
- Fluid level checks

**MONTHLY TASKS:**
- Vibration analysis
- Oil sampling
- Alignment checks
- Performance testing

**QUARTERLY MAINTENANCE:**
- Major inspections
- Calibrations
- Bearing assessments
- Deep cleaning

**ANNUAL OVERHAULS:**
- Component replacements
- Major servicing
- Record updates
- Performance reviews

📝 **Note**: Always consult equipment manuals for specific intervals!"""
                ],
            },
            "troubleshooting_steps": {
                "patterns": [
                    "troubleshooting",
                    "diagnostic",
                    "how to diagnose",
                    "finding problem",
                    "problem solving",
                ],
                "responses": [
                    """Systematic troubleshooting approach:

🔍 **PROFESSIONAL METHODOLOGY:**

**1️⃣ INFORMATION GATHERING**
   - What was happening when problem occurred?
   - Any recent changes or maintenance?
   - Error codes or unusual symptoms?

**2️⃣ VISUAL INSPECTION**
   - Look for obvious damage, leaks, loose connections
   - Check indicators and displays
   - Listen for unusual noises

**3️⃣ CHECK BASICS**
   - Power supply and connections
   - Control settings and parameters
   - Mechanical connections

**4️⃣ SYSTEMATIC TESTING**
   - Work from simple to complex
   - Test one component at a time
   - Document all findings

**5️⃣ VERIFY SOLUTION**
   - Test operation after repair
   - Monitor for problem recurrence
   - Update maintenance records

🔍 **Remember**: Patience and systematic approach prevent misdiagnosis!"""
                ],
            },
            "help": {
                "patterns": [
                    "help",
                    "what can you do",
                    "capabilities",
                    "commands",
                    "assist",
                ],
                "responses": [
                    """I can help you with:

🔧 **TECHNICAL SUPPORT AREAS:**

**Equipment Troubleshooting:**
- Motors, pumps, HVAC systems
- Electrical and mechanical issues
- Performance problems

**Maintenance Support:**
- Preventive maintenance schedules
- Maintenance procedures
- Equipment care guidelines

**Safety Guidance:**
- Lockout/tagout procedures
- PPE requirements
- Safety protocols

**Technical Assistance:**
- Diagnostic procedures
- Step-by-step guides
- Best practices

**Example questions:**
- "Motor won't start"
- "How often should I service the pump?"
- "What are the lockout tagout procedures?"
- "HVAC system not cooling"
- "Safety procedures for electrical work"

Just describe your issue or ask about any maintenance topic!"""
                ],
            },
        }

    def respond(self, user_input, intent=None):
        """Generate response based on user input and intent"""
        try:
            # Sanitize input
            clean_input = self._sanitize_input(user_input)

            if not clean_input:
                return {
                    "response": "I didn't receive a clear message. Could you please rephrase your question?",
                    "rule_matched": "error",
                    "confidence": 0.0,
                    "source": "rule_based",
                }

            # Find matching rule
            best_match = self._find_best_match(clean_input, intent)

            if best_match:
                rule_name, similarity_score = best_match
                response = self._get_response(rule_name)

                return {
                    "response": response,
                    "rule_matched": rule_name,
                    "confidence": similarity_score,
                    "source": "rule_based",
                }
            else:
                # No good match found
                return {
                    "response": self._get_fallback_response(clean_input),
                    "rule_matched": "fallback",
                    "confidence": 0.3,
                    "source": "rule_based",
                }

        except Exception as e:
            logger.error(f"Error in rule-based response: {str(e)}")
            return {
                "response": "I'm sorry, I encountered an error. Please try rephrasing your question or contact technical support.",
                "rule_matched": "error",
                "confidence": 0.0,
                "source": "rule_based",
            }

    def _find_best_match(self, user_input, intent_hint=None):
        """Find the best matching rule for user input"""
        user_input_lower = user_input.lower()
        best_match = None
        best_score = 0.0

        for rule_name, rule_data in self.rules.items():
            for pattern in rule_data["patterns"]:
                # Calculate similarity
                similarity = self._calculate_similarity(
                    user_input_lower, pattern.lower()
                )

                # Also check for direct substring matches (higher weight)
                if pattern.lower() in user_input_lower:
                    similarity = max(similarity, 0.8)

                if similarity > best_score and similarity > 0.4:  # Minimum threshold
                    best_score = similarity
                    best_match = (rule_name, similarity)

        return best_match

    def _calculate_similarity(self, text1, text2):
        """Calculate simple similarity between two texts"""
        words1 = set(text1.split())
        words2 = set(text2.split())

        if not words1 or not words2:
            return 0.0

        intersection = words1.intersection(words2)
        union = words1.union(words2)

        return len(intersection) / len(union)

    def _get_response(self, rule_name):
        """Get response for a specific rule"""
        rule_data = self.rules.get(rule_name, {})
        responses = rule_data.get("responses", [])

        if responses:
            # For now, just return the first response
            return responses[0]
        else:
            return "I found a relevant topic but don't have a specific response. Please contact technical support."

    def _get_fallback_response(self, user_input):
        """Generate fallback response when no rules match"""
        technical_keywords = [
            "machine",
            "equipment",
            "device",
            "system",
            "component",
            "part",
            "repair",
            "fix",
            "broken",
            "malfunctioning",
            "issue",
            "problem",
            "maintenance",
            "service",
            "check",
            "inspect",
            "replace",
        ]

        input_lower = user_input.lower()
        technical_score = sum(
            1 for keyword in technical_keywords if keyword in input_lower
        )

        if technical_score >= 2:
            return """I understand you have a technical question, but I don't have a specific rule for this situation. 

**General troubleshooting steps:**
1. Check power supply and connections
2. Look for obvious damage or wear
3. Verify proper settings and controls
4. Check for error codes or indicators
5. Consult equipment manual

For complex issues, I can connect you with advanced diagnostic assistance. Would you like me to help with that?"""
        else:
            return """I'm specialized in technical and maintenance support. I can help with:
- Equipment troubleshooting
- Maintenance procedures  
- Safety protocols
- Basic diagnostics

Could you please ask about a specific technical issue or maintenance topic?"""

    def _sanitize_input(self, text):
        """Sanitize user input"""
        if not text or not isinstance(text, str):
            return ""

        # Remove excessive whitespace and normalize
        clean_text = re.sub(r"\s+", " ", text.strip())

        # Basic length check
        if len(clean_text) > 1000:
            clean_text = clean_text[:1000]

        return clean_text

    def _save_rules(self, rules):
        """Save rules to file"""
        try:
            os.makedirs(os.path.dirname(self.rules_path), exist_ok=True)
            with open(self.rules_path, "w") as f:
                json.dump(rules, f, indent=2)
            logger.info(f"Rules saved to {self.rules_path}")
        except Exception as e:
            logger.error(f"Error saving rules: {str(e)}")

    def get_rule_statistics(self):
        """Get statistics about the rule database"""
        if not self.rules:
            return {"total_rules": 0, "total_patterns": 0, "total_responses": 0}

        total_rules = len(self.rules)
        total_patterns = sum(
            len(rule.get("patterns", [])) for rule in self.rules.values()
        )
        total_responses = sum(
            len(rule.get("responses", [])) for rule in self.rules.values()
        )

        return {
            "total_rules": total_rules,
            "total_patterns": total_patterns,
            "total_responses": total_responses,
            "average_patterns_per_rule": total_patterns / total_rules
            if total_rules > 0
            else 0,
            "average_responses_per_rule": total_responses / total_rules
            if total_rules > 0
            else 0,
            "rules_list": list(self.rules.keys()),
        }
