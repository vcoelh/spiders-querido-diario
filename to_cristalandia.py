from datetime import date

from vale import ValeGazetteSpider


class ToCristalandiaSpider(ValeGazetteSpider):
    TERRITORY_ID = "1706100"
    name = "to_cristalandia"
    allowed_domains = ["diario.cristalandia.to.gov.br"]
    start_date = date(2017, 3, 20)