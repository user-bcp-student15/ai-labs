import os

TEST_TOKEN_SECRET = "test-only-secret-with-32-bytes-or-more"

os.environ["AUTH_TOKEN_SECRET"] = TEST_TOKEN_SECRET
