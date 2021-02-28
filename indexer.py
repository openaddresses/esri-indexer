import requests
import posixpath


class Indexer(object):
    def __init__(self, logger=None):
        self.logger = logger

    def spider_services(self, url, root_url=None):
        root_url = root_url or url

        # Fetch the metadata for the root URL
        response = requests.get(url, params=dict(f='json'))
        self.logger.debug('HTTP %s %s: %s', response.request.method, response.url, response.status_code)
        response.raise_for_status()
        data = response.json()

        err = data.get('error')
        if err:
            raise ValueError("Server gave error response: %s", err)

        # Build URLs for the services listed at this level
        services = data.get('services')
        if services is None:
            raise ValueError("No services in response JSON. Is this a /services URL?")

        for service in services:
            if not service.get('url'):
                service['url'] = posixpath.join(root_url, service.get('name'), service.get('type'))

        # Recurse into folders
        folders = data.get('folders', [])
        for folder in folders:
            folder_url = posixpath.join(url, folder)
            services_to_add = self.spider_services(folder_url, root_url)
            services.extend(services_to_add)

        return services

    def get_service_details(self, service_url):
        response = requests.get(service_url, params=dict(f='json'))
        self.logger.debug('HTTP %s %s: %s', response.request.method, response.url, response.status_code)
        response.raise_for_status()
        data = response.json()

        err = data.get('error')
        if err:
            raise ValueError("Server gave error response", err)

        return data


if __name__ == '__main__':
    import argparse
    import logging

    parser = argparse.ArgumentParser()
    parser.add_argument('service', help="Service URL(s)")
    args = parser.parse_args()

    logger = logging.getLogger('indexer')
    logger.setLevel(logging.DEBUG)
    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    ch.setFormatter(formatter)
    logger.addHandler(ch)

    indexer = Indexer(logger)
    services = indexer.spider_services(args.service)

    for service in services:
        details = indexer.get_service_details(service.get('url'))
        print("{} Name: {}".format(service.get('type'), service.get('name')))

        for layer in details.get('layers', []):
            print("    Layer {}: {}".format(layer.get('id'), layer.get('name')))
