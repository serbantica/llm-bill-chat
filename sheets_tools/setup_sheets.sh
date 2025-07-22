#!/bin/bash

# Google Sheets Automation Setup Script
echo "🚀 Setting up Google Sheets Automation Environment"
echo "=================================================="

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3 first."
    exit 1
fi

echo "✅ Python 3 found"

# Install required packages
echo "📦 Installing required packages..."
pip3 install -r sheets_requirements.txt

if [ $? -eq 0 ]; then
    echo "✅ All packages installed successfully!"
else
    echo "❌ Failed to install some packages. Please check your pip installation."
    exit 1
fi

echo ""
echo "🔧 NEXT STEPS:"
echo "1. Go to Google Cloud Console (https://console.cloud.google.com/)"
echo "2. Create a project and enable Google Sheets API + Google Drive API"
echo "3. Create a Service Account and download the JSON credentials"
echo "4. Save the credentials as 'google_sheets_credentials.json'"
echo "5. Share your Google Sheet with the service account email"
echo "6. Run: python3 sheets_examples.py"
echo ""
echo "📚 Documentation: https://gspread.readthedocs.io/"
