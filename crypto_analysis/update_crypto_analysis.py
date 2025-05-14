#!/usr/bin/env python3
"""
Cryptocurrency Analysis Updater

This script automatically updates the cryptocurrency analysis HTML files
with the latest data from the CSV files.
"""

import os
import csv
import json
import re
from datetime import datetime
import glob
from bs4 import BeautifulSoup

def get_latest_csv_file(data_dir, prefix):
    """Get the latest CSV file with the given prefix."""
    pattern = os.path.join(data_dir, f"{prefix}_*.csv")
    files = glob.glob(pattern)
    if not files:
        return None
    return max(files, key=os.path.getctime)

def extract_news_from_csv(csv_file):
    """Extract cryptocurrency news from the CSV file."""
    if not csv_file or not os.path.exists(csv_file):
        return {}
    
    news_data = {}
    with open(csv_file, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        next(reader)  # Skip header
        for row in reader:
            if len(row) >= 4:
                timestamp, source, cryptocurrencies, news = row
                try:
                    news_json = json.loads(news)
                    for tag, tag_data in news_json.get('tags', {}).items():
                        if tag not in news_data:
                            news_data[tag] = []
                        
                        for article in tag_data.get('articles', []):
                            if article and 'headline' in article and 'link' in article:
                                # Avoid duplicates
                                if not any(a.get('headline') == article['headline'] for a in news_data[tag]):
                                    news_data[tag].append(article)
                except (json.JSONDecodeError, KeyError) as e:
                    print(f"Error parsing news data: {e}")
    
    return news_data

def update_index_html(news_data):
    """Update the index.html file with the latest news."""
    index_file = os.path.join(os.path.dirname(__file__), 'index.html')
    if not os.path.exists(index_file):
        print(f"Error: {index_file} not found")
        return
    
    with open(index_file, 'r', encoding='utf-8') as f:
        soup = BeautifulSoup(f, 'html.parser')
    
    # Update the date
    date_elem = soup.select_one('.date')
    if date_elem:
        date_elem.string = datetime.now().strftime('%B %d, %Y')
    
    # Update news section
    news_section = soup.select_one('.news-section')
    if news_section:
        news_items = news_section.select('.news-item')
        
        # Clear existing news items
        for item in news_items:
            item.decompose()
        
        # Add new news items
        added_headlines = set()
        for tag in ['BTC', 'ETH', 'XRP', 'SOL']:
            if tag in news_data:
                for article in news_data[tag][:2]:  # Limit to 2 articles per tag
                    headline = article.get('headline')
                    if headline and headline not in added_headlines:
                        added_headlines.add(headline)
                        
                        news_item = soup.new_tag('div')
                        news_item['class'] = 'news-item'
                        
                        title = soup.new_tag('h3')
                        title['class'] = 'news-title'
                        title.string = headline
                        
                        source = soup.new_tag('p')
                        source['class'] = 'news-source'
                        source.string = 'Source: CoinTelegraph'
                        
                        news_item.append(title)
                        news_item.append(source)
                        news_section.append(news_item)
    
    # Write the updated HTML
    with open(index_file, 'w', encoding='utf-8') as f:
        f.write(str(soup))
    
    print(f"Updated {index_file}")

def update_coin_html(coin, news_data):
    """Update the individual coin HTML file with the latest news."""
    coin_file = os.path.join(os.path.dirname(__file__), f'{coin.lower()}.html')
    if not os.path.exists(coin_file):
        print(f"Error: {coin_file} not found")
        return
    
    with open(coin_file, 'r', encoding='utf-8') as f:
        soup = BeautifulSoup(f, 'html.parser')
    
    # Update the date
    date_elem = soup.select_one('.date')
    if date_elem:
        date_elem.string = datetime.now().strftime('%B %d, %Y')
    
    # Update news section
    news_section = soup.select_one('.news-section')
    if news_section and coin in news_data:
        news_items = news_section.select('.news-item')
        
        # Clear existing news items
        for item in news_items:
            item.decompose()
        
        # Add new news items
        for article in news_data[coin][:3]:  # Limit to 3 articles
            headline = article.get('headline')
            if headline:
                news_item = soup.new_tag('div')
                news_item['class'] = 'news-item'
                
                title = soup.new_tag('h3')
                title['class'] = 'news-title'
                title.string = headline
                
                source = soup.new_tag('p')
                source['class'] = 'news-source'
                source.string = 'Source: CoinTelegraph'
                
                content = soup.new_tag('p')
                content.string = 'Updated article content based on latest data.'
                
                news_item.append(title)
                news_item.append(source)
                news_item.append(content)
                news_section.append(news_item)
    
    # Write the updated HTML
    with open(coin_file, 'w', encoding='utf-8') as f:
        f.write(str(soup))
    
    print(f"Updated {coin_file}")

def update_footer_dates():
    """Update the footer dates in all HTML files."""
    html_files = glob.glob(os.path.join(os.path.dirname(__file__), '*.html'))
    today_str = datetime.now().strftime('%B %d, %Y')
    
    for html_file in html_files:
        with open(html_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Update the footer date
        pattern = r'Generated on [A-Za-z]+ \d+, \d{4}'
        updated_content = re.sub(pattern, f'Generated on {today_str}', content)
        
        with open(html_file, 'w', encoding='utf-8') as f:
            f.write(updated_content)
        
        print(f"Updated footer date in {os.path.basename(html_file)}")

def main():
    """Main function to update all cryptocurrency analysis files."""
    print("Updating cryptocurrency analysis files...")
    
    # Get the latest CSV files
    data_dir = os.path.join(os.path.dirname(__file__), '..', 'data')
    crypto_csv = get_latest_csv_file(data_dir, 'crypto')
    news_csv = get_latest_csv_file(data_dir, 'news')
    
    print(f"Using crypto data: {os.path.basename(crypto_csv) if crypto_csv else 'None'}")
    print(f"Using news data: {os.path.basename(news_csv) if news_csv else 'None'}")
    
    # Extract news data
    news_data = extract_news_from_csv(crypto_csv)
    
    # Update HTML files
    update_index_html(news_data)
    for coin in ['BTC', 'ETH', 'XRP', 'SOL']:
        update_coin_html(coin, news_data)
    
    # Update footer dates
    update_footer_dates()
    
    print("Cryptocurrency analysis files updated successfully!")

if __name__ == "__main__":
    main()