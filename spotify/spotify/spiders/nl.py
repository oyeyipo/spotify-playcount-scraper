import scrapy


class NlSpider(scrapy.Spider):
    name = "nl"
    allowed_domains = ["nairaland.com"]
    start_urls = ["https://www.nairaland.com/"]

    def parse(self, response):
        featured = response.css("td.featured")
        for index, item in enumerate(featured.css("a")):
            headline = "".join(item.css(":text").getall())
            self.log(f"{index} -> {headline}")
