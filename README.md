# Fincalls-Earnings_Calls_Analyzer
This project enhances corporate call analysis by employing transcription, transcript summarization, financial data extraction, and interactive data visualization. By integrating these methods, valuable insights can be drawn from the earning calls, which will in turn, help the investors and other stakeholders in decision making.


## Prerequisites

- Python 3.8 or higher
- pip (Python package manager)

## Installation

1. Clone the repository:
git clone https://github.com/yourusername/fincalls-backend.git
cd fincalls-backend


2. Create and activate a virtual environment:

On Linux/macOS:

python3 -m venv venv
source venv/bin/activate


On Windows (PowerShell):

python -m venv venv
.\venv\Scripts\activate


3. Install the Python dependencies:

pip install -r requirements.txt


---

## Configuration

Create a `.env` file in the root directory with the following environment variables:

FLASK_APP=app.py
FLASK_ENV=development
MONGO_URI=your_mongodb_connection_string
SECRET_KEY=your_secret_key


Make sure `.env` is listed in `.gitignore` to avoid exposing sensitive information.

---

## Running the Application

To run the Flask application locally: flask run

Alternatively, run directly using Python: python app.py
