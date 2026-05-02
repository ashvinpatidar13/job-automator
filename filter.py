import anthropic
import json
import os
import time
from dotenv import load_dotenv

load_dotenv()
client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_KEY"))

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
Relevant Courses: Intro to ML, Generative AI, Linear Algebra, Applied Probability, AI/ML for designers
"""

def score_job(job):
    description_snippet = job.get("description", "")[:1500].strip()
    prompt = f"""
You are a job-fit evaluator. Given a candidate's CV and a job listing, score the fit.

CV:
{MY_CV}

Job Title: {job['title']}
Company: {job['company']}
Location: {job['location']}
Job Description (first 1500 chars):
{description_snippet if description_snippet else '(not available)'}

Return ONLY a JSON object like this, nothing else, no markdown, no backticks:
{{
  "fit_score": <integer 0-100>,
  "matching_skills": ["skill1", "skill2"],
  "gaps": ["gap1", "gap2"],
  "should_apply": <true or false>
}}

Rules:
- fit_score above 60 means should_apply is true
- Be honest about gaps
- Consider that candidate is a final year IIT student, so some experience gaps are acceptable
- Use the job description heavily to find specific skill matches and gaps
"""
    message = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=300,
        messages=[{"role": "user", "content": prompt}]
    )
    
    text = message.content[0].text.strip()
    if text.startswith("```"):
        text = text.split("```")[1]
        if text.startswith("json"):
            text = text[4:]
    text = text.strip()
    return json.loads(text)


def filter_jobs(jobs):
    print(f"\nScoring {len(jobs)} jobs against your CV...\n")
    suitable = []
    
    for i, job in enumerate(jobs):
        try:
            result = score_job(job)
            job["fit_score"] = result["fit_score"]
            job["matching_skills"] = result["matching_skills"]
            job["gaps"] = result["gaps"]
            job["should_apply"] = result["should_apply"]
            
            status = "✓ APPLY" if result["should_apply"] else "✗ SKIP"
            print(f"[{i+1}] {status} (Score: {result['fit_score']}) - {job['title']} @ {job['company']}")
            
            if result["should_apply"]:
                suitable.append(job)
                
        except Exception as e:
            print(f"[{i+1}] Error scoring {job['title']}: {e}")
            continue
        
        time.sleep(1)
    
    with open("logs/suitable_jobs.json", "w") as f:
        json.dump(suitable, f, indent=2)
    
    print(f"\n{len(suitable)} suitable jobs saved to logs/suitable_jobs.json")
    return suitable


if __name__ == "__main__":
    with open("logs/raw_jobs.json", "r") as f:
        jobs = json.load(f)
    filter_jobs(jobs)