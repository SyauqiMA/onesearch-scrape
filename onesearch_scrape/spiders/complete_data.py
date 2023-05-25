import scrapy
from onesearch_scrape.items import CompleteDataItem
import pandas as pd
import xml.etree.ElementTree as ET
import re


class CompleteDataSpider(scrapy.Spider):
    name = "complete_data"
    custom_settings = {
        'FEEDS': {
            'data_storage/data_result_final_test.jsonl': {
                'format': 'jsonlines',
                'overwrite': False
            }
        },
        'LOG_LEVEL': 'ERROR',
        'LOG_FILE': 'spider_logs/complete_dataspider.log',
        # 'CONCURRENT_REQUESTS': 200,
        # 'DOWNLOAD_DELAY': 0.2,
        # 'AUTOTHROTTLE_ENABLED': False,
        'AUTOTHROTTLE_TARGET_CONCURRENCY': 10.0,
        # 'HTTPCACHE_IGNORE_MISSING': True,
        'AUTOTHROTTLE_START_DELAY': 1
    }

    PAGE_AMOUNT = 41678 # look at the target url

    allowed_domains = ["onesearch.id"]
    start_urls = [f"https://onesearch.id/Search/Results?type=AllFields&filter%5B%5D=format%3A%22Thesis%3ABachelors%22&page={i+1}" for i in range(0, PAGE_AMOUNT, PAGE_AMOUNT // 4100)]

    def parse(self, response):
        print(f'Scraping page {response.url}...')

        # get all document link in a page
        ios_number_links = response.css('table.w-100 tr:nth-child(2) a::attr(href)').getall()

        for doc_link in ios_number_links:
            ajax_tab_link = "https://onesearch.id" + doc_link + "/AjaxTab"
            yield scrapy.FormRequest(ajax_tab_link,
                                     formdata={"tab": "details"},
                                     callback=self.parse_ajax_tab,
                                     cb_kwargs={'ios_link': doc_link})
        
        # Handle Pagination link
        pagination_link_selector = "ul.pagination li:nth-last-child(2) a::text"
        pagination_link = response.css(pagination_link_selector).get()
        # print(pagination_link)
        if("Next" in pagination_link):
            pagination_link_href_selector = "ul.pagination li:nth-last-child(2) a::attr(href)"
            pagination_link_href = response.css(pagination_link_href_selector).get()
            yield response.follow(pagination_link_href, callback=self.parse)
        

    def parse_ajax_tab(self, response, **kwargs):
        filter_regex = r'[\n\t]+|[ ]{2,}'
        raw_html = response.body
        df = pd.read_html(raw_html, index_col=0)[0].transpose()
        item = CompleteDataItem()

        item["title"] = df['title'].values[0] if 'title' in df.columns else "None"
        item["author"] = df['author'].values[0] if 'author' in df.columns else "None"
        item["published_year"] = df['publishDate'].values[0] if 'publishDate' in df.columns else "None"
        item["institution"] = df['institution'].values[0] if 'institution' in df.columns else "None"
        item["library"] = df['library'].values[0] if 'library' in df.columns else "None"
        item["collection"] = df['collection'].values[0] if 'collection' in df.columns else "None"
        item["abstract_text"] = self.get_abstract(df)
        item["ios_url"] = kwargs['ios_link']
        item["repo_url"] = re.split(filter_regex, df['url'].values[0]) if 'url' in df.columns else "None"
        item["subject_area"] = re.split(filter_regex, df['subject_area'].values[0]) if 'subject_area' in df.columns else "None"
        item["topic"] = re.split(filter_regex, df['topic'].values[0]) if 'topic' in df.columns else "None"
        item["format"] = re.split(filter_regex, df['format'].values[0]) if 'format' in df.columns else "None"
        item["language"] = df['language'].values[0] if 'language' in df.columns else "None"

        yield item

    def get_abstract(self, df: pd.DataFrame):
        fullrecord_xml = ET.fromstring(df['fullrecord'].values[0].strip())
        abstract_tag = fullrecord_xml.find('abstract')
        description_tag = fullrecord_xml.find('description')
        if (abstract_tag is not None):
            return abstract_tag.text
        elif (description_tag is not None):
            return description_tag.text
        else:
            return "None"