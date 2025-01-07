
# Sustain: Empowering Sustainable Decisions Through ESG Analytics 🌱

## Overview

Sustain is an AI-powered platform designed to help financial institutions and organizations evaluate, prioritize, and optimize their ESG (Environmental, Social, and Governance) investments. The platform combines advanced analytics, machine learning, and optimization techniques to maximize sustainability impact while maintaining financial viability.

## Key Features 🚀

### 1. ESG Project Scoring & Analysis
- Comprehensive ESG scoring framework
- Real-time project evaluation
- Multi-dimensional sustainability metrics
- Risk assessment and categorization

### 2. Interactive Analytics Dashboard
- Portfolio-level performance tracking
- Project comparison visualization
- Risk distribution analysis
- Customizable filters and views

### 3. Portfolio Optimization Engine
- AI-driven investment optimization
- Multi-objective optimization considering:
  - ESG impact
  - Risk tolerance
  - Budget constraints
  - Portfolio diversification
- Efficient frontier analysis

### 4. Document Analysis
- Automated ESG report processing
- NLP-powered insight extraction
- Category-wise analysis for:
  - Environmental factors
  - Social impact
  - Governance practices

## Technology Stack 💻

- **Frontend**: Streamlit
- **Data Processing**: Pandas, NumPy
- **Visualization**: Plotly
- **Machine Learning**: scikit-learn
- **Optimization**: PuLP
- **Document Processing**: PyTesseract, pdf2image
- **AI/NLP**: Groq API

## Installation 🔧

```bash
# Clone the repository
git clone https://github.com/sukrithpvs/sustain.git

# Navigate to project directory
cd sustain

# Install required packages
pip install -r requirements.txt
```

## Usage 📋

1. Start the application:
```bash
streamlit run app.py
```

2. Upload your project data in CSV format with the following required columns:
   - Project Name
   - Project Type
   - Project Phase
   - Project Budget (USD)
   - ESG metrics (carbon emissions, energy efficiency, etc.)

3. Navigate through the different tabs to:
   - Analyze individual projects
   - View portfolio analytics
   - Run optimization scenarios
   - Process ESG documents

## Data Requirements 📊

The platform expects CSV files with the following structure:
```
Project Name, Project Type, Project Phase, Project Budget (USD),
Carbon Emissions (tons CO2/year), Energy Efficiency (%),
Water Usage (liters/year), etc.
```


## License 📄

This project is licensed under the MIT License - see the [LICENSE.md](LICENSE.md) file for details.
