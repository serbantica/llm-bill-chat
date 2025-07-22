#!/usr/bin/env python3
"""
Practical Google Sheets Multi-Sheet Examples
===========================================

This script shows practical examples of automating multiple sheet operations.
Common use cases included:
1. Data consolidation across sheets
2. Bulk formatting and updates
3. Report generation
4. Data validation across sheets
"""

from google_sheets_automation import GoogleSheetsAutomator
import pandas as pd
from datetime import datetime
import json

def setup_credentials():
    """
    Setup instructions for Google Sheets API credentials.
    """
    instructions = """
    🔧 SETUP INSTRUCTIONS:
    
    1. Go to Google Cloud Console (https://console.cloud.google.com/)
    2. Create a new project or select existing one
    3. Enable Google Sheets API and Google Drive API
    4. Create a Service Account:
       - Go to IAM & Admin > Service Accounts
       - Click "Create Service Account"
       - Download the JSON credentials file
    5. Share your Google Sheet with the service account email
    6. Update the credentials_file path below
    
    📁 Save your credentials file as 'google_sheets_credentials.json'
    """
    print(instructions)
    return "google_sheets_credentials.json"

def consolidate_data_from_multiple_sheets(automator, spreadsheet):
    """
    Example: Consolidate data from multiple sheets into a summary sheet.
    """
    print("\n📊 CONSOLIDATING DATA FROM MULTIPLE SHEETS")
    print("-" * 50)
    
    # Get all sheet names
    sheet_names = automator.list_all_sheets(spreadsheet)
    
    # Filter out summary sheet if it exists
    data_sheets = [name for name in sheet_names if name.lower() != 'summary']
    
    consolidated_data = []
    
    # Read data from each sheet
    for sheet_name in data_sheets:
        print(f"📖 Reading data from: {sheet_name}")
        df = automator.read_sheet_data(spreadsheet, sheet_name)
        
        if not df.empty:
            # Add source sheet column
            df['source_sheet'] = sheet_name
            df['processed_date'] = datetime.now().strftime('%Y-%m-%d')
            consolidated_data.append(df)
    
    # Combine all data
    if consolidated_data:
        combined_df = pd.concat(consolidated_data, ignore_index=True)
        
        # Create or update summary sheet
        try:
            automator.create_new_sheet(spreadsheet, "Summary")
        except:
            print("📝 Summary sheet already exists, updating...")
        
        # Write consolidated data
        automator.write_sheet_data(spreadsheet, "Summary", combined_df)
        
        # Format the header row
        header_format = {
            'backgroundColor': {'red': 0.2, 'green': 0.6, 'blue': 0.9},
            'textFormat': {'bold': True, 'foregroundColor': {'red': 1, 'green': 1, 'blue': 1}}
        }
        automator.format_cells(spreadsheet, "Summary", "A1:Z1", header_format)
        
        print(f"✅ Consolidated {len(combined_df)} rows from {len(data_sheets)} sheets")
    
    return combined_df if consolidated_data else pd.DataFrame()

def bulk_update_headers(automator, spreadsheet, new_headers):
    """
    Example: Update headers across multiple sheets.
    """
    print("\n🔄 BULK UPDATING HEADERS")
    print("-" * 30)
    
    sheet_names = automator.list_all_sheets(spreadsheet)
    
    for sheet_name in sheet_names:
        if sheet_name.lower() != 'summary':  # Skip summary sheet
            print(f"📝 Updating headers in: {sheet_name}")
            
            # Update headers
            header_updates = []
            for i, header in enumerate(new_headers):
                col_letter = chr(65 + i)  # A, B, C, etc.
                header_updates.append([header])
            
            # Update each header cell
            for i, header in enumerate(new_headers):
                col_letter = chr(65 + i)
                cell = f"{col_letter}1"
                try:
                    worksheet = spreadsheet.worksheet(sheet_name)
                    worksheet.update(cell, header)
                except Exception as e:
                    print(f"⚠️ Couldn't update {cell} in {sheet_name}: {e}")
            
            # Format headers
            header_format = {
                'backgroundColor': {'red': 0.9, 'green': 0.9, 'blue': 0.9},
                'textFormat': {'bold': True}
            }
            range_to_format = f"A1:{chr(65 + len(new_headers) - 1)}1"
            automator.format_cells(spreadsheet, sheet_name, range_to_format, header_format)

def add_formulas_to_multiple_sheets(automator, spreadsheet):
    """
    Example: Add calculation formulas to multiple sheets.
    """
    print("\n🧮 ADDING FORMULAS TO MULTIPLE SHEETS")
    print("-" * 40)
    
    sheet_names = automator.list_all_sheets(spreadsheet)
    
    for sheet_name in sheet_names:
        if sheet_name.lower() != 'summary':
            print(f"📐 Adding formulas to: {sheet_name}")
            
            # Example formulas (adjust based on your data structure)
            formulas = {
                'D1': '=SUM(B:B)',  # Sum of column B
                'E1': '=AVERAGE(C:C)',  # Average of column C
                'F1': '=COUNT(A:A)',  # Count of non-empty cells in column A
            }
            
            for cell, formula in formulas.items():
                automator.add_formula(spreadsheet, sheet_name, cell, formula)

def validate_data_across_sheets(automator, spreadsheet):
    """
    Example: Validate data consistency across sheets.
    """
    print("\n✅ VALIDATING DATA ACROSS SHEETS")
    print("-" * 35)
    
    sheet_names = automator.list_all_sheets(spreadsheet)
    validation_results = []
    
    for sheet_name in sheet_names:
        if sheet_name.lower() != 'summary':
            print(f"🔍 Validating: {sheet_name}")
            df = automator.read_sheet_data(spreadsheet, sheet_name)
            
            if not df.empty:
                # Example validations
                validation = {
                    'sheet_name': sheet_name,
                    'total_rows': len(df),
                    'empty_cells': df.isnull().sum().sum(),
                    'duplicate_rows': df.duplicated().sum(),
                    'validation_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }
                
                # Check for required columns (adjust as needed)
                required_columns = ['Name', 'Email', 'Amount']  # Example columns
                missing_columns = [col for col in required_columns if col not in df.columns]
                validation['missing_columns'] = ', '.join(missing_columns) if missing_columns else 'None'
                
                validation_results.append(validation)
    
    # Create validation report
    if validation_results:
        validation_df = pd.DataFrame(validation_results)
        
        try:
            automator.create_new_sheet(spreadsheet, "Validation_Report")
        except:
            print("📝 Validation report sheet already exists, updating...")
        
        automator.write_sheet_data(spreadsheet, "Validation_Report", validation_df)
        print(f"✅ Created validation report with {len(validation_results)} sheet validations")
    
    return validation_results

def export_filtered_data(automator, spreadsheet, filter_criteria):
    """
    Example: Export filtered data from multiple sheets.
    """
    print("\n📤 EXPORTING FILTERED DATA")
    print("-" * 30)
    
    sheet_names = automator.list_all_sheets(spreadsheet)
    
    for sheet_name in sheet_names:
        if sheet_name.lower() not in ['summary', 'validation_report']:
            df = automator.read_sheet_data(spreadsheet, sheet_name)
            
            if not df.empty:
                # Apply filter (example: filter by amount > 1000)
                if 'Amount' in df.columns:
                    filtered_df = df[df['Amount'] > filter_criteria.get('min_amount', 0)]
                    
                    if not filtered_df.empty:
                        # Create new sheet with filtered data
                        filtered_sheet_name = f"{sheet_name}_Filtered"
                        try:
                            automator.create_new_sheet(spreadsheet, filtered_sheet_name)
                            automator.write_sheet_data(spreadsheet, filtered_sheet_name, filtered_df)
                            print(f"✅ Created filtered sheet: {filtered_sheet_name}")
                        except Exception as e:
                            print(f"⚠️ Couldn't create filtered sheet: {e}")

def main():
    """Main execution function with practical examples."""
    
    print("🚀 GOOGLE SHEETS MULTI-SHEET AUTOMATION")
    print("=" * 50)
    
    # Setup credentials
    credentials_file = setup_credentials()
    
    # Your Google Sheets ID (get from the URL)
    spreadsheet_id = input("\n📋 Enter your Google Sheets ID: ").strip()
    
    if not spreadsheet_id:
        print("❌ No spreadsheet ID provided. Exiting.")
        return
    
    try:
        # Initialize automator
        automator = GoogleSheetsAutomator(credentials_file)
        
        # Open spreadsheet
        spreadsheet = automator.open_spreadsheet(spreadsheet_id)
        
        if not spreadsheet:
            print("❌ Failed to open spreadsheet. Check your ID and permissions.")
            return
        
        print(f"\n📊 Working with spreadsheet: {spreadsheet.title}")
        
        # Example operations (uncomment the ones you need)
        
        # 1. Consolidate data from multiple sheets
        consolidated_data = consolidate_data_from_multiple_sheets(automator, spreadsheet)
        
        # 2. Update headers across sheets
        new_headers = ['Name', 'Email', 'Amount', 'Date', 'Status']
        bulk_update_headers(automator, spreadsheet, new_headers)
        
        # 3. Add formulas to sheets
        add_formulas_to_multiple_sheets(automator, spreadsheet)
        
        # 4. Validate data across sheets
        validation_results = validate_data_across_sheets(automator, spreadsheet)
        
        # 5. Export filtered data
        filter_criteria = {'min_amount': 1000}
        export_filtered_data(automator, spreadsheet, filter_criteria)
        
        # 6. Export all sheets to CSV
        automator.export_sheets_to_csv(spreadsheet, "./sheet_exports")
        
        print("\n🎉 AUTOMATION COMPLETED SUCCESSFULLY!")
        print("Check your Google Sheet for the updates.")
        
    except Exception as e:
        print(f"❌ Error during automation: {e}")
        print("Make sure your credentials file exists and you have access to the sheet.")

if __name__ == "__main__":
    main()
