from __future__ import annotations

import sys
from pathlib import Path
import webbrowser

import pandas as pd

# Ensure src/ is importable when running this file directly (python src/imbalance_report.py).
_SRC_DIR = str(Path(__file__).parent)
if _SRC_DIR not in sys.path:
    sys.path.insert(0, _SRC_DIR)

from api_client import APIClient
from data_processing import DataProcessor
from generate_report import export_report_pdf, generate_report
from imbalance_visualisation import ImbalanceVisualisation
from logging_config import logger 


def build_imbalance_report(settlement_date: str | None = None, open_browser: bool = True) -> str:
    """Fetch, process, visualise, and render the HTML report, then export to PDF."""
    logger.info(f"Starting imbalance report generation for settlement date: {settlement_date or 'latest available'}")
    api_client = APIClient()
    data_processor = DataProcessor(api_client)
    logger.debug("Initialized API client and data processor.")
    report_for_date = settlement_date or api_client.get_settlement_date()

    report_dir = Path(__file__).parent
    output_dir = report_dir / "output"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"Output directory created at: {output_dir}")

    # DataFrame is returned directly.
    # CSV is exported for persistence.
    df, _ = data_processor.process_data(
        output_format="json",
        settlement_date=report_for_date,
        output_dir=output_dir,
    )

    file_stem = f"imbalance_report_{report_for_date}"
    html_output = output_dir / f"{file_stem}.html"
    pdf_output = output_dir / f"{file_stem}.pdf"

    visualiser = ImbalanceVisualisation(
        df=df,
        output_dir=output_dir / "assets",
        base_dir=output_dir,
    )
    visualisations = visualiser.generate_visualisations(limit=1)

    logger.debug(f"Generated visualisations: {list(visualisations[0].keys()) if visualisations else 'None'}")

    report_path = generate_report(
        df=df,
        visualisations=visualisations,
        output_file=str(html_output),
        report_title=f"Daily System Imbalance Report ({report_for_date})",
    )
    pdf_path = export_report_pdf(report_path, str(pdf_output))

    if open_browser:
        webbrowser.open(Path(report_path).resolve().as_uri())

    logger.info(f"Report generation completed. HTML: {report_path} | PDF: {pdf_path}")

    return f"HTML: {report_path} | PDF: {pdf_path}"


if __name__ == "__main__":
    path = build_imbalance_report()
    print(f"Report generated: {path}")
