from __future__ import annotations

from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


class ImbalanceVisualisation:
    """Create chart images for the imbalance report."""

    def __init__(
        self,
        df: pd.DataFrame,
        output_dir: str | Path | None = None,
        base_dir: str | Path | None = None,
    ) -> None:
        self.df = df.copy()
        self.output_dir = Path(output_dir) if output_dir else Path(__file__).parent / "output" / "assets"
        self.base_dir = Path(base_dir) if base_dir else None
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def _path_for_html(self, image_path: Path) -> str:
        if self.base_dir:
            try:
                return image_path.relative_to(self.base_dir).as_posix()
            except ValueError:
                return image_path.resolve().as_uri()
        return image_path.as_posix()

    def _save_figure(self, fig: plt.Figure, filename: str) -> Path:
        file_path = self.output_dir / filename
        fig.tight_layout()
        fig.savefig(file_path, dpi=150)
        plt.close(fig)
        return file_path

    def _compact_time_labels(self) -> list[str]:
        """Create compact axis labels in the format T-1 : HH:MM and T : HH:MM."""
        parsed = pd.to_datetime(self.df["settlementPeriod"], errors="coerce")
        if parsed.isna().all():
            return [str(value) for value in self.df["settlementPeriod"]]

        settlement_day = parsed.dt.date.max()
        labels: list[str] = []
        for ts in parsed:
            if pd.isna(ts):
                labels.append("Unknown")
                continue
            prefix = "T" if ts.date() == settlement_day else "T-1"
            labels.append(f"{prefix} : {ts.strftime('%H:%M')}")
        return labels

    def plot_combined_volume_price(self) -> dict[str, Any]:
        """Bar chart for NIV with overlaid single-price line and missing period shading."""
        fig, ax_left = plt.subplots(figsize=(12, 5))
        x = np.arange(len(self.df))
        labels = self._compact_time_labels()

        missing_mask = (
            self.df["missingData"].fillna(False)
            if "missingData" in self.df.columns
            else pd.Series(False, index=self.df.index)
        )

        for idx in self.df.index[missing_mask]:
            ax_left.axvspan(idx - 0.5, idx + 0.5, color="#f4b9b9", alpha=0.35, zorder=0)

        bar_colors = ["#f4b9b9" if is_missing else "#007f5f" for is_missing in missing_mask.tolist()]
        ax_left.bar(x, self.df["netImbalanceVolume"], color=bar_colors, zorder=2)
        ax_left.set_title("Net Imbalance Volume and Price by Settlement Period")
        ax_left.set_xlabel("Settlement Period")
        ax_left.set_ylabel("Net Imbalance Volume", color="#007f5f")
        ax_left.tick_params(axis="y", labelcolor="#007f5f")
        ax_left.grid(axis="y", alpha=0.25)

        ax_right = ax_left.twinx()
        price_series = self.df["systemSellPrice"] if "systemSellPrice" in self.df.columns else self.df["systemBuyPrice"]
        ax_right.plot(x, price_series, color="#7a0019", linewidth=2.4, marker="o", markersize=2.5, zorder=3)
        ax_right.set_ylabel("Price", color="#7a0019")
        ax_right.tick_params(axis="y", labelcolor="#7a0019")

        step = max(1, len(x) // 12)
        tick_positions = x[::step]
        tick_labels = [labels[i] for i in tick_positions]
        ax_left.set_xticks(tick_positions)
        ax_left.set_xticklabels(tick_labels, rotation=35, ha="right")

        if missing_mask.any():
            missing_labels = [labels[i] for i in self.df.index[missing_mask]]
            note_text = (
                "Missing periods imputed as 0 and shaded red: "
                + ", ".join(missing_labels)
            )
        else:
            note_text = "No missing periods in this run."

        fig.text(0.01, 0.01, note_text, fontsize=8.5, color="#6b1f1f")

        image_path = self._save_figure(fig, "combined_volume_price.png")
        return {
            "title": "Net Imbalance Volume with Price Overlay",
            "description": "Bars show net imbalance volume and the overlaid line shows system price (buy/sell equivalent); missing periods are shaded light red.",
            "image_path": self._path_for_html(image_path),
        }

    def generate_visualisations(self, limit: int = 1) -> list[dict[str, Any]]:
        """Generate the trader-focused combined visualisation."""
        charts = [self.plot_combined_volume_price]
        selected = charts[: max(1, min(limit, 1))]
        return [chart() for chart in selected]
