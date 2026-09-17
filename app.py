import streamlit as st
import pandas as pd
import numpy as np
import requests
import plotly.graph_objects as go
from datetime import datetime

st.set_page_config(page_title="Electricity Price Correlation", layout="wide")

st.title("⚡ European Electricity Price Correlation Analysis")
st.markdown("Analyze correlations between electricity prices across European grids")

# Define grid zones
GRIDS = {
    "DE-LU": {"name": "Germany-Luxembourg"},
    "DK1": {"name": "Denmark West"},
    "DK2": {"name": "Denmark East"},
    "FR": {"name": "France"},
    "IT": {"name": "Italy"},
    "AT": {"name": "Austria"},
    "SE1": {"name": "Sweden North"},
    "SE2": {"name": "Sweden Central"},
    "SE3": {"name": "Sweden South"},
    "SE4": {"name": "Sweden East"},
    "NO1": {"name": "Norway South"},
    "NO2": {"name": "Norway Central"},
    "NO3": {"name": "Norway Mid"},
    "NO4": {"name": "Norway North"},
    "NO5": {"name": "Norway Far North"},
    "CZ": {"name": "Czech Republic"},
    "PL": {"name": "Poland"},
}



@st.cache_data(ttl=3600)
def fetch_grid_data(grid):
    """Fetch electricity price data for a specific grid"""
    try:
        response = requests.get(f'https://api.energy-charts.info/price?bzn={grid}', timeout=10)
        result = response.json()
        
        if 'unix_seconds' not in result or 'price' not in result:
            return None
        
        df = pd.DataFrame({
            'unix_seconds': result.get('unix_seconds', []),
            'price': result.get('price', []),
        })
        
        if len(df) == 0:
            return None
        
        df['datetime'] = pd.to_datetime(df['unix_seconds'], unit='s')
        return df
    except Exception as e:
        st.warning(f"Failed to fetch data for {grid}: {str(e)}")
        return None

def create_correlation_matrix(data_dict):
    """Create correlation matrix from grid data"""
    prices_dict = {}
    
    # Extract prices aligned by datetime
    for grid, df in data_dict.items():
        if df is not None and len(df) > 0:
            prices_dict[grid] = df.set_index('datetime')['price']
    
    if len(prices_dict) < 2:
        return None
    
    # Align all data to common datetime index
    combined = pd.DataFrame(prices_dict)
    
    # Drop rows with NaN values
    combined = combined.dropna()
    
    if len(combined) == 0:
        return None
    
    # Calculate correlation matrix
    corr_matrix = combined.corr()
    return corr_matrix

# Main app
col1, col2 = st.columns([3, 1])

with col2:
    st.markdown("### ⚙️ Settings")
    selected_grids = st.multiselect(
        "Select grids to analyze:",
        options=list(GRIDS.keys()),
        default=["DE-LU", "DK1", "DK2", "FR", "AT", "SE2", "NO1"],
        help="Choose which European grids to include in the correlation analysis"
    )

if not selected_grids:
    st.warning("Please select at least 2 grids to analyze")
else:
    with col1:
        st.markdown("### 📊 Fetching Data...")
    
    # Fetch data for selected grids
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    data_dict = {}
    for idx, grid in enumerate(selected_grids):
        status_text.text(f"Fetching data for {GRIDS[grid]['name']}...")
        data_dict[grid] = fetch_grid_data(grid)
        progress_bar.progress((idx + 1) / len(selected_grids))
    
    status_text.empty()
    progress_bar.empty()
    
    # Create correlation matrix
    corr_matrix = create_correlation_matrix(data_dict)
    
    if corr_matrix is None:
        st.error("Could not create correlation matrix. Try different grids.")
    else:
        st.markdown("### 📈 Correlation Matrix Heatmap")
        
        fig = go.Figure(data=go.Heatmap(
            z=corr_matrix.values,
            x=corr_matrix.columns.tolist(),
            y=corr_matrix.index.tolist(),
            colorscale='RdBu',
            zmid=0.5,
            text=np.round(corr_matrix.values, 3),
            texttemplate='%{text:.3f}',
            textfont={"size": 10},
            colorbar=dict(title="Correlation"),
        ))
        
        fig.update_layout(
            height=600,
            title_text="Electricity Price Correlations Between Grids",
            xaxis_title="Grid",
            yaxis_title="Grid",
        )
        
        st.plotly_chart(fig, use_container_width=True)
