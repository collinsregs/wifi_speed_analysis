import os
import glob
import logging
from google.cloud import bigquery
from google.oauth2 import service_account

# Configure logging
logging.basicConfig(
    filename='upload_log.txt',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def upload_csv_to_bigquery(csv_directory, processed_directory, credentials_path,
                            project_id, dataset_id, table_id):
    """
    Upload CSV files to BigQuery and move processed files to another directory.
    Logs the process to a log file.

    Parameters:
    - csv_directory: Directory containing CSV files to upload
    - processed_directory: Directory to move processed files to
    - credentials_path: Path to Google Cloud service account credentials JSON
    - project_id: Google Cloud project ID
    - dataset_id: BigQuery dataset ID
    - table_id: BigQuery table ID
    """
    # Set up credentials and client
    try:
        credentials = service_account.Credentials.from_service_account_file(credentials_path)
        client = bigquery.Client(credentials=credentials, project=project_id)
    except Exception as e:
        logging.error(f"Error authenticating with Google Cloud: {e}")
        return

    # Get full table reference
    table_ref = f"{project_id}.{dataset_id}.{table_id}"

    # Create processed directory if it doesn't exist
    if not os.path.exists(processed_directory):
        os.makedirs(processed_directory)


    # Get all CSV files
    csv_files = glob.glob(os.path.join(csv_directory, "*.csv"))


    for csv_file in csv_files:
        file_name = os.path.basename(csv_file)


        # Configure the load job
        job_config = bigquery.LoadJobConfig(
            source_format=bigquery.SourceFormat.CSV,
            skip_leading_rows=1,  # Skip header row
            autodetect=True,  # Auto-detect schema
        )

        try:
            with open(csv_file, "rb") as source_file:
                job = client.load_table_from_file(source_file, table_ref, job_config=job_config)


            job.result()
            processed_file_path = os.path.join(processed_directory, file_name)
            os.rename(csv_file, processed_file_path)

        except Exception as e:
            logging.error(f"Error processing {file_name}: {e}")

if __name__ == "__main__":
    upload_csv_to_bigquery(
        csv_directory="./data",
        processed_directory="./data/processed",
        credentials_path="internet-speeds-analysis-25d14302b8d0.json",
        project_id="internet-speeds-analysis",
        dataset_id="Speed_Test_Data_Work",
        table_id="silver"
    )