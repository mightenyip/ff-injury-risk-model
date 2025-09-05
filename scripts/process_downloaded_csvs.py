#!/usr/bin/env python3
"""
Process Downloaded CSVs from Browser Scraper
This script helps organize and process the CSV files downloaded from the browser scraper.
"""

import pandas as pd
import os
import glob
from pathlib import Path

def setup_directories():
    """Create necessary directories for organizing the data"""
    directories = [
        "data/weekly_raw",
        "data/weekly_processed",
        "data/weekly_combined"
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        print(f"✅ Created directory: {directory}")

def find_downloaded_csvs():
    """Find all downloaded CSV files in the Downloads folder and current directory"""
    # Common download locations
    download_paths = [
        os.path.expanduser("~/Downloads"),
        os.getcwd()
    ]
    
    csv_files = []
    for path in download_paths:
        if os.path.exists(path):
            # Look for files matching our naming pattern
            pattern = os.path.join(path, "*_*_gamelog.csv")
            found_files = glob.glob(pattern)
            csv_files.extend(found_files)
    
    return csv_files

def organize_csvs():
    """Organize downloaded CSV files into the proper directory structure"""
    csv_files = find_downloaded_csvs()
    
    if not csv_files:
        print("❌ No downloaded CSV files found!")
        print("Make sure you've run the browser scraper and downloaded some files.")
        return
    
    print(f"Found {len(csv_files)} CSV files to organize:")
    
    # Create the target directory
    target_dir = "data/weekly_raw"
    Path(target_dir).mkdir(parents=True, exist_ok=True)
    
    moved_count = 0
    for csv_file in csv_files:
        filename = os.path.basename(csv_file)
        target_path = os.path.join(target_dir, filename)
        
        try:
            # Move the file
            if os.path.exists(target_path):
                print(f"⚠️  File already exists: {filename}")
                continue
                
            # Use shutil.move for better cross-platform support
            import shutil
            shutil.move(csv_file, target_path)
            print(f"✅ Moved: {filename}")
            moved_count += 1
            
        except Exception as e:
            print(f"❌ Error moving {filename}: {e}")
    
    print(f"\n✅ Successfully organized {moved_count} CSV files")
    print(f"Files are now in: {target_dir}")

def analyze_csv_structure():
    """Analyze the structure of downloaded CSV files"""
    csv_dir = "data/weekly_raw"
    if not os.path.exists(csv_dir):
        print("❌ No CSV files found. Run organize_csvs() first!")
        return
    
    csv_files = glob.glob(os.path.join(csv_dir, "*.csv"))
    if not csv_files:
        print("❌ No CSV files in weekly_raw directory!")
        return
    
    print(f"Analyzing {len(csv_files)} CSV files...")
    
    # Sample a few files to understand the structure
    sample_files = csv_files[:3]
    
    for csv_file in sample_files:
        filename = os.path.basename(csv_file)
        print(f"\n--- {filename} ---")
        
        try:
            df = pd.read_csv(csv_file)
            print(f"Columns: {list(df.columns)}")
            print(f"Rows: {len(df)}")
            print(f"Sample data:")
            print(df.head(2).to_string())
        except Exception as e:
            print(f"Error reading {filename}: {e}")

def create_combined_dataset():
    """Create a combined dataset from all individual CSV files"""
    csv_dir = "data/weekly_raw"
    if not os.path.exists(csv_dir):
        print("❌ No CSV files found. Run organize_csvs() first!")
        return
    
    csv_files = glob.glob(os.path.join(csv_dir, "*.csv"))
    if not csv_files:
        print("❌ No CSV files in weekly_raw directory!")
        return
    
    print(f"Combining {len(csv_files)} CSV files...")
    
    all_data = []
    processed_count = 0
    
    for csv_file in csv_files:
        filename = os.path.basename(csv_file)
        
        try:
            df = pd.read_csv(csv_file)
            
            # Extract player ID and season from filename
            # Format: playerid_season_gamelog.csv
            parts = filename.replace('_gamelog.csv', '').split('_')
            if len(parts) >= 2:
                player_id = parts[0]
                season = parts[1]
                
                # Add metadata columns
                df['player_id'] = player_id
                df['season'] = int(season)
                df['source_file'] = filename
                
                all_data.append(df)
                processed_count += 1
                
                if processed_count % 50 == 0:
                    print(f"Processed {processed_count}/{len(csv_files)} files...")
                    
        except Exception as e:
            print(f"❌ Error processing {filename}: {e}")
    
    if all_data:
        # Combine all data
        combined_df = pd.concat(all_data, ignore_index=True)
        
        # Save combined dataset
        output_file = "data/weekly_combined/all_rb_weekly_data.csv"
        combined_df.to_csv(output_file, index=False)
        
        print(f"\n✅ Successfully combined {processed_count} files!")
        print(f"Combined dataset: {output_file}")
        print(f"Total rows: {len(combined_df)}")
        print(f"Columns: {list(combined_df.columns)}")
        
        # Show sample of combined data
        print(f"\nSample of combined data:")
        print(combined_df.head(3).to_string())
        
    else:
        print("❌ No data could be processed!")

def main():
    """Main function to process downloaded CSVs"""
    print("CSV Processing and Organization Tool")
    print("=" * 40)
    
    while True:
        print("\nChoose an option:")
        print("1. Setup directories")
        print("2. Organize downloaded CSV files")
        print("3. Analyze CSV structure")
        print("4. Create combined dataset")
        print("5. Run full workflow")
        print("6. Exit")
        
        choice = input("\nEnter your choice (1-6): ").strip()
        
        if choice == "1":
            setup_directories()
        elif choice == "2":
            organize_csvs()
        elif choice == "3":
            analyze_csv_structure()
        elif choice == "4":
            create_combined_dataset()
        elif choice == "5":
            print("\nRunning full workflow...")
            setup_directories()
            organize_csvs()
            analyze_csv_structure()
            create_combined_dataset()
            print("\n✅ Full workflow complete!")
        elif choice == "6":
            print("Goodbye!")
            break
        else:
            print("Invalid choice. Please enter 1-6.")

if __name__ == "__main__":
    main()

