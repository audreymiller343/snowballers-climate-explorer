import requests
from collections.abc import MutableMapping
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

class HTTPSStore(MutableMapping):
    def __init__(self, uri):
        self.url = uri.replace('gs://', 'https://storage.googleapis.com/').rstrip('/')
        self.session = requests.Session()
        self.session.mount('https://', HTTPAdapter(max_retries=Retry(total=5, backoff_factor=1, status_forcelist=[429,500,502,503,504]), pool_maxsize=12))
    def __getitem__(self, key):
        response = self.session.get(f'{self.url}/{key}', timeout=120)
        if response.status_code == 404:
            raise KeyError(key)
        response.raise_for_status()
        return response.content
    def __iter__(self):
        return iter(['.zmetadata'])
    def __len__(self):
        return 1
    def __setitem__(self, key, value):
        raise TypeError('Read-only public data')
    def __delitem__(self, key):
        raise TypeError('Read-only public data')

EXPERIMENTS = ['historical', 'ssp126', 'ssp245', 'ssp585']

def run():
    from process_seasonal import run as seasonal_run
    seasonal_run()

if __name__ == '__main__':
    run()
