from benchling import api_post, api_get, api_patch
import requests
import json


def main():
    folder_path = './Data/C'  # Move the path of the json file that you want.
    with open(folder_path + '/benchling_run_test.json', 'r') as file:
        data = json.load(file)
        keys = data.keys()
        keys = list(keys)

# now i want to upload on benchling
    domain = 'multiplylabstest.benchling.com'
    api_key = 'sk_pLytaKiuqk6D6draYkwwK3Yq8KNPe'  
    fede_folder = api_get(domain, api_key, 'folders', params={"nameIncludes": "Federico"})
    fede_folder = fede_folder["folders"]
    fede_proj_id = fede_folder[0]["projectId"]
    response = api_get(domain, api_key, 'assay-schemas')
    # print(json.dumps(response, indent=2))
    idassay = "assaysch_XTyEtiJ4"
    response = api_get(domain, api_key, 'assay-runs', params={"schemaId": idassay})
    # print(json.dumps(response, indent=2))
    runid_fede = "19e3c601-3dfb-408f-ad25-8bc3665ccf46"  # this is the run id associated to the my run
    # you can see uncomment the line 23 and see your run
    reading = api_get(domain, api_key,
                      'assay-runs/{}'.format(runid_fede))
    print(json.dumps(reading, indent=2))
    patch = api_patch(domain, api_key,
                      'assay-runs/{}'.format(runid_fede),
                      {
                          "fields": {
                              "barcode": {"value": data["barcode"]},
                              "temp": {"value": data["temp"]},
                              "status": {"value": data["status"]},
                              }
                      }
                      )


if __name__ == "__main__":
    main()
