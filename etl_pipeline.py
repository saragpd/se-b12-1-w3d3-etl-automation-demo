import os
import json
import pandas as pd
from openai import OpenAI
from dotenv import load_dotenv # optional if using .env file

load_dotenv()

# 1. Initialize OpenAI client
# Ensure your OPENAI_API_KEY is set in your environment variables
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

def clean_row_with_openai(dirty_data_string):
    """
    Sends a dirty row of data to OpenAI to be cleaned and formatted.
    """
    prompt = f"""
    You are an expert data cleaning assistant. I will give you a row of student data that contains errors, typos, improper casing, or missing values.
    
    Clean the data and return it strictly as a JSON object with these exact keys:
    - "Student_ID": Keep as-is or fix formatting if broken.
    - "Name": Fix typos, capitalize properly (e.g., "john doe" -> "John Doe").
    - "Email": Convert to strictly lowercase and ensure valid formatting.
    - "Phone": Standardize format if possible, or leave clean string.
    - "Course": Standardize name if there are obvious typos.
    - "Fee_Paid": Ensure it's a clean number or standardized currency representation.
    - "City": Capitalize properly (e.g., "new york" -> "New York").
    - "Enrolled_Date": Standardize to YYYY-MM-DD format if possible.
    - "Email_Valid": Evaluate if the email looks logically valid (True/False).

    Dirty Data: {dirty_data_string}
    """

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini", # Using a fast, cost-effective model for data tasks
            messages=[
                {"role": "system", "content": "You are a precise data cleaning tool. Respond only with valid JSON."},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"} # Forces OpenAI to return valid JSON
        )
        
        # Parse and return the JSON response
        cleaned_json = json.loads(response.choices[0].message.content)
        return cleaned_json
    except Exception as e:
        print(f"Error cleaning data: {e}")
        return None

def run_etl(input_file, output_file):
    # --- STEP 1 & 2: Load and Read the File ---
    print(f"🔄 Loading {input_file}...")
    df = pd.read_csv(input_file)
    
    cleaned_rows = []
    
    # --- STEP 3: OpenAI Clean the Data ---
    print("🧠 Cleaning data with OpenAI (this might take a moment)...")
    for index, row in df.iterrows():
        # Convert the row to a string format OpenAI can easily read
        dirty_string = row.to_dict()
        
        print(f"Processing row {index + 1}/{len(df)}...")
        cleaned_data = clean_row_with_openai(dirty_string)
        
        if cleaned_data:
            cleaned_rows.append(cleaned_data)
        else:
            # Fallback if API fails: keep original data or mark as failed
            cleaned_rows.append(dirty_string)

    # --- STEP 4: Create the Final CSV File ---
    print(f"💾 Saving cleaned data to {output_file}...")
    cleaned_df = pd.DataFrame(cleaned_rows)
    cleaned_df.to_csv(output_file, index=False)
    
    print("✅ ETL Pipeline Completed Successfully!")

if __name__ == "__main__":
    # Replace these with your actual file paths
    INPUT_CSV = "student_enrollment_raw.csv"
    OUTPUT_CSV = "clean_students.csv"
    
    run_etl(INPUT_CSV, OUTPUT_CSV)