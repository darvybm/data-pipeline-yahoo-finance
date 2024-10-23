import requests
from requests.auth import HTTPBasicAuth
from airflow.exceptions import AirflowException
import time

class AirbyteSync:
    """
    Clase para manejar la sincronización de datos utilizando Airbyte.

    Esta clase permite disparar un trabajo de sincronización en Airbyte y
    monitorizar su estado hasta que se complete o falle.

    Attributes:
        airbyte_host (str): URL del servidor Airbyte.
        connection_id (str): ID de la conexión de Airbyte a utilizar.
        auth (HTTPBasicAuth): Credenciales de autenticación para Airbyte.
    """
    def __init__(self, airbyte_host, connection_id, username, password):
        self.airbyte_host = airbyte_host
        self.connection_id = connection_id
        self.auth = HTTPBasicAuth(username, password)

    def trigger_sync(self):
        """
        Dispara un trabajo de sincronización en Airbyte.

        Envía una solicitud POST a Airbyte para iniciar la sincronización y espera
        a que se complete. Si ocurre un error en la solicitud o en la sincronización,
        se lanza una excepción AirflowException.

        Raises:
            AirflowException: Si la sincronización falla o si no se puede obtener el ID del trabajo.
        """
        url = f"{self.airbyte_host}/api/v1/connections/sync"
        payload = {"connectionId": self.connection_id}

        try:
            response = requests.post(url, json=payload, auth=self.auth)
            response.raise_for_status()
            job_info = response.json()
            job_id = job_info.get('job', {}).get('id')

            if not job_id:
                raise AirflowException("Failed to retrieve job ID after triggering sync.")

            self._wait_for_sync_completion(job_id)
        except requests.exceptions.RequestException as e:
            raise AirflowException(f"Failed to trigger Airbyte sync: {str(e)}")

    def _wait_for_sync_completion(self, job_id):
        """
        Espera hasta que se complete el trabajo de sincronización.

        Consulta periódicamente el estado del trabajo de Airbyte utilizando su ID.
        Si el trabajo falla o excede el tiempo máximo de espera, se lanza una excepción.

        Args:
            job_id (str): ID del trabajo de Airbyte a monitorizar.

        Raises:
            AirflowException: Si el trabajo falla o se excede el tiempo máximo de espera.
        """
        url = f"{self.airbyte_host}/api/public/v1/jobs/{job_id}"
        max_wait_time = 1800
        start_time = time.time()
        wait_time = 5

        while True:
            try:
                response = requests.get(url, auth=self.auth)
                response.raise_for_status()
                status = response.json()['status']

                if status == "succeeded":
                    return
                elif status == "failed":
                    raise AirflowException(f"Airbyte job {job_id} failed.")
            except requests.exceptions.RequestException as e:
                raise AirflowException(f"Failed to get job status: {str(e)}")

            elapsed_time = time.time() - start_time
            if elapsed_time > max_wait_time:
                raise AirflowException(f"Max wait time of {max_wait_time} seconds exceeded for job {job_id}.")

            time.sleep(wait_time)