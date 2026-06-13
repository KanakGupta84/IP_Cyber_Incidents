STATE = "Maharashtra"

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
        "fake company job offer",
    ],

    "cyber_loan_fraud": [
        "loan app fraud", "loan scam", "digital lending fraud",
        "fake loan app", "loan app harassment", "loan agent scam", 
        "loan agent fraud", "fake loan approval scam", "instant loan app scam",
        "personal loan fraud", "home loan fraud", "education loan fraud",
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
    ]

}


REJECT_TERMS = [

    # Awareness
    "awareness campaign", "cyber awareness drive",
    "awareness drive", "cyber awareness", "cyber safety",

    # Tips
    "how to avoid", "how to protect", "safety tips",
    "tips to stay safe", "stay safe", "protect yourself",
    "stay vigilant", "personal safety",

    # Advisory
    "advisory", "issued advisory", "government advisory",
    "warning", "warns citizens", "police warning",

    # Reports
    "survey", "study",
    "research", "statistics", "annual report",

    # Education
    "what is", "explained", "guide to",

    "tops list", "logs",
    "cases in 2026", "cases in 2025", "cases in 2024", "cases in 2023", "cases in 2022", "cases in 2021", "cases in 2020", 
    "cases in 2019", "cases in 2018", "cases in 2017",  
    "report", "statistics", "under scanner",
    "official says", "official urges", "assembly session",
    "chain of command", "policy", "response framework",
    
]