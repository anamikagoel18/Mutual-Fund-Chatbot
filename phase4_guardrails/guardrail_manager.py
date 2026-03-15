import re

class GuardrailManager:
    """
    Centralized safety and intent management for the Mutual Fund Chatbot.
    Implements PII filtering and Investment Advice/Opinion detection.
    """

    def __init__(self):
        # PII Patterns: PAN, Aadhaar, Bank Account, Phone, Email, OTP
        self.pii_patterns = [
            r"\b[A-Z]{5}[0-9]{4}[A-Z]{1}\b", # PAN
            r"\b[0-9]{12}\b", # Aadhaar (simple)
            r"\b[0-9]{9,18}\b", # Bank Account
            r"\b[0-9]{10}\b", # Phone (10 digits)
            r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b", # Email
            r"\b[0-9]{4,6}\b" # OTP
        ]
        
        # Advisory/Opinion Keywords
        self.advisory_keywords = [
            "buy", "sell", "recommend", "best", "good", "suggest", 
            "invest in", "should i", "which is better", "top fund",
            "opinion", "advice", "growth prediction", "forecast"
        ]

    def contains_pii(self, text):
        """Checks if the text contains sensitive personal information."""
        for pattern in self.pii_patterns:
            if re.search(pattern, text):
                return True
        return False

    def is_advisory_intent(self, text):
        """Detects if the user is seeking investment advice or opinions."""
        text_lower = text.lower()
        for keyword in self.advisory_keywords:
            if keyword in text_lower:
                return True
        return False

    def is_multi_intent(self, text):
        """Detects if the user is asking multiple questions (e.g., mentioning multiple funds)."""
        # Count mentions of common fund keywords or multiple '?' marks
        fund_keywords = ["hdfc", "icici", "kotak", "fund", "nav", "expense ratio", "exit load"]
        found_keywords = [kw for kw in fund_keywords if kw in text.lower()]
        
        # If multiple funds are mentioned or multiple question marks are present
        fund_names = ["hdfc", "icici", "kotak"]
        mentioned_funds = [f for f in fund_names if f in text.lower()]
        
        if len(mentioned_funds) > 1 or text.count('?') > 1:
            return True
            
        # Also check for 'and' or ',' separating likely distinct queries
        if " and " in text.lower() and len(found_keywords) > 2:
            return True
            
        return False

    def get_pii_refusal(self):
        return "I am unable to process requests containing sensitive personal information such as PAN, Aadhaar, bank details, or contact info. Please remove these details and try again."

    def get_advisory_refusal(self):
        return "I do not provide investment advice, personal opinions, or recommendations. I can only serve factual data from official records. For fund comparisons or investment decisions, please refer to the official fund factsheet."

    def get_multi_intent_refusal(self):
        return "I can process only one question at a time to ensure accuracy. Please ask about one fund or one specific property (like NAV or Expense Ratio) per message."
