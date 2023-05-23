import scrapy
from onesearch_scrape.items import PilotTestItem
from scrapy.loader import ItemLoader


class PilotTestSpider(scrapy.Spider):
    name = "pilot_test"
    custom_settings = {
        'FEEDS': {
            'pilot_test_result.jsonl': {
                'format': 'jsonlines',
                'overwrite': False
            }
        }
    }
    allowed_domains = ["onesearch.id"]
    start_urls = ["https://onesearch.id/Search/Results?type=AllFields&filter%5B%5D=format%3A%22Thesis%3ABachelors%22&filter%5B%5D=publishDate%3A%222022%22"]

    def parse(self, response):
        print(response.url)
        # get all document link in a page
        for doc_link in response.css('table.w-100 tr:nth-child(2) a::attr(href)').getall():
            yield response.follow(doc_link, callback=self.parse_document_page)
        
        # TODO: Handle Pagination link
        # this is a bit dumb...
        pagination_link_selector = "ul.pagination li:nth-last-child(2) a::text"
        pagination_link = response.css(pagination_link_selector).get()
        # print(pagination_link)
        if("Next" in pagination_link):
            pagination_link_href_selector = "ul.pagination li:nth-last-child(2) a::attr(href)"
            pagination_link_href = response.css(pagination_link_href_selector).get()
            yield response.follow(pagination_link_href, callback=self.parse)
    
    def parse_document_page(self, response):
        title_selector = "div.col-sm-9 h3::text"
        author_selector = "span[property='author'] a::text"
        pub_year_selector = "span[property='publicationDate']::text"
        institution_selector = ".table-holding tr:nth-child(3) td::text"

        # TODO: get the above 4 elements
        title = response.css(title_selector).get()
        author = response.css(author_selector).get()
        pub_year = response.css(pub_year_selector).get()
        institution = response.css(institution_selector).get()

        # Change url to /AjaxTab
        tab_url = f"{response.url}/AjaxTab"

        # POST request to the ajaxtab, sending {"tab": "toc"}
        yield scrapy.FormRequest(tab_url, formdata={"tab": "toc"}, callback=self.parse_abstract_from_toc, cb_kwargs={"title": title, "author": author, "pub_year": pub_year, "institution": institution})

    
    def parse_abstract_from_toc(self, response, **kwargs):
        # Check if abstract is here
        abstract_toc_selector = "ul.toc li:first-child::text"
        abstract_found = False
        abstract = response.css(abstract_toc_selector).get()

        if(abstract):
            kwargs["abstract"] = abstract
            kwargs["is_xml"] = 0
            abstract_found = True

        # if not, send {"tab": "details"} and get the full XML in 'fullrecord' for cleaning later
        kwargs["abstract_found"] = abstract_found # another way to do this???
        yield scrapy.FormRequest(response.url, formdata={"tab": "details"}, callback=self.parse_xml_from_details, cb_kwargs=kwargs)

    def parse_xml_from_details(self, response, **kwargs):
        if(not kwargs["abstract_found"]): # another way to do this???
            fullrecord_xml_selector = "table tr:nth-child(2) td::text"
            fullrecord_xml = response.css(fullrecord_xml_selector).get()
            kwargs["abstract"] = fullrecord_xml
            kwargs["is_xml"] = 1
        # print(kwargs)
        item = PilotTestItem()
        item['title'] = kwargs["title"]
        item['author'] = kwargs["author"]
        item['published_year'] = kwargs["pub_year"]
        item['institution'] = kwargs["institution"]
        item['abstract_text'] = kwargs["abstract"]
        item['is_xml'] = kwargs["is_xml"]
        # print("Item created?")
        yield item

    # def load_items(self, response, **kwargs):
        
        


