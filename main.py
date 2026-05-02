import asyncio
import json
from scraper import scrape_linkedin_jobs
from filter import filter_jobs
from emailer import process_jobs

async def main():
    print("=== Job Automator Starting ===\n")
    
    # Step 1 - Scrape
    print("Step 1: Scraping LinkedIn jobs...")
    jobs = await scrape_linkedin_jobs(
        keywords="AI Engineer",
        location="Remote"
    )
    
    # Step 2 - Filter
    print("\nStep 2: Filtering jobs with AI...")
    suitable = filter_jobs(jobs)
    
    # Step 3 - Email
    print("\nStep 3: Sending emails...")
    process_jobs(suitable, dry_run=False)
    
    print("\n=== Done ===")

if __name__ == "__main__":
    asyncio.run(main())