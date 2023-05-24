# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy


class PilotTestItem(scrapy.Item):
    title = scrapy.Field()
    author = scrapy.Field()
    published_year = scrapy.Field()
    institution = scrapy.Field()
    abstract_text = scrapy.Field()
    url = scrapy.Field()

class CompleteDataItem(scrapy.Item):
    title = scrapy.Field()
    author = scrapy.Field()
    published_year = scrapy.Field()
    institution = scrapy.Field()
    abstract_text = scrapy.Field()
    is_xml = scrapy.Field()
    subject_area = scrapy.Field()
    topic = scrapy.Field()
    language = scrapy.Field()
