from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, HttpUrl
import httpx
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from collections import deque


app = FastAPI()

# Allow the Next.js frontend on localhost:3000 to call this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ScoreRequest(BaseModel):
    url: HttpUrl


class SiteScores(BaseModel):
    overall: int
    content: int
    aeo: int
    tech: int
    mobile: int


class PageScores(BaseModel):
    url: str
    depth: int
    title: str | None
    word_count: int
    overall: int
    content: int
    aeo: int
    tech: int
    mobile: int


class PageDetail(BaseModel):
    url: str
    title: str | None
    word_count: int
    overall: int
    content: int
    aeo: int
    tech: int
    mobile: int
    headings: list[str]
    issues: list[str]


@app.get("/health")
def health():
    return {"status": "ok"}


def fetch_html(url: str) -> str:
    """Download the HTML for a given URL."""
    try:
        with httpx.Client(timeout=10.0, follow_redirects=True) as client:
            resp = client.get(url)
            resp.raise_for_status()
            return resp.text
    except httpx.RequestError as e:
        raise HTTPException(status_code=502, detail=f"Error fetching site: {e}") from e
    except httpx.HTTPStatusError as e:
        raise HTTPException(
            status_code=e.response.status_code,
            detail=f"Site returned status {e.response.status_code}",
        ) from e


def score_content(word_count: int) -> int:
    """Very simple content-depth scoring based on word count."""
    if word_count >= 2500:
        return 85
    if word_count >= 1500:
        return 78
    if word_count >= 800:
        return 70
    if word_count >= 400:
        return 60
    if word_count >= 200:
        return 50
    return 40


def score_aeo(soup: BeautifulSoup, text: str) -> int:
    """
    AEO score based on presence of question-style headings and FAQ-like content.
    """
    headings = soup.find_all(["h1", "h2", "h3"])
    question_heads = 0
    q_starters = ("how", "what", "why", "when", "where", "can", "does", "should")

    for h in headings:
        htext = (h.get_text() or "").strip().lower()
        if any(htext.startswith(q) for q in q_starters):
            question_heads += 1

    score = 50
    if question_heads >= 3:
        score = 80
    elif question_heads >= 1:
        score = 70

    lower_text = text.lower()
    if "faq" in lower_text or "frequently asked questions" in lower_text:
        score += 5

    return min(score, 90)


def score_tech(url: str, html: str, soup: BeautifulSoup) -> int:
    """
    Basic technical score: HTTPS, title/description, canonical, schema hints, viewport.
    """
    score = 55

    # HTTPS
    if url.startswith("https://"):
        score += 5

    # Title + meta description
    title = soup.find("title")
    meta_desc = soup.find("meta", attrs={"name": "description"})
    if title and title.get_text(strip=True):
        score += 5
    if meta_desc and meta_desc.get("content"):
        score += 5

    # Canonical
    canonical = soup.find("link", rel="canonical")
    if canonical and canonical.get("href"):
        score += 5

    # Schema presence
    if "schema.org" in html:
        score += 10

    # Viewport (also helps mobile)
    viewport = soup.find("meta", attrs={"name": "viewport"})
    if viewport:
        score += 5

    return max(40, min(score, 90))


def score_mobile(soup: BeautifulSoup, html: str) -> int:
    """
    Rough mobile score based on viewport and hints of responsive styles.
    """
    score = 45

    viewport = soup.find("meta", attrs={"name": "viewport"})
    if viewport:
        score += 15

    # crude check for responsive css
    if "max-width" in html or "@media" in html:
        score += 10

    return max(40, min(score, 90))


def compute_scores_for_html(url: str, html: str, depth: int = 0) -> tuple[SiteScores, PageScores, BeautifulSoup]:
    """Compute scores for a single HTML page and return soup for reuse."""
    soup = BeautifulSoup(html, "html.parser")
    text = soup.get_text(" ", strip=True)
    words = text.split()
    word_count = len(words)

    content = score_content(word_count)
    aeo = score_aeo(soup, text)
    tech = score_tech(url, html, soup)
    mobile = score_mobile(soup, html)

    overall = int(
        0.3 * content +
        0.3 * aeo +
        0.2 * tech +
        0.2 * mobile
    )

    title_tag = soup.find("title")
    title = title_tag.get_text(strip=True) if title_tag else None

    site_scores = SiteScores(
        overall=overall,
        content=content,
        aeo=aeo,
        tech=tech,
        mobile=mobile,
    )

    page_scores = PageScores(
        url=url,
        depth=depth,
        title=title,
        word_count=word_count,
        overall=overall,
        content=content,
        aeo=aeo,
        tech=tech,
        mobile=mobile,
    )

    return site_scores, page_scores, soup


def build_page_issues(page: PageScores) -> list[str]:
    """Generate human readable issues list based on page scores."""
    issues: list[str] = []

    if page.content < 60:
        issues.append("Content depth is low – consider expanding this page.")
    if page.content >= 60 and page.content < 70:
        issues.append("Content depth is decent but could go deeper to stand out.")

    if page.aeo < 60:
        issues.append("Few question-based headings – add How/What/Why sections or an FAQ block.")
    if page.tech < 60:
        issues.append("Technical SEO is weak – check title, meta description, canonical, and schema.")
    if page.mobile < 60:
        issues.append("Mobile experience may be weak – check responsive layout and tap targets.")

    if not issues:
        issues.append("This page is generally strong – focus on internal linking and conversion.")

    return issues


@app.post("/api/v3/scores", response_model=SiteScores)
def get_scores(payload: ScoreRequest):
    """
    Fetch the homepage, analyse the HTML, and return scores.
    """
    url = str(payload.url)
    html = fetch_html(url)
    site_scores, _, _ = compute_scores_for_html(url, html)
    return site_scores


def is_same_domain(root: str, href: str) -> bool:
    """Check if href is on the same domain as root."""
    try:
        root_netloc = urlparse(root).netloc
        target = urlparse(href).netloc
        return root_netloc == target or target == ""
    except Exception:
        return False


@app.post("/api/v3/crawl", response_model=list[PageScores])
def crawl_site(payload: ScoreRequest, max_pages: int = 20, max_depth: int = 2):
    """
    Simple BFS crawl of a site returning page-level scores.
    """
    root_url = str(payload.url)
    visited: set[str] = set()
    queue: deque[tuple[str, int]] = deque()
    queue.append((root_url, 0))

    pages: list[PageScores] = []

    while queue and len(pages) < max_pages:
        url, depth = queue.popleft()
        if url in visited or depth > max_depth:
            continue
        visited.add(url)

        try:
            html = fetch_html(url)
        except HTTPException:
            # skip pages that fail
            continue

        site_scores, page_scores, soup = compute_scores_for_html(url, html, depth)
        pages.append(page_scores)

        # enqueue internal links
        for a in soup.find_all("a", href=True):
            href = a["href"]
            absolute = urljoin(url, href)
            if absolute not in visited and is_same_domain(root_url, absolute):
                queue.append((absolute, depth + 1))

    return pages


@app.post("/api/v3/page-detail", response_model=PageDetail)
def page_detail(payload: ScoreRequest):
    """
    Return detailed information for a single page:
    scores, headings, and issues.
    """
    url = str(payload.url)
    html = fetch_html(url)

    # depth isn't critical here, we just pass 0
    _, page_scores, soup = compute_scores_for_html(url, html, depth=0)

    # collect first ~10 h1/h2/h3 headings
    headings: list[str] = []
    for h in soup.find_all(["h1", "h2", "h3"])[:10]:
        txt = (h.get_text() or "").strip()
        if txt:
            headings.append(txt)

    issues = build_page_issues(page_scores)

    return PageDetail(
        url=page_scores.url,
        title=page_scores.title,
        word_count=page_scores.word_count,
        overall=page_scores.overall,
        content=page_scores.content,
        aeo=page_scores.aeo,
        tech=page_scores.tech,
        mobile=page_scores.mobile,
        headings=headings,
        issues=issues,
    )

