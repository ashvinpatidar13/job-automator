import anthropic
import smtplib
import json
import os
import re
import time
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from dotenv import load_dotenv

load_dotenv()

ANTHROPIC_KEY = os.getenv("ANTHROPIC_KEY")
EMAIL_ADDRESS = os.getenv("EMAIL_ADDRESS")
EMAIL_APP_PASSWORD = os.getenv("EMAIL_APP_PASSWORD")
CV_PATH = "Ashvin_Patidar_CV.pdf"  # put your CV pdf in the project folder with this name

client = anthropic.Anthropic(api_key=ANTHROPIC_KEY)

MY_CV = """
Name: Ashvin Patidar
Institution: IIT Kanpur, B.Tech Civil Engineering, Final Year, CPI 7.3

Work Experience:
- Cisco (May'25-Jul'25): Software Engineering Intern. Built intelligent agent for AI-powered test failure analysis. Fine-tuned DistilBERT for log classification (92% accuracy). Built data pipeline processing 50GB logs. Containerized with Docker, exposed via Flask REST API into multi-agent framework.
- RWS (May'24-Jul'24): ML Intern. Built glossary-enforcement for NMT pipeline. Modified Transformer beam search with constrained decoding using token-level automata. Achieved 95% terminology accuracy.

Projects:
- Image to Handwriting Generation: Extended Handwriting Transformer with GRU-driven tokenizer, CNN style embeddings, Transformer cross-attention, adversarial + CTC + curve loss.
- Real-Time Age/Gender/Emotion Recognition: Multi-output CNN pipeline with OpenCV, 89.7% gender accuracy.
- Multi-Level PUFs: 81-dimensional feature map, LinearSVC 100% accuracy in 0.12s.
- Loan Portfolio Optimization: KNN credit risk model, 91.4% accuracy on 887k records.

Skills: Python, C/C++, PyTorch, TensorFlow, scikit-learn, OpenCV, Docker, Flask, Git, numpy, pandas
"""


def extract_email_from_description(text):
    pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
    emails = re.findall(pattern, text)
    # filter out common non-HR emails
    blacklist = ["example.com", "sentry.io", "linkedin.com", "disability", "accommodation", "noreply", "no-reply"]
    emails = [e for e in emails if not any(b in e for b in blacklist)]
    return emails[0] if emails else None

def find_email_via_hunter(company_name, job_link=""):
    import requests
    hunter_key = os.getenv("HUNTER_API_KEY")
    try:
        # Extract domain from job link
        domain = None
        if job_link and job_link != "N/A":
            from urllib.parse import urlparse
            # LinkedIn links don't give company domain, so use company name search
            pass

        # Search by company name
        url = f"https://api.hunter.io/v2/domain-search?company={requests.utils.quote(company_name)}&api_key={hunter_key}&limit=3"
        response = requests.get(url, timeout=10)
        data = response.json()
        domain_found = data.get("data", {}).get("domain")
        emails = data.get("data", {}).get("emails", [])
        print(f"     Hunter: {company_name} → domain={domain_found}, emails={len(emails)}")
        if emails:
            return emails[0]["value"]
    except Exception as e:
        print(f"     Hunter.io error: {e}")
    return None

def generate_email(job):
    prompt = f"""
You are writing a job application email on behalf of Ashvin Patidar, a final year IIT Kanpur student.

CV Summary:
{MY_CV}

Job Title: {job['title']}
Company: {job['company']}
Matching Skills: {', '.join(job.get('matching_skills', []))}
Gaps: {', '.join(job.get('gaps', []))}

Write a short, human, non-generic application email. Follow this EXACT structure:

1. Start with "Hi," or "Hi [team name]," or "Hello," as a greeting on its own line
2. One blank line
3. First paragraph: show you understand what the company does and why this specific role excites you. Be specific, not generic.
4. Second paragraph: 2-3 specific things from the CV most relevant to THIS job. Reference actual numbers and project names.
5. Third paragraph: one line asking for a call, mention CV is attached.
6. Sign off as:

Best,
Ashvin Patidar
ashvinp22@iitk.ac.in
+91-9589772288

Rules:
- ALWAYS start with a greeting like "Hi," or "Hi [company] team,"
- Do NOT start with "I hope this email finds you well" or any filler
- Do NOT use "I am writing to express my interest" or corporate phrases
- Sound like a sharp, confident student — direct and human
- Keep it under 200 words total

Return ONLY the email body, no subject line, no markdown.
"""
    message = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=500,
        messages=[{"role": "user", "content": prompt}]
    )
    return message.content[0].text.strip()


def send_email(to_address, subject, body, cv_path=None):
    msg = MIMEMultipart()
    msg['From'] = EMAIL_ADDRESS
    msg['To'] = to_address
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain'))

    if cv_path and os.path.exists(cv_path):
        with open(cv_path, "rb") as f:
            part = MIMEBase('application', 'octet-stream')
            part.set_payload(f.read())
            encoders.encode_base64(part)
            part.add_header('Content-Disposition', f'attachment; filename="{os.path.basename(cv_path)}"')
            msg.attach(part)

    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
        server.login(EMAIL_ADDRESS, EMAIL_APP_PASSWORD)
        server.send_message(msg)


def process_jobs(jobs, dry_run=True):
    """
    dry_run=True  → just prints emails, does not send
    dry_run=False → actually sends emails
    """
    print(f"\n{'DRY RUN' if dry_run else 'SENDING'} - Processing {len(jobs)} jobs...\n")
    log = []

    for i, job in enumerate(jobs):
        hr_email = extract_email_from_description(job.get("description", ""))

        if not hr_email:
            print(f"     No email in description, trying Hunter.io...")
            hr_email = find_email_via_hunter(job['company'], job.get('link', ''))

        if not hr_email:
            print(f"[{i+1}] SKIP (no email found) - {job['title']} @ {job['company']}")
            continue

        body = generate_email(job)
        subject = f"Application – {job['title']} | Ashvin Patidar, IIT Kanpur"

        print(f"\n[{i+1}] {job['title']} @ {job['company']}")
        print(f"     To: {hr_email}")
        print(f"     Subject: {subject}")
        print(f"     ---EMAIL PREVIEW---")
        print(body)
        print(f"     ---END---\n")

        if not dry_run:
            try:
                send_email(hr_email, subject, body, CV_PATH)
                print(f"     ✓ Sent to {hr_email}")
            except Exception as e:
                print(f"     ✗ Failed to send: {e}")

        log.append({
            "company": job['company'],
            "title": job['title'],
            "hr_email": hr_email,
            "subject": subject,
            "sent": not dry_run
        })

        time.sleep(2)

    with open("logs/email_log.json", "w") as f:
        json.dump(log, f, indent=2)

    print(f"\nLog saved to logs/email_log.json")


if __name__ == "__main__":
    with open("logs/suitable_jobs.json") as f:
        jobs = json.load(f)
    
    process_jobs(jobs, dry_run=False)