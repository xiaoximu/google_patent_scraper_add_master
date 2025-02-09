# Scrape #
from urllib.request import Request, ProxyHandler, build_opener
from urllib.error import HTTPError
from bs4 import BeautifulSoup
# json #
import json
# errors #
from .errors import *
# download #
import os
import ssl


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
#           Create scraper class
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
class scraper_class:

    def __init__(self, return_abstract=False, return_description=False, return_claim=False,
                 auto_download_pdf=False, download_path='./pdfs', proxy_address=None):
        self.list_of_patents = []
        self.scrape_status = {}
        self.parsed_patents = {}
        self.return_abstract = return_abstract
        self.return_description = return_description
        self.return_claim = return_claim
        # New parameters for auto download and download directory
        self.auto_download_pdf = auto_download_pdf
        self.download_path = download_path
        # Allow users to specify a proxy address
        self.proxy_address = proxy_address if proxy_address else ''

    def add_patents(self, patent):
        # Check if patent is string
        if not isinstance(patent, str):
            raise (PatentClassError("'patent' variable must be a string"))
        # Append patent to list to be scrapped
        else:
            self.list_of_patents.append(patent)

    def delete_patents(self, patent):
        # Check if patent is in list
        if patent in self.list_of_patents:
            self.list_of_patents.pop(self.list_of_patents.index(patent))
        else:
            print('Patent {0} not in patent list'.format(patent))

    def add_scrape_status(self, patent, success_value):
        """Add status of scrape to dictionary self.scrape_status"""
        self.scrape_status[patent] = success_value

    def request_single_patent(self, patent, url=False):
        try:
            if not url:
                url = 'https://patents.google.com/patent/{0}'.format(patent)
            else:
                url = patent
            print(url)
            # Set up proxy configuration
            proxy = {
                'http': self.proxy_address,
                'https': self.proxy_address
            }
            # Create ProxyHandler
            proxy_handler = ProxyHandler(proxy)
            # Build an opener with proxy
            opener = build_opener(proxy_handler)
            req = Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            # Use the opener to open the request
            webpage = opener.open(req).read()
            soup = BeautifulSoup(webpage, features="html.parser")
            return (('Success', soup, url))
        except HTTPError as e:
            print('Patent: {0}, Error Status Code : {1}'.format(patent, e.code))
            return (e.code, '', url)

    def parse_citation(self, single_citation):
        try:
            patent_number = single_citation.find('span', itemprop='publicationNumber').get_text()
        except:
            patent_number = ''
        try:
            priority_date = single_citation.find('td', itemprop='priorityDate').get_text()
        except:
            priority_date = ''
        try:
            pub_date = single_citation.find('td', itemprop='publicationDate').get_text()
        except:
            pub_date
        return ({'patent_number': patent_number,
                 'priority_date': priority_date,
                 'pub_date': pub_date})

    def process_patent_html(self, soup):
        # Get title
        title = soup.find('meta', attrs={'name': 'DC.title'})
        title_text = title['content'].rstrip()

        try:
            inventor_name = [{'inventor_name': x.get_text()} for x in soup.find_all('dd', itemprop='inventor')]
        except:
            inventor_name = []
        # Assignee
        try:
            assignee_name_orig = [{'assignee_name': x.get_text()} for x in
                                  soup.find_all('dd', itemprop='assigneeOriginal')]
        except:
            assignee_name_orig = []
        try:
            assignee_name_current = [{'assignee_name': x.get_text()} for x in
                                     soup.find_all('dd', itemprop='assigneeCurrent')]
        except:
            assignee_name_current = []
        # Download PDFlink
        try:
            pdf_link = soup.find('a', {'itemprop': 'pdfLink'})['href']
        except:
            pdf_link = ''
        # Publication Date
        try:
            pub_date = soup.find('dd', itemprop='publicationDate').get_text()
        except:
            pub_date = ''
        # Application Number
        try:
            application_number = soup.find('dd', itemprop="applicationNumber").get_text()
        except:
            application_number = ''
        # Filing Date
        try:
            filing_date = soup.find('dd', itemprop='filingDate').get_text()
        except:
            filing_date = ''
        # Loop through all events
        list_of_application_events = soup.find_all('dd', itemprop='events')
        priority_date = ''
        grant_date = ''
        for app_event in list_of_application_events:
            try:
                title_info = app_event.find('span', itemprop='type').get_text()
                timeevent = app_event.find('time', itemprop='date').get_text()
                if title_info == 'priority':
                    priority_date = timeevent
                if title_info == 'granted':
                    grant_date = timeevent
                if title_info == 'publication' and pub_date == '':
                    pub_date = timeevent
            except:
                continue

        # Forward Citations (No Family to Family)
        found_forward_cites_orig = soup.find_all('tr', itemprop="forwardReferencesOrig")
        forward_cites_no_family = []
        if len(found_forward_cites_orig) > 0:
            for citation in found_forward_cites_orig:
                forward_cites_no_family.append(self.parse_citation(citation))

        # Forward Citations (Yes Family to Family)
        found_forward_cites_family = soup.find_all('tr', itemprop="forwardReferencesFamily")
        forward_cites_yes_family = []
        if len(found_forward_cites_family) > 0:
            for citation in found_forward_cites_family:
                forward_cites_yes_family.append(self.parse_citation(citation))

        # Backward Citations (No Family to Family)
        found_backward_cites_orig = soup.find_all('tr', itemprop='backwardReferences')
        backward_cites_no_family = []
        if len(found_backward_cites_orig) > 0:
            for citation in found_backward_cites_orig:
                backward_cites_no_family.append(self.parse_citation(citation))

        # Backward Citations (Yes Family to Family)
        found_backward_cites_family = soup.find_all('tr', itemprop='backwardReferencesFamily')
        backward_cites_yes_family = []
        if len(found_backward_cites_family) > 0:
            for citation in found_backward_cites_family:
                backward_cites_yes_family.append(self.parse_citation(citation))

        # Detailed Non-Patent Literature
        found_detailed_non_patent_lit = soup.find_all('tr', itemprop='detailedNonPatentLiterature')
        detailed_non_patent_lit = []

        if len(found_detailed_non_patent_lit) > 0:
            for citation in found_detailed_non_patent_lit:
                title_element = citation.find('span', itemprop='title')
                title = title_element.get_text(strip=True) if title_element else None
                link_element = title_element.find('a') if title_element else None
                link = link_element['href'] if link_element else None
                full_text = title_element.get_text(separator=' ', strip=True) if title_element else None
                detailed_non_patent_lit.append({
                    'full_text': full_text,
                    'link': link,
                })

        # Similar Documents
        found_similar_documents = soup.find_all('tr', itemprop='similarDocuments')
        similar_documents = []

        if len(found_similar_documents) > 0:
            for doc in found_similar_documents:
                publication_element = doc.find('span', itemprop='publicationNumber')
                publication_number = publication_element.get_text(strip=True) if publication_element else None
                publication_date_element = doc.find('time', itemprop='publicationDate')
                publication_date = publication_date_element.get_text(strip=True) if publication_date_element else None
                similar_documents.append({
                    'publication_number': publication_number,
                    'publication_date': publication_date
                })

        # Get abstract
        abstract_text = ''
        if self.return_abstract:
            abstract = soup.find('meta', attrs={'name': 'DC.description'})
            if abstract:
                abstract_text = abstract['content']

        # Get Description
        description_text = ''
        if self.return_description:
            description_section = soup.find('section', {'itemprop': 'description'})
            if description_section:
                description_paragraphs = description_section.find_all('div', class_='description-paragraph')
                description_text = "\n".join([para.get_text(strip=True) for para in description_paragraphs])

        # Get Claims
        claim_text = ''
        if self.return_claim:
            claim_section = soup.find('section', {'itemprop': 'claims'})
            if claim_section:
                claim_paragraphs = claim_section.find_all('div', class_='claim-text')
                claim_text = "\n".join([para.get_text(strip=True) for para in claim_paragraphs])

        # Get Legal Events
        events = soup.find_all('tr', {'itemprop': 'legalEvents'})
        legal_events = []
        seen_events = set()
        for row in events:
            tds = row.find_all('td')
            if len(tds) > 0:
                date = tds[0].find('time').text.strip() if tds[0].find('time') else None
                code = tds[1].text.strip() if tds[1] else None
                title = tds[2].text.strip() if tds[2] else None
                description = None
                description_tag = tds[3].find_all('p', {'itemprop': 'attributes'})
                if description_tag:
                    description = []
                    for p_tag in description_tag:
                        strong_tag = p_tag.find('strong', {'itemprop': 'label'})
                        span_tag = p_tag.find('span', {'itemprop': 'value'})
                        if strong_tag and span_tag:
                            description.append(f"{strong_tag.text.strip()}: {span_tag.text.strip()}")
                    description = "\n".join(description) if description else None
                unique_id = (date, code)
                if unique_id not in seen_events:
                    seen_events.add(unique_id)
                    legal_events.append({
                        'Date': date,
                        'Code': code,
                        'Title': title,
                        'Description': description
                    })

        # Get Classifications
        classifications = soup.find_all('ul', itemprop='classifications')
        classification_values = []
        for ul in classifications:
            lis = ul.find_all('li', itemprop='classifications')
            for li in lis:
                meta_tag = li.find('meta', {'itemprop': 'Leaf'})
                if meta_tag:
                    code = li.find('span', {'itemprop': 'Code'}).text.strip()
                    description = li.find('span', {'itemprop': 'Description'}).text.strip()
                    classification_values.append(f"{code} {description}")

        return ({
            'title': title_text,
            'inventor_name': json.dumps(inventor_name, ensure_ascii=False),
            'assignee_name_orig': json.dumps(assignee_name_orig, ensure_ascii=False),
            'assignee_name_current': json.dumps(assignee_name_current, ensure_ascii=False),
            'pub_date': pub_date,
            'priority_date': priority_date,
            'grant_date': grant_date,
            'filing_date': filing_date,
            'pdf_link': pdf_link,
            'forward_cite_no_family': json.dumps(forward_cites_no_family, ensure_ascii=False),
            'forward_cite_yes_family': json.dumps(forward_cites_yes_family, ensure_ascii=False),
            'backward_cite_no_family': json.dumps(backward_cites_no_family, ensure_ascii=False),
            'backward_cite_yes_family': json.dumps(backward_cites_yes_family, ensure_ascii=False),
            'detailed_non_patent_lit': json.dumps(detailed_non_patent_lit, ensure_ascii=False),
            'similar_documents': json.dumps(similar_documents, ensure_ascii=False),
            'abstract_text': abstract_text,
            'description_text': description_text,
            'claim_text': claim_text,
            'legal_events': legal_events,
            'classifications': classification_values
        })

    def get_scraped_data(self, soup, patent, url):
        # Parse individual patent
        parsing_individ_patent = self.process_patent_html(soup)
        # Add url + patent to dictionary
        parsing_individ_patent['url'] = url
        parsing_individ_patent['patent'] = patent
        if self.auto_download_pdf and parsing_individ_patent['pdf_link']:
            success, path = self.download_pdf(parsing_individ_patent['pdf_link'], save_path=self.download_path)
            parsing_individ_patent['pdf_local_path'] = path if success else None
        return parsing_individ_patent

    def scrape_all_patents(self):
        # Check if there are any patents
        if len(self.list_of_patents) == 0:
            raise (NoPatentsError(
                "no patents to scrape specified in 'patent' variable: add patent using class.add_patents([<PATENTNUMBER>])"))
        # Loop through list of patents and scrape them
        else:
            for patent in self.list_of_patents:
                error_status, soup, url = self.request_single_patent(patent)
                # Add scrape status variable
                self.add_scrape_status(patent, error_status)
                if error_status == 'Success':
                    self.parsed_patents[patent] = self.get_scraped_data(soup, patent, url)
                else:
                    self.parsed_patents[patent] = {}

    def download_pdf(self, pdf_link, save_path='./pdfs', filename=None):
        """
        Download PDF file and save it locally

        Arguments:
            pdf_link (str): PDF link from parse_patent_html
            save_path (str): Directory to save the PDF (default is './pdfs')
            filename (str): Custom filename (defaults to patent number)

        Returns:
            (bool, str): (Success status, file path or error message)
        """
        # Handle SSL certificate verification issues (optional)
        ssl._create_default_https_context = ssl._create_unverified_context

        try:
            os.makedirs(save_path, exist_ok=True)

            if not filename:
                patent_number = pdf_link.split('/')[-1].replace('.pdf', '')
                filename = f"{patent_number}.pdf"

            clean_filename = "".join([c for c in filename if c not in r'<>:"/\|?*'])
            full_path = os.path.join(save_path, clean_filename)

            # Reuse proxy configuration
            proxy = {
                'http': self.proxy_address,
                'https': self.proxy_address
            }
            proxy_handler = ProxyHandler(proxy)
            opener = build_opener(proxy_handler)

            req = Request(pdf_link, headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Accept': 'application/pdf'
            })

            response = opener.open(req)

            with open(full_path, 'wb') as f:
                f.write(response.read())

            return True, full_path

        except HTTPError as e:
            return False, f"HTTP Error {e.code}"
        except Exception as e:
            return False, f"Error: {str(e)}"
