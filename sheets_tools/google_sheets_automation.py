#!/usr/bin/env python3
"""
Google Sheets Multi-Sheet Automation Script
===========================================

This script helps automate editing multiple sheets in a Google Sheets file.
Features:
- Read/write data from multiple sheets
- Batch operations across sheets
- Format cells, add formulas, update values
- Create new sheets, delete sheets
- Export data to different formats

Requirements:
- Google Sheets API credentials
- gspread library for easy Google Sheets access
"""

import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
import json
from typing import List, Dict, Any, Optional
import time
from datetime import datetime

class GoogleSheetsAutomator:
    """Automate operations across multiple Google Sheets."""
    
    def __init__(self, credentials_file: str):
        """
        Initialize with Google Service Account credentials.
        
        Args:
            credentials_file: Path to the JSON credentials file
        """
        self.scope = [
            'https://www.googleapis.com/auth/spreadsheets',
            'https://www.googleapis.com/auth/drive'
        ]
        
        try:
            self.creds = Credentials.from_service_account_file(
                credentials_file, scopes=self.scope
            )
            self.client = gspread.authorize(self.creds)
            print("✅ Successfully connected to Google Sheets API")
        except Exception as e:
            print(f"❌ Failed to initialize Google Sheets client: {e}")
            raise
    
    def open_spreadsheet(self, spreadsheet_id: str):
        """
        Open a Google Spreadsheet by ID.
        
        Args:
            spreadsheet_id: The Google Sheets file ID
            
        Returns:
            gspread.Spreadsheet object
        """
        try:
            spreadsheet = self.client.open_by_key(spreadsheet_id)
            print(f"✅ Opened spreadsheet: {spreadsheet.title}")
            return spreadsheet
        except Exception as e:
            print(f"❌ Failed to open spreadsheet: {e}")
            return None
    
    def list_all_sheets(self, spreadsheet) -> List[str]:
        """Get list of all sheet names in the spreadsheet."""
        try:
            sheet_names = [sheet.title for sheet in spreadsheet.worksheets()]
            print(f"📋 Found {len(sheet_names)} sheets: {sheet_names}")
            return sheet_names
        except Exception as e:
            print(f"❌ Failed to list sheets: {e}")
            return []
    
    def read_sheet_data(self, spreadsheet, sheet_name: str) -> pd.DataFrame:
        """
        Read all data from a specific sheet into a DataFrame.
        
        Args:
            spreadsheet: gspread.Spreadsheet object
            sheet_name: Name of the sheet to read
            
        Returns:
            pandas.DataFrame with the sheet data
        """
        try:
            worksheet = spreadsheet.worksheet(sheet_name)
            data = worksheet.get_all_records()
            df = pd.DataFrame(data)
            print(f"✅ Read {len(df)} rows from sheet '{sheet_name}'")
            return df
        except Exception as e:
            print(f"❌ Failed to read sheet '{sheet_name}': {e}")
            return pd.DataFrame()
    
    def write_sheet_data(self, spreadsheet, sheet_name: str, df: pd.DataFrame, 
                        start_cell: str = 'A1', include_headers: bool = True):
        """
        Write DataFrame data to a specific sheet.
        
        Args:
            spreadsheet: gspread.Spreadsheet object
            sheet_name: Name of the sheet to write to
            df: pandas.DataFrame to write
            start_cell: Starting cell (e.g., 'A1')
            include_headers: Whether to include column headers
        """
        try:
            worksheet = spreadsheet.worksheet(sheet_name)
            
            # Clear existing data
            worksheet.clear()
            
            # Prepare data
            if include_headers:
                data = [df.columns.tolist()] + df.values.tolist()
            else:
                data = df.values.tolist()
            
            # Write data
            worksheet.update(start_cell, data)
            print(f"✅ Written {len(df)} rows to sheet '{sheet_name}'")
            
        except Exception as e:
            print(f"❌ Failed to write to sheet '{sheet_name}': {e}")
    
    def batch_update_cells(self, spreadsheet, updates: List[Dict]):
        """
        Perform batch updates across multiple sheets.
        
        Args:
            spreadsheet: gspread.Spreadsheet object
            updates: List of update dictionaries with format:
                    [{"sheet": "Sheet1", "range": "A1:B2", "values": [[1,2],[3,4]]}]
        """
        try:
            for update in updates:
                sheet_name = update["sheet"]
                cell_range = update["range"]
                values = update["values"]
                
                worksheet = spreadsheet.worksheet(sheet_name)
                worksheet.update(cell_range, values)
                print(f"✅ Updated {cell_range} in sheet '{sheet_name}'")
                
                # Small delay to avoid rate limiting
                time.sleep(0.1)
                
        except Exception as e:
            print(f"❌ Failed batch update: {e}")
    
    def create_new_sheet(self, spreadsheet, sheet_name: str, rows: int = 1000, cols: int = 26):
        """Create a new sheet in the spreadsheet."""
        try:
            worksheet = spreadsheet.add_worksheet(title=sheet_name, rows=rows, cols=cols)
            print(f"✅ Created new sheet: '{sheet_name}'")
            return worksheet
        except Exception as e:
            print(f"❌ Failed to create sheet '{sheet_name}': {e}")
            return None
    
    def delete_sheet(self, spreadsheet, sheet_name: str):
        """Delete a sheet from the spreadsheet."""
        try:
            worksheet = spreadsheet.worksheet(sheet_name)
            spreadsheet.del_worksheet(worksheet)
            print(f"✅ Deleted sheet: '{sheet_name}'")
        except Exception as e:
            print(f"❌ Failed to delete sheet '{sheet_name}': {e}")
    
    def format_cells(self, spreadsheet, sheet_name: str, cell_range: str, 
                    format_dict: Dict[str, Any]):
        """
        Apply formatting to a range of cells.
        
        Args:
            spreadsheet: gspread.Spreadsheet object
            sheet_name: Name of the sheet
            cell_range: Range to format (e.g., 'A1:B10')
            format_dict: Formatting options (e.g., {'backgroundColor': {'red': 1}})
        """
        try:
            worksheet = spreadsheet.worksheet(sheet_name)
            worksheet.format(cell_range, format_dict)
            print(f"✅ Applied formatting to {cell_range} in '{sheet_name}'")
        except Exception as e:
            print(f"❌ Failed to format cells: {e}")
    
    def add_formula(self, spreadsheet, sheet_name: str, cell: str, formula: str):
        """Add a formula to a specific cell."""
        try:
            worksheet = spreadsheet.worksheet(sheet_name)
            worksheet.update(cell, formula)
            print(f"✅ Added formula to {cell} in '{sheet_name}': {formula}")
        except Exception as e:
            print(f"❌ Failed to add formula: {e}")
    
    def export_sheets_to_csv(self, spreadsheet, output_dir: str = "./exports"):
        """Export all sheets to separate CSV files."""
        import os
        
        try:
            os.makedirs(output_dir, exist_ok=True)
            sheet_names = self.list_all_sheets(spreadsheet)
            
            for sheet_name in sheet_names:
                df = self.read_sheet_data(spreadsheet, sheet_name)
                if not df.empty:
                    csv_path = os.path.join(output_dir, f"{sheet_name}.csv")
                    df.to_csv(csv_path, index=False)
                    print(f"✅ Exported '{sheet_name}' to {csv_path}")
                    
        except Exception as e:
            print(f"❌ Failed to export sheets: {e}")


def example_usage():
    """Example of how to use the GoogleSheetsAutomator."""
    
    # Initialize the automator
    automator = GoogleSheetsAutomator("path/to/your/credentials.json")
    
    # Open your spreadsheet
    spreadsheet_id = "your_google_sheets_id_here"
    spreadsheet = automator.open_spreadsheet(spreadsheet_id)
    
    if spreadsheet:
        # List all sheets
        sheets = automator.list_all_sheets(spreadsheet)
        
        # Read data from multiple sheets
        all_data = {}
        for sheet_name in sheets:
            df = automator.read_sheet_data(spreadsheet, sheet_name)
            all_data[sheet_name] = df
        
        # Example: Process data and write back
        for sheet_name, df in all_data.items():
            if not df.empty:
                # Add a timestamp column
                df['last_updated'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                
                # Write back to sheet
                automator.write_sheet_data(spreadsheet, sheet_name, df)
        
        # Example: Batch updates
        updates = [
            {
                "sheet": "Sheet1",
                "range": "A1",
                "values": [["Updated Header"]]
            },
            {
                "sheet": "Sheet2", 
                "range": "B1",
                "values": [["New Value"]]
            }
        ]
        automator.batch_update_cells(spreadsheet, updates)
        
        # Example: Add formulas
        automator.add_formula(spreadsheet, "Sheet1", "C1", "=SUM(A1:B1)")
        
        # Example: Format cells
        format_dict = {
            'backgroundColor': {'red': 0.8, 'green': 0.8, 'blue': 0.8},
            'textFormat': {'bold': True}
        }
        automator.format_cells(spreadsheet, "Sheet1", "A1:C1", format_dict)
        
        # Export all sheets to CSV
        automator.export_sheets_to_csv(spreadsheet)


if __name__ == "__main__":
    # Run example usage
    example_usage()
