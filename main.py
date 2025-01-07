import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from sklearn.preprocessing import MinMaxScaler
import io
import base64
from typing import Dict, List
import pulp
import pytesseract
from pdf2image import convert_from_path
import json
from groq import Groq
import os
import tempfile
import hashlib

# Hardcoded API key (consider moving to environment variable)
GROQ_API_KEY = "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"

# Set page configuration
st.set_page_config(
    page_title="Sustain",
    page_icon="📊",
    layout="wide"
)

# Initialize session state
if 'data' not in st.session_state:
    st.session_state.data = None

def calculate_esg_scores(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate ESG scores for projects
    """
    df_scored = df.copy()
    scaler = MinMaxScaler()
    
    # Environmental Score Components (40%)
    carbon_emissions_normalized = scaler.fit_transform(
        df[['Carbon Emissions (tons CO2/year)']].values.reshape(-1, 1)
    )
    df_scored['Carbon_Score'] = (1 - carbon_emissions_normalized) * 100
    df_scored['Energy_Score'] = df['Energy Efficiency (%)']
    
    df_scored['Climate_Score'] = (
        df_scored['Carbon_Score'] * 0.6 +
        df_scored['Energy_Score'] * 0.4
    )
    
    water_usage_normalized = scaler.fit_transform(
        df[['Water Usage (liters/year)']].values.reshape(-1, 1)
    )
    df_scored['Water_Score'] = (1 - water_usage_normalized) * 100
    df_scored['Waste_Score'] = df['Waste Management (%)']
    
    df_scored['Resource_Score'] = (
        df_scored['Water_Score'] * 0.5 +
        df_scored['Waste_Score'] * 0.5
    )
    
    df_scored['Pollution_Score'] = 100 - df['Pollution Impact Score (0-100)']
    
    df_scored['Environmental_Score'] = (
        df_scored['Climate_Score'] * 0.4 +
        df_scored['Resource_Score'] * 0.3 +
        df_scored['Pollution_Score'] * 0.3
    )
    
    # Social Score Components (35%)
    local_employment_normalized = scaler.fit_transform(
        df[['Local Employment (%)']].values.reshape(-1, 1)
    )
    df_scored['Local_Employment_Score'] = local_employment_normalized * 100
    
    community_normalized = scaler.fit_transform(
        df[['Community Investment (USD)']].values.reshape(-1, 1)
    )
    df_scored['Community_Score'] = community_normalized * 100
    
    df_scored['Social_Score'] = (
        df_scored['Local_Employment_Score'] * 0.6 +
        df_scored['Community_Score'] * 0.4
    )
    
    # Governance Score (25%)
    df_scored['Sustainability_Score'] = df['Sustainability Integration (%)']
    
    budget_normalized = scaler.fit_transform(
        df[['Project Budget (USD)']].values.reshape(-1, 1)
    )
    df_scored['Budget_Score'] = budget_normalized * 100
    
    df_scored['Governance_Score'] = (
        df_scored['Sustainability_Score'] * 0.7 +
        df_scored['Budget_Score'] * 0.3
    )
    
    # Calculate Raw ESG Score
    df_scored['ESG_Score_Raw'] = (
        df_scored['Environmental_Score'] * 0.40 +
        df_scored['Social_Score'] * 0.35 +
        df_scored['Governance_Score'] * 0.25
    )
    
    # Project Type Adjustment
    df_scored['Project_Type_Avg'] = df_scored.groupby('Project Type')['ESG_Score_Raw'].transform('mean')
    df_scored['Project_Type_Std'] = df_scored.groupby('Project Type')['ESG_Score_Raw'].transform('std')
    
    df_scored['Project_Type_Z_Score'] = (
        (df_scored['ESG_Score_Raw'] - df_scored['Project_Type_Avg']) / 
        df_scored['Project_Type_Std'].replace(0, 1)
    )
    
    # Phase-based adjustment
    phase_multiplier = {
        'Planning': 0.9,
        'Implementation': 1.0,
        'Operation': 1.1,
        'Completion': 1.2
    }
    df_scored['Phase_Multiplier'] = df_scored['Project Phase'].map(phase_multiplier)
    
    df_scored['ESG_Score'] = (50 + (df_scored['Project_Type_Z_Score'] * 10)) * df_scored['Phase_Multiplier']
    df_scored['ESG_Score'] = df_scored['ESG_Score'].clip(0, 100)
    
    # Calculate ESG Rating
    df_scored['ESG_Rating'] = pd.cut(
        df_scored['ESG_Score'],
        bins=[0, 20, 35, 50, 65, 80, 90, 100],
        labels=['CCC', 'B', 'BB', 'BBB', 'A', 'AA', 'AAA'],
        include_lowest=True
    )
    
    # Risk Metrics
    df_scored['ESG_Risk_Score'] = 100 - df_scored['ESG_Score']
    df_scored['Risk_Category'] = pd.cut(
        df_scored['ESG_Risk_Score'],
        bins=[0, 20, 40, 60, 80, 100],
        labels=['Negligible', 'Low', 'Medium', 'High', 'Severe']
    )
    
    # Rankings and Percentiles
    df_scored['ESG_Percentile'] = df_scored['ESG_Score'].rank(pct=True) * 100
    df_scored['Project_Type_Percentile'] = df_scored.groupby('Project Type')['ESG_Score'].rank(pct=True) * 100
    
    # Performance Categories
    for score_type in ['Environmental', 'Social', 'Governance']:
        df_scored[f'{score_type}_Status'] = pd.cut(
            df_scored[f'{score_type}_Score'],
            bins=[0, 40, 60, 80, 100],
            labels=['Poor', 'Average', 'Good', 'Excellent']
        )
    
    return df_scored

def data_upload_tab():
    st.header("Project Data Upload")
    
    uploaded_file = st.file_uploader(
        "Upload your Project ESG metrics data (CSV)",
        type=['csv']
    )
    
    if uploaded_file:
        try:
            data = pd.read_csv(uploaded_file)
            
            required_columns = [
                'Project Name',
                'Project Type',
                'Project Phase',
                'Project Budget (USD)',
                'Carbon Emissions (tons CO2/year)',
                'Energy Efficiency (%)',
                'Waste Management (%)',
                'Water Usage (liters/year)',
                'Pollution Impact Score (0-100)',
                'Local Employment (%)',
                'Community Investment (USD)',
                'Sustainability Integration (%)'
            ]
            
            missing_columns = [col for col in required_columns if col not in data.columns]
            
            if missing_columns:
                st.error(f"Missing required columns: {', '.join(missing_columns)}")
                return
            
            scored_data = calculate_esg_scores(data)
            st.session_state.data = scored_data
            
            st.success("Data processed successfully!")
            
            # preview of processed data
            st.subheader("Preview of Processed Data")
            st.dataframe(scored_data.head())
            
            # Download button for processed data
            csv = scored_data.to_csv(index=False)
            b64 = base64.b64encode(csv.encode()).decode()
            st.download_button(
                label="Download Processed Data",
                data=csv,
                file_name="project_esg_scores.csv",
                mime="text/csv"
            )
            
        except Exception as e:
            st.error(f"Error processing file: {str(e)}")
        
def project_analysis_tab():
    if st.session_state.data is None:
        st.warning("Please upload project data first")
        return
    
    st.header("Project ESG Analysis")
    
    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        selected_project = st.selectbox(
            "Select Project",
            st.session_state.data['Project Name'].tolist()
        )
    
    with col2:
        selected_type = st.selectbox(
            "Filter by Project Type",
            ['All'] + list(st.session_state.data['Project Type'].unique())
        )
    
    with col3:
        selected_phase = st.selectbox(
            "Filter by Project Phase",
            ['All'] + list(st.session_state.data['Project Phase'].unique())
        )
    
    # Filter data
    filtered_data = st.session_state.data.copy()
    if selected_type != 'All':
        filtered_data = filtered_data[filtered_data['Project Type'] == selected_type]
    if selected_phase != 'All':
        filtered_data = filtered_data[filtered_data['Project Phase'] == selected_phase]
    
    project_data = filtered_data[
        filtered_data['Project Name'] == selected_project
    ].iloc[0]
    
    # Project Overview
    # Project Overview
    st.subheader("Project Overview")
    col1, col2, col3, col4 = st.columns(4)

# Custom CSS for white text on black background
    st.markdown("""
        <style>
        .metric-container {
            background-color: #0E1117;
            padding: 20px;
            border-radius: 5px;
            margin: 5px;
            border: 1px solid #2D2D2D;
        }
        .metric-label {
            color: #FFFFFF;
            font-size: 14px;
            font-weight: 500;
            opacity: 0.8;
        }
        .metric-value {
            color: #FFFFFF;
            font-size: 24px;
            font-weight: bold;
        }
        .metric-delta {
            color: #FFFFFF;
            font-size: 12px;
            opacity: 0.7;
        }
        </style>
    """, unsafe_allow_html=True)

    with col1:
        st.markdown(f"""
            <div class="metric-container">
                <div class="metric-label">ESG Score</div>
                <div class="metric-value">{project_data['ESG_Score']:.1f}</div>
                <div class="metric-delta">{project_data['ESG_Score'] - project_data['Project_Type_Avg']:.1f} vs Type Avg</div>
            </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown(f"""
            <div class="metric-container">
                <div class="metric-label">ESG Rating</div>
                <div class="metric-value">{project_data['ESG_Rating']}</div>
                <div class="metric-delta">Percentile: {project_data['Project_Type_Percentile']:.1f}%</div>
            </div>
        """, unsafe_allow_html=True)

    with col3:
        st.markdown(f"""
            <div class="metric-container">
                <div class="metric-label">Risk Category</div>
                <div class="metric-value">{project_data['Risk_Category']}</div>
                <div class="metric-delta">Risk Score: {project_data['ESG_Risk_Score']:.1f}</div>
            </div>
        """, unsafe_allow_html=True)

    with col4:
        st.markdown(f"""
            <div class="metric-container">
                <div class="metric-label">Project Budget</div>
                <div class="metric-value">${project_data['Project Budget (USD)']:,.0f}</div>
                <div class="metric-delta">Phase: {project_data['Project Phase']}</div>
            </div>
        """, unsafe_allow_html=True)
    
    # ESG Component Scores
    st.subheader("ESG Component Scores")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        fig = go.Figure(go.Indicator(
            mode="gauge+number+delta",
            value=project_data['Environmental_Score'],
            delta={'reference': filtered_data['Environmental_Score'].mean()},
            title={'text': "Environmental Score (40%)"},
            gauge={
                'axis': {'range': [0, 100]},
                'bar': {'color': "green"},
                'steps': [
                    {'range': [0, 40], 'color': "lightgray"},
                    {'range': [40, 70], 'color': "gray"},
                    {'range': [70, 100], 'color': "darkgray"}
                ],
                'threshold': {
                    'line': {'color': "red", 'width': 4},
                    'thickness': 0.75,
                    'value': filtered_data['Environmental_Score'].mean()
                }
            }
        ))
        st.plotly_chart(fig)
        
        # Environmental components
        st.write("Environmental Components:")
        st.write(f"- Climate Impact: {project_data['Climate_Score']:.1f}")
        st.write(f"- Resource Use: {project_data['Resource_Score']:.1f}")
        st.write(f"- Pollution: {project_data['Pollution_Score']:.1f}")
    
    with col2:
        fig = go.Figure(go.Indicator(
            mode="gauge+number+delta",
            value=project_data['Social_Score'],
            delta={'reference': filtered_data['Social_Score'].mean()},
            title={'text': "Social Score (35%)"},
            gauge={
                'axis': {'range': [0, 100]},
                'bar': {'color': "blue"},
                'steps': [
                    {'range': [0, 40], 'color': "lightgray"},
                    {'range': [40, 70], 'color': "gray"},
                    {'range': [70, 100], 'color': "darkgray"}
                ],
                'threshold': {
                    'line': {'color': "red", 'width': 4},
                    'thickness': 0.75,
                    'value': filtered_data['Social_Score'].mean()
                }
            }
        ))
        st.plotly_chart(fig)
        
        # Social components
        st.write("Social Components:")
        st.write(f"- Local Employment: {project_data['Local_Employment_Score']:.1f}")
        st.write(f"- Community Impact: {project_data['Community_Score']:.1f}")
    
    with col3:
        fig = go.Figure(go.Indicator(
            mode="gauge+number+delta",
            value=project_data['Governance_Score'],
            delta={'reference': filtered_data['Governance_Score'].mean()},
            title={'text': "Governance Score (25%)"},
            gauge={
                'axis': {'range': [0, 100]},
                'bar': {'color': "purple"},
                'steps': [
                    {'range': [0, 40], 'color': "lightgray"},
                    {'range': [40, 70], 'color': "gray"},
                    {'range': [70, 100], 'color': "darkgray"}
                ],
                'threshold': {
                    'line': {'color': "red", 'width': 4},
                    'thickness': 0.75,
                    'value': filtered_data['Governance_Score'].mean()
                }
            }
        ))
        st.plotly_chart(fig)
        
        # Governance components
        st.write("Governance Components:")
        st.write(f"- Sustainability Integration: {project_data['Sustainability_Score']:.1f}")
        st.write(f"- Budget Management: {project_data['Budget_Score']:.1f}")
    
    # Detailed Metrics
    st.subheader("Detailed Project Metrics")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("Environmental Metrics")
        metrics_df = pd.DataFrame({
            'Metric': [
                'Carbon Emissions',
                'Energy Efficiency',
                'Water Usage',
                'Waste Management',
                'Pollution Impact'
            ],
            'Value': [
                f"{project_data['Carbon Emissions (tons CO2/year)']:,.0f} tons",
                f"{project_data['Energy Efficiency (%)']}%",
                f"{project_data['Water Usage (liters/year)']:,.0f} L",
                f"{project_data['Waste Management (%)']}%",
                f"{project_data['Pollution Impact Score (0-100)']}/100"
            ]
        })
        st.table(metrics_df)
    
    with col2:
        st.write("Social & Governance Metrics")
        metrics_df = pd.DataFrame({
            'Metric': [
                'Local Employment',
                'Community Investment',
                'Sustainability Integration',
                'Project Budget'
            ],
            'Value': [
                f"{project_data['Local Employment (%)']}%",
                f"${project_data['Community Investment (USD)']:,.2f}",
                f"{project_data['Sustainability Integration (%)']}%",
                f"${project_data['Project Budget (USD)']:,.2f}"
            ]
        })
        st.table(metrics_df)
    
    # Peer Comparison
    st.subheader("Project Comparison")
    
    fig = px.scatter(
        filtered_data,
        x='Environmental_Score',
        y='Social_Score',
        size='Project Budget (USD)',
        color='ESG_Rating',
        hover_data=['Project Name', 'ESG_Score', 'Project Phase'],
        title='ESG Score Distribution by Project'
    )
    
    # Highlight selected project
    fig.add_trace(
        go.Scatter(
            x=[project_data['Environmental_Score']],
            y=[project_data['Social_Score']],
            mode='markers',
            marker=dict(
                symbol='star',
                size=20,
                color='yellow',
                line=dict(color='black', width=2)
            ),
            name=selected_project,
            showlegend=True
        )
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
def analytics_dashboard_tab():
    if st.session_state.data is None:
        st.warning("Please upload project data first")
        return
    
    st.header("Project Portfolio Analytics Dashboard")
    
    # Simple Filters
    col1, col2 = st.columns(2)
    with col1:
        selected_types = st.multiselect(
            "Project Type",
            options=list(st.session_state.data['Project Type'].unique()),
            default=list(st.session_state.data['Project Type'].unique())
        )
    
    with col2:
        selected_phases = st.multiselect(
            "Project Phase",
            options=list(st.session_state.data['Project Phase'].unique()),
            default=list(st.session_state.data['Project Phase'].unique())
        )
    
    # Filter data
    filtered_data = st.session_state.data[
        (st.session_state.data['Project Type'].isin(selected_types)) &
        (st.session_state.data['Project Phase'].isin(selected_phases))
    ]
    
    # Key Metrics Row
    st.subheader("Portfolio Overview")
    col1, col2, col3, col4 = st.columns(4)
    
    # Key Metrics Row
    st.subheader("Portfolio Overview")
    col1, col2, col3, col4 = st.columns(4)

    st.markdown("""
        <style>
        .metric-container {
            background-color: #0E1117;
            padding: 20px;
            border-radius: 5px;
            margin: 5px;
            border: 1px solid #2D2D2D;
        }
        .metric-label {
            color: #FFFFFF;
            font-size: 14px;
            font-weight: 500;
            opacity: 0.8;
        }
        .metric-value {
            color: #FFFFFF;
            font-size: 24px;
            font-weight: bold;
        }
        .metric-delta {
            color: #FFFFFF;
            font-size: 12px;
            opacity: 0.7;
        }
        </style>
    """, unsafe_allow_html=True)

    with col1:
        st.markdown(f"""
            <div class="metric-container">
                <div class="metric-label">Total Projects</div>
                <div class="metric-value">{len(filtered_data)}</div>
                <div class="metric-delta">${filtered_data['Project Budget (USD)'].sum():,.0f} Total Budget</div>
            </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown(f"""
            <div class="metric-container">
                <div class="metric-label">Average ESG Score</div>
                <div class="metric-value">{filtered_data['ESG_Score'].mean():.1f}</div>
                <div class="metric-delta">Range: {filtered_data['ESG_Score'].min():.1f} - {filtered_data['ESG_Score'].max():.1f}</div>
            </div>
        """, unsafe_allow_html=True)

    with col3:
        st.markdown(f"""
            <div class="metric-container">
                <div class="metric-label">Average Risk Score</div>
                <div class="metric-value">{filtered_data['ESG_Risk_Score'].mean():.1f}</div>
                <div class="metric-delta">{len(filtered_data[filtered_data['Risk_Category'] == 'High'])} High Risk Projects</div>
            </div>
        """, unsafe_allow_html=True)

    with col4:
        st.markdown(f"""
            <div class="metric-container">
                <div class="metric-label">Projects in Progress</div>
                <div class="metric-value">{len(filtered_data[filtered_data['Project Phase'] != 'Completion'])}</div>
                <div class="metric-delta">{len(filtered_data[filtered_data['Project Phase'] == 'Completion'])} Completed</div>
            </div>
        """, unsafe_allow_html=True)
    
    # Two main sections
    col1, col2 = st.columns(2)
    
    with col1:
        # ESG Score Distribution
        st.subheader("ESG Score Distribution")
        fig = px.histogram(
            filtered_data,
            x='ESG_Score',
            color='ESG_Rating',
            title="ESG Score Distribution by Rating"
        )
        st.plotly_chart(fig, use_container_width=True)
        
        # Project Type Performance
        st.subheader("Performance by Project Type")
        type_performance = filtered_data.groupby('Project Type').agg({
            'ESG_Score': 'mean',
            'Project Budget (USD)': 'sum',
            'Project Name': 'count'
        }).round(2)
        st.dataframe(type_performance)
    
    with col2:
        # Risk Analysis
        st.subheader("Risk Analysis")
        fig = px.pie(
            filtered_data,
            names='Risk_Category',
            values='Project Budget (USD)',
            title="Portfolio Risk Distribution"
        )
        st.plotly_chart(fig, use_container_width=True)
        
        # Phase Analysis
        st.subheader("Project Phase Analysis")
        phase_analysis = filtered_data.groupby('Project Phase').agg({
            'ESG_Score': 'mean',
            'Project Budget (USD)': 'sum',
            'Project Name': 'count'
        }).round(2)
        st.dataframe(phase_analysis)
    
    # Bottom section - Key Findings
    st.subheader("Key Findings & Key Performance Indicators")
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### Desirable Projects")
        top_projects = filtered_data.nlargest(5, 'ESG_Score')[
            ['Project Name', 'Project Type', 'ESG_Score', 'ESG_Rating']
        ]
        st.dataframe(top_projects)
    
    with col2:
        st.markdown("### High Risk Projects")
        risk_projects = filtered_data[filtered_data['Risk_Category'] == 'High'][
            ['Project Name', 'Project Type', 'ESG_Risk_Score', 'Risk_Category']
        ]
        st.dataframe(risk_projects)
    
    # Export Options
    st.subheader("Export Dashboard Data")
    col1, col2 = st.columns(2)
    
    with col1:
        csv = filtered_data.to_csv(index=False)
        b64 = base64.b64encode(csv.encode()).decode()
        st.download_button(
            label="Download Full Dataset",
            data=csv,
            file_name="portfolio_analysis.csv",
            mime="text/csv"
        )
    
    with col2:
        summary_stats = filtered_data.describe()
        csv_summary = summary_stats.to_csv()
        b64_summary = base64.b64encode(csv_summary.encode()).decode()
        st.download_button(
            label="Download Summary Statistics",
            data=csv_summary,
            file_name="portfolio_summary.csv",
            mime="text/csv"
        )
        

def optimization_tab():
    if st.session_state.data is None:
        st.warning("Please upload project data first")
        return
    
    st.header("ESG Portfolio Optimization Engine")
    
    # Optimization Settings
    st.subheader("Optimization Parameters")
    
    col1, col2 = st.columns(2)
    
    with col1:
        total_budget = st.number_input(
            "Total Portfolio Budget (USD)",
            min_value=0.0,
            value=float(st.session_state.data['Project Budget (USD)'].sum()),
            format="%0.2f"
        )
        
        min_esg_score = st.slider(
            "Minimum ESG Score Target",
            0, 100, 60
        )
        
        risk_tolerance = st.slider(
            "Risk Tolerance (0-100)",
            0, 100, 50,
            help="Higher values allow for more risky projects"
        )
        
        diversification_factor = st.slider(
            "Project Type Diversification Factor",
            0.0, 1.0, 0.3,
            help="Higher values enforce more diversification across project types"
        )
    
    with col2:
        st.markdown("### Optimization Objectives")
        objective_weights = {
            'ESG_Score': st.slider("ESG Score Weight", 0.0, 1.0, 0.4),
            'Risk': st.slider("Risk Minimization Weight", 0.0, 1.0, 0.3),
            'Return': st.slider("Return Maximization Weight", 0.0, 1.0, 0.3)
        }
        
        # Normalize weights
        total_weight = sum(objective_weights.values())
        objective_weights = {k: v/total_weight for k, v in objective_weights.items()}
        
        st.markdown("### Constraints")
        max_project_allocation = st.slider(
            "Maximum Allocation per Project (%)",
            0, 100, 30
        )
    
    # Run Optimization
    if st.button("Run Portfolio Optimization"):
        with st.spinner("Optimizing portfolio allocation..."):
            try:
                # Prepare optimization model
                prob = pulp.LpProblem("ESG_Portfolio_Optimization", pulp.LpMaximize)
                
                # Decision variables (allocation to each project)
                projects = st.session_state.data['Project Name'].tolist()
                x = pulp.LpVariable.dicts("project",
                                        projects,
                                        lowBound=0,
                                        upBound=1)
                
                # Objective function
                prob += (
                    objective_weights['ESG_Score'] * 
                    pulp.lpSum([x[p] * st.session_state.data.loc[st.session_state.data['Project Name']==p, 'ESG_Score'].iloc[0]
                              for p in projects]) +
                    objective_weights['Return'] * 
                    pulp.lpSum([x[p] * (100 - st.session_state.data.loc[st.session_state.data['Project Name']==p, 'ESG_Risk_Score'].iloc[0])
                              for p in projects]) -
                    objective_weights['Risk'] * 
                    pulp.lpSum([x[p] * st.session_state.data.loc[st.session_state.data['Project Name']==p, 'ESG_Risk_Score'].iloc[0]
                              for p in projects])
                )
                
                # Constraints
                # Budget constraint
                prob += pulp.lpSum([x[p] * st.session_state.data.loc[st.session_state.data['Project Name']==p, 'Project Budget (USD)'].iloc[0]
                                  for p in projects]) <= total_budget
                
                # Minimum ESG score constraint
                prob += pulp.lpSum([x[p] * st.session_state.data.loc[st.session_state.data['Project Name']==p, 'ESG_Score'].iloc[0]
                                  for p in projects]) >= min_esg_score
                
                # Risk tolerance constraint
                prob += pulp.lpSum([x[p] * st.session_state.data.loc[st.session_state.data['Project Name']==p, 'ESG_Risk_Score'].iloc[0]
                                  for p in projects]) <= risk_tolerance
                
                # Maximum allocation per project
                for p in projects:
                    prob += x[p] <= max_project_allocation/100
                
                # Diversification constraints
                project_types = st.session_state.data['Project Type'].unique()
                for pt in project_types:
                    type_projects = st.session_state.data[st.session_state.data['Project Type']==pt]['Project Name'].tolist()
                    prob += pulp.lpSum([x[p] for p in type_projects]) <= 1 - diversification_factor
                
                # Solve the optimization problem
                prob.solve()
                
                # Display results
                st.success("Portfolio optimization completed!")
                
                # Create results dataframe
                results = []
                for p in projects:
                    if pulp.value(x[p]) > 0.001:  # Filter out very small allocations
                        project_data = st.session_state.data[st.session_state.data['Project Name']==p].iloc[0]
                        results.append({
                            'Project Name': p,
                            'Project Type': project_data['Project Type'],
                            'Allocation (%)': pulp.value(x[p]) * 100,
                            'Budget Allocation (USD)': pulp.value(x[p]) * project_data['Project Budget (USD)'],
                            'ESG Score': project_data['ESG_Score'],
                            'Risk Score': project_data['ESG_Risk_Score']
                        })
                
                results_df = pd.DataFrame(results)
                
                
                
                # Display portfolio metrics
                # Custom CSS for white text on black background with specific metric styling
                st.markdown("""
                    <style>
                    .metric-container {
                        background-color: #0E1117;
                        padding: 20px;
                        border-radius: 5px;
                        margin: 5px;
                        border: 1px solid #2D2D2D;
                    }
                    .metric-label {
                        color: #FFFFFF;
                        font-size: 14px;
                        font-weight: 500;
                        opacity: 0.8;
                    }
                    .metric-value {
                        color: #FFFFFF;
                        font-size: 24px;
                        font-weight: bold;
                    }
                    .metric-delta {
                        color: #FFFFFF;
                        font-size: 12px;
                        opacity: 0.7;
                    }
                    .metric-text {
                        background-color: #0E1117;
                        color: #FFFFFF;
                        padding: 2px 6px;
                        border-radius: 3px;
                        display: inline-block;
                    }
                    </style>
                """, unsafe_allow_html=True)

                # Display portfolio metrics
                col1, col2, col3 = st.columns(3)

                with col1:
                    st.markdown(f"""
                        <div class="metric-container">
                            <div class="metric-label">Portfolio ESG Score</div>
                            <div class="metric-value">{(results_df['ESG Score'] * results_df['Allocation (%)']/100).sum():.2f}</div>
                            <div class="metric-delta">
                                <span class="metric-text">Target: {min_esg_score}</span>
                            </div>
                        </div>
                    """, unsafe_allow_html=True)

                with col2:
                    st.markdown(f"""
                        <div class="metric-container">
                            <div class="metric-label">Portfolio Risk Score</div>
                            <div class="metric-value">{(results_df['Risk Score'] * results_df['Allocation (%)']/100).sum():.2f}</div>
                            <div class="metric-delta">
                                <span class="metric-text">Tolerance: {risk_tolerance}</span>
                            </div>
                        </div>
                    """, unsafe_allow_html=True)

                with col3:
                    st.markdown(f"""
                        <div class="metric-container">
                            <div class="metric-label">Total Allocation</div>
                            <div class="metric-value">${results_df['Budget Allocation (USD)'].sum():,.2f}</div>
                            <div class="metric-delta">
                                <span class="metric-text">Budget: ${total_budget:,.2f}</span>
                            </div>
                        </div>
                    """, unsafe_allow_html=True)
                
                # Visualization of results
                st.subheader("Optimized Portfolio Allocation")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    # Allocation by Project
                    fig = px.bar(
                        results_df,
                        x='Project Name',
                        y='Allocation (%)',
                        color='Project Type',
                        title="Portfolio Allocation by Project"
                    )
                    st.plotly_chart(fig, use_container_width=True)
                
                with col2:
                    # Allocation by Project Type
                    fig = px.pie(
                        results_df,
                        values='Budget Allocation (USD)',
                        names='Project Type',
                        title="Allocation by Project Type"
                    )
                    st.plotly_chart(fig, use_container_width=True)
                
                # Efficient Frontier
                st.subheader("Portfolio Efficient Frontier")
                
                # Generate efficient frontier points
                frontier_points = []
                for risk_level in range(0, 101, 5):
                    prob.constraints[3] = pulp.lpSum([x[p] * st.session_state.data.loc[st.session_state.data['Project Name']==p, 'ESG_Risk_Score'].iloc[0]
                                                    for p in projects]) <= risk_level
                    prob.solve()
                    if pulp.LpStatus[prob.status] == 'Optimal':
                        esg_score = sum(pulp.value(x[p]) * st.session_state.data.loc[st.session_state.data['Project Name']==p, 'ESG_Score'].iloc[0]
                                      for p in projects)
                        frontier_points.append({
                            'Risk Level': risk_level,
                            'ESG Score': esg_score
                        })
                
                frontier_df = pd.DataFrame(frontier_points)
                
                fig = px.line(
                    frontier_df,
                    x='Risk Level',
                    y='ESG Score',
                    title="Efficient Frontier: ESG Score vs Risk"
                )
                fig.add_scatter(
                    x=[results_df['Risk Score'].mean()],
                    y=[results_df['ESG Score'].mean()],
                    mode='markers',
                    marker=dict(size=15, color='red'),
                    name='Selected Portfolio'
                )
                st.plotly_chart(fig, use_container_width=True)
                
                # Detailed results table
                st.subheader("Detailed Allocation Results")
                st.dataframe(results_df)
                
                # Export results
                csv = results_df.to_csv(index=False)
                b64 = base64.b64encode(csv.encode()).decode()
                href = f'<a href="data:file/csv;base64,{b64}" download="optimized_portfolio.csv">Download Optimization Results</a>'
                st.markdown(href, unsafe_allow_html=True)
                
            except Exception as e:
                st.error(f"Optimization error: {str(e)}")

class DetailedESGAnalyzer:
    def __init__(self):
        self.groq_client = Groq(api_key=GROQ_API_KEY)
        self.esg_categories = {
            'environmental': {
                'carbon_emissions': [
                    'carbon emissions', 'greenhouse gas', 'ghg', 'carbon footprint',
                    'emission reduction', 'carbon neutral', 'net zero'
                ],
                'climate_change': [
                    'climate change', 'global warming', 'climate risk',
                    'climate vulnerability', 'climate adaptation'
                ],
                'environmental_impact': [
                    'environmental impact', 'environmental financing',
                    'green financing', 'sustainable finance', 'green bonds'
                ],
                'water_stress': [
                    'water stress', 'water scarcity', 'water management',
                    'water consumption', 'water usage', 'water conservation'
                ],
                'electronic_waste': [
                    'electronic waste', 'e-waste', 'electronics recycling',
                    'electronic disposal', 'technology waste'
                ],
                'packaging_waste': [
                    'packaging material', 'packaging waste', 'sustainable packaging',
                    'waste reduction', 'recycling initiatives'
                ]
            },
            'social': {
                'health_safety': [
                    'health and safety', 'workplace safety', 'occupational health',
                    'safety protocols', 'safety measures'
                ],
                'human_capital': [
                    'human capital', 'employee development', 'training',
                    'skill development', 'career growth', 'talent management'
                ],
                'controversial_sourcing': [
                    'controversial sourcing', 'supply chain ethics',
                    'responsible sourcing', 'ethical sourcing', 'supplier compliance'
                ],
                'healthcare_access': [
                    'healthcare access', 'medical access', 'healthcare availability',
                    'medical care', 'health services'
                ]
            },
            'governance': {
                'board_diversity': [
                    'board diversity', 'director diversity', 'board composition',
                    'diverse leadership', 'board representation'
                ],
                'pay_diversity': [
                    'pay diversity', 'wage gap', 'salary equality',
                    'compensation equity', 'equal pay'
                ],
                'ownership_control': [
                    'ownership structure', 'control rights', 'voting rights',
                    'shareholder rights', 'corporate control'
                ],
                'business_ethics': [
                    'business ethics', 'corporate ethics', 'ethical practices',
                    'code of conduct', 'compliance'
                ],
                'tax_transparency': [
                    'tax transparency', 'tax reporting', 'tax disclosure',
                    'tax compliance', 'tax policy'
                ]
            }
        }

    def generate_file_hash(self, file_content: bytes) -> str:
        """Generate a unique hash for the file content"""
        return hashlib.md5(file_content).hexdigest()

    def get_json_path(self, file_hash: str) -> str:
        """Get the path for the JSON file based on the hash"""
        cache_dir = "cache"
        if not os.path.exists(cache_dir):
            os.makedirs(cache_dir)
        return os.path.join(cache_dir, f"{file_hash}_ocr.json")

    def pdf_to_images(self, pdf_path: str) -> List:
        return convert_from_path(pdf_path)

    def perform_ocr(self, images: List) -> str:
        text = ""
        for image in images:
            text += pytesseract.image_to_string(image)
        return text

    def save_to_json(self, text: str, output_path: str) -> None:
        pages_dict = {
            "full_text": text,
            "pages": [{"page_num": i, "content": page} 
                     for i, page in enumerate(text.split('\n\n'), 1)]
        }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(pages_dict, f, ensure_ascii=False, indent=4)

    def find_category_content(self, text: str, category_keywords: List[str]) -> List[str]:
        paragraphs = text.split('\n\n')
        relevant_paragraphs = []
        
        for paragraph in paragraphs:
            if any(keyword.lower() in paragraph.lower() for keyword in category_keywords):
                relevant_paragraphs.append(paragraph.strip())
        
        return relevant_paragraphs

    def analyze_esg_categories(self, json_path: str) -> Dict:
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        text = data['full_text']
        analysis_results = {
            'environmental': {},
            'social': {},
            'governance': {}
        }
        
        for main_category, subcategories in self.esg_categories.items():
            for subcategory, keywords in subcategories.items():
                relevant_content = self.find_category_content(text, keywords)
                if relevant_content:
                    summary = self.get_category_summary(relevant_content, subcategory)
                    analysis_results[main_category][subcategory] = {
                        'content': relevant_content,
                        'summary': summary
                    }
        
        return analysis_results

    def get_category_summary(self, content: List[str], category: str) -> str:
        if not content:
            return f"No content found related to {category}."
        
        combined_text = "\n\n".join(content)
        prompt = f"""Please analyze and summarize the following content related to {category}:
        {combined_text}
        Provide a concise summary that includes:
        1. Key initiatives and practices
        2. Notable metrics or targets (if any)
        3. Areas of focus or improvement
        """
        
        completion = self.groq_client.chat.completions.create(
            model="mixtral-8x7b-32768",
            messages=[
                {"role": "system", "content": f"You are an expert in analyzing {category} aspects of ESG reporting."},
                {"role": "user", "content": prompt}
            ]
        )
        
        return completion.choices[0].message.content

def document_analysis_tab():
    st.header("ESG Document Analysis")
    
    uploaded_file = st.file_uploader("Upload ESG Report (PDF)", type="pdf", key="doc_analysis")

    if uploaded_file is not None:
        try:
            analyzer = DetailedESGAnalyzer()
            file_content = uploaded_file.getvalue()
            file_hash = analyzer.generate_file_hash(file_content)
            json_path = analyzer.get_json_path(file_hash)

            # Check if JSON file already exists
            if os.path.exists(json_path):
                st.info("Using existing analysis from cache.")
            else:
                with st.spinner('Processing PDF...'):
                    with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
                        tmp_file.write(file_content)
                        pdf_path = tmp_file.name

                    images = analyzer.pdf_to_images(pdf_path)
                    text = analyzer.perform_ocr(images)
                    analyzer.save_to_json(text, json_path)
                    os.unlink(pdf_path)

            results = analyzer.analyze_esg_categories(json_path)

            env_tab, social_tab, gov_tab = st.tabs(["Environmental", "Social", "Governance"])

            with env_tab:
                for subcategory, data in results['environmental'].items():
                    with st.expander(f"{subcategory.replace('_', ' ').title()}"):
                        st.markdown("### Summary")
                        st.write(data['summary'])
                        st.markdown("### Content")
                        for content in data['content']:
                            st.markdown(f"> {content}")

            with social_tab:
                for subcategory, data in results['social'].items():
                    with st.expander(f"{subcategory.replace('_', ' ').title()}"):
                        st.markdown("### Summary")
                        st.write(data['summary'])
                        st.markdown("### Content")
                        for content in data['content']:
                            st.markdown(f"> {content}")

            with gov_tab:
                for subcategory, data in results['governance'].items():
                    with st.expander(f"{subcategory.replace('_', ' ').title()}"):
                        st.markdown("### Summary")
                        st.write(data['summary'])
                        st.markdown("### Content")
                        for content in data['content']:
                            st.markdown(f"> {content}")

            if st.button("Export Analysis"):
                st.download_button(
                    "Download JSON",
                    data=json.dumps(results, indent=4),
                    file_name="esg_analysis.json",
                    mime="application/json"
                )

        except Exception as e:
            st.error(f"Error: {str(e)}")

def main():
    st.title("Sustain : Empowering Sustainable Decisions Through ESG Analytics")
    
    # Custom CSS for better styling
    st.markdown("""
        <style>
        .main {
            padding: 20px;
        }
        .stMetric {
            background-color: #f0f2f6;
            padding: 10px;
            border-radius: 5px;
        }
        .stAlert {
            padding: 10px;
            margin: 10px 0;
        }
        .css-1d391kg {
            padding-top: 3rem;
        }
        .sidebar .sidebar-content {
            background-color: #f0f2f6;
        }
        .stTabs [data-baseweb="tab-list"] {
            gap: 24px;
        }
        .stTabs [data-baseweb="tab"] {
            height: 50px;
            white-space: pre-wrap;
            border-radius: 4px;
            padding: 10px 20px;
            font-weight: 500;
        }
        .stTabs [aria-selected="true"] {
            background-color: transparent;
            color: inherit;
        }
        </style>
    """, unsafe_allow_html=True)
    
    # Sidebar
    with st.sidebar:
        # Logo and Title Container
        st.image(r"logo.jpg", width=300)  # Update path to your logo
        st.title("Sustain")
        
        st.markdown("<p style='color: #666; margin-top: -15px; font-style: italic;'>Empowering Sustainable Decisions Through ESG Analytics</p>", unsafe_allow_html=True)
        st.markdown("---")
        st.markdown("""
        ## About
        This tool helps analyze and optimize projects based on ESG criteria:
        - Environmental Impact
        - Social Responsibility
        - Governance Standards
        
        ### Features
        - ESG Scoring
        - Project Analysis
        - Portfolio Analytics
        - Optimization Engine
        - Document Analysis
        """)
    
    # Create tabs with icons and better styling
    tabs = st.tabs([
        "📤 Data Upload",
        "📊 Project Analysis",
        "📈 Analytics Dashboard",
        "🎯 Portfolio Optimization",
        "📄 Document Analysis"
    ])
    
    with tabs[0]:
        data_upload_tab()
    
    with tabs[1]:
        project_analysis_tab()
    
    with tabs[2]:
        analytics_dashboard_tab()
    
    with tabs[3]:
        optimization_tab()
    
    with tabs[4]:
        document_analysis_tab()

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        st.error(f"An error occurred: {str(e)}")
        if st.button("Reset Application"):
            st.session_state.clear()
            st.experimental_rerun()
