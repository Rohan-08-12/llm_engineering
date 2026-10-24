from concurrent.futures import ThreadPoolExecutor

from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright
import requests


# Standard headers to fetch a website
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36"
}


def fetch_website_contents(url):
    """
    Return the title and contents of the website at the given url;
    truncate to 2,000 characters as a sensible limit
    """
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.content, "html.parser")
    title = soup.title.string if soup.title else "No title found"
    if soup.body:
        for irrelevant in soup.body(["script", "style", "img", "input"]):
            irrelevant.decompose()
        text = soup.body.get_text(separator="\n", strip=True)
    else:
        text = ""
    return (title + "\n\n" + text)[:2_000]


def fetch_website_links(url):
    """
    Return the links on the webiste at the given url
    I realize this is inefficient as we're parsing twice! This is to keep the code in the lab simple.
    Feel free to use a class and optimize it!
    """
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.content, "html.parser")
    links = [link.get("href") for link in soup.find_all("a")]
    return [link for link in links if link]


def _render_with_browser_sync(url):
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        page = browser.new_page(user_agent=headers["User-Agent"])
        page.goto(url, wait_until="networkidle")
        html = page.content()
        browser.close()
    return html


def _render_with_browser(url):
    """
    Load a page with a real (headless) browser so that Javascript gets to run,
    and return the fully rendered HTML. Use this for React/Next.js/Vue-style sites
    where fetch_website_contents/fetch_website_links come back empty.

    Playwright's sync API refuses to run on a thread that already has an asyncio
    event loop running (e.g. inside a Jupyter notebook), so we run it in a fresh
    worker thread, which has no event loop of its own.
    """
    with ThreadPoolExecutor(max_workers=1) as executor:
        return executor.submit(_render_with_browser_sync, url).result()


def fetch_rendered_website_contents(url):
    """
    Same as fetch_website_contents, but renders Javascript first via a headless browser.
    """
    html = _render_with_browser(url)
    soup = BeautifulSoup(html, "html.parser")
    title = soup.title.string if soup.title else "No title found"
    if soup.body:
        for irrelevant in soup.body(["script", "style", "img", "input"]):
            irrelevant.decompose()
        text = soup.body.get_text(separator="\n", strip=True)
    else:
        text = ""
    return (title + "\n\n" + text)[:2_000]


def fetch_rendered_website_links(url):
    """
    Same as fetch_website_links, but renders Javascript first via a headless browser.
    """
    html = _render_with_browser(url)
    soup = BeautifulSoup(html, "html.parser")
    links = [link.get("href") for link in soup.find_all("a")]
    return [link for link in links if link]
