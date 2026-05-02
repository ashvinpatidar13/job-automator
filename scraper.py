import asyncio
from playwright.async_api import async_playwright
import json


async def scrape_linkedin_jobs(keywords, location, max_jobs=20):
    jobs = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()

        search_url = f"https://www.linkedin.com/jobs/search/?keywords={keywords}&location={location}&f_TPR=r86400&sortBy=DD"

        print(f"Opening LinkedIn jobs search...")
        await page.goto(search_url, wait_until="domcontentloaded", timeout=30000)
        await asyncio.sleep(3)

        # Scroll to load more jobs
        for _ in range(5):
            await page.keyboard.press("End")
            await asyncio.sleep(2)

        job_cards = await page.query_selector_all(".job-search-card")
        print(f"Found {len(job_cards)} job cards")

        # Step 1 — collect all basic info and links first
        raw = []
        for i, card in enumerate(job_cards[:max_jobs]):
            try:
                title_el = await card.query_selector(".base-search-card__title")
                company_el = await card.query_selector(".base-search-card__subtitle")
                location_el = await card.query_selector(".job-search-card__location")
                link_el = await card.query_selector("a.base-card__full-link")

                title = await title_el.inner_text() if title_el else "N/A"
                company = await company_el.inner_text() if company_el else "N/A"
                loc = await location_el.inner_text() if location_el else "N/A"
                link = await link_el.get_attribute("href") if link_el else "N/A"

                raw.append({
                    "title": title.strip(),
                    "company": company.strip(),
                    "location": loc.strip(),
                    "link": link,
                    "description": "",
                    "hr_email": ""
                })
                print(f"  [{i+1}] Collected: {title.strip()} @ {company.strip()}")

            except Exception as e:
                print(f"  Error collecting card {i}: {e}")
                continue

        print(f"\nNow fetching descriptions for {len(raw)} jobs...\n")

        # Step 2 — visit each job link separately
        for i, job in enumerate(raw):
            try:
                if job["link"] and job["link"] != "N/A":
                    await page.goto(job["link"], wait_until="domcontentloaded", timeout=30000)
                    await asyncio.sleep(2)

                    selectors = [
                        ".description__text",
                        ".show-more-less-html__markup",
                        ".job-description",
                        "[class*='description']"
                    ]

                    description = ""
                    for selector in selectors:
                        el = await page.query_selector(selector)
                        if el:
                            text = await el.inner_text()
                            if len(text) > 100:
                                description = text.strip()
                                break

                    job["description"] = description
                    print(f"  [{i+1}] ✓ {job['title']} @ {job['company']} ({len(description)} chars)")

            except Exception as e:
                print(f"  [{i+1}] Error fetching description: {e}")

            await asyncio.sleep(2)

        await browser.close()

    with open("logs/raw_jobs.json", "w") as f:
        json.dump(raw, f, indent=2)
    print(f"\nSaved {len(raw)} jobs to logs/raw_jobs.json")

    return raw


if __name__ == "__main__":
    asyncio.run(scrape_linkedin_jobs(
        keywords="AI Engineer",
        location="Remote"
    ))