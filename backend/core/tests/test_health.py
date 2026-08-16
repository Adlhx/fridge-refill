from django.test import TestCase


class HealthCheckTests(TestCase):
    def test_status_page_reports_server_and_database(self):
        response = self.client.get('/')

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Running successfully')
        self.assertContains(response, 'Connected successfully')

    def test_health_endpoint_returns_machine_readable_status(self):
        response = self.client.get('/health/')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {
            'status': 'ok',
            'server': 'running',
            'database': 'connected',
        })
