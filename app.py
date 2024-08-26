from firecrawl import FirecrawlApp
from dotenv import load_dotenv
import pandas as pd
import numpy as np
import json
from datetime import datetime
from langchain_groq import ChatGroq
import streamlit as st
import os

def scrape_data(url):
    load_dotenv()
    # Initialize the FirecrawlApp with your API key
    app = FirecrawlApp(api_key=os.getenv('Firecrawl_API_KEY'))
    
    # Scrape a single URL
    scraped_data = app.scrape_url(url, {'pageOptions': {'onlyMainContent': True}})
    
    # Check if 'markdown' key exists in the scraped data
    if 'markdown' in scraped_data:
        return scraped_data['markdown']
    else:
        raise KeyError("The key 'markdown' does not exist in the scraped data.")
    
def save_raw_data(raw_data, timestamp, output_folder='output'):
    # Ensure the output folder exists
    os.makedirs(output_folder, exist_ok=True)
    
    # Save the raw markdown data with timestamp in filename
    raw_output_path = os.path.join(output_folder, f'rawData_{timestamp}.md')
    with open(raw_output_path, 'w', encoding='utf-8') as f:
        f.write(raw_data)
    st.write(f"Raw data saved to {raw_output_path}")

def format_data(data, fields=None):
    load_dotenv()
    # Instantiate the Groq API client
    client = ChatGroq(api_key=os.getenv('Groq_AI'))

    # Assign default fields if not provided
    if fields is None:
        fields = ["Title", "Authors", "Abstract", "Publication Date", "DOI", "Journal", "Keywords", "Research URL"]

    # Create a query for extracting the desired fields
    query = {
        "prompt": f"Extract the following information from the provided text:\nPage content:\n\n{data}\n\nInformation to extract: {fields}",
        "fields": fields
    }

    # Send the request to Groq API
    response = client.extract_information(query)

    # Check if the response contains the expected data
    if response and 'result' in response:
        formatted_data = response['result']
        st.write(f"Formatted data received from API: {formatted_data}")

        try:
            parsed_json = json.loads(formatted_data)
        except json.JSONDecodeError as e:
            st.error(f"JSON decoding error: {e}")
            st.write(f"Formatted data that caused the error: {formatted_data}")
            raise ValueError("The formatted data could not be decoded into JSON.")
        
        return parsed_json
    else:
        raise ValueError("The Groq API response did not contain the expected data.")
    

def save_formatted_data(formatted_data, timestamp, output_folder='output'):
    # Ensure the output folder exists
    os.makedirs(output_folder, exist_ok=True)
    
    # Save the formatted data as JSON with timestamp in filename
    output_path = os.path.join(output_folder, f'sorted_data_{timestamp}.json')

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(formatted_data, f, indent=4)
    st.write(f"Formatted data saved to {output_path}")

    # Check if data is a dictionary and contains exactly one key
    if isinstance(formatted_data, dict) and len(formatted_data) == 1:
        key = next(iter(formatted_data))  # Get the single key
        formatted_data = formatted_data[key]

    # Convert the formatted data to a pandas DataFrame
    df = pd.DataFrame(formatted_data)

    # Save the DataFrame to an Excel file
    excel_output_path = os.path.join(output_folder, f'sorted_data_{timestamp}.xlsx')
    df.to_excel(excel_output_path, index=False)
    st.write(f"Formatted data saved to Excel at {excel_output_path}")

# Streamlit UI components
st.title("Research Paper Data Extractor")

# Input URL
url = st.text_input("Enter the URL of the research paper:", "https://www.researchgate.net/publication/382451475_A_journey_from_AI_to_Gen-AI")

if st.button("Scrape and Process Data"):
    try:
        # Generate timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Scrape data
        raw_data = scrape_data(url)
        st.write("Raw data scraped successfully.")
        
        # Save raw data
        save_raw_data(raw_data, timestamp)
        
        # Format data
        formatted_data = format_data(raw_data)
        
        # Save formatted data
        save_formatted_data(formatted_data, timestamp)
        st.success("Data processing completed successfully.")
    except Exception as e:
        st.error(f"An error occurred: {e}")
