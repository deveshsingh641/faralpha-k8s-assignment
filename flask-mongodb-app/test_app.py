import unittest
from unittest.mock import MagicMock, patch
from app import app

class FlaskAppTestCase(unittest.TestCase):
    def setUp(self):
        app.config['TESTING'] = True
        self.client = app.test_client()

    def test_index_route(self):
        """Test GET / returns welcome message with current time"""
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Welcome to the Flask app! The current time is:", response.data)

    @patch('app.collection')
    def test_get_data_route(self, mock_collection):
        """Test GET /data retrieves records excluding _id"""
        mock_collection.find.return_value = [{"sampleKey": "sampleValue"}]
        response = self.client.get('/data')
        self.assertEqual(response.status_code, 200)
        json_data = response.get_json()
        self.assertEqual(len(json_data), 1)
        self.assertEqual(json_data[0]["sampleKey"], "sampleValue")

    @patch('app.collection')
    def test_post_data_route(self, mock_collection):
        """Test POST /data inserts document and returns 201"""
        mock_collection.insert_one.return_value = MagicMock(inserted_id="mock_id_123")
        payload = {"sampleKey": "sampleValue"}
        response = self.client.post('/data', json=payload)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.get_json(), {"status": "Data inserted"})

    @patch('app.client')
    def test_health_check_healthy(self, mock_client):
        """Test GET /health returns 200 when database is responsive"""
        mock_client.admin.command.return_value = {"ok": 1.0}
        response = self.client.get('/health')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["status"], "healthy")

if __name__ == '__main__':
    unittest.main()

