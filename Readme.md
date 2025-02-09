# Patent Scraper
A python package to scrape patents from 'https://patents.google.com/'. Portions of this project are based on [ryanlstevens/google_patent_scraper](https://github.com/ryan_lstevens/google_patent_scraper).

## Request

```shell
pip install bs4
```

## Available Data

The following elements are always returned by the scraper class:

    title                     (str)   : title
    application_number        (str)   : application number
    inventor_name             (json)  : inventors of patent 
    assignee_name_orig        (json)  : original assignees to patent
    assignee_name_current     (json)  : current assignees to patent
    pub_date                  (str)   : publication date
    filing_date               (str)   : filing date
    priority_date             (str)   : priority date
    grant_date                (str)   : grant date
    pdf_link                  (str)   : Download PDF
    forward_cites_no_family   (json)  : forward citations that are not family-to-family cites
    forward_cites_yes_family  (json)  : forward citations that are family-to-family cites
    backward_cites_no_family  (json)  : backward citations that are not family-to-family cites
    backward_cites_yes_family (json)  : backward citations that are family-to-family cites
    detailed_non_patent_lit   (json)  : Non-Patent Citations
    similar_documents         (json)  : Similar Documents
    abstract_text             (str)   : Abstract
    description_text          (str)   : Description
    claim_text                (str)   : Claims
    legal_events              (str)   : Legal Events

    
 There are optional elements you can have returned, see examples below:
 
    abstract_text             (str)   : text of abstract (if exists)     
    description_text          (str)   : Description
    claim_text                (str)   : Claims

### Example Output

```text
{
    'inventor_name': '[{"inventor_name": "John Doe"}]',
    'assignee_name_orig': '[{"assignee_name": "Company A"}]',
    'assignee_name_current': '[{"assignee_name": "Company B"}]',
    'pub_date': '2020-01-01',
    'priority_date': '2019-01-01',
    'grant_date': '2021-01-01',
    'filing_date': '2019-06-15',
    'pdf_link': 'https://.../US2668287A.pdf',
    'forward_cite_no_family': '[{"patent_number": "US1234567A", "priority_date": "2018-01-01", "pub_date": "2019-01-01"}]',
    'forward_cite_yes_family': '[]',
    'backward_cite_no_family': '[]',
    'backward_cite_yes_family': '[{"patent_number": "US7654321A", "priority_date": "2015-03-15", "pub_date": "2017-06-01"}]',
    'detailed_non_patent_lit': '[{"full_text": "Some research paper title", "link": "http://link-to-paper.com"}]',
    'similar_documents': '[{"publication_number": "US2345678A", "publication_date": "2019-07-10"}]',
    'abstract_text': 'This is a brief summary of the patent.',
    'description_text': 'This is the full description of the patent.',
    'claim_text': 'These are the claims associated with the patent.',
    'legal_events': '[{"Date": "2020-01-01", "Code": "CODE123", "Title": "Patent granted", "Description": "Patent granted to assignee."}]',
    'classifications': ['A01B 3/00 - Agriculture', 'C02F 1/10 - Water treatment']
}
```

## Package Installation

```git
pip install git+https://github.com/xiaoximu/google_patent_scraper_add_master.git
```

## Main Use Cases

There are two primary ways to use this package:
1. Scrape a single patent

```python
# ~ Import packages ~ #
from google_patent_scraper_add import scraper_class

# ~ Initialize scraper class ~ #
scraper=scraper_class(proxy_address='http://your.proxy.address:port') 

# ~~ Scrape patents individually ~~ #
patent_1 = 'US2668287A'
patent_2 = 'US266827A'
err_1, soup_1, url_1 = scraper.request_single_patent(patent_1)
err_2, soup_2, url_2 = scraper.request_single_patent(patent_2)

# ~ Parse results of scrape ~ #
patent_1_parsed = scraper.get_scraped_data(soup_1,patent_1,url_1)
patent_2_parsed = scraper.get_scraped_data(soup_2,patent_2,url_2)
```

2. Scrape a list of patents

```python
# ~ Import packages ~ #
from google_patent_scraper_add import scraper_class
import json

# ~ Initialize scraper class ~ #
scraper=scraper_class(proxy_address='http://your.proxy.address:port')

# ~ Add patents to list ~ #
scraper.add_patents('US2668287A')
scraper.add_patents('US266827A')

# ~ Scrape all patents ~ #
scraper.scrape_all_patents()

# ~ Get results of scrape ~ #
patent_1_parsed = scraper.parsed_patents['US2668287A']
patent_2_parsed = scraper.parsed_patents['US266827A']

# ~ Print inventors of patent US2668287A ~ #
for inventor in json.loads(patent_1_parsed['inventor_name']):
  print('Patent inventor : {0}'.format(inventor['inventor_name']))
```

### Additional optional information

__Return Abstract Information__

Scrape a patent and retrieve abstract information

```python
# ~ Import packages ~ #
from google_patent_scraper_add import scraper_class

# ~ Initialize scraper class ~ #
scraper=scraper_class(proxy_address='http://your.proxy.address:port', return_abstract=True)  #<- TURN ON ABSTRACT TEXT  

# ~~ Scrape patents individually ~~ #
patent_1 = 'US2668287A'
err_1, soup_1, url_1 = scraper.request_single_patent(patent_1)

# ~ Parse results of scrape ~ #
patent_1_parsed = scraper.get_scraped_data(soup_1,patent_1,url_1)

# ~ Print abstract text ~ #
print(patent_1_parsed['abstract_text'])
```

__Download PDF__

```python
from google_patent_scraper_add import scraper_class

# Enable auto-download upon initialization and specify the download directory
scraper = scraper_class(proxy_address='http://your.proxy.address:port', auto_download_pdf=True, download_path="D:/Downloads/PDFs")

# Add patent and perform scraping
scraper.add_patents('US2668287A')
scraper.scrape_all_patents()

# View the result
result = scraper.parsed_patents['US2668287A']
print(f"PDF saved at: {result.get('pdf_local_path', 'Not downloaded')}")
```