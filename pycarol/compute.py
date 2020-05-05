import requests

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



    def create_job(self):
        pass
