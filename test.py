from google_patent_scraper_add import scraper_class

# Enable auto-download upon initialization and specify the download directory
scraper = scraper_class(proxy_address='http://127.0.0.1:10809')

# Add patent and perform scraping
scraper.add_patents('US2668287A')
scraper.scrape_all_patents()

# View the result
result = scraper.parsed_patents['US2668287A']
print(result)