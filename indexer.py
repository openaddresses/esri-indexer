import requests

class Indexer(object):
    def __init__(self, logger=None):
        self.logger = logger

    def get_services(self, url_base, path=None):
        url = url_base

        if path:
            url += '/' + path

        response = requests.get(url, params=dict(f='json'))
        self.logger.debug('HTTP %s %s: %s', response.request.method, response.url, response.status_code)
        response.raise_for_status()
        data = response.json()

        services = data.get('services')

        for service in services:
            if not service.get('url'):
                service['url'] = url_base + '/' + service.get('name') + '/' + service.get('type')

        folders = data.get('folders', [])
        for folder in folders:
            services_to_add = self.get_services(url_base, folder)
            services.extend(services_to_add)

        return services

    def get_service_details(self, service_url):
        response = requests.get(service_url, params=dict(f='json'))
        self.logger.debug('HTTP %s %s: %s', response.request.method, response.url, response.status_code)
        response.raise_for_status()
        return response.json()

if __name__ == '__main__':
    indexer = Indexer()
    services = indexer.get_services('http://www.geostor.arkansas.gov/arcgis/rest/services')

    for service in services:
        print(service)
        details = indexer.get_service_details(service.get('url'))
        print("{} Name: {}".format(service.get('type'), service.get('name')))

        for layer in details.get('layers', []):
            print("    Layer {}: {}".format(layer.get('id'), layer.get('name')))
