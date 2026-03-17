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
        
        # Advisory/Opinion Keywords (Granular to catch variations)
        self.advisory_keywords = [
            "buy", "sell", "recommend", "best", "better", "good", "suggest", 
            "invest in", "should i", "opinion", "advice", "prediction", "forecast",
            "top fund", "star rating", "highest return", "future return", "choose",
            "guide", "help me decide"
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
        """Detects if the user is asking multiple questions (e.g., mentioning multiple funds/attributes)."""
        text_lower = text.lower()
        
        # 1. Fund Mentions
        fund_names = ["hdfc", "icici", "kotak", "tata", "sbi", "axis", "nippon", "mirae", "quant"]
        mentioned_funds = [f for f in fund_names if f in text_lower]
        
        # 2. Attribute Mentions
        attributes = ["nav", "expense ratio", "aum", "fund manager", "exit load", "risk", "lumpsum", "sip", "objective"]
        mentioned_attrs = [a for a in attributes if a in text_lower]
        
        # Multi-intent triggers:
        # - Multiple distinct funds
        if len(mentioned_funds) > 1:
            return True
            
        # - Multiple attributes for one or more funds
        if len(mentioned_attrs) > 1:
            return True
            
        # - Multiple questions or connectors with multiple keywords
        if (text_lower.count('?') > 1 or " and " in text_lower or "," in text_lower):
            if len(mentioned_funds) >= 1 and len(mentioned_attrs) >= 1:
                # e.g., "NAV of HDFC and expense ratio"
                return True
            if len(mentioned_attrs) > 1:
                return True
            
        return False

    def get_pii_refusal(self):
        return "I am unable to process requests containing sensitive personal information such as PAN, Aadhaar, bank details, or contact info. Please remove these details and try again."

    def get_advisory_refusal(self):
        return "I do not provide investment advice, personal opinions, or recommendations. I can only serve factual data from official records. For fund comparisons or investment decisions, please refer to the official fund factsheet."

    def get_multi_intent_refusal(self):
        return "I can process only one question at a time to ensure accuracy. Please ask about one fund or one specific property (like NAV or Expense Ratio) per message."
