from html import escape
from pathlib import Path


TEMPLATE_PATH = Path("templates/top_ai_card.html")


def _build_tool_card(tool: dict, rank: int) -> str:
    rank_labels = {1: "TOP 1", 2: "TOP 2", 3: "TOP 3"}
    score = tool.get("external_rating", 0)
    favorites = tool.get("favorites_count", 0)
    image = escape(tool.get("image") or "", quote=True)
    name = escape(tool["name"])
    initials = escape((tool["name"][:2] or "?").upper())

    if image:
        visual = (
            f'<div class="logo-wrapper">'
            f'<img class="tool-logo" src="{image}" alt="{name}" '
            f'onerror="this.style.display=\'none\'; this.nextElementSibling.style.display=\'flex\';">'
            f'<div class="tool-logo-fallback" style="display:none;">{initials}</div>'
            f'</div>'
        )
    else:
        visual = (
            f'<div class="logo-wrapper">'
            f'<div class="tool-logo-fallback">{initials}</div>'
            f'</div>'
        )

    return f"""
    <article class="tool-card rank-{rank}">
      <div class="tool-rank">{rank_labels[rank]}</div>
      <div class="tool-visual">
        {visual}
      </div>
      <div class="tool-content">
        <h2 class="tool-name">{name}</h2>
        <div class="tool-meta">
          <span class="meta-pill">Rating {score}</span>
          <span class="meta-pill">Favorites {favorites}</span>
        </div>
      </div>
    </article>
    """


def _render_html(category_name: str, top3: list[dict]) -> str:
    template = TEMPLATE_PATH.read_text(encoding="utf-8")
    cards_html = "\n".join(
        _build_tool_card(tool, index)
        for index, tool in enumerate(top3[:3], start=1)
    )

    return (
        template.replace("{{ category_name }}", escape(category_name))
        .replace("{{ cards }}", cards_html)
    )


async def generate_top_image(category_name, top3, output_path="top.png"):
    try:
        from playwright.async_api import async_playwright
    except ModuleNotFoundError as exc:
        raise RuntimeError(
            "Playwright не установлен. Установи `python -m pip install playwright`, "
            "а затем `python -m playwright install chromium`."
        ) from exc

    if not TEMPLATE_PATH.exists():
        raise FileNotFoundError(f"HTML template not found: {TEMPLATE_PATH}")

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    html = _render_html(category_name, top3)

    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch()
        page = await browser.new_page(
            viewport={"width": 1200, "height": 760},
            device_scale_factor=2,
        )
        await page.set_content(html, wait_until="networkidle")
        await page.screenshot(path=str(output_path), full_page=True)
        await browser.close()

    return str(output_path)
