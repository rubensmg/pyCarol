import requests
import os
class Compute:

    """
    Compute.

    """

    def __init__(self, carol):
        self.carol = carol

    def get_machine_types(self):

        response = self.carol.call_api(path=f'v1/compute/machineTypes',
                                       method='GET')

        return response


    def create_job(self, name,tenant,  env, image, labels, type, preemptible=False ):
        payload = {
            "env": env,
            "image": image,
            "labels": labels,
            "name": name,
            "preemptible": preemptible,
            "tenant": tenant,
            "type": type
        }

        headers = {"x-auth-token": os.environ['OPERATORTOKEN']}

        url = 'https://api.operator.qarol.ai/api/batches'
        r = requests.request('POST', url=url, headers=headers, json=payload)

        return r.json()

    def track_process(self, uri):

        headers = {"x-auth-token": os.environ['OPERATORTOKEN']}

        url = f'https://api.operator.qarol.ai{uri}'
        r = requests.request('GET', url=url, headers=headers)
        return r.json()
