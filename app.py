import streamlit as st
import pandas as pd
import numpy as np
import requests
import plotly.graph_objects as go
from datetime import datetime
import time

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

def are_neighbors(grid1, grid2):
    """Check if two grids are neighbors"""
    neighbors1 = GRIDS[grid1]["neighbors"]
    neighbors2 = GRIDS[grid2]["neighbors"]
    
    # Extract country codes for comparison
    country1 = grid1.split("-")[0] if "-" not in grid1 else grid1
    country2 = grid2.split("-")[0] if "-" not in grid2 else grid2
    
    # Check if in each other's neighbor lists
    if any(n.startswith(country2) for n in neighbors1):
        return True
    if any(n.startswith(country1) for n in neighbors2):
        return True
    
    return False

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

def get_correlation_pairs(corr_matrix):
    """Extract all unique correlation pairs"""
    pairs = []
    grids = corr_matrix.index.tolist()
    
    for i in range(len(grids)):
        for j in range(i + 1, len(grids)):
            grid1, grid2 = grids[i], grids[j]
            corr_value = corr_matrix.loc[grid1, grid2]
            is_neighbor = are_neighbors(grid1, grid2)
            pairs.append({
                'grid1': grid1,
                'grid2': grid2,
                'correlation': corr_value,
                'is_neighbor': is_neighbor
            })
    
    return pairs

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
        # Display correlation matrix heatmap
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
        
        # Get all correlation pairs and sort
        pairs = get_correlation_pairs(corr_matrix)
        pairs_df = pd.DataFrame(pairs)
        
        col1, col2 = st.columns(2)
        
        # Top 5 Highest Correlations
        with col1:
            st.markdown("### 🔥 Top 5 Highest Correlations")
            top_5 = pairs_df.nlargest(5, 'correlation')
            
            for idx, row in top_5.iterrows():
                neighbor_badge = "🤝 **Neighboring**" if row['is_neighbor'] else "📍 Not neighbors"
                corr_value = row['correlation']
                
                st.markdown(f"""
                **{row['grid1']} ↔ {row['grid2']}**
                - Correlation: `{corr_value:.4f}`
                - {neighbor_badge}
                """)
        
        # Top 5 Lowest Correlations
        with col2:
            st.markdown("### ❄️ Top 5 Lowest Correlations")
            bottom_5 = pairs_df.nsmallest(5, 'correlation')
            
            for idx, row in bottom_5.iterrows():
                neighbor_badge = "🤝 **Neighboring**" if row['is_neighbor'] else "📍 Not neighbors"
                corr_value = row['correlation']
                
                st.markdown(f"""
                **{row['grid1']} ↔ {row['grid2']}**
                - Correlation: `{corr_value:.4f}`
                - {neighbor_badge}
                """)
        
        # Summary statistics
        st.markdown("---")
        st.markdown("### 📊 Summary Statistics")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            avg_corr = pairs_df['correlation'].mean()
            st.metric("Average Correlation", f"{avg_corr:.4f}")
        
        with col2:
            neighbor_avg = pairs_df[pairs_df['is_neighbor']]['correlation'].mean()
            st.metric("Neighbor Average", f"{neighbor_avg:.4f}")
        
        with col3:
            non_neighbor_avg = pairs_df[~pairs_df['is_neighbor']]['correlation'].mean()
            st.metric("Non-Neighbor Average", f"{non_neighbor_avg:.4f}")
        
        with col4:
            num_pairs = len(pairs_df)
            st.metric("Total Pairs Analyzed", num_pairs)
        
        # Data table
        with st.expander("📋 View All Correlations"):
            display_df = pairs_df.copy()
            display_df['Neighbors'] = display_df['is_neighbor'].apply(lambda x: "Yes" if x else "No")
            display_df['Correlation'] = display_df['correlation'].apply(lambda x: f"{x:.4f}")
            display_df = display_df[['grid1', 'grid2', 'Correlation', 'Neighbors']].rename(
                columns={'grid1': 'Grid 1', 'grid2': 'Grid 2'}
            )
            st.dataframe(display_df, use_container_width=True)
