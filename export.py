"""
Export CRM-ready data files for Salesforce Marketing Cloud.

Produces a CSV structured as a Data Extension that can be:
  1. Uploaded directly to SFMC
  2. Consumed by Journey Builder to trigger the right creative per fan
"""

from __future__ import annotations

import datetime
import io
import pandas as pd

from generator import EmailCreative


def build_crm_dataframe(
    creative: EmailCreative,
    fan_df: pd.DataFrame,
    segment_key: str,
    send_date: datetime.date | None = None,
) -> pd.DataFrame:
    """
    Merge generated creative with the fan list for a given segment.

    Parameters
    ----------
    creative : EmailCreative
        The generated email content.
    fan_df : pd.DataFrame
        Fan database. Expected columns:
        email, first_name, segment_primary, segment_score, city, state
    segment_key : str
        Which segment to filter fans for.
    send_date : date, optional
        When the email should be sent. Defaults to 3 days before game.

    Returns
    -------
    pd.DataFrame
        One row per recipient, ready for SFMC Data Extension upload.
    """
    if send_date is None:
        game_dt = datetime.date.fromisoformat(creative.game_date)
        send_date = game_dt - datetime.timedelta(days=3)

    # Filter fans belonging to this segment
    segment_fans = fan_df[fan_df["segment_primary"] == segment_key].copy()

    # Build the export rows
    segment_fans["subject_line"] = creative.subject_line
    segment_fans["preview_text"] = creative.preview_text
    segment_fans["headline"] = creative.headline
    segment_fans["body"] = creative.body
    segment_fans["cta_text"] = creative.cta_text
    segment_fans["image_concept"] = creative.image_concept
    segment_fans["creative_version_id"] = f"v_{segment_key}_{creative.game_date}"
    segment_fans["game_date"] = creative.game_date
    segment_fans["game_time"] = creative.game_time
    segment_fans["opponent"] = creative.opponent
    segment_fans["send_date"] = send_date.isoformat()
    segment_fans["segment"] = segment_key

    # Select and order columns for SFMC
    export_cols = [
        "email",
        "first_name",
        "segment",
        "segment_score",
        "subject_line",
        "preview_text",
        "headline",
        "body",
        "cta_text",
        "image_concept",
        "creative_version_id",
        "game_date",
        "game_time",
        "opponent",
        "send_date",
    ]
    # Only include columns that exist
    export_cols = [c for c in export_cols if c in segment_fans.columns]

    return segment_fans[export_cols].reset_index(drop=True)


def dataframe_to_csv_bytes(df: pd.DataFrame) -> bytes:
    """Convert a DataFrame to CSV bytes for download."""
    buffer = io.BytesIO()
    df.to_csv(buffer, index=False)
    return buffer.getvalue()


def build_full_export(
    creatives: dict[str, EmailCreative],
    fan_df: pd.DataFrame,
    send_date: datetime.date | None = None,
) -> pd.DataFrame:
    """
    Build a combined CRM export for multiple segments at once.

    Parameters
    ----------
    creatives : dict[str, EmailCreative]
        Mapping of segment_key -> generated creative.
    fan_df : pd.DataFrame
        Full fan database.
    send_date : date, optional
        Override send date for all segments.

    Returns
    -------
    pd.DataFrame
        Combined export, all segments.
    """
    frames = []
    for seg_key, creative in creatives.items():
        seg_df = build_crm_dataframe(creative, fan_df, seg_key, send_date)
        frames.append(seg_df)

    if not frames:
        return pd.DataFrame()

    return pd.concat(frames, ignore_index=True)
