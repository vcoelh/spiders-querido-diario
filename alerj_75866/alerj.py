from re import findall
from sys import path
from time import sleep
from os.path import abspath, dirname
from typing import Tuple

DAGS_FOLDER = dirname(dirname(dirname(abspath(__file__))))
path.insert(0, DAGS_FOLDER)

from pandas import concat, DataFrame

from single_scrapers.util.browser import LocalBrowser
from single_scrapers.util.path import make_path
from single_scrapers.util.reader import request_order
from single_scrapers.util.scraper import BaseScraper
from single_scrapers.util.writer import schematize_and_export

class AlerjScraper(BaseScraper):
    informant_codes = ['75866']
    domain = 'www.alerj.rj.gov.br'
    name = 'alerj'
    delay = 0
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
    def _get_text(self)-> str:
        elements = self.driver.find_elements(
            'css selector',
            '.margintop11:nth-child(12) , .margintop11:nth-child(11)'
        )
        texts = [e.text for e in elements]
        return texts
    
    def _get_faixa_and_price(self, texts):
        for text in texts:
            match = findall(r'(Faixa V|Faixa VI)\s*–\s*R\$\s*([\d.,]+)', text)
            if match:
                faixa, price = match[0]
                yield faixa, price
   
    def _screenshot(self, aux: DataFrame, output_path):    
        filename = f'{output_path}/prints/{("_").join(aux)}.png'
            
        self.driver.execute_script('document.body.style.zoom=0.83')
        self.driver.save_screenshot(filename)
        self.driver.execute_script('document.body.style.zoom=1')
    
    def collect(self, dataframe: DataFrame, output_path: str):
        dataframe["REFERENCE"] = dataframe[
            'DS_SINO_NOME_INS_INSINF'
            ].str.extract(r'(FAIXA VI|FAIXA V)')
        dfs = []
        self.driver = LocalBrowser(
            'Chrome', optional_args=['--start-maximized', '--headless'])()
        
        url = dataframe['URL'].iloc[0]
        self.driver.get(url)
        sleep(1.5)
        texts = self._get_text()
        self._screenshot(output_path=output_path ,
                         aux=dataframe['NR_SEQ_INSINF'])
        self.driver.quit()
        
        for faixa, price in self._get_faixa_and_price(texts):
            print(faixa.upper())
            aux = dataframe[
                dataframe['REFERENCE'] == faixa.upper()
            ]
            aux['preco_coleta'] = price 
            dfs.append(aux)
        collect = concat(dfs, ignore_index=True)
        return collect

if __name__ == "__main__":
    scraper = AlerjScraper()
    name = str(scraper)
    output_path = make_path(name)
    dataframe = request_order(scraper.informant_codes, delay=scraper.delay, date_filter=False)
    dataframe = scraper.collect(dataframe, output_path)
    schematize_and_export(dataframe, name.lower(), output_path)
            