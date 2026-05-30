from locust import HttpUser, task, between

class APIUser(HttpUser):
    # Simula un ritardo umano tra 1 e 5 secondi per ogni richiesta
    wait_time = between(1, 5)

    @task
    def analyze_endpoint(self):
        """
        Simula una richiesta di ingestion all'endpoint principale.
        In uno scenario reale, la pipeline di test verrebbe agganciata
        ad Azure Load Testing per verificare il behavior dell'Auto-Scaling.
        """
        self.client.post(
            "/api/v1/analyze", 
            json={"target_url": "https://linkedin.com/in/loadtest-account"}
        )
