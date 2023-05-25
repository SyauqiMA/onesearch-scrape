import scrapy
from onesearch_scrape.items import PilotTestItem
import pandas as pd
import xml.etree.ElementTree as ET


class PilotTestSpider(scrapy.Spider):
    name = "pilot_test"
    custom_settings = {
        'FEEDS': {
            'data_storage/pilot_test_result.jsonl': {
                'format': 'jsonlines',
                'overwrite': True
            }
        },
        'LOG_LEVEL': 'ERROR',
        'AUTOTHROTTLE_TARGET_CONCURRENCY': 20,
        'AUTOTHROTTLE_START_DELAY': 1
    }
    page_amount = 246
    allowed_domains = ["onesearch.id"]
    start_urls = (f"https://onesearch.id/Search/Results?type=AllFields&filter%5B%5D=format%3A%22Thesis%3ABachelors%22&filter%5B%5D=publishDate%3A%222022%22&page={i+1}" for i in range(0, page_amount, 12))

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
        raw_html = response.body
        df = pd.read_html(raw_html, index_col=0)[0].transpose()
        item = PilotTestItem()

        item["title"] = df['title'].values[0] if 'title' in df.columns else "None"
        item["author"] = df['author'].values[0] if 'author' in df.columns else "None"
        item["published_year"] = df['publishDate'].values[0] if 'publishDate' in df.columns else "None"
        item["institution"] = df['institution'].values[0] if 'institution' in df.columns else "None"
        item["abstract_text"] = self.get_abstract(df)
        item["url"] = kwargs['ios_link']

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