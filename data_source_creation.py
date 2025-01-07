import requests
import pandas as pd
from bs4 import BeautifulSoup

# Perplexity API base URL
PERPLEXITY_API_URL = "https://api.perplexity.ai"  # Replace with the actual endpoint
PERPLEXITY_API_KEY = "your_perplexity_api_key"

# Function to query Perplexity API
def search_perplexity(query):
    headers = {
        "Authorization": f"Bearer {PERPLEXITY_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {"query": query}
    response = requests.post(f"{PERPLEXITY_API_URL}/search", json=payload, headers=headers)
    if response.status_code == 200:
        return response.json()  # Assuming API returns JSON results
    else:
        print(f"Error: {response.status_code} - {response.text}")
        return None

# Extract relevant ESG data from search results
def extract_esg_data_from_search(results):
    data = []
    for result in results.get("results", []):
        try:
            # Visit each result URL and scrape for data
            response = requests.get(result["url"])
            soup = BeautifulSoup(response.text, "html.parser")
            
            # Extract data fields (adjust based on webpage structure)
            company_name = soup.find("h1", class_="company-name").text.strip()  # Replace with actual HTML class/id
            industry = soup.find("div", class_="industry").text.strip()  # Replace with actual HTML class/id
            carbon_emissions = soup.find("span", class_="carbon-emissions").text.strip()  # Replace with actual HTML class/id
            energy_efficiency = soup.find("span", class_="energy-efficiency").text.strip()  # Replace with actual HTML class/id
            waste_management = soup.find("span", class_="waste-management").text.strip()  # Replace with actual HTML class/id
            water_usage = soup.find("span", class_="water-usage").text.strip()  # Replace with actual HTML class/id
            pollution_score = soup.find("span", class_="pollution-score").text.strip()  # Replace with actual HTML class/id
            employee_turnover_rate = soup.find("span", class_="turnover-rate").text.strip()  # Replace with actual HTML class/id
            community_investment = soup.find("span", class_="community-investment").text.strip()  # Replace with actual HTML class/id
            sustainable_product_dev = soup.find("span", class_="sustainable-dev").text.strip()  # Replace with actual HTML class/id
            target_classification = "High Risk"  # Example placeholder; can be inferred dynamically
            
            # Append extracted data to the list
            data.append({
                "Company Name": company_name,
                "Industry": industry,
                "Carbon Emissions (tons CO2/year)": carbon_emissions,
                "Energy Efficiency (%)": energy_efficiency,
                "Waste Management (%)": waste_management,
                "Water Usage (liters/year)": water_usage,
                "Pollution Impact Score (0-100)": pollution_score,
                "Employee Turnover Rate (%)": employee_turnover_rate,
                "Community Investment (USD)": community_investment,
                "Sustainable Product Development (%)": sustainable_product_dev,
                "Target Classification": target_classification
            })
        except Exception as e:
            print(f"Error extracting data: {e}")
    return data

# Build dataset for a list of companies
def build_esg_dataset(company_names):
    dataset = []
    for company in company_names:
        print(f"Fetching data for {company}...")
        query = f"ESG report {company}"
        search_results = search_perplexity(query)
        if search_results:
            data = extract_esg_data_from_search(search_results)
            dataset.extend(data)
    return pd.DataFrame(dataset)

# List of companies to search for
companies = ["Apple", "Microsoft", "Google", "Tesla", "Amazon"]  # Add more companies as needed

# Generate the ESG dataset
esg_dataset = build_esg_dataset(companies)

# Save the dataset to an Excel file
output_file = "ESG_Web_Searched_Data.xlsx"
esg_dataset.to_excel(output_file, index=False)
print(f"Dataset saved as {output_file}")
