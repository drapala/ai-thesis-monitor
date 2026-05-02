"""Earnings call transcript text-mining adapter.

STATUS: stub. Tracks frequency of AI-adoption + AI-substitution language
in S&P 500 earnings call transcripts.

Two metric families:
- earnings_call_ai_mentions_yoy — diffusion signal (rising = adoption rhetoric).
  Both citadel and citrini predict UP.
- earnings_call_headcount_reduction_mentions — substitution signal.
  Citrini-direct: rising count = explicit AI-driven labor compression rhetoric.
  Citadel: should remain near baseline.

Source options:
- AlphaSense API (paid, ~$10K+/year for enterprise) — best quality
- Sentieo (paid, ~$5K+/year) — second tier
- Seeking Alpha (free but rate-limited, scraping fragile)
- Company IR pages (manual, exhaustive but slow)
- DIY: SEC EDGAR 8-K filings (which sometimes attach transcripts)

Recommended for cost-conscious start:
- Begin with the top-50 by market cap from S&P 500
- Quarterly cadence
- DIY scrape from company IR pages (many publish call transcripts as PDFs)
- Use a small model (Sonnet/Haiku) to count mentions per term family

Term families (regex-style, case-insensitive):
- AI_TERMS = ["ai", "artificial intelligence", "generative ai", "agent",
              "agentic", "automate", "automation", "autonomous"]
- HEADCOUNT_REDUCTION_TERMS = ["headcount reduction", "workforce optimization",
                                "rightsizing", "operational efficiency program",
                                "restructuring", "reduction in force"]

Output schema:
- per company per quarter: {term_family: count}
- aggregate to S&P 500 monthly count_4w / yoy

To implement:
1. Choose data source (paid vs DIY scrape).
2. Define ticker list (S&P 500 or top-N by market cap).
3. Per quarter: fetch transcript, regex-count term families.
4. Persist to expanded_proxy_data.py via upsert.
5. Wire CLI command `seed-transcript-mentions`.

Cost estimate (DIY): ~30 min / quarter for top-50 tickers manually,
or ~$50-100 / quarter via paid API.
"""

from __future__ import annotations


AI_TERMS: tuple[str, ...] = (
    r"\bai\b",
    r"artificial intelligence",
    r"generative\s+ai",
    r"\bagent(s|ic)?\b",
    r"automat(e|ion|ed|ing)",
    r"autonomous",
)

HEADCOUNT_REDUCTION_TERMS: tuple[str, ...] = (
    r"headcount\s+reduction",
    r"workforce\s+optim(ization|isation)",
    r"rightsiz(ing|e)",
    r"operational\s+efficiency\s+program",
    r"restructur(ing|e)",
    r"reduction\s+in\s+force",
)


def count_mentions(transcript_text: str, term_family: tuple[str, ...]) -> int:
    """Count regex matches across a term family in a transcript.

    Pure function; no I/O. NOT YET WIRED to a fetcher.
    """
    import re

    total = 0
    for pattern in term_family:
        total += len(re.findall(pattern, transcript_text, flags=re.I))
    return total


def fetch_quarterly_mentions(tickers: list[str], quarter_end: str) -> list[dict]:
    """Fetch transcripts for tickers + count term-family mentions.

    NOT YET IMPLEMENTED. Returns a list of {ticker, term_family, count}.
    """
    raise NotImplementedError(
        "transcripts adapter is a stub. count_mentions() is implemented for "
        "offline use; the fetcher is not. Choose AlphaSense / Sentieo / scraping "
        "first. See file docstring for cost estimates."
    )
