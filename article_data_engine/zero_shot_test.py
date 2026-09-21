# from transformers import pipeline

# print("Loading model...")

# classifier = pipeline(
#     "zero-shot-classification",
#     model="facebook/bart-large-mnli"
# )

# LABELS = [

#     "Investment Fraud",
#     "Cyber Loan Fraud",
#     "Insurance Fraud",
#     "Fake Social Media Trading Fraud",

#     "UPI Fraud",
#     "QR Code Scam",
#     "Phishing",
#     "OTP Fraud",
#     "Vishing",
#     "Data Breach",
#     "Dos Ddos",
#     "Website Defacement",
#     "Cyber Squatting",
#     "Pharming",
#     "Cryptojacking",
#     "Online Drug Trafficking",
#     "Debit Credit Card Fraud",
#     "Online Survey Fraud",
#     "Cloned Websites",
#     "ATS Fraud",
#     "Child Exploitation",
#     "Sextortion",
#     "Cyber Grooming",
#     "Blackmail",
#     "Cyber Stalking Bullying",
#     "SIM Swap Cloning",


#     "Digital Arrest Scam",
#     "Job Scam",
#     "Deepfake Scam",
#     "Smishing",
#     "Impersonation Identity Theft",
#     "Spamming",
#     "Ransomware",
#     "Malware",

#     "Awareness",
#     "Government Policy",
#     "Court Case",
#     "Arrest",

#     "Other"

# ]

# text = """
# Teacher loses Rs 15 lakh after joining Telegram stock trading group
# promising guaranteed monthly returns.
# """

# result = classifier(
#     text,
#     candidate_labels=LABELS
# )

# print("\nPredictions:\n")

# for label, score in zip(result['labels'], result['scores']):
#     print(f"{label:<25} {score:.3f}")


# from transformers import pipeline
# import pandas as pd

# print("Loading model...")

# classifier = pipeline(
#     "zero-shot-classification",
#     model="facebook/bart-large-mnli"
# )

# FRAUD_LABELS = [

#     "Investment Fraud",
#     "Cyber Loan Fraud",
#     "Insurance Fraud",
#     "Fake Social Media Trading Fraud",
#     "UPI Fraud",
#     "QR Code Scam",
#     "Phishing",
#     "OTP Fraud",
#     "Vishing",
#     "Digital Arrest Scam",
#     "Job Scam",
#     "Deepfake Scam",
#     "SIM Swap Cloning",
#     "Debit Credit Card Fraud",
#     "Sextortion",
#     "Malware",
#     "Ransomware",
#     "Other"
# ]

# ARTICLE_LABELS = [

#     "Incident",
#     "Awareness",
#     "Government Policy",
#     "Court Case",
#     "Arrest",
#     "Analysis",
#     "Other"

# ]

# df = pd.read_csv("TEST/full_articles_Maharashtra.csv")


# for i, row in df.head(10).iterrows():

#     text = f"""
#     Title:
#     {row['title']}

#     Article:
#     {str(row['article_text'])[:1500]}
#     """

#     fraud = classifier(
#         text,
#         candidate_labels=FRAUD_LABELS
#     )

#     article = classifier(
#         text,
#         candidate_labels=ARTICLE_LABELS
#     )

#     print("\n" + "="*80)

#     print("\nTITLE:\n")
#     print(row['title'])

#     print("\nSEARCH INTENT:")
#     print(row['search_intent'])

#     print("\nFRAUD TYPE")
#     print(fraud['labels'][0],
#           round(fraud['scores'][0],3))

#     print("\nARTICLE TYPE")
#     print(article['labels'][0],
#           round(article['scores'][0],3))

from transformers import pipeline
import pandas as pd
from tqdm import tqdm

# ---------------------------------------------------
# CONFIG
# ---------------------------------------------------

CSV_PATH = "full_articles_Maharashtra.csv"

THRESHOLD = 0.55         # try 0.65 / 0.70 / 0.75


FRAUD_LABELS = [

    "UPI Fraud",    
    "Government scheme scam"
    "QR Code Scam",
    "Investment Fraud",     
    "Job Scam",
    "Cyber Loan Fraud",     
    "OTP Fraud",
    "Insurance Fraud",
    "Digital Arrest Scam",
    "crypro scam",
    "trading scam",

    "Smishing",     ## text msg scams, sms scams
    "Phishing",     ## looks legit but is not, websites with typos, act now in bank accounts, etc.
    "Vishing",      ## phone call related scams, call centres
    "Spamming",

    "Identity Theft",
    "Impersonation",    ## have separated impersonation and identity thdt for bettr labelling
    "Ransomware",      ## asks for ransom (money) to let go but cyber
    "Malware",      ## virus, trojan, worm virus

    "Data Breach",
    "Dos Ddos",     ## overwhelm the servers using many fake users
    "Website Defacement",      ## website hack and defacement
    "Cyber Squatting",      ## using identical websites to profit from people accidently visiting this fake website instead of the legit one to profit from it and scam
    "Pharming",     ## cyber attack that redirects users tapping on correct url to malicious websites
    "Cryptojacking",        ## cryptomining attacks and illegal crypto mining
    "Online Drug Trafficking",
    "Forged documents",  ## original documents which are modified
    "Fake documents"  ## completely new documents which are fake

    "Debit Credit Card Fraud",
    "Online Survey Fraud",
    "Cloned Websites",

    "ATS Fraud",        ## automatic bank fraud, unauthorized bank transfer
    
    "Cyber Extortion",
    "Child Exploitation",
    "Sextortion",
    "Cyber Grooming",
    "Blackmail",
    "Cyber Stalking Bullying",
    "SIM Swap Cloning",
    "Deepfake Scam",

    "Online gaming platform scams",     ## online gaming platform scams, fantasy games, betting apps scams like dream 11, teen patti, pokerbaazi etc

    "Social media platform in op",
    "Online exam fruad"
    "Other"

]


ARTICLE_LABELS = [

    "Awareness",    "Government Policy",    "Court Case",
    "Arrest",    "Analysis",    "Other"

]

## ARTICLE LABELS CANNOT BE MULTIPLE, CHOOSE ONE........ FRAUD LABELS CAN BE MULTIPLE

## is_incident ---- TRUE if any money or hardware theft involved else false
## Arrest ---- when arrest written or police
## Court case ---- only when case written like case on Pranit More & Himanshu Jangra after derogatory remarks in youtube video

## in articles where first Arrest is there and is_incident, at end of article it is Awareness then will be classified as Arrest only


# ---------------------------------------------------
# LOAD MODEL
# ---------------------------------------------------

print("Loading model...\n")

classifier = pipeline(

    "zero-shot-classification",

    model="facebook/bart-large-mnli"

)

print("Model loaded!\n")



# ---------------------------------------------------
# LOAD CSV
# ---------------------------------------------------

df = pd.read_csv(CSV_PATH)
df = df.head(30)        ##### change no of articles to process



predicted_fraud = []
fraud_scores = []

predicted_article = []
article_scores = []



# ---------------------------------------------------
# CLASSIFICATION
# ---------------------------------------------------

for _, row in tqdm(df.iterrows(), total=len(df)):



    title = str(row['title'])

    article = str(row['article_text'])


    text = f"""

    Title:

    {title}


    Article:


    {article[:1500]}

    """



    # ------------------------------

    # FRAUD TYPE

    # ------------------------------


    fraud = classifier(

        text,

        candidate_labels=FRAUD_LABELS,

        multi_label=True

    )



    labels = []


    for l, s in zip(

            fraud['labels'],

            fraud['scores']

    ):


        if s >= THRESHOLD:

            labels.append(l)



    if len(labels) == 0:

        labels = ["Other"]



    predicted_fraud.append(

        ";".join(labels)

    )



    fraud_scores.append(

        round(

            max(fraud['scores']),

            3

        )

    )



    # ------------------------------

    # ARTICLE TYPE

    # ------------------------------


    article_pred = classifier(

        text,

        candidate_labels=ARTICLE_LABELS,

        multi_label=False

    )



    predicted_article.append(

        article_pred['labels'][0]

    )



    article_scores.append(

        round(

            article_pred['scores'][0],

            3

        )

    )



# ---------------------------------------------------
# SAVE
# ---------------------------------------------------


df['hf_categories'] = predicted_fraud


df['hf_score'] = fraud_scores



df['hf_article_type'] = predicted_article


df['hf_article_score'] = article_scores



df.to_csv(

    "TEST/predictions.csv",

    index=False

)



print("\nDone!\n")

print(

"Saved to TEST/predictions.csv"

)
