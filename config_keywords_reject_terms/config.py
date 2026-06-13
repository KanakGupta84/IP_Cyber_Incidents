MIN_ARTICLE_LENGTH = 50



FRAUD_CATEGORIES = {
    "cyber_fraud": [
        "cyber fraud", "online fraud", "digital fraud",
    ],
    "upi_fraud": [
        "upi fraud", "upi scam", "fraudulent upi transaction",
        "payment app scam", "online payment fraud", "collect request scam",
        "digital payment fraud",
        "google pay scam", "google pay fraud",
        "gpay scam", "gpay fraud",
        "phonepe scam", "phonepe fraud",
        "paytm scam", "paytm fraud",
        "bhim scam", "bhim fraud",
        "apple pay scam", "apple pay fraud",
        "amazon pay scam", "amazon pay fraud",
        "bharatpe scam", "bharatpe fraud",
    ],
    "qr_code_scam": [
        "qr code scam", "upi scanner", "fake payment qr",
        "fake payment scanner", "qr code fraud", "qr code arrest",
        "qr code cyber fraud",
    ],
    "investment_fraud": [
        "investment fraud", "investment scam", "share market scam",
        "stock market scam", "stock market fraud", "share market fraud",
        "trading scam", "crypto scam", "fake investment platform",
        "trading fraud", "crypto fraud", "telegram trading fraud",
        "telegram scam", "telegram trading scam", "whatsapp scam",
        "whatsapp trading scam", "whatsapp trading fraud", "fake trading group",
    ],
    "job_scam": [
        "job scam", "fake job offer", "recruitment fraud",
        "job scam victim", "fake recruitment", "online job scam",
        "job fraud", "work from home scam", "employment scam",
        "fake company job offer", "online job fraud", "part time job scam",
        "part time job fraud", "data entry job scam", "data entry job fraud",
    ],
    "cyber_loan_fraud": [
        "loan app fraud", "loan scam", "digital lending fraud",
        "fake loan app", "loan app harassment", "loan agent scam",
        "loan agent fraud", "fake loan approval scam", "instant loan app scam",
        "personal loan fraud", "home loan fraud", "education loan fraud",
        "fake loan apps",
    ],
    "otp_fraud": [
        "otp fraud", "otp scam",
    ],
    "insurance_fraud": [
        "insurance fraud", "insurance scam", "fake insurance policy",
        "fake insurance scam",
    ],
    "digital_arrest_scam": [
        "digital arrest scam",
    ],

    # --- NEW CATEGORIES ---

    "smishing": [
        "smishing", "sms scam", "fake sms", "sms phishing",
        "text message scam", "sms fraud", "fake text message",
    ],
    "phishing": [
        "phishing", "phishing attack", "phishing scam", "phishing email",
        "fake website", "credential phishing", "spear phishing",
        "email phishing", "phishing link",
    ],
    "vishing": [
        "vishing", "voice phishing", "phone call scam", "fake call fraud",
        "fraud phone call", "impersonation call", "fake bank call",
        "fake police call", "fake cbi call", "fake it officer call",
    ],
    "impersonation_identity_theft": [
        "impersonation", "identity theft", "fake identity",
        "identity fraud", "impersonation fraud", "fake profile",
        "fake account", "account takeover", "social media impersonation",
        "impersonating officer", "fake cop", "fake government official",
    ],
    "spamming": [
        "spamming", "spam call", "spam email", "spam message",
        "bulk spam", "email spam", "unsolicited message",
    ],
    "ransomware": [
        "ransomware", "ransomware attack", "ransomware threat",
        "file encryption attack", "ransom demand", "ransomware victim",
        "ransomware gang",
    ],
    "malware": [
        "virus attack", "computer virus", "malware", "malware attack",
        "worm virus", "trojan horse", "trojan malware", "spyware",
        "adware", "rootkit", "keylogger", "worm attack",
    ],
    "data_breach": [
        "data breach", "data leak", "data theft", "data stolen",
        "personal data leak", "database hack", "data exposure",
        "user data leaked", "sensitive data breach",
    ],
    "dos_ddos": [
        "denial of service", "dos attack", "ddos attack",
        "distributed denial of service", "website down attack",
        "server attack", "network attack",
    ],
    "website_defacement": [
        "website defacement", "website hacked", "website defaced",
        "web defacement", "government website hacked",
    ],
    "cyber_squatting": [
        "cyber squatting", "cybersquatting", "domain squatting",
        "fake domain", "typosquatting", "domain fraud",
    ],
    "pharming": [
        "pharming", "dns hijacking", "dns spoofing",
        "fake website redirect", "dns poisoning",
    ],
    "cryptojacking": [
        "cryptojacking", "crypto mining malware", "illegal crypto mining",
        "browser crypto mining", "cryptomining attack",
    ],
    "online_drug_trafficking": [
        "online drug trafficking", "darknet drugs", "drug delivery scam",
        "online drug sale", "dark web drugs", "narcotics online",
    ],
    "debit_credit_card_fraud": [
        "credit card fraud", "debit card fraud", "card cloning",
        "atm fraud", "card skimming", "card skimmer",
        "stolen card", "card not present fraud", "atm skimming",
        "atm card fraud",
    ],
    "online_survey_fraud": [
        "online survey fraud", "fake survey", "survey scam",
        "paid survey scam", "survey reward scam",
    ],
    "cloned_websites": [
        "cloned website", "fake website", "duplicate website",
        "suspicious marketplace", "fake online store", "fake ecommerce",
        "fake shopping site", "fraudulent website",
    ],
    "automatic_transfer_system": [
        "automatic transfer system", "ats fraud", "auto transfer fraud",
        "unauthorized bank transfer", "automatic bank fraud",
    ],
    "fake_social_media_trading": [
        "fake trading group", "fake social media trading",
        "whatsapp trading group scam", "telegram trading group scam",
        "instagram trading scam", "fake stock tips group",
        "fake investment group",
    ],
    "child_exploitation": [
        "child pornography", "csam", "child sexual abuse material",
        "child exploitation online", "child abuse content",
    ],
    "sextortion": [
        "sextortion", "online sextortion", "nude video blackmail",
        "intimate video scam", "video call sextortion",
        "honeytrap scam", "sexting scam", "morphing",
        "morphed image", "fake nude image",
    ],
    "cyber_grooming": [
        "cyber grooming", "online grooming", "child grooming online",
        "grooming scam",
    ],
    "blackmail": [
        "blackmail", "online blackmail", "cyber blackmail",
        "extortion", "cyber extortion", "threatening message",
    ],
    "cyber_stalking_bullying": [
        "cyber stalking", "cyberstalking", "online stalking",
        "cyber bullying", "cyberbullying", "online harassment",
        "trolling", "hate message", "online abuse",
        "online hate crime", "online threat",
    ],
    "sim_swap_cloning": [
        "sim swap", "sim swap scam", "sim swap fraud",
        "sim cloning", "sim hijacking", "mobile number portability fraud",
        "sim card fraud",
    ],
}




