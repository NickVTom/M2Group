# Electricity Price Correlation Analysis

This Streamlit application analyzes and visualizes the correlation between electricity prices across different European grids.

## Features

- **Correlation Matrix Heatmap**: Visual representation of price correlations between selected grids
- **Top 5 Highest Correlations**: Shows which grids have the most similar price movements
- **Top 5 Lowest Correlations**: Shows which grids have the most different price behaviors
- **Neighbor Identification**: Automatically identifies whether correlated grids are neighboring countries
- **Summary Statistics**: Provides average correlations for neighbors vs non-neighbors
- **Interactive Selection**: Choose which grids to include in the analysis

## Supported Grids

- Germany-Luxembourg (DE-LU)
- Denmark (DK1, DK2)
- France (FR)
- Italy (IT)
- Austria (AT)
- Sweden (SE1-SE4)
- Norway (NO1-NO5)
- Czech Republic (CZ)
- Poland (PL)

## Installation

```bash
pip install -r requirements.txt
```

## Usage

```bash
streamlit run app.py
```

## Data Source

Electricity price data is fetched from [Energy Charts API](https://www.energy-charts.info/)

## License

CC BY 4.0 from Bundesnetzagentur | SMARD.de
