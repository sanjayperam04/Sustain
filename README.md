
# Sustain 
**Revolutionizing Sustainable Decision-Making Through Advanced ESG Analytics**



## Introducing Sustain

In an era where sustainability is paramount, **Sustain** emerges as a game-changer. Sustain is an AI-driven ESG (Environmental, Social, and Governance) analytics platform designed to empower organizations with the insights and tools needed to make informed, sustainable decisions.



## Why Sustain?

Sustain bridges the gap between data overload and actionable insights. By leveraging cutting-edge AI and machine learning, we transform complex ESG data into clear, strategic guidance.

- **Tailored Analysis**: Move beyond generic datasets with company and project-specific ESG reporting.
- **Optimization Engine**: Maximize your investments with our advanced optimization tools.
- **Interactive Visualizations**: Understand your data like never before with dynamic, intuitive dashboards.



## Key Features 

### 1. **AI-Powered Data Acquisition**

- **Comprehensive Data Gathering**: Harness the power of AI to collect ESG data from company websites and public sources using the Perplexity API.
- **Seamless Integration**: Upload your project’s ESG metrics effortlessly via CSV, ensuring your data is always up-to-date and relevant.

### 2. **Advanced Data Processing**

- **Standardized Scoring**: Compute ESG scores using the industry-standard MSCI Rating Methodology.
- **Machine Learning Integration**: Enhance analysis accuracy and uncover deeper insights with integrated machine learning algorithms.

### 3. **Deep Dive Project Analysis**

- **Detailed Metrics**: Analyze each project's ESG performance with precision.
- **Interactive Visuals**: Leverage intuitive charts and graphs to visualize ESG component scores and trends.

### 4. **Dynamic Analytics Dashboard**

- **Portfolio Overview**: Get a holistic view of your projects, including total count, average ESG scores, risk levels, and project phases.
- **Customizable Insights**: Filter and customize data views to focus on what's most important to your organization.

### 5. **Powerful Optimization Engine**

- **Set Your Parameters**: Define budgets, ESG targets, risk tolerance, and diversification preferences.
- **Advanced Algorithms**: Utilize linear and mixed-integer programming models with PuLP to optimize your portfolio.
- **Multi-Objective Optimization**: Balance ESG impact, financial returns, and risk according to your strategic goals.



## How Sustain Works 

### **Data Normalization & Scoring**

1. **Normalization**: Standardize metrics using Min-Max scaling for comparability.
2. **Component Scoring**: Calculate individual environmental, social, and governance scores based on weighted factors.
3. **Aggregate ESG Score**: Combine component scores into an overall ESG score (Environmental: 40%, Social: 35%, Governance: 25%).
4. **Adjustments**:
   - **Project Type**: Adjust scores within project categories to account for inherent differences.
   - **Project Phase**: Apply multipliers based on project maturity.
5. **Final Rating**: Assign ratings (e.g., AAA, AA) and categorize risk levels for comprehensive evaluation.



## Unique Advantages 

### **Unmatched Data Acquisition**

Sustain excels where others falter—providing granular, project-specific ESG data rather than generic industry averages. This precision enables more accurate assessments and tailored strategies.

### **Innovative Optimization Engine**

Our optimization engine sets us apart. Users can input specific parameters, and our system leverages advanced algorithms to recommend optimal investment strategies that maximize ESG impact while considering financial returns.



## Benefits & Use Cases 

- **Informed Decision-Making**: Leverage data-driven insights to enhance ESG performance and investment outcomes.
- **Operational Efficiency**: Automate complex calculations, freeing up resources and time.
- **Interactive Exploration**: Utilize our dynamic dashboard for real-time data exploration and swift decision-making.
- **Strategic Investment Planning**: Optimize portfolios to align with sustainability goals and financial objectives.



## Who Should Use Sustain?

- **Financial Institutions**: Optimize ESG investments and meet regulatory requirements.
- **Corporations**: Assess and improve ESG performance across projects and operations.
- **Investors**: Identify opportunities that offer both sustainability and profitability.
- **Consultants & Analysts**: Provide clients with detailed ESG insights and recommendations.



## Technology Stack 

- **Frontend**: Streamlit for sleek, user-friendly interfaces.
- **Data Processing**: Pandas and NumPy for robust data manipulation.
- **Visualization**: Plotly for interactive and insightful charts.
- **Machine Learning**: scikit-learn for advanced predictive analytics.
- **Optimization**: PuLP library for powerful optimization modeling.
- **Document Processing**: PyTesseract and pdf2image for efficient OCR and document analysis.
- **AI/NLP**: Groq API for sophisticated natural language processing capabilities.



## Join Us in Shaping a Sustainable Future 

Sustain is more than just a platform—it's a movement towards responsible and strategic sustainability. We invite forward-thinking organizations to join us in leveraging technology for positive environmental and social impact.



## Get Started Today

Elevate your ESG strategy with Sustain.
- **🌐 Website**: [https://sustain.streamlit.app/](https://sustain.streamlit.app/)


*Empower your organization with the tools to make decisions that matter—for your business, for society, and for the planet.

```bash
# Clone the repository
git clone https://github.com/sukrithpvs/sustain.git

# Navigate to project directory
cd sustain

# Install required packages
pip install -r requirements.txt
```

## Usage 
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


## License 

This project is licensed under the MIT License - see the [LICENSE.md](LICENSE.md) file for details.
