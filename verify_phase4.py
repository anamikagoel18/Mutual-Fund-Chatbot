from phase4_guardrails.guardrail_manager import GuardrailManager

gm = GuardrailManager()

test_queries = [
    "My PAN is ABCDE1234F",
    "Which is the best fund to buy?",
    "Should I invest in HDFC?",
    "What is the NAV of Kotak Midcap?"
]

print("--- Phase 4 Guardrail Verification ---")
for q in test_queries:
    pii = gm.contains_pii(q)
    adv = gm.is_advisory_intent(q)
    print(f"Q: {q}")
    print(f"  PII Detected: {pii}")
    print(f"  Advisory Intent Detected: {adv}")
    if pii:
        print(f"  Refusal: {gm.get_pii_refusal()}")
    elif adv:
        print(f"  Refusal: {gm.get_advisory_refusal()}")
    print("-" * 30)
