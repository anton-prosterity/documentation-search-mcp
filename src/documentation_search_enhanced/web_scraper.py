#!/usr/bin/env python3
"""
An advanced web scraper using Playwright to handle dynamic, JS-heavy sites.
"""

import sys
from typing import Optional

from bs4 import BeautifulSoup
from playwright.async_api import Browser, async_playwright


class PlaywrightScraper:
    """A web scraper that uses a real browser to render pages."""

    _browser: Optional[Browser] = None
    _playwright = None

    async def _get_browser(self) -> Browser:
        """Initializes and returns a shared browser instance."""
        if self._browser is None or not self._browser.is_connected():
            self._playwright = await async_playwright().start()
            self._browser = await self._playwright.chromium.launch()
        return self._browser

    async def scrape_url(self, url: str) -> str:
        """
        Scrapes a URL using Playwright, returning the clean, readable text content.

        This method can handle dynamic content, as it waits for the page
        to fully load and can execute scripts if needed.
        """
        browser = await self._get_browser()
        page = await browser.new_page()

        try:
            # Navigate to the page and wait for it to be fully loaded
            await page.goto(url, wait_until="networkidle", timeout=60000)

            # Scroll to the bottom to trigger lazy-loaded content
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            await page.wait_for_timeout(1000)  # Wait for any new content to load

            # Get the page content after JavaScript has rendered
            html_content = await page.content()

            # Use BeautifulSoup to parse and clean the final HTML
            soup = BeautifulSoup(html_content, "html.parser")

            # Remove non-content elements
            for element in soup(
                ["script", "style", "nav", "footer", "header", "aside"]
            ):
                element.decompose()

            # Get clean text
            text = soup.get_text(separator=" ", strip=True)
            return text

        except Exception as e:
            print(f"Failed to scrape {url}: {e}", file=sys.stderr)
            return f"Error: Could not retrieve content from {url}."
        finally:
            await page.close()

    async def close(self):
        """Closes the browser instance."""
        if self._browser and self._browser.is_connected():
            await self._browser.close()
        if self._playwright:
            await self._playwright.stop()


scraper = PlaywrightScraper()
