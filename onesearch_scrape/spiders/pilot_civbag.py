import json
import scrapy
import xml.etree.ElementTree as ET


class PilotCivbag(scrapy.Spider):
    name = 'pilot_civbag'
    start_urls = ["https://onesearch.id/Search/Results?type=AllFields&filter%5B%5D=format%3A%22Thesis%3ABachelors%22&filter%5B%5D=publishDate%3A%222022%22&page=" + str(n+1) for n in range(246)]

    def parse(self, res):
        print(f'INGFOO: KITA SAMPAI {res.url[-3:]}')
        ios = res.css('table.w-100 tr:nth-child(2) a::attr(href)').getall()
        ios = ["https://onesearch.id" + a + "/AjaxTab" for a in ios]
        for a in ios:
            yield scrapy.FormRequest(a, formdata={'tab': 'details'}, callback=self.parse_document_page)

        # for title in res.css('.oxy-post-title'):
        #     yield {'title': title.css('::text').get()}

        # for next_page in res.css('a.next'):
        #     yield res.follow(next_page, self.parse)

    def parse_document_page(self, res):
        td = res.css('td::text')[2].getall()
        td = [t.strip() for t in td][0]
        # th = [t for t in th if 'fullrecord' in t]
        data = {
            'title': self.get_text_from_tag(td, 'title'),
            'date': self.get_text_from_tag(td, 'date'),
            'abstract': self.get_text_from_tag(td, 'abstract'),
            'description': self.get_text_from_tag(td, 'description')
        }
        # print(data)
        yield data
    
    def get_text_from_tag(self, html, tag):
        opening = f'<{tag}>'
        closing = f'</{tag}>'
        if not opening in html:
            return ''
        cut1 = html.split(opening)[1]
        cut2 = cut1.split(closing)[0]
        return cut2
