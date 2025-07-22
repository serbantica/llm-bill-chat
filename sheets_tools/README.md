# 🎨 Google Sheets Multi-Sheet Formatting Guide

## Quick Setup (5 minutes)

### Step 1: Get Your Google Sheets Ready
1. Open your Google Sheet
2. Copy the **Spreadsheet ID** from the URL:
   ```
   https://docs.google.com/spreadsheets/d/[YOUR_SPREADSHEET_ID]/edit
   ```

### Step 2: Setup API Access
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project (or use existing)
3. Enable these APIs:
   - Google Sheets API
   - Google Drive API
4. Create Service Account:
   - Go to IAM & Admin → Service Accounts
   - Click "Create Service Account"
   - Download the JSON credentials file
   - Save it as `google_sheets_credentials.json` in this folder

### Step 3: Share Your Sheet
1. In your Google Sheet, click "Share"
2. Add the service account email (from the JSON file)
3. Give it "Editor" permissions

### Step 4: Install Dependencies
```bash
# Run this command:
pip3 install gspread google-auth pandas
```

### Step 5: Configure and Run
1. **Edit `sheets_config.json`:**
   ```json
   {
     "spreadsheet_id": "PUT_YOUR_SHEET_ID_HERE",
     "credentials_file": "google_sheets_credentials.json",
     "operations": {
       "copy_format_from_template": true,
       "format_sheets": true
     },
     "settings": {
       "template_sheet_name": "Template",
       "target_sheets": ["Sheet1", "Sheet2", "Sheet3"]
     }
   }
   ```

2. **Run the formatter:**
   ```bash
   python3 format_sheets.py
   ```

## What This Will Do:

✅ **Copy column structure** from your template sheet to all other sheets
✅ **Apply consistent formatting**: headers, colors, fonts
✅ **Auto-detect sheets** if you don't specify template/targets
✅ **Preserve your data** while updating formatting

## 🎯 Two Formatting Options:

### Option A: Template-Based Formatting
- Uses one sheet as a template
- Copies its column structure and formatting to other sheets
- Best for: Consistent formatting across similar sheets

### Option B: Custom Formatting
- Applies specific colors and styles you define
- More control over exact appearance
- Best for: Branded or specific formatting requirements

## 📞 Need Help?

If you prefer not to set up the API, you can:
1. **Download your sheets as CSV/Excel** and I can help format them locally
2. **Share your sheet publicly** (view-only) and describe the formatting you want
3. **Use Google Apps Script** (I can provide the code)

Would you like me to help with any of these approaches?
