# Bulk Declaration Automation Tool

This project automates the process of creating and downloading official declarations in bulk from the Greek government's public services portal (gov.gr). It uses a CSV file as input to generate multiple declarations for different recipients, handling web automation, SMS verification, and file downloads.

## Features

- **Bulk Processing**: Creates multiple declarations from a single CSV file.
- **Web Automation**: Uses Selenium to automate browser interactions with the gov.gr portal.
- **SMS Code Extraction**: Automatically reads SMS verification codes from Windows notifications using Tesseract OCR.
- **Status Reporting**: Generates HTML reports to track the status of each declaration.

## Requirements

- **Python 3.x**
- **Tesseract OCR**: Must be installed and configured with support for Greek (`ell`), German (`deu`), and English (`eng`) languages.
- **Windows Operating System**: The SMS notification parsing is designed for a German Windows system, as it identifies the Notification Center by its German name (`Benachrichtigungscenter`).

## Setup Instructions

1.  **Clone the Repository**:
    ```bash
    git clone <repository-url>
    cd <repository-directory>
    ```

2.  **Install Python Dependencies**:
    It is recommended to use a virtual environment.
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
    pip install -r requirements.txt
    ```

3.  **Install Tesseract OCR**:
    - Download and install Tesseract from the [official repository](https://github.com/tesseract-ocr/tesseract).
    - During installation, make sure to select the language packs for **Greek**, **German**, and **English**.
    - After installation, you may need to update the Tesseract command path in `SMSnotificationParser.py` if it's not in the default location (`C:\Program Files\Tesseract-OCR\tesseract.exe`).

    ```python
    # SMSnotificationParser.py
    SMS_DEFAULTS = {
        # ...
        'tesseract_cmd' : r"C:\path\to\your\tesseract.exe"
        # ...
    }
    ```

## Usage

The main script for running the automation is `bulkDeclare.py`. It requires several command-line arguments to function correctly.

### CSV File Structure

The input CSV file must be structured as follows:
- The **header row** contains the names of the recipients for the declaration.
- Each subsequent row contains the **text of the declaration** for the corresponding recipient in that column.
- An optional column named `folder` can be included. If present, the downloaded PDF for that row will be saved in a subdirectory named after the value in the `folder` column.

**Example `declarations.csv`:**

```csv
Recipient A;Recipient B;folder
"Text for Recipient A, first set";"Text for Recipient B, first set";declarations_01
"Text for Recipient A, second set";"Text for Recipient B, second set";declarations_02
```
**Note:** The default CSV separator is a semicolon (`;`). You can change this with the `--csv-sep` argument.

### Command-Line Interface

Here is the basic command to run the script:

```bash
python bulkDeclare.py --user "your_username" --password "your_password" --taxid "your_taxid" --email "your_email" --csv "path/to/your/declarations.csv"
```

### All Arguments

- `--user`: Your Taxisnet username. (Required)
- `--password`: Your Taxisnet password. (Required)
- `--taxid`: Your tax ID number for verification. (Required)
- `--email`: Your email address. (Required)
- `--csv`: Path to the input CSV file. (Required)
- `--download-dir`: The main directory to store downloaded files. (Default: `./downloads`)
- `--url`: The URL for the declaration portal. (Default: `https://dilosi.services.gov.gr/templates/YPDIL/create`)
- `--web-timeout`: Timeout in seconds for web driver waits. (Default: `60`)
- `--sms-timeout`: Timeout in seconds to wait for the SMS notification. (Default: `120`)
- `--tesseract-cmd`: Full path to the `tesseract.exe` binary.
- `--sms-pattern`: The regex pattern to find the code in the SMS text.
- `--csv-sep`: The separator used in the CSV file. (Default: `;`)
- `--notification-center-name`: The name of the Windows Notification Center. (Default: `Benachrichtigungscenter`)
- `--clear-button-label`: The label of the "Clear All" button in notifications. (Default: `Alle löschen`)

## How It Works

1.  **CSV Parsing**: The `bulkDeclare.py` script reads the input CSV file to get the recipient names and declaration texts.
2.  **Web Automation**: For each entry, `gsisDeclaration.py` launches a Selenium-controlled Chrome browser to navigate to the gov.gr portal.
3.  **Authentication**: It logs in using the provided Taxisnet credentials and verifies the user's tax ID.
4.  **Form Filling**: The script fills in the declaration text and recipient information.
5.  **SMS Verification**: When the portal sends an SMS code, `SMSnotificationParser.py` is triggered. It takes a screenshot of the Windows notification area, uses Tesseract OCR to extract the text, and parses the 6-digit code.
6.  **PDF Download**: Once the code is submitted, the script downloads the final declaration as a PDF and saves it to the specified directory.
7.  **Reporting**: HTML reports are generated to show the status and results of the bulk operation.