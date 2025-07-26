#!/usr/bin/env python3
"""
DuckDuckGo URL Web Scraper
Simple script to search for information about URLs using DuckDuckGo
"""

import requests
import json
import sys
import time
from urllib.parse import quote, urlparse

class DDGScraper:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
    
    def search_ddg(self, query, max_results=10):
        """Search DuckDuckGo for the given query"""
        try:
            # DuckDuckGo instant answer API
            url = "https://api.duckduckgo.com/"
            params = {
                'q': query,
                'format': 'json',
                'no_html': '1',
                'skip_disambig': '1'
            }
            
            response = self.session.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            
            results = []
            
            # Extract abstract
            if data.get('Abstract'):
                results.append({
                    'type': 'abstract',
                    'title': data.get('AbstractSource', 'Abstract'),
                    'text': data.get('Abstract'),
                    'url': data.get('AbstractURL', '')
                })
            
            # Extract related topics
            for topic in data.get('RelatedTopics', []):
                if isinstance(topic, dict) and topic.get('Text'):
                    results.append({
                        'type': 'related',
                        'title': 'Related Topic',
                        'text': topic.get('Text'),
                        'url': topic.get('FirstURL', '')
                    })
            
            # If no instant answers, try HTML scraping approach
            if not results:
                results = self._scrape_ddg_html(query, max_results)
            
            return results
            
        except Exception as e:
            print(f"Error searching DuckDuckGo: {e}")
            return []
    
    def _scrape_ddg_html(self, query, max_results):
        """Fallback method to scrape DuckDuckGo HTML results"""
        try:
            url = f"https://duckduckgo.com/html/?q={quote(query)}"
            response = self.session.get(url)
            response.raise_for_status()
            
            # Simple HTML parsing (you might want to use BeautifulSoup for better parsing)
            html = response.text
            results = []
            
            # Basic extraction - this is simplified and may need improvement
            import re
            
            # Look for result links and titles
            pattern = r'<a[^>]*class="result__a"[^>]*href="([^"]*)"[^>]*>([^<]*)</a>'
            matches = re.findall(pattern, html)
            
            for i, (url, title) in enumerate(matches[:max_results]):
                if url and title:
                    results.append({
                        'type': 'search_result',
                        'title': title.strip(),
                        'text': f"Search result for: {query}",
                        'url': url
                    })
            
            return results
            
        except Exception as e:
            print(f"Error scraping DuckDuckGo HTML: {e}")
            return []
    
    def analyze_url(self, url):
        """Analyze a URL by searching for information about it"""
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
        
        parsed = urlparse(url)
        domain = parsed.netloc
        
        print(f"\n=== Analyzing URL: {url} ===")
        print(f"Domain: {domain}")
        
        # Search queries to run
        queries = [
            f'site:{domain}',
            f'"{domain}" information',
            f'"{domain}" review',
            f'what is {domain}',
            f'{domain} website'
        ]
        
        all_results = []
        
        for query in queries:
            print(f"\nSearching: {query}")
            results = self.search_ddg(query, max_results=5)
            
            if results:
                for result in results:
                    print(f"\n[{result['type'].upper()}] {result['title']}")
                    print(f"Text: {result['text']}")
                    if result['url']:
                        print(f"URL: {result['url']}")
                    print("-" * 50)
                
                all_results.extend(results)
            else:
                print("No results found.")
            
            # Rate limiting
            time.sleep(1)
        
        return all_results
    
    def save_results(self, results, filename):
        """Save results to a JSON file"""
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=2, ensure_ascii=False)
            print(f"\nResults saved to {filename}")
        except Exception as e:
            print(f"Error saving results: {e}")

def main():
    scraper = DDGScraper()
    
    if len(sys.argv) > 1:
        url = sys.argv[1]
    else:
        url = input("Enter URL to analyze: ")
    
    if not url:
        print("No URL provided.")
        return
    
    results = scraper.analyze_url(url)
    
    # Option to save results
    save = input("\nSave results to file? (y/n): ").lower()
    if save == 'y':
        filename = f"ddg_results_{int(time.time())}.json"
        scraper.save_results(results, filename)

if __name__ == "__main__":
    main()