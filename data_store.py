from __future__ import annotations
from io import BytesIO
from pathlib import Path
import pandas as pd


class CSVDataStore:
    def __init__(self, cfg):
        self.cfg = cfg

    @property
    def path(self) -> Path:
        return self.cfg.data_path

    def load(self) -> pd.DataFrame:
        df = pd.read_csv(self.path)

        # Ensure required columns exist
        if "WorkStatus" not in df.columns:
            df["WorkStatus"] = ""

        if "Comments" not in df.columns:
            df["Comments"] = ""

        if "LastUpdatedAt" not in df.columns:
            df["LastUpdatedAt"] = ""

        return df.fillna("")

    def save(self, df: pd.DataFrame) -> None:
        df = df.fillna("")
        df.to_csv(self.path, index=False)

    def to_csv_bytes(self, df: pd.DataFrame) -> bytes:
        return df.fillna("").to_csv(index=False).encode("utf-8")

    def validate(self, df: pd.DataFrame) -> list[str]:
        errors = []

        ws = df["WorkStatus"].astype(str).str.strip()
        comments = df["Comments"].astype(str).str.strip()

        missing_ws = ws.eq("")
        if missing_ws.any():
            for idx in df.index[missing_ws]:
                errors.append(f"- Row {idx+1}: WorkStatus is required.")

        missing_comments = ws.eq("Not Required") & comments.eq("")
        if missing_comments.any():
            for idx in df.index[missing_comments]:
                errors.append(
                    f"- Row {idx+1}: Comments required when WorkStatus = 'Not Required'."
                )

        return errors