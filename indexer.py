import requests
import posixpath

class Indexer(object):
    def __init__(self, logger=None):
        self.logger = logger

    def get_services(self, url):
        response = requests.get(url, params=dict(f='json'))
        self.logger.debug('HTTP %s %s: %s', response.request.method, response.url, response.status_code)
        response.raise_for_status()
        data = response.json()

        version = data.get('currentVersion')
        if not version:
            raise ValueError("No currentVersion in the response JSON. Is this an Esri URL?")
        else:
            self.logger.debug("Esri server version %s", version)

        services = data.get('services')
        if services is None:
            raise ValueError("No services in response JSON. Is this a /services URL?")

        for service in services:
            if not service.get('url'):
                service['url'] = posixpath.join(url, service.get('name'), service.get('type'))

        folders = data.get('folders', [])
        for folder in folders:
            folder_url = posixpath.join(url, folder)
            services_to_add = self.get_services(folder_url)
            services.extend(services_to_add)

        return services

    def get_service_details(self, service_url):
        response = requests.get(service_url, params=dict(f='json'))
        self.logger.debug('HTTP %s %s: %s', response.request.method, response.url, response.status_code)
        response.raise_for_status()
        return response.json()

if __name__ == '__main__':
    import argparse
    import logging

    parser = argparse.ArgumentParser()
    parser.add_argument('service', help="Service URL(s)")
    args = parser.parse_args()

    logger = logging.getLogger('indexer')
    logger.setLevel(logging.INFO)
    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    ch.setFormatter(formatter)
    logger.addHandler(ch)

    indexer = Indexer(logger)
    services = indexer.get_services(args.service)

    for service in services:
        details = indexer.get_service_details(service.get('url'))
        print("{} Name: {}".format(service.get('type'), service.get('name')))

        for layer in details.get('layers', []):
            print("    Layer {}: {}".format(layer.get('id'), layer.get('name')))
