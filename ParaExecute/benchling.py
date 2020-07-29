import requests
import json


def api_get(domain, api_key, path, params={}):
    url = "https://{}/api/v2/{}".format(domain, path)
    rv = requests.get(url, auth=(api_key, ""), params=params)
    if rv.status_code >= 400:
        raise Exception(
            "Server returned status {}. Response:\n{}".format(
                rv.status_code, json.dumps(rv.json())
            )
        )
    return rv.json()


def api_post(domain, api_key, path, payload={}):
    url = "https://{}/api/v2/{}".format(domain, path)
    rv = requests.post(url, auth=(api_key, ""), json=payload, verify=True)
    if rv.status_code >= 400:
        raise Exception(
            "Server returned status {}. Response:\n{}".format(
                rv.status_code, json.dumps(rv.json())
            )
        )
    return rv.json()


def api_patch(domain, api_key, path, payload={}):
    url = "https://{}/api/v2/{}".format(domain, path)
    rv = requests.patch(url, auth=(api_key, ""), json=payload, verify=True)
    if rv.status_code >= 400:
        raise Exception(
            "Server returned status {}. Response:\n{}".format(
                rv.status_code, json.dumps(rv.json())
            )
        )
    return rv.json()
