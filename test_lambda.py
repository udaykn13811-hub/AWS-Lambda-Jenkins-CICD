

import io
import unittest
from unittest.mock import patch
import os

os.environ["OUTPUT_BUCKET"] = "aa-lambda-processed-files-2026"
os.environ["AWS_EC2_METADATA_DISABLED"] = "true"

import lambda_function


class TestLambda(unittest.TestCase):

    @patch("lambda_function.s3.put_object")
    @patch("lambda_function.s3.get_object")
    def test_csv_processing(self, mock_get, mock_put):

        csv_data = (
            "name,email\n"
            "John,john@GMAIL.COM\n"
            ",invalid@gmail.com\n"
            "David,david@gmail.com\n"
        )

        mock_get.return_value = {
            "Body": io.BytesIO(csv_data.encode())
        }

        event = {
            "Records": [{
                "s3": {
                    "bucket": {
                        "name": "aa-lambda-raw-files-2026"
                    },
                    "object": {
                        "key": "uploads/sample.csv"
                    }
                }
            }]
        }

        result = lambda_function.lambda_handler(
            event, None
        )

        self.assertEqual(result["statusCode"], 200)

        mock_put.assert_called_once()

        saved_data = mock_put.call_args.kwargs["Body"].decode()

        self.assertIn("john@gmail.com", saved_data)
        self.assertIn("david@gmail.com", saved_data)
        self.assertNotIn("invalid@gmail.com", saved_data)


if __name__ == "__main__":
    unittest.main()
