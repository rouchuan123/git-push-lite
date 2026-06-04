import unittest

from github_hq.url_validation import is_github_remote_url, normalize_github_remote_url


class GitHubUrlValidationTests(unittest.TestCase):
    def test_accepts_https_urls(self):
        self.assertTrue(is_github_remote_url("https://github.com/octo/repo"))
        self.assertTrue(is_github_remote_url("https://github.com/octo/repo.git"))

    def test_accepts_ssh_urls(self):
        self.assertTrue(is_github_remote_url("git@github.com:octo/repo"))
        self.assertTrue(is_github_remote_url("git@github.com:octo/repo.git"))

    def test_rejects_non_github_urls(self):
        self.assertFalse(is_github_remote_url("https://gitlab.com/octo/repo.git"))
        self.assertFalse(is_github_remote_url("git@example.com:octo/repo.git"))
        self.assertFalse(is_github_remote_url(""))

    def test_normalizes_trailing_slash(self):
        self.assertEqual(
            normalize_github_remote_url("https://github.com/octo/repo.git/"),
            "https://github.com/octo/repo.git",
        )


if __name__ == "__main__":
    unittest.main()
