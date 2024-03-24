from datetime import date, datetime
from re import findall

import scrapy

from gazette.items import Gazette
from gazette.spiders.base import BaseGazetteSpider


class ValeGazetteSpider(BaseGazetteSpider):
    """
    Base spider for cities using the Framework Vale as design system.
    """

    def start_requests(self):
        yield scrapy.Request(url=self._get_url(page=1))

    def _get_url(self, page=1):
        url = (
            f"https://{self.allowed_domains[0]}/"
            f"diariooficial/pesquisa/all/all/all/all/{page}"
        )
        return url

    def _get_gazette_date(self, gazette):
        MONTHS = {
            "janeiro": "01",
            "fevereiro": "02",
            "março": "03",
            "abril": "04",
            "maio": "05",
            "junho": "06",
            "julho": "07",
            "agosto": "08",
            "setembro": "09",
            "outubro": "10",
            "novembro": "11",
            "dezembro": "12",
        }

        website_date_text = gazette.xpath(
            '//*[contains(text(), "Publicado")]/text()'
        ).get()
        [day, month, year] = findall(r", (.*) de (.*) de (.*)", website_date_text)[0]
        datetime_date = date(int(year), int(MONTHS[month]), int(day))
        return datetime_date

    def parse(self, response):
        gazettes = response.css(".ant-list-item")

        for gazette in gazettes:
            gazette_date = self._get_gazette_date(gazette)
            file_url = gazette.css("a ::attr(href)").get()
            edition_text = ''.join(
                gazette.css(".edition-number ::text").getall())
            edition_number = findall(r'(\d+)', edition_text)[0]
            is_extra_edition = "Extra" in edition_text

            yield Gazette(
                date=gazette_date,
                file_url=[file_url],
                edition_number=edition_number,
                is_extra_edition=is_extra_edition,
                power="executive",
            )
        last_page = response.css('[title="Última página"] ::attr(href)').get()
        if last_page == response.url:
            return
        else:
            current_page = findall("/(\d+)", response.url)[0]
            next_page = int(current_page) + 1
            yield scrapy.Request(self._get_url(page=next_page), callback=self.parse)
            