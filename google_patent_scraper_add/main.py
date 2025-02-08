# Scrape #
# 注意可能需要更改代理
from urllib.request import Request, urlopen, ProxyHandler, build_opener
import urllib.parse
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
    """
    Google scraper class used to scrape data from 'https://patents.google.com/'

    There are two primary ways to use the class:

        (1) Add list of patents to class and scrape all patents at once

        scraper=scraper_class() #<- Initialize class

        # ~ Add patents to list ~ #
        scraper.add_patents('US2668287A')
        scraper.add_patents('US266827A')

        # ~ Scrape all patents ~ #
        scraper.scrape_all_patents()

        # ~ Get results of scrape ~ #
        patent_1_parsed = scraper.parsed_patents['2668287A']
        patent_2_parsed = scraper.parsed_patents['266827A']



        (2) Scrape each patent individually

        scraper=scraper_class() #<- Initialize class

        # ~~ Scrape patents individually ~~ #
        patent_1 = 'US2668287A'
        patent_2 = 'US266827A'
        err_1, soup_1, url_1 = scraper.request_single_patent(patent_1)
        err_2, soup_2, url_2 = scraper.request_single_patent(patent_2)

        # ~ Parse results of scrape ~ #
        patent_1_parsed = scraper.get_scraped_data(soup_1,patent_1,url_1)
        patent_2_parsed = scraper.get_scraped_data(soup_2,patetn_2,url_2)

    Attributes:
        - list_of_patents (list) : patents to be scraped
        - scrape_status   (dict) : status of request using patent
        - parsed_patents  (dict) : result of parsing patent html
        - return_abstract (bool) : boolean for whether the code should return the abstract

    """

    def __init__(self, return_abstract=False, return_description=False, return_claim=False,
                 auto_download_pdf=False, download_path='./pdfs'):
        self.list_of_patents = []
        self.scrape_status = {}
        self.parsed_patents = {}
        self.return_abstract = return_abstract
        self.return_description = return_description
        self.return_claim = return_claim
        # 新增自动下载和下载目录参数
        self.auto_download_pdf = auto_download_pdf
        self.download_path = download_path

    def add_patents(self, patent):
        """Append patent to patent list attribute self.list_of_patents


        Inputs:
            - patent (str) : patent number

        """
        # ~ Check if patent is string ~ #
        if not isinstance(patent, str):
            raise (PatentClassError("'patent' variable must be a string"))
        # ~ Append patent to list to be scrapped ~ #
        else:
            self.list_of_patents.append(patent)

    def delete_patents(self, patent):
        """Remove patent from patent list attribute self.list_of_patents

        Inputs:
            - patent (str) : patent number
        """
        # ~ Check if patent is in list ~ #
        if patent in self.list_of_patents:
            self.list_of_patents.pop(self.list_of_patents.index(patent))
        else:
            print('Patent {0} not in patent list'.format(patent))

    def add_scrape_status(self, patent, success_value):
        """Add status of scrape to dictionary self.scrape_status"""
        self.scrape_status[patent] = success_value

    def request_single_patent(self, patent, url=False):
        """Calls request function to retreive google patent data and parses returned html using BeautifulSoup


        Returns:
            - Status of scrape   <- String
            - Html of patent     <- BS4 object

        Inputs:
            - patent (str)  : if    url == False then patent is patent number
                              elif  url == True  then patent is google patent url
            - url    (bool) : determines whether patent is treated as patent number
                                or google patent url

        """
        try:
            if not url:
                url = 'https://patents.google.com/patent/{0}'.format(patent)
            else:
                url = patent
            print(url)
            # Set up proxy configuration
            proxy = {
                'http': 'http://127.0.0.1:10809',
                'https': 'http://127.0.0.1:10809'
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
        """Parses patent citation, returning results as a dictionary


        Returns (variables returned in dictionary, following are key names):
            - patent_number (str)  : patent number
            - priority_date (str)  : priority date of patent
            - pub_date      (str)  : publication date of patent

        Inputs:
            - single_citation (str) : html string from citation section in google patent html

        """

        try:
            patent_number = single_citation.find('span', itemprop='publicationNumber').get_text()
        except:
            patent_number = ''
        # ~ Get priority date ~ #
        try:
            priority_date = single_citation.find('td', itemprop='priorityDate').get_text()
        except:
            priority_date = ''
        # ~ Get publication date ~ #
        try:
            pub_date = single_citation.find('td', itemprop='publicationDate').get_text()
        except:
            pub_date
        return ({'patent_number': patent_number,
                 'priority_date': priority_date,
                 'pub_date': pub_date})

    def process_patent_html(self, soup):
        """ Parse patent html using BeautifulSoup module


        Returns (variables returned in dictionary, following are key names):
            - application_number        (str)   : application number
            - inventor_name             (json)  : inventors of patent
            - assignee_name_orig        (json)  : original assignees to patent
            - assignee_name_current     (json)  : current assignees to patent
            - pub_date                  (str)   : publication date
            - filing_date               (str)   : filing date
            - priority_date             (str)   : priority date
            - grant_date                (str)   : grant date
            - forward_cites_no_family   (json)  : forward citations that are not family-to-family cites
            - forward_cites_yes_family  (json)  : forward citations that are family-to-family cites
            - backward_cites_no_family  (json)  : backward citations that are not family-to-family cites
            - backward_cites_yes_family (json)  : backward citations that are family-to-family cites

        Inputs:
            - soup (str) : html string from of google patent html


        """
        title_text = ''
        # Get title #
        title = soup.find('meta', attrs={'name': 'DC.title'})
        title_text = title['content'].rstrip()

        try:
            inventor_name = [{'inventor_name': x.get_text()} for x in soup.find_all('dd', itemprop='inventor')]
        except:
            inventor_name = []
        # Assignee #
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
        # Download PDFlink #
        try:
            pdf_link = soup.find('a', {'itemprop': 'pdfLink'})['href']
        except:
            pdf_link = ''
        # Publication Date #
        try:
            pub_date = soup.find('dd', itemprop='publicationDate').get_text()
        except:
            pub_date = ''
        # Application Number #
        try:
            application_number = soup.find('dd', itemprop="applicationNumber").get_text()
        except:
            application_number = ''
        # Filing Date #
        try:
            filing_date = soup.find('dd', itemprop='filingDate').get_text()
        except:
            filing_date = ''
        # Loop through all events #
        list_of_application_events = soup.find_all('dd', itemprop='events')
        priority_date = ''
        grant_date = ''
        for app_event in list_of_application_events:
            # Get information #
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

                # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
        #             Citations
        #
        # All citations are of the same format
        #   -Find all citations
        #   -If there are any citations, parse each individually using "parse_citation"
        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
        # ~~~ Forward Citations (No Family to Family) ~~~ #
        found_forward_cites_orig = soup.find_all('tr', itemprop="forwardReferencesOrig")
        forward_cites_no_family = []
        if len(found_forward_cites_orig) > 0:
            for citation in found_forward_cites_orig:
                forward_cites_no_family.append(self.parse_citation(citation))

        # ~~~ Forward Citations (Yes Family to Family) ~~~ #
        found_forward_cites_family = soup.find_all('tr', itemprop="forwardReferencesFamily")
        forward_cites_yes_family = []
        if len(found_forward_cites_family) > 0:
            for citation in found_forward_cites_family:
                forward_cites_yes_family.append(self.parse_citation(citation))

        # ~~~ Backward Citations (No Family to Family) ~~~ #
        found_backward_cites_orig = soup.find_all('tr', itemprop='backwardReferences')
        backward_cites_no_family = []
        if len(found_backward_cites_orig) > 0:
            for citation in found_backward_cites_orig:
                backward_cites_no_family.append(self.parse_citation(citation))

        # ~~~ Backward Citations (Yes Family to Family) ~~~ #
        found_backward_cites_family = soup.find_all('tr', itemprop='backwardReferencesFamily')
        backward_cites_yes_family = []
        if len(found_backward_cites_family) > 0:
            for citation in found_backward_cites_family:
                backward_cites_yes_family.append(self.parse_citation(citation))

        # ~~~ Detailed Non-Patent Literature ~~~ #
        found_detailed_non_patent_lit = soup.find_all('tr', itemprop='detailedNonPatentLiterature')
        detailed_non_patent_lit = []

        if len(found_detailed_non_patent_lit) > 0:
            for citation in found_detailed_non_patent_lit:
                # 获取文献标题
                title_element = citation.find('span', itemprop='title')
                title = title_element.get_text(strip=True) if title_element else None

                # 获取相关链接
                link_element = title_element.find('a') if title_element else None
                link = link_element['href'] if link_element else None

                # 获取其他信息，如出版物、日期等
                full_text = title_element.get_text(separator=' ', strip=True) if title_element else None

                # 处理文献具体信息
                detailed_non_patent_lit.append({
                    'full_text': full_text,
                    'link': link,
                })

        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
        #  Similar Documents
        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
        found_similar_documents = soup.find_all('tr', itemprop='similarDocuments')
        similar_documents = []

        if len(found_similar_documents) > 0:
            for doc in found_similar_documents:
                # 获取专利号和链接（Publication）
                publication_element = doc.find('span', itemprop='publicationNumber')
                publication_number = publication_element.get_text(strip=True) if publication_element else None

                # 获取出版日期（Publication Date）
                publication_date_element = doc.find('time', itemprop='publicationDate')
                publication_date = publication_date_element.get_text(strip=True) if publication_date_element else None

                # 将数据添加到结果列表
                similar_documents.append({
                    'publication_number': publication_number,
                    'publication_date': publication_date
                })

        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
        #  Get abstract
        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
        abstract_text = ''
        if self.return_abstract:
            # Get abstract #
            abstract = soup.find('meta', attrs={'name': 'DC.description'})
            # Get text
            if abstract:
                abstract_text = abstract['content']

        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
        #  Get Description
        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
        description_text = ''
        if self.return_description:
            # Get abstract #
            description_section = soup.find('section', {'itemprop': 'description'})
            # Get text
            if description_section:
                description_paragraphs = description_section.find_all('div', class_='description-paragraph')
                description_text = "\n".join([para.get_text(strip=True) for para in description_paragraphs])

        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
        #  Get Claims
        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
        claim_text = ''
        if self.return_claim:
            # Get abstract #
            claim_section = soup.find('section', {'itemprop': 'claims'})
            # Get text
            if claim_section:
                claim_paragraphs = claim_section.find_all('div', class_='claim-text')
                claim_text = "\n".join([para.get_text(strip=True) for para in claim_paragraphs])

        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
        #  Get Legal Events
        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
        # 找到所有legalEvents条目
        events = soup.find_all('tr', {'itemprop': 'legalEvents'})
        # 存储所有事件的信息
        legal_events = []
        # 存储已爬取的法律事件标识符
        seen_events = set()
        # 遍历所有的legalEvents条目
        for row in events:
            # 获取每个<tr>中的各个<td>
            tds = row.find_all('td')

            if len(tds) > 0:
                # 提取Date, Code, Title
                date = tds[0].find('time').text.strip() if tds[0].find('time') else None
                code = tds[1].text.strip() if tds[1] else None
                title = tds[2].text.strip() if tds[2] else None

                # 提取Description (如果有的话)
                description = None
                description_tag = tds[3].find_all('p', {'itemprop': 'attributes'})

                if description_tag:
                    # 遍历每个<p>标签并提取<strong>和<span>内容
                    description = []
                    for p_tag in description_tag:
                        strong_tag = p_tag.find('strong', {'itemprop': 'label'})
                        span_tag = p_tag.find('span', {'itemprop': 'value'})

                        if strong_tag and span_tag:
                            description.append(f"{strong_tag.text.strip()}: {span_tag.text.strip()}")

                    # 合并所有的描述行
                    description = "\n".join(description) if description else None

                unique_id = (date, code)  # 组合日期和代码作为唯一标识符
                # 检查是否已经爬取过该事件
                if unique_id not in seen_events:
                    seen_events.add(unique_id)
                    # 将提取的数据添加到legal_events列表
                    legal_events.append({
                        'Date': date,
                        'Code': code,
                        'Title': title,
                        'Description': description
                    })

        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
        #  Get Classifications
        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
        # 查找所有包含分类信息的 ul
        classifications = soup.find_all('ul', itemprop='classifications')
        # 用于存储最终的分类值
        classification_values = []
        # 遍历每个 ul 标签，提取最后一个有效的分类项
        for ul in classifications:
            # 查找所有的 li 标签
            lis = ul.find_all('li', itemprop='classifications')
            for li in lis:
                # 查找包含 "meta" 标签并检查是否有 itemprop="Leaf" 属性
                meta_tag = li.find('meta', {'itemprop': 'Leaf'})
                if meta_tag:
                    # 提取最终的分类值（Code 和 Description）
                    code = li.find('span', {'itemprop': 'Code'}).text.strip()
                    description = li.find('span', {'itemprop': 'Description'}).text.strip()
                    classification_values.append(f"{code} {description}")

        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
        #  Return data as a dictionary
        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
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
        # ~~ Parse individual patent ~~ #
        parsing_individ_patent = self.process_patent_html(soup)
        # ~~ Add url + patent to dictionary ~~ #
        parsing_individ_patent['url'] = url
        parsing_individ_patent['patent'] = patent
        # 新增PDF下载逻辑，使用实例变量决定是否自动下载以及保存位置
        if self.auto_download_pdf and parsing_individ_patent['pdf_link']:
            success, path = self.download_pdf(parsing_individ_patent['pdf_link'], save_path=self.download_path)
            parsing_individ_patent['pdf_local_path'] = path if success else None
        return parsing_individ_patent

    def scrape_all_patents(self):
        """ Scrapes all patents in list self.list_of_patents using function "request_single_patent".

        If you want to scrape a single patent without adding it to the class variable,
            use "request_single_patent" function as a method on the class. See the doc string
            in the class module for an example.

        """
        # ~ Check if there are any patents ~ #
        if len(self.list_of_patents) == 0:
            raise (NoPatentsError(
                "no patents to scrape specified in 'patent' variable: add patent using class.add_patents([<PATENTNUMBER>])"))
        # ~ Loop through list of patents and scrape them ~ #
        else:
            for patent in self.list_of_patents:
                error_status, soup, url = self.request_single_patent(patent)
                # ~ Add scrape status variable ~ #
                self.add_scrape_status(patent, error_status)
                if error_status == 'Success':
                    self.parsed_patents[patent] = self.get_scraped_data(soup, patent, url)
                else:
                    self.parsed_patents[patent] = {}

    def download_pdf(self, pdf_link, save_path='./pdfs', filename=None):
        """
        下载PDF文件并保存到本地

        参数:
            pdf_link (str): 从parse_patent_html获取的pdf链接
            save_path (str): PDF保存目录(默认当前目录下的pdfs文件夹)
            filename (str): 自定义文件名(默认使用专利号)

        返回:
            (bool, str): (是否成功, 文件路径或错误信息)
        """
        # 处理SSL证书验证问题(可选)
        ssl._create_default_https_context = ssl._create_unverified_context

        try:
            # 创建保存目录
            os.makedirs(save_path, exist_ok=True)

            # 生成文件名
            if not filename:
                patent_number = pdf_link.split('/')[-1].replace('.pdf', '')
                filename = f"{patent_number}.pdf"

            # 过滤非法字符
            clean_filename = "".join([c for c in filename if c not in r'<>:"/\|?*'])
            full_path = os.path.join(save_path, clean_filename)

            # 复用代理配置
            proxy = {
                'http': 'http://127.0.0.1:10809',
                'https': 'http://127.0.0.1:10809'
            }
            proxy_handler = ProxyHandler(proxy)
            opener = build_opener(proxy_handler)

            # 设置请求头
            req = Request(pdf_link, headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Accept': 'application/pdf'
            })

            # 发起请求
            response = opener.open(req)

            # 保存文件
            with open(full_path, 'wb') as f:
                f.write(response.read())

            return True, full_path

        except HTTPError as e:
            return False, f"HTTP Error {e.code}"
        except Exception as e:
            return False, f"Error: {str(e)}"