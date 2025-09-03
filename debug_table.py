#!/usr/bin/env python3
"""
Debug script to examine the table structure from downloaded PFR HTML.
"""
import pandas as pd
from bs4 import BeautifulSoup, Comment

def examine_table(html_file):
    """Examine the table structure from the HTML file."""
    with open(html_file, 'r', encoding='utf-8') as f:
        html_content = f.read()
    
    soup = BeautifulSoup(html_content, "lxml")
    
    # Try to find the rushing table
    table = soup.find("table", id="rushing")
    if table:
        print("✓ Found direct table with id='rushing'")
        print(f"Table HTML length: {len(str(table))}")
        
        # Try to read with pandas
        try:
            df = pd.read_html(str(table))[0]
            print(f"✓ Successfully parsed table with pandas")
            print(f"Table shape: {df.shape}")
            print(f"Columns: {list(df.columns)}")
            print("\nFirst few rows:")
            print(df.head())
            return df
        except Exception as e:
            print(f"✗ Failed to parse with pandas: {e}")
    
    # Look for commented table
    wrapper = soup.find(id="all_rushing")
    if wrapper:
        print("✓ Found wrapper div 'all_rushing'")
        
        # Look for comments
        comments = wrapper.find_all(string=lambda text: isinstance(text, Comment))
        print(f"Found {len(comments)} comments in wrapper")
        
        for i, comment in enumerate(comments):
            if 'id="rushing"' in comment or "id='rushing'" in comment:
                print(f"✓ Found rushing table in comment {i}")
                try:
                    df = pd.read_html(str(comment))[0]
                    print(f"✓ Successfully parsed commented table")
                    print(f"Table shape: {df.shape}")
                    print(f"Columns: {list(df.columns)}")
                    print("\nFirst few rows:")
                    print(df.head())
                    return df
                except Exception as e:
                    print(f"✗ Failed to parse commented table: {e}")
    
    print("✗ Could not find or parse rushing table")
    return None

if __name__ == "__main__":
    df = examine_table("debug_pfr_2024.html")

