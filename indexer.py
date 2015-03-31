import requests

def get_services(url_base, path=None):
    url = url_base

    if path:
        url += '/' + path

    response = requests.get(url, params=dict(f='json'))
    print response.url, response.status_code
    response.raise_for_status()
    data = response.json()

    services = data.get('services')

    for service in services:
        if not service.get('url'):
            service['url'] = url_base + '/' + service.get('name') + '/' + service.get('type')

    folders = data.get('folders', [])
    for folder in folders:
        services_to_add = get_services(url_base, folder)
        services.extend(services_to_add)

    return services

def get_service_details(service_url):
    response = requests.get(service_url, params=dict(f='json'))
    # print response.url, response.status_code
    response.raise_for_status()
    return response.json()

if __name__ == '__main__':
    services = get_services('http://www.geostor.arkansas.gov/arcgis/rest/services')

    for service in services:
        print service
        details = get_service_details(service.get('url'))
        print "{} Name: {}".format(service.get('type'), service.get('name'))

        for layer in details.get('layers', []):
            print "    Layer {}: {}".format(layer.get('id'), layer.get('name'))
