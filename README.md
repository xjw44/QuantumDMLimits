# QuantumDMLimits

[![MIT Licence](https://badges.frapsoft.com/os/mit/mit.svg?v=103)](https://opensource.org/licenses/mit-license.php)

An open-source plotting tool for compiling public dark matter direct detection limits. The goal of this repository is to collect exclusion limits and projected sensitivities from published dark matter direct detection experiments (e.g. DarkSide, LZ, PandaX, SuperCDMS) into a common set of digitized curves, and to provide notebooks for reproducing publication-quality comparison plots from them.

Curves are gathered either by digitizing figures from papers (via `qdmlimits`'s pixel-extraction tools), reading data released alongside a publication (e.g. HEPData YAML), or parsing native experiment data files (e.g. MATLAB `.mat` sensitivity outputs). Each digitized curve is saved as a plain CSV so it can be reused across plots without repeating the extraction step.

**Disclaimer:** limits collected here come from a wide range of papers with differing conventions, assumptions, and levels of statistical rigor — some are observed exclusions, others are projected/future sensitivities. Digitized curves are approximations of the original published figures and may carry some pixel-extraction error. Always check the original source before relying on a curve for quantitative work.

## Repository layout

- `qdmlimits/` — the core Python package: PDF/image loading (`pdf.py`), axis calibration (`calibration.py`), and curve extraction (`extraction.py`).
- `curves/` — one subdirectory per source (paper, experiment, or data release), each with an `outputs/` folder of digitized CSV curves.
- `notebooks/` — one `digitize_*.ipynb` notebook per source curve, plus `plot_curves.ipynb` which combines the digitized curves into comparison plots.

## Getting started

```bash
conda env create -f environment.yml
conda activate qdmlimits
pip install -e .
```

Then open any `notebooks/digitize_*.ipynb` to extract a new curve, or `notebooks/plot_curves.ipynb` to reproduce the combined limit plot.

## Curves currently included

- DarkSide-50 (NQ analysis)
- LZ (observed, via HEPData)
- PandaX-4T
- SuperCDMS SNOLAB HV (projected)
