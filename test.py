from google_patent_scraper_add import scraper_class

# Enable auto-download upon initialization and specify the download directory
scraper = scraper_class(auto_download_pdf=True, download_path="D:/Downloads/PDFs")

# Add patent and perform scraping
scraper.add_patents('US2668287A')
scraper.scrape_all_patents()

# View the result
result = scraper.parsed_patents['US2668287A']
print(f"PDF saved at: {result.get('pdf_local_path', 'Not downloaded')}")