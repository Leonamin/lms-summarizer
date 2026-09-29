import unittest

from src.core.runtime.executor import ai_error_code


class _Status(Exception):
    def __init__(self, status_code):
        super().__init__('boom')
        self.status_code = status_code


class _Genai(Exception):
    """google-genai APIError exposes `code` (int) and `status` (name)."""

    def __init__(self, code, status):
        super().__init__('boom')
        self.code = code
        self.status = status


class AiErrorCodeTests(unittest.TestCase):
    def test_http_status_mapping(self):
        self.assertEqual(ai_error_code(_Status(429)), 'ai_quota')
        self.assertEqual(ai_error_code(_Status(401)), 'ai_auth')
        self.assertEqual(ai_error_code(_Status(403)), 'ai_auth')
        self.assertEqual(ai_error_code(_Status(503)), 'ai_unavailable')
        self.assertEqual(ai_error_code(_Status(500)), 'ai_unavailable')
        self.assertEqual(ai_error_code(_Status(400)), 'stage_failed')

    def test_genai_style_errors(self):
        self.assertEqual(ai_error_code(_Genai(503, 'UNAVAILABLE')), 'ai_unavailable')
        self.assertEqual(ai_error_code(_Genai(429, 'RESOURCE_EXHAUSTED')), 'ai_quota')
        self.assertEqual(ai_error_code(_Genai(403, 'PERMISSION_DENIED')), 'ai_auth')

    def test_timeout_and_connection(self):
        class APITimeoutError(Exception):
            pass

        class APIConnectionError(Exception):
            pass

        self.assertEqual(ai_error_code(APITimeoutError()), 'ai_timeout')
        self.assertEqual(ai_error_code(APIConnectionError()), 'ai_unavailable')

    def test_unknown_is_generic(self):
        self.assertEqual(ai_error_code(ValueError('nope')), 'stage_failed')


if __name__ == '__main__':
    unittest.main()
