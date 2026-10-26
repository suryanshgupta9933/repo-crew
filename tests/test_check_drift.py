import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "skills" / "repo-crew" / "scripts"))

from check_drift import glob_to_regex, parse_frontmatter


class GlobToRegex(unittest.TestCase):
    def test_matches_plain_paths(self):
        self.assertTrue(glob_to_regex("src/**").match("src/app/page.tsx"))
        self.assertFalse(glob_to_regex("src/**").match("docs/crew/ROSTER.md"))

    def test_strips_only_a_leading_dot_slash(self):
        # lstrip("./") would eat the leading dot of a dot-directory and make
        # .claude-plugin/** match nothing at all.
        self.assertTrue(glob_to_regex(".claude-plugin/**").match(".claude-plugin/plugin.json"))
        self.assertTrue(glob_to_regex(".github/workflows/**").match(".github/workflows/validate.yml"))
        self.assertTrue(glob_to_regex("./src/**").match("src/app/page.tsx"))

    def test_star_does_not_cross_directories(self):
        self.assertFalse(glob_to_regex("src/*.ts").match("src/app/page.tsx"))
        self.assertTrue(glob_to_regex("src/*.ts").match("src/main.ts"))

    def test_trailing_slash_covers_the_directory(self):
        self.assertTrue(glob_to_regex("supabase/").match("supabase/migrations/001.sql"))

    def test_globs_are_anchored_to_the_repo_root(self):
        # covers: patterns are repo-relative, so a bare name means the root.
        self.assertTrue(glob_to_regex("plugin.json").match("plugin.json"))
        self.assertFalse(glob_to_regex("plugin.json").match(".claude-plugin/plugin.json"))


class ParseFrontmatter(unittest.TestCase):
    def test_reads_a_glob_list(self):
        fm = parse_frontmatter("---\ncovers:\n  - src/**\n  - docs/crew/**\nverified_at: abc123\n---\nbody\n")
        self.assertEqual(fm["covers"], ["src/**", "docs/crew/**"])
        self.assertEqual(fm["verified_at"], "abc123")

    def test_reads_a_single_cover_written_inline(self):
        fm = parse_frontmatter("---\ncovers: src/**\n---\n")
        self.assertEqual(fm["covers"], "src/**")

    def test_no_frontmatter_is_empty(self):
        self.assertEqual(parse_frontmatter("no frontmatter here\n"), {})


if __name__ == "__main__":
    unittest.main()
