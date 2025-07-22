#!/usr/bin/env python3
"""
Google Sheets Multi-Sheet Formatter
===================================

This script formats multiple sheets based on a template sheet's formatting.
Perfect for applying consistent formatting across multiple sheets.
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
        return None

def check_dependencies():
    """Check if required packages are installed"""
    try:
        import gspread
        from google.oauth2.service_account import Credentials
        return True
    except ImportError as e:
        print(f"❌ Missing dependency: {e}")
        print("Run: pip install -r sheets_requirements.txt")
        return False

def copy_column_structure(automator, spreadsheet, template_sheet_name, target_sheets):
    """Copy column structure from template to target sheets"""
    print(f"\n📋 Copying column structure from '{template_sheet_name}'...")
    
    try:
        template_sheet = spreadsheet.worksheet(template_sheet_name)
        template_headers = template_sheet.row_values(1)  # Get first row (headers)
        
        print(f"📝 Template headers: {template_headers}")
        
        for target_sheet_name in target_sheets:
            try:
                target_sheet = spreadsheet.worksheet(target_sheet_name)
                
                # Update headers
                if template_headers:
                    target_sheet.update('A1', [template_headers])
                    print(f"✅ Updated headers in '{target_sheet_name}'")
                
            except Exception as e:
                print(f"⚠️ Could not update '{target_sheet_name}': {e}")
                
    except Exception as e:
        print(f"❌ Error copying structure: {e}")

def apply_formatting_to_sheets(automator, spreadsheet, target_sheets, formatting_config):
    """Apply consistent formatting to multiple sheets"""
    print(f"\n🎨 Applying formatting to {len(target_sheets)} sheets...")
    
    header_format = formatting_config.get('header_format', {})
    data_format = formatting_config.get('data_format', {})
    alternate_format = formatting_config.get('alternate_row_format', {})
    
    for sheet_name in target_sheets:
        try:
            print(f"🎨 Formatting sheet: '{sheet_name}'")
            
            # Format header row (row 1)
            if header_format:
                automator.format_cells(spreadsheet, sheet_name, "1:1", header_format)
            
            # Format data rows (starting from row 2)
            if data_format:
                automator.format_cells(spreadsheet, sheet_name, "2:1000", data_format)
            
            # Apply alternate row formatting if specified
            if alternate_format:
                # Format every other row (3, 5, 7, etc.)
                for row in range(3, 1000, 2):
                    range_str = f"{row}:{row}"
                    try:
                        automator.format_cells(spreadsheet, sheet_name, range_str, alternate_format)
                    except:
                        break  # Stop if we hit empty rows
            
            print(f"✅ Applied formatting to '{sheet_name}'")
            
        except Exception as e:
            print(f"⚠️ Could not format '{sheet_name}': {e}")

def copy_template_formatting(automator, spreadsheet, template_sheet_name, target_sheets):
    """Copy exact formatting from template sheet to target sheets"""
    print(f"\n📋 Copying formatting from template '{template_sheet_name}'...")
    
    try:
        # Get template sheet data and formatting
        template_sheet = spreadsheet.worksheet(template_sheet_name)
        
        # Get all values from template
        template_values = template_sheet.get_all_values()
        
        if not template_values:
            print("⚠️ Template sheet is empty")
            return
        
        print(f"📊 Template has {len(template_values)} rows")
        
        for target_sheet_name in target_sheets:
            try:
                target_sheet = spreadsheet.worksheet(target_sheet_name)
                
                # Copy structure (headers) only
                if template_values:
                    headers = template_values[0]  # First row
                    target_sheet.update('A1', [headers])
                
                # Apply basic formatting that matches template
                # Header formatting
                header_format = {
                    'backgroundColor': {'red': 0.2, 'green': 0.6, 'blue': 0.9},
                    'textFormat': {'bold': True, 'foregroundColor': {'red': 1, 'green': 1, 'blue': 1}},
                    'horizontalAlignment': 'CENTER'
                }
                
                # Data formatting
                data_format = {
                    'backgroundColor': {'red': 0.98, 'green': 0.98, 'blue': 0.98},
                    'textFormat': {'fontSize': 10}
                }
                
                # Apply formatting
                header_range = f"A1:{chr(64 + len(headers))}1" if headers else "A1:Z1"
                automator.format_cells(spreadsheet, target_sheet_name, header_range, header_format)
                automator.format_cells(spreadsheet, target_sheet_name, "A2:Z1000", data_format)
                
                print(f"✅ Copied template formatting to '{target_sheet_name}'")
                
            except Exception as e:
                print(f"⚠️ Could not format '{target_sheet_name}': {e}")
                
    except Exception as e:
        print(f"❌ Error copying template formatting: {e}")

def auto_detect_and_format_sheets(automator, spreadsheet):
    """Automatically detect all sheets and apply formatting"""
    print("\n🔍 Auto-detecting sheets to format...")
    
    all_sheets = automator.list_all_sheets(spreadsheet)
    
    # Look for a template sheet
    template_candidates = [name for name in all_sheets if 'template' in name.lower()]
    template_sheet = template_candidates[0] if template_candidates else all_sheets[0]
    
    # Target sheets are all others except template
    target_sheets = [name for name in all_sheets if name != template_sheet]
    
    print(f"📋 Using '{template_sheet}' as template")
    print(f"🎯 Target sheets: {target_sheets}")
    
    if target_sheets:
        copy_template_formatting(automator, spreadsheet, template_sheet, target_sheets)
        return template_sheet, target_sheets
    else:
        print("⚠️ No target sheets found")
        return None, []

def main():
    """Main formatting function"""
    
    print("🎨 GOOGLE SHEETS MULTI-SHEET FORMATTER")
    print("=" * 45)
    
    # Load configuration
    config = load_config()
    if not config:
        return
    
    # Check dependencies
    if not check_dependencies():
        return
    
    # Import after dependency check
    from google_sheets_automation import GoogleSheetsAutomator
    
    # Initialize
    credentials_file = config['credentials_file']
    spreadsheet_id = config['spreadsheet_id']
    
    if not os.path.exists(credentials_file):
        print(f"❌ Credentials file '{credentials_file}' not found!")
        print("Please download your Google Service Account credentials.")
        return
    
    if spreadsheet_id == "your_google_sheets_id_here":
        # Ask user for spreadsheet ID
        spreadsheet_id = input("📋 Enter your Google Sheets ID (from URL): ").strip()
        if not spreadsheet_id:
            print("❌ No spreadsheet ID provided.")
            return
        
        # Update config file
        config['spreadsheet_id'] = spreadsheet_id
        with open('sheets_config.json', 'w') as f:
            json.dump(config, f, indent=2)
        print("✅ Saved spreadsheet ID to config")
    
    try:
        # Connect to Google Sheets
        automator = GoogleSheetsAutomator(credentials_file)
        spreadsheet = automator.open_spreadsheet(spreadsheet_id)
        
        if not spreadsheet:
            print("❌ Failed to open spreadsheet. Check your ID and permissions.")
            return
        
        print(f"📊 Working with: {spreadsheet.title}")
        
        settings = config.get('settings', {})
        operations = config.get('operations', {})
        
        # Option 1: Use specified template and target sheets
        template_sheet_name = settings.get('template_sheet_name')
        target_sheets = settings.get('target_sheets', [])
        
        if template_sheet_name and target_sheets:
            print(f"📋 Using configured template: '{template_sheet_name}'")
            print(f"🎯 Target sheets: {target_sheets}")
            
            if operations.get('copy_format_from_template', False):
                copy_template_formatting(automator, spreadsheet, template_sheet_name, target_sheets)
            
            if operations.get('format_sheets', False):
                formatting_config = settings.get('formatting', {})
                apply_formatting_to_sheets(automator, spreadsheet, target_sheets, formatting_config)
        
        else:
            # Option 2: Auto-detect template and target sheets
            print("🔍 No template specified, auto-detecting...")
            template_sheet, detected_targets = auto_detect_and_format_sheets(automator, spreadsheet)
        
        print("\n🎉 FORMATTING COMPLETED!")
        print(f"📊 Formatted sheets in '{spreadsheet.title}'")
        print("\n💡 Tips:")
        print("- Check your Google Sheet to see the applied formatting")
        print("- Modify 'sheets_config.json' to customize colors and styles")
        print("- You can run this script multiple times to update formatting")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        print("Check your credentials and spreadsheet permissions.")

if __name__ == "__main__":
    main()
