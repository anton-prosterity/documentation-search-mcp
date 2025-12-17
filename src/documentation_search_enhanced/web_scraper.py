#!/usr/bin/env python3
"""
An advanced web scraper using Playwright to handle dynamic, JS-heavy sites.
"""

import sys
from typing import Optional

from bs4 import BeautifulSoup
import httpx
from playwright.async_api import Browser, async_playwright


class PlaywrightScraper:
    """A web scraper that uses a real browser to render pages."""

    _browser: Optional[Browser] = None
    _playwright = None
    _disabled_reason: Optional[str] = None

    async def _get_browser(self) -> Browser:
        """Initializes and returns a shared browser instance."""
        if self._disabled_reason:
            raise RuntimeError(self._disabled_reason)
        if self._browser is None or not self._browser.is_connected():
            try:
                self._playwright = await async_playwright().start()
                self._browser = await self._playwright.chromium.launch()
            except Exception as e:
                self._disabled_reason = f"Playwright disabled: {e}"
                if self._playwright:
                    try:
                        await self._playwright.stop()
                    except Exception:
                        pass
                    self._playwright = None
                self._browser = None
                raise
        return self._browser

    async def scrape_url(self, url: str) -> str:
        """
        Scrapes a URL using Playwright, returning the clean, readable text content.

        This method can handle dynamic content, as it waits for the page
        to fully load and can execute scripts if needed.
        """
        page = None

        try:
            if self._disabled_reason:
                return await self._scrape_url_fallback(url)

            browser = await self._get_browser()
            page = await browser.new_page()

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
            return await self._scrape_url_fallback(url)
        finally:
            if page is not None:
                await page.close()

    async def _scrape_url_fallback(self, url: str) -> str:
        """Fallback fetcher when Playwright cannot launch (e.g., sandboxed environments)."""
        headers = {"User-Agent": "docs-app/1.0"}
        try:
            async with httpx.AsyncClient(
                timeout=httpx.Timeout(15.0, read=30.0),
                follow_redirects=True,
                headers=headers,
            ) as client:
                response = await client.get(url)
                response.raise_for_status()

            soup = BeautifulSoup(response.text, "html.parser")
            for element in soup(
                ["script", "style", "nav", "footer", "header", "aside"]
            ):
                element.decompose()
            return soup.get_text(separator=" ", strip=True)
        except Exception as e:
            print(f"Fallback fetch failed for {url}: {e}", file=sys.stderr)
            return f"Error: Could not retrieve content from {url}."

    async def close(self):
        """Closes the browser instance."""
        if self._browser and self._browser.is_connected():
            await self._browser.close()
        if self._playwright:
            await self._playwright.stop()


scraper = PlaywrightScraper()
