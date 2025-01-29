"""
scam definitions
"""

scam_categories = {
    1: [
        "Fake Authority Call",
        "Scammers impersonating law enforcement officials (e.g., CBI, customs, police) or service agents, coercing victims into making payments or money.",
    ],
    2: [
        "UPI Scam",
        "Scammers claim accidental UPI payments and request refunds, or attempt scams related to UPI, PhonePe, Google Pay, or any quick payment interface.",
    ],
    3: [
        "OTP Scam",
        "Scammers request OTPs to gain unauthorized access to bank account.",
    ],
    4: [
        "Fake Buyer/Seller Scam",
        "Scammers pose as buyers requesting refunds or as fraudulent sellers asking for advance payments.",
    ],
    5: [
        "Phishing or Link Scam",
        "Fraudulent SMS or calls designed to gain unauthorized access to banking platforms by sending malicious links or asking for sensitive details.",
    ],
    6: [
        "Video Call Scam",
        "Blackmail involving compromising video calls, or screenshots, used to demand money.",
    ],
    7: [
        "Fake Bank Staff Scam",
        "Calls from scammers posing as bank officials, requesting sensitive banking details.",
    ],
    8: [
        "Fake Job Scam",
        "Scammers posing as recruiters, demanding service or registration fees for fake job offers.",
    ],
    9: [
        "Lottery Scam",
        "Messages claiming lottery wins, lucky draws, or prizes, and requesting fees for processing.",
    ],
    10: [
        "Fake Identity Scam",
        "Scammers imitate known individuals and request money transfers.",
    ],
}

scam_categories_str = "\n".join(
    [f"{k}: {v[0]}-{v[1]}" for k, v in scam_categories.items()]
)
