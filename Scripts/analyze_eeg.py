"""
Analyze EEG data stored in a MATLAB .mat file.

Expected project structure:

project/
├── data/
│   └── S14_EEG.mat
├── results/
└── src/
    ├── __init__.py
    └── analyze_eeg.py

Example:

python src/analyze_eeg.py \
    --input data/S14_EEG.mat \
    --output results
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy import signal
from scipy.io import loadmat


DATA_VARIABLE_NAMES = [
    "data",
    "eeg_data",
    "EEG",
    "signal",
    "signals",
    "X",
]

SAMPLING_RATE_VARIABLE_NAMES = [
    "fs",
    "srate",
    "sampling_rate",
    "sample_rate",
    "sampling_frequency",
]

LABEL_VARIABLE_NAMES = [
    "labels",
    "channel_labels",
    "chanlabels",
    "channels",
    "ch_names",
]

BANDS = {
    "delta": (1, 4),
    "theta": (4, 8),
    "alpha": (8, 13),
    "beta": (13, 30),
    "gamma": (30, 45),
}


def find_variable(
    contents: dict[str, Any],
    candidate_names: list[str],
) -> tuple[Any | None, str | None]:
    """
    Find a variable using exact or case-insensitive matching.
    """
    for name in candidate_names:
        if name in contents_names:
        if name in contents:
            return contents[name], name

    lower_map
        for key in contents.keys()
    }

    for name in candidate_names:
        if name.lower() in lower_map:
            original_key = lower_map[name.lower()]
            return contents[original_key], original_key

    return None, None


def clean_label(item: Any) -> str:
    """
    Convert a MATLAB label object into a readable string.
    """
    value = item

    if isinstance(value, np.ndarray):
        value = value.squeeze()

        if value.size == 1:
            value = value.item()

    return str(value)


def load_eeg_mat(
    mat_path: Path,
) -> tuple[np.ndarray, float, list[str], dict[str, Any]]:
    """
    Load EEG data, sampling rate, and channel labels from a MAT file.

    Returns
    -------
    data_uv:
        EEG matrix in channels x samples format.

    fs:
        Sampling rate in Hz.

    labels:
        Channel names.

    metadata:
        Loading metadata and provenance warning.
    """
    if not mat_path.exists():
        raise FileNotFoundError(
            f"MAT file not found: {mat_path}"
        )

    mat_contents = loadmat(
        mat_path,
        squeeze_me=True,
        struct_as_record=False,
    )

    data_raw, data_variable_name = find_variable(
        mat_contents,
        DATA_VARIABLE_NAMES,
    )

    fs_raw, fs_variable_name = find_variable(
        mat_contents,
        SAMPLING_RATE_VARIABLE_NAMES,
    )

    labels_raw, labels_variable_name = find_variable(
        mat_contents,
        LABEL_VARIABLE_NAMES,
    )

    if data_raw is None:
        available = [
            key
            for key in mat_contents
            if not key.startswith("__")
        ]

        raise KeyError(
            "No EEG data variable was detected. "
            f"Expected one of: {DATA_VARIABLE_NAMES}. "
            f"Available variables: {available}"
        )

    if fs_raw is None:
        available = [
            key
            for key in mat_contents
            if not key.startswith("__")
        ]

        raise KeyError(
            "No sampling-rate variable was detected. "
            f"Expected one of: {SAMPLING_RATE_VARIABLE_NAMES}. "
            f"Available variables: {available}"
        )

    data_uv = np.asarray(
        data_raw,
        dtype=float,
    )

    data_uv = np.squeeze(data_uv)

    if data_uv.ndim != 2:
        raise ValueError(
            "EEG data must be a two-dimensional matrix. "
            f"Received shape: {data_uv.shape}"
        )

    fs = float(
        np.asarray(fs_raw).squeeze()
    )

    if not np.isfinite(fs) or fs <= 0:
        raise ValueError(
            f"Sampling rate must be positive. Received: {fs}"
        )

    if labels_raw is not None:
        labels_array = np.asarray(
            labels_raw,
            dtype=object,
        ).squeeze()

        labels = [
            clean_label(item)
            for item in np.atleast_1d(labels_array)
        ]
    else:
        labels = []

    # Convert to channels x samples.
    if (
        labels
        and len(labels) == data_uv.shape[1]
        and len(labels) != data_uv.shape[0]
    ):
        data_uv = data_uv.T

    elif not labels and data_uv.shape[0] > data_uv.shape[1]:
        data_uv = data_uv.T

    n_channels, n_samples = data_uv.shape

    if len(labels) != n_channels:
        labels = [
            f"Channel_{index + 1}"
            for index in range(n_channels)
        ]

    metadata = {
        "input_file": str(mat_path),
        "data_variable": data_variable_name,
        "sampling_rate_variable": fs_variable_name,
        "labels_variable": labels_variable_name,
        "sampling_rate_hz": fs,
        "n_channels": n_channels,
        "n_samples": n_samples,
        "duration_seconds": n_samples / fs,
        "channels": labels,
        "unit_assumption": (
            "microvolts; verify this from the MAT-file "
            "documentation before interpretation"
        ),
        "provenance_warning": (
            "Verify provenance and authenticity independently. "
            "Do not claim that the data were collected from human "
            "participants without appropriate documentation."
        ),
    }

    return data_uv, fs, labels, metadata


def calculate_summary(
    data_uv: np.ndarray,
    fs: float,
    labels: list[str],
) -> pd.DataFrame:
    """
    Calculate descriptive statistics for each channel.
    """
    n_channels, n_samples = data_uv.shape
    duration_seconds = n_samples / fs

    return pd.DataFrame(
        {
            "channel": labels,
            "sampling_rate_hz": fs,
            "n_samples": n_samples,
            "duration_seconds": duration_seconds,
            "mean_uv": np.mean(data_uv, axis=1),
            "std_uv": np.std(data_uv, axis=1, ddof=1),
            "minimum_uv": np.min(data_uv, axis=1),
            "maximum_uv": np.max(data_uv, axis=1),
            "rms_uv": np.sqrt(
                np.mean(data_uv ** 2, axis=1)
            ),
        }
    )


def plot_raw_eeg(
    data_uv: np.ndarray,
    fs: float,
    labels: list[str],
    output_path: Path,
) -> None:
    """
    Plot and save raw EEG signals.
    """
    n_channels, n_samples = data_uv.shape
    time = np.arange(n_samples) / fs

    fig, axes = plt.subplots(
        n_channels,
        1,
        figsize=(14, max(4, 2.5 * n_channels)),
        sharex=True,
    )

    axes = np.atleast_1d(axes)

    for index, axis in enumerate(axes):
        axis.plot(
            time,
            data_uv[index],
            linewidth=0.6,
        )
        axis.set_ylabel("µV")
        axis.set_title(labels[index])
        axis.grid(alpha=0.25)

    axes[-1].set_xlabel("Time (seconds)")
    fig.suptitle(
        "S14 EEG Raw Signals",
        fontsize=16,
    )

    plt.tight_layout()
    fig.savefig(
        output_path,
        dpi=300,
        bbox_inches="tight",
    )
    plt.close(fig)


def calculate_psd(
    data_uv: np.ndarray,
    fs: float,
    labels: list[str],
) -> tuple[
    dict[str, dict[str, np.ndarray]],
    pd.DataFrame,
]:
    """
    Calculate Welch PSD and dominant frequency per channel.
    """
    n_channels, n_samples = data_uv.shape

    psd_results = {}
    dominant_frequency_rows = []

    for index, label in enumerate(labels):
        frequencies, psd = signal.welch(
            data_uv[index],
            fs=fs,
            nperseg=min(
                n_samples,
                max(8, int(fs * 4)),
            ),
        )

        psd_results[label] = {
            "frequencies": frequencies,
            "psd": psd,
        }

        valid = (
            (frequencies >= 1)
            & (frequencies <= 45)
        )

        if np.any(valid):
            peak_index = np.argmax(psd[valid])
            dominant_frequency = frequencies[valid][peak_index]
        else:
            dominant_frequency = np.nan

        dominant_frequency_rows.append(
            {
                "channel": label,
                "dominant_frequency_hz": (
                    dominant_frequency
                ),
            }
        )

    dominant_frequency_table = pd.DataFrame(
        dominant_frequency_rows
    )

    return psd_results, dominant_frequency_table


def plot_psd(
    psd_results: dict[str, dict[str, np.ndarray]],
    output_path: Path,
) -> None:
    """
    Plot and save power spectral density curves.
    """
    labels = list(psd_results.keys())
    n_channels = len(labels)

    fig, axes = plt.subplots(
        n_channels,
        1,
        figsize=(12, max(4, 2.5 * n_channels)),
        sharex=True,
    )

    axes = np.atleast_1d(axes)

    for index, label in enumerate(labels):
        frequencies = psd_results[label]["frequencies"]
        psd = psd_results[label]["psd"]

        mask = frequencies <= 50

        axes[index].semilogy(
            frequencies[mask],
            psd[mask],
            linewidth=1,
        )

        axes[index].set_ylabel("PSD")
        axes[index].set_title(label)
        axes[index].grid(alpha=0.25)

    axes[-1].set_xlabel("Frequency (Hz)")
    fig.suptitle(
        "S14 EEG Power Spectral Density",
        fontsize=16,
    )

    plt.tight_layout()
    fig.savefig(
        output_path,
        dpi=300,
        bbox_inches="tight",
    )
    plt.close(fig)


def bandpower(
    x: np.ndarray,
    fs: float,
    low: float,
    high: float,
) -> float:
    """
    Estimate absolute band power using Welch PSD.
    """
    frequencies, psd = signal.welch(
        x,
        fs=fs,
        nperseg=min(
            len(x),
            max(8, int(fs * 4)),
        ),
    )

    mask = (
        (frequencies >= low)
        & (frequencies <= high)
    )

    if np.sum(mask) < 2:
        return float("nan")

    return float(
        np.trapezoid(
            psd[mask],
            frequencies[mask],
        )
    )


def calculate_bandpower(
    data_uv: np.ndarray,
    fs: float,
    labels: list[str],
) -> pd.DataFrame:
    """
    Calculate absolute and relative frequency-band power.
    """
    band_rows = []

    for index, label in enumerate(labels):
        row = {"channel": label}
        absolute_powers = {}

        for band_name, limits in BANDS.items():
            low, high = limits

            power = bandpower(
                data_uv[index],
                fs,
                low,
                high,
            )

            absolute_powers[band_name] = power

            row[
                f"{band_name}_power_uv_squared"
            ] = power

        valid_powers            if np.isfinite(value)
        ]

       _powers.values()
            if np.isfinite(value)
        ]

        total_power = sum(valid_powers)

        for band_name, power in absolute_powers.items():
            if total_power > 0 and np.isfinite(power):
                relative_power = power / total_power
            else:
                relative_power = np.nan

            row[
                f"{band_name}_relative_power"
            ] = relative_power

        band_rows.append(row)

    return pd.DataFrame(band_rows)


def run_analysis(
    input_path: Path,
    output_dir: Path,
) -> None:
    """
    Run the complete EEG analysis pipeline.
    """
    output_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    data_uv, fs, labels, metadata = load_eeg_mat(
        input_path
    )

    summary = calculate_summary(
        data_uv,
        fs,
        labels,
    )

    psd_results, dominant_frequency_table = (
        calculate_psd(
            data_uv,
            fs,
            labels,
        )
    )

    bandpower_table = calculate_bandpower(
        data_uv,
        fs,
        labels,
    )

    final_summary = (
        summary
        .merge(
            dominant_frequency_table,
            on="channel",
            how="left",
        )
        .merge(
            bandpower_table,
            on="channel",
            how="left",
        )
    )

    raw_figure_path = output_dir / "S14_raw_eeg.png"
    psd_figure_path = output_dir / "S14_psd.png"
    summary_path = output_dir / "S14_channel_summary.csv"
    metadata_path = output_dir / "S14_mat_metadata.json"

    plot_raw_eeg(
        data_uv,
        fs,
        labels,
        raw_figure_path,
    )

    plot_psd(
        psd_results,
        psd_figure_path,
    )

    final_summary.to_csv(
        summary_path,
        index=False,
    )

    with metadata_path.open(
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            metadata,
            file,
            ensure_ascii=False,
            indent=2,
        )

    print("Analysis completed successfully.")
    print(f"Input: {input_path}")
    print(f"Output directory: {output_dir}")
    print(f"Saved: {summary_path}")
    print(f"Saved: {metadata_path}")
    print(f"Saved: {raw_figure_path}")
    print(f"Saved: {psd_figure_path}")


def parse_arguments() -> argparse.Namespace:
    """
    Parse command-line arguments.
    """
    parser = argparse.ArgumentParser(
        description=(
            "Analyze EEG data stored in a MATLAB MAT file."
        )
    )

    parser.add_argument(
        "--input",
        required=True,
        type=Path,
        help="Path to the input MAT file.",
    )

    parser.add_argument(
        "--output",
        required=True,
        type=Path,
        help="Directory for CSV, JSON, and PNG outputs.",
    )

    return parser.parse_args()


def main() -> None:
    """
    Command-line entry point.
    """
    arguments = parse_arguments()

    run_analysis(
        input_path=arguments.input,
        output_dir=arguments.output,
    )


if __name__ == "__main__":
    main()
