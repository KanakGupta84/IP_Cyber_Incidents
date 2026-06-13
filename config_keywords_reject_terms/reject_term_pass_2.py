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
    "survey", "study", "research", "statistics", "annual report",

    # Education
    "what is", "explained", "guide to", "tops list", "logs",
    "cases in 2026", "cases in 2025", "cases in 2024", "cases in 2023",
    "cases in 2022", "cases in 2021", "cases in 2020",
    "cases in 2019", "cases in 2018", "cases in 2017",
    "report", "statistics", "under scanner",
    "official says", "official urges", "assembly session",
    "chain of command", "policy", "response framework",

    # Government schemes / policy noise
    "loan waiver", "msp scam", "yojana", "scheme launched",
    "crop insurance scheme", "fasal bima",

    # Elections / political noise
    "assembly polls", "municipal election", "civic polls",
    "voters list", "election commission", "poll campaign",
    "vidhan sabha", "lok sabha", "mla", "mlc", "deputy cm", "chief minister",
    "bitcoin scam", "bjp", "congress", "ncp", "shiv sena",

    # QR code mandates / govt initiatives
    "qr code initiative", "qr code mandatory",
    "know your doctor", "verification mandatory",

    # Generic civic/infra/weather
    "weather forecast", "rain alert", "imd issues", "monsoon",
    "traffic update", "road closed", "school closed", "public holiday",
    "cabinet approves", "govt orders inquiry", "irrigation scam",
    "land scam", "toll tax",

    # Old/aggregated stat pieces
    "sprouts news", "in last 5 years", "in 10 years", "over the years",
    "crosses rs", "tops list",

    # Court/legal procedural updates
    "grants bail", "denies bail", "anticipatory bail",
    "chargesheet filed", "court rejects", "court grants",

    # Generic finance/market news
    "share price", "ipo allotment", "stock market closed",
    "market holiday", "rbi proposes", "rbi launches", "new upi rules",
    "sebi bans", "sebi advises", "sebi launches", "sebi proposes",

    # ---- EXTENDED SECOND-PASS TERMS ----

    # More political/party noise
    "aam aadmi party", "aap leader", "bjp leader", "congress leader",
    "opposition demands", "ruling party", "political party",
    "minister inaugurates", "minister launches", "minister visits",
    "cm inaugurates", "pm modi", "rahul gandhi", "amit shah",
    "governor approves", "state government", "central government announces",
    "government to set up", "government forms committee",
    "government mulls", "government plans", "government to introduce",
    "parliament session", "rajya sabha", "budget session",
    "election result", "bypoll", "by-election", "party manifesto",

    # More court/legal procedural noise
    "high court", "supreme court", "sessions court",
    "district court", "magistrate court", "tribunal",
    "filed petition", "writ petition", "pil filed",
    "contempt of court", "court notice", "summons issued",
    "conviction upheld", "acquitted", "sentence commuted",
    "hearing scheduled", "next hearing", "matter adjourned",
    "case transferred", "suo motu", "judicial inquiry",
    "probe ordered", "probe committee", "sit formed",
    "ed raids", "cbi probe", "income tax raid",
    "enforcement directorate", "money laundering probe",

    # More regulatory/policy noise
    "rbi circular", "rbi guidelines", "rbi directive",
    "sebi circular", "sebi order", "sebi regulation",
    "trai directive", "dot notification", "meity notification",
    "it act amendment", "data protection bill", "cyber law",
    "new regulation", "compliance deadline", "regulatory framework",
    "licensing requirement", "mandatory kyc", "kyc deadline",
    "due diligence", "audit report", "compliance report",

    # Infrastructure / digital india noise
    "digital india", "smart city", "e-governance",
    "digital infrastructure", "fiber rollout", "broadband expansion",
    "5g launch", "5g rollout", "telecom upgrade",
    "it park", "tech hub", "startup ecosystem",
    "hackathon", "innovation challenge", "tech summit",

    # Bank/finance product launches (not fraud)
    "new bank account", "savings account launch", "fd rates",
    "interest rate hike", "repo rate", "bank merger",
    "bank strike", "bank holiday", "atm upgrade",
    "new credit card launch", "cashback offer", "reward points",
    "emi scheme", "zero interest loan", "loan disbursement",
    "mudra loan", "pm kisan", "kcc loan",

    # Aggregated trend/roundup pieces
    "year in review", "monthly roundup", "weekly roundup",
    "top 10", "top 5", "list of", "ranked",
    "most common scams", "types of fraud", "kinds of cyber crime",
    "common cyber threats", "biggest scams of",
    "fraud trends", "emerging threats", "threat landscape",
    "cybercrime trends", "cybercrime statistics",
    "india ranks", "india position", "global index",

    # Prevention/training programs
    "training program", "cyber training", "police training",
    "workshop conducted", "seminar held", "awareness seminar",
    "awareness workshop", "outreach program", "nukkad natak",
    "school program", "college program", "student awareness",
    "ngo initiative", "community awareness", "jan jagran",

    # Generic crime (not cyber) leaking via keyword overlap
    "murder", "rape", "robbery", "kidnapping", "abduction",
    "assault", "theft", "burglary", "dacoity",
    "drug bust", "drug peddler", "narcotics seized",
    "bootlegger", "liquor seized", "gold smuggling",
    "hawala", "land grabbing", "property dispute",

    # Media/entertainment noise
    "box office", "film release", "movie review",
    "celebrity", "actor", "actress", "bollywood",
    "cricket match", "ipl", "sports news", "tournament",

    # Health/disaster noise
    "hospital fire", "flood relief", "earthquake",
    "covid", "pandemic", "vaccination drive",
    "health scheme", "ayushman bharat",

    # Old case follow-ups
    "years after", "months after", "conviction in",
    "sentenced in old case", "cold case", "unsolved case",
    "historic fraud", "decade old",

    # Opinion/editorial
    "opinion", "editorial", "columnist",
    "analysis", "commentary", "perspective",
    "expert says", "expert opinion", "expert warns",
    "think tank", "white paper", "policy brief",

    # International noise
    "us fraud", "uk scam", "china hack",
    "russian hackers", "north korea cyber",
    "interpol operation", "global cybercrime",
    "international scam ring",

    # ---- CATEGORY-SPECIFIC SECOND-PASS TERMS ----

    # Online Job Fraud / Fake Job Offers
    "job fair", "recruitment drive", "hiring event",
    "placement drive", "campus placement", "job portal launched",
    "employment exchange", "rozgar mela", "skill india",
    "pm rojgar yojana", "employment scheme", "job guarantee scheme",
    "how to spot fake job", "fake job awareness",
    "job market report", "unemployment statistics",
    "labour market", "workforce report",

    # Smishing
    "smishing awareness", "sms filter", "spam sms block",
    "how to block spam sms", "trai sms rules",
    "dnd service", "do not disturb registration",
    "bulk sms regulation", "sms marketing rules",
    "telecom sms policy",

    # Impersonation & Identity Theft
    "identity theft awareness month", "how to protect identity",
    "identity protection tips", "identity theft report",
    "identity theft statistics", "fake id awareness",
    "document verification tips", "aadhaar security tips",
    "pan card safety", "voter id safety",
    "digital identity explained", "ekyc explained",

    # Spamming
    "anti spam law", "spam filter launched",
    "email security tips", "inbox protection",
    "spam report statistics", "spam trends",
    "bulk email regulation", "email marketing compliance",

    # Ransomware
    "ransomware report", "ransomware statistics",
    "ransomware trends", "ransomware prevention guide",
    "how to recover from ransomware", "ransomware backup tips",
    "ransomware simulation", "ransomware drill",
    "ransomware insurance", "cyber insurance",
    "ransomware as a service explained",

    # Virus / Worms / Trojans / Malware
    "antivirus review", "antivirus comparison", "best antivirus",
    "malware report", "malware statistics", "malware trends",
    "virus database update", "patch update released",
    "security patch", "software vulnerability disclosed",
    "zero day explained", "cve disclosed", "vulnerability report",
    "malware analysis report", "threat intelligence report",

    # Data Breach
    "data breach report", "data breach statistics",
    "data breach trends", "data breach study",
    "data protection tips", "data privacy day",
    "gdpr compliance", "pdpb compliance", "data protection bill",
    "data localisation", "data residency policy",
    "breach notification law", "data audit",
    "privacy policy update", "terms of service update",

    # Denial of Service / DDoS
    "ddos report", "ddos statistics", "ddos trends",
    "ddos mitigation tips", "how to prevent ddos",
    "cdn protection", "firewall tips", "network security report",
    "ddos as a service explained", "botnet explained",

    # Website Defacement
    "website defacement report", "defacement statistics",
    "website security tips", "web security report",
    "owasp report", "web vulnerability report",
    "website security audit", "ssl certificate tips",

    # Cyber Squatting
    "domain registration tips", "how to protect domain",
    "domain dispute resolution", "udrp explained",
    "domain squatting awareness", "brand protection online",
    "trademark online tips",

    # Pharming
    "dns security tips", "dns explained",
    "how dns works", "dns protection guide",
    "vpn tips", "secure browsing tips",
    "https awareness", "certificate authority explained",

    # Cryptojacking
    "cryptojacking report", "cryptojacking statistics",
    "cryptojacking prevention", "browser mining explained",
    "crypto regulation", "crypto tax", "crypto policy",
    "cryptocurrency ban", "crypto bill", "virtual asset regulation",

    # Online Drug Trafficking
    "drug policy report", "narcotics control report",
    "ndps act amendment", "drug awareness campaign",
    "anti drug drive", "drug de-addiction",
    "darknet explained", "tor browser explained",
    "dark web awareness",

    # Phishing
    "phishing report", "phishing statistics", "phishing trends",
    "phishing simulation", "phishing test", "phishing drill",
    "anti phishing tips", "email authentication explained",
    "spf dkim explained", "phishing kit explained",

    # Vishing
    "vishing report", "vishing statistics",
    "call spoofing explained", "caller id spoofing awareness",
    "robocall regulation", "telemarketing rules",
    "trai call regulation", "nuisance call block",

    # Debit / Credit Card Fraud
    "card security tips", "chip card explained",
    "contactless payment safety", "card tokenisation explained",
    "pci dss compliance", "card fraud statistics",
    "card fraud report", "card fraud trends",
    "atm safety tips", "pos terminal security",

    # UPI Fraud
    "upi safety tips", "upi guidelines", "npci guidelines",
    "upi limit increase", "upi new feature", "upi update",
    "upi statistics", "upi transaction report",
    "upi growth report", "digital payment report",
    "cashless economy", "less cash society",

    # QR Code Scam
    "qr code safety tips", "how qr code works",
    "qr code standard", "bharat qr explained",
    "qr code payment guide",

    # Online Survey Frauds
    "survey methodology", "market research report",
    "consumer survey", "public opinion poll",
    "survey platform launched", "google forms tips",

    # Cloned Websites / Fake Marketplaces
    "ecommerce policy", "online marketplace regulation",
    "consumer protection act", "e-commerce rules",
    "online shopping tips", "safe online shopping guide",
    "fake review awareness", "online seller verification",

    # Automatic Transfer System
    "banking automation", "neft explained", "rtgs explained",
    "imps explained", "swift explained", "banking technology",
    "core banking upgrade", "digital banking report",

    # Investment Fraud / Fake Trading Groups
    "sebi investor awareness", "investor education",
    "mutual fund awareness", "sip tips",
    "stock market basics", "trading explained",
    "demat account tips", "how to invest safely",
    "ponzi scheme explained", "pyramid scheme explained",
    "multi level marketing awareness",

    # Fake Loan Apps
    "rbi registered lender", "nbfc guidelines",
    "digital lending guidelines", "loan app regulation",
    "rbi approved loan app", "loan eligibility tips",
    "credit score tips", "cibil score explained",

    # Insurance Frauds
    "insurance literacy", "insurance awareness",
    "insurance ombudsman", "irdai guidelines",
    "insurance policy tips", "term insurance explained",
    "health insurance tips", "motor insurance tips",

    # CSAM / Child Safety
    "child safety online tips", "parental control guide",
    "safe internet day", "child internet safety",
    "pocso act explained", "child protection law",
    "digital literacy for children",

    # Online Sextortion / Sexting / Morphing
    "sextortion awareness", "sexting dangers awareness",
    "morphing awareness", "deepfake awareness",
    "deepfake detection tips", "image misuse awareness",
    "revenge porn law", "it act section 67",
    "intimate image abuse law",

    # Cyber Grooming
    "online grooming awareness", "child grooming prevention",
    "internet safety for teens", "predator awareness",
    "safe chatting tips", "online stranger danger",

    # Blackmail / Extortion
    "blackmail awareness", "extortion awareness",
    "how to report blackmail", "what to do if blackmailed",
    "extortion law explained", "ipc 383 explained",

    # Cyber Stalking / Bullying / Hate Crimes
    "cyberbullying awareness", "anti bullying day",
    "cyberbullying statistics", "cyberbullying report",
    "cyberbullying prevention guide", "online harassment report",
    "hate speech law", "it act hate speech",
    "online safety for women", "women cyber safety",
    "cyber crime against women report",

    # Fake Profile
    "fake profile awareness", "how to report fake profile",
    "social media verification tips", "blue tick explained",
    "account verification tips", "social media safety tips",

    # SIM Swap / SIM Cloning
    "sim swap awareness", "sim swap prevention",
    "how to protect sim", "port out scam awareness",
    "telecom kyc tips", "sim registration rules",
    "trai sim rules", "porting rules",
]
