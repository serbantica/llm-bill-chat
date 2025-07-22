#!/usr/bin/env python3
"""
Quick Google Sheets Multi-Sheet Editor
=====================================

A simplified script for common multi-sheet operations.
Just update the configuration and run!
"""

import json
import os
from datetime import datetime

def load_config():
    """Load configuration from sheets_config.json"""
    try:
        with open('sheets_config.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print("❌ Configuration file 'sheets_config.json' not found!")
        print("Please copy and edit the sheets_config.json file.")
        return None

def check_dependencies():
    """Check if required packages are installed"""
    try:
        import gspread
        from google.oauth2.service_account import Credentials
        import pandas as pd
        return True
    except ImportError as e:
        print(f"❌ Missing dependency: {e}")
        print("Run: pip install -r sheets_requirements.txt")
        return False

def quick_multi_sheet_operations():
    """Perform operations on multiple sheets based on configuration"""
    
    # Load configuration
    config = load_config()
    if not config:
        return
    
    # Check dependencies
    if not check_dependencies():
        return
    
    # Import after dependency check
    from google_sheets_automation import GoogleSheetsAutomator
    import pandas as pd
    
    print("🚀 QUICK GOOGLE SHEETS MULTI-SHEET OPERATIONS")
    print("=" * 50)
    
    # Initialize
    credentials_file = config['credentials_file']
    spreadsheet_id = config['spreadsheet_id']
    
    if not os.path.exists(credentials_file):
        print(f"❌ Credentials file '{credentials_file}' not found!")
        print("Please download your Google Service Account credentials and save as '{credentials_file}'")
        return
    
    if spreadsheet_id == "your_google_sheets_id_here":
        print("❌ Please update the spreadsheet_id in sheets_config.json")
        return
    
    try:
        # Connect to Google Sheets
        automator = GoogleSheetsAutomator(credentials_file)
        spreadsheet = automator.open_spreadsheet(spreadsheet_id)
        
        if not spreadsheet:
            print("❌ Failed to open spreadsheet. Check your ID and permissions.")
            return
        
        print(f"📊 Working with: {spreadsheet.title}")
        operations = config['operations']
        settings = config['settings']
        
        # Get all sheets
        all_sheets = automator.list_all_sheets(spreadsheet)
        data_sheets = [name for name in all_sheets if name.lower() not in ['summary', 'validation_report']]
        
        print(f"📋 Found {len(data_sheets)} data sheets to process")
        
        # 1. Consolidate Data
        if operations.get('consolidate_data', False):
            print("\n📊 Consolidating data from multiple sheets...")
            consolidated_data = []
            
            for sheet_name in data_sheets:
                df = automator.read_sheet_data(spreadsheet, sheet_name)
                if not df.empty:
                    df['source_sheet'] = sheet_name
                    df['processed_date'] = datetime.now().strftime('%Y-%m-%d')
                    consolidated_data.append(df)
            
            if consolidated_data:
                combined_df = pd.concat(consolidated_data, ignore_index=True)
                
                # Create/update summary sheet
                try:
                    automator.create_new_sheet(spreadsheet, "Summary")
                except:
                    pass  # Sheet exists
                
                automator.write_sheet_data(spreadsheet, "Summary", combined_df)
                print(f"✅ Consolidated {len(combined_df)} rows into Summary sheet")
        
        # 2. Update Headers
        if operations.get('update_headers', False):
            print("\n🔄 Updating headers across sheets...")
            new_headers = settings.get('new_headers', [])
            
            for sheet_name in data_sheets:
                for i, header in enumerate(new_headers):
                    col_letter = chr(65 + i)  # A, B, C, etc.
                    cell = f"{col_letter}1"
                    try:
                        worksheet = spreadsheet.worksheet(sheet_name)
                        worksheet.update(cell, header)
                    except:
                        pass
                
                # Format headers
                if new_headers:
                    header_format = {
                        'backgroundColor': {'red': 0.9, 'green': 0.9, 'blue': 0.9},
                        'textFormat': {'bold': True}
                    }
                    range_to_format = f"A1:{chr(65 + len(new_headers) - 1)}1"
                    automator.format_cells(spreadsheet, sheet_name, range_to_format, header_format)
            
            print(f"✅ Updated headers in {len(data_sheets)} sheets")
        
        # 3. Add Formulas
        if operations.get('add_formulas', False):
            print("\n🧮 Adding formulas to sheets...")
            
            for sheet_name in data_sheets:
                # Basic formulas (adjust as needed)
                formulas = {
                    'D1': '=SUM(B:B)',
                    'E1': '=AVERAGE(C:C)',
                    'F1': '=COUNT(A:A)',
                }
                
                for cell, formula in formulas.items():
                    try:
                        automator.add_formula(spreadsheet, sheet_name, cell, formula)
                    except:
                        pass
            
            print(f"✅ Added formulas to {len(data_sheets)} sheets")
        
        # 4. Validate Data
        if operations.get('validate_data', False):
            print("\n✅ Validating data across sheets...")
            validation_results = []
            
            for sheet_name in data_sheets:
                df = automator.read_sheet_data(spreadsheet, sheet_name)
                if not df.empty:
                    validation = {
                        'sheet_name': sheet_name,
                        'total_rows': len(df),
                        'empty_cells': df.isnull().sum().sum(),
                        'duplicate_rows': df.duplicated().sum(),
                        'validation_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    }
                    validation_results.append(validation)
            
            if validation_results:
                validation_df = pd.DataFrame(validation_results)
                try:
                    automator.create_new_sheet(spreadsheet, "Validation_Report")
                except:
                    pass
                
                automator.write_sheet_data(spreadsheet, "Validation_Report", validation_df)
                print(f"✅ Created validation report for {len(validation_results)} sheets")
        
        # 5. Export to CSV
        if operations.get('export_csv', False):
            print("\n📤 Exporting sheets to CSV...")
            export_dir = settings.get('export_directory', './sheet_exports')
            automator.export_sheets_to_csv(spreadsheet, export_dir)
            print(f"✅ Exported sheets to {export_dir}")
        
        print("\n🎉 ALL OPERATIONS COMPLETED SUCCESSFULLY!")
        print(f"📊 Processed {len(data_sheets)} sheets in '{spreadsheet.title}'")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        print("Check your credentials and spreadsheet permissions.")

if __name__ == "__main__":
    quick_multi_sheet_operations()
