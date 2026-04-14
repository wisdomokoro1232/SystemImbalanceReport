from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any
import html

import pandas as pd

from imbalance_summary import build_missing_period_note_html, generate_imbalance_summary


def build_summary_table_html(summary_df: pd.DataFrame) -> str:
    """Build HTML for a summary table from a dataframe."""
    headers = "".join(f"<th>{html.escape(str(col))}</th>" for col in summary_df.columns)

    row_html: list[str] = []
    for _, row in summary_df.iterrows():
        cells = "".join(f"<td>{html.escape(str(value))}</td>" for value in row)
        row_html.append(f"<tr>{cells}</tr>")

    return f"""
    <table class=\"summary-table\">
        <thead>
            <tr>{headers}</tr>
        </thead>
        <tbody>
            {''.join(row_html)}
        </tbody>
    </table>
    """


def build_visual_card_html(title: str, description: str, image_path: str | None = None) -> str:
    """Build one visualisation card section."""
    safe_title = html.escape(title)
    safe_description = html.escape(description)

    if image_path:
        safe_image_path = html.escape(image_path)
        visual_body = f'<img src="{safe_image_path}" alt="{safe_title}" class="visual-image" />'
    else:
        visual_body = '<div class="visual-placeholder">Visualisation to be added</div>'

    return f"""
    <article class=\"visual-card\">
        <h3>{safe_title}</h3>
        <p>{safe_description}</p>
        {visual_body}
    </article>
    """


def render_report_html(
    summary_df: pd.DataFrame,
    visualisations: list[dict[str, Any]] | None = None,
    missing_period_note_html: str = "",
    output_file: str = "imbalance_report.html",
    report_title: str = "Daily System Imbalance Report",
) -> str:
    """Render and save an HTML report from summary data and 1 visualisation."""
    script_dir = Path(__file__).parent
    template_path = script_dir / "main" / "report_template.html"
    template = template_path.read_text(encoding="utf-8")

    visuals = (visualisations or [])[:1]

    visual_html = "\n".join(
        build_visual_card_html(
            title=str(visual.get("title", "Untitled visualisation")),
            description=str(visual.get("description", "")),
            image_path=visual.get("image_path"),
        )
        for visual in visuals
    )

    rendered = (
        template.replace("{{REPORT_TITLE}}", html.escape(report_title))
        .replace("{{REPORT_DATE}}", datetime.now().strftime("%Y-%m-%d %H:%M"))
        .replace("{{SUMMARY_TABLE}}", build_summary_table_html(summary_df))
        .replace("{{MISSING_PERIOD_NOTE}}", missing_period_note_html)
        .replace("{{VISUALISATIONS}}", visual_html)
    )

    output_path = Path(output_file)
    if not output_path.is_absolute():
        output_path = script_dir / output_file

    output_path.write_text(rendered, encoding="utf-8")
    return str(output_path)


def generate_report(
    df: pd.DataFrame,
    visualisations: list[dict[str, Any]] | None = None,
    output_file: str = "imbalance_report.html",
    report_title: str = "Daily System Imbalance Report",
) -> str:
    """Build summary data and render the final HTML report."""
    imbalance_summary = generate_imbalance_summary(df)
    missing_period_note_html = build_missing_period_note_html(df)
    return render_report_html(
        summary_df=imbalance_summary,
        visualisations=visualisations,
        missing_period_note_html=missing_period_note_html,
        output_file=output_file,
        report_title=report_title,
    )


def export_report_pdf(html_file: str, pdf_file: str | None = None) -> str:
    """Export the generated HTML report to PDF using Playwright - ensures precise rendering and layout."""
    from playwright.sync_api import sync_playwright

    html_path = Path(html_file).resolve()
    output_pdf = Path(pdf_file).resolve() if pdf_file else html_path.with_suffix(".pdf")

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        page = browser.new_page()
        page.goto(html_path.as_uri(), wait_until="networkidle")
        page.pdf(
            path=str(output_pdf),
            format="A4",
            print_background=True,
            margin={"top": "10mm", "right": "10mm", "bottom": "10mm", "left": "10mm"},
        )
        browser.close()

    return str(output_pdf)
