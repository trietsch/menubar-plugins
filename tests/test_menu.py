import re
from datetime import datetime
from io import StringIO
from unittest.mock import patch

import pytest

from pull_requests.domain import PullRequest, PullRequestStatus, PullRequestsOverview, PullRequestException
from pull_requests.menu import print_xbar_pull_request_menu, sort_pull_requests, print_prs
from pull_requests.config import PullRequestsConstants
from common.icons import Icons


def make_pr(**kwargs) -> PullRequest:
    defaults = dict(
        id="1",
        title="Fix bug",
        slug="my-repo",
        from_ref="feature/branch",
        to_ref="main",
        overall_status=PullRequestStatus.NO_VOTE,
        is_draft=False,
        activity=datetime(2024, 1, 1),
        time_ago="1 day ago",
        all_prs_href="https://example.com/prs",
        href="https://example.com/pr/1",
    )
    defaults.update(kwargs)
    return PullRequest(**defaults)


def capture_menu(overview, statuses=None, sort_on=None, cache_file="/tmp/test.pkl",
                 notifications_enabled=False) -> str:
    from pull_requests.domain import PullRequestSort
    if statuses is None:
        statuses = {s: Icons.PULL_REQUEST for s in PullRequestStatus}
    if sort_on is None:
        sort_on = PullRequestSort.ACTIVITY
    with patch("builtins.open"), patch("pickle.dump"), patch("pickle.load", side_effect=Exception):
        buf = StringIO()
        with patch("builtins.print", side_effect=lambda *a, **kw: buf.write(" ".join(str(x) for x in a) + "\n")):
            print_xbar_pull_request_menu(overview, statuses, sort_on, cache_file, notifications_enabled)
    return buf.getvalue()


class TestSortPullRequests:
    def test_sort_by_activity_most_recent_first(self):
        from pull_requests.domain import PullRequestSort
        pr1 = make_pr(id="1", activity=datetime(2024, 1, 1))
        pr2 = make_pr(id="2", activity=datetime(2024, 3, 1))
        result = sort_pull_requests([pr1, pr2], PullRequestSort.ACTIVITY)
        assert result[0].id == "2"

    def test_sort_by_name(self):
        from pull_requests.domain import PullRequestSort
        pr1 = make_pr(id="1", title="Zebra")
        pr2 = make_pr(id="2", title="Alpha")
        result = sort_pull_requests([pr1, pr2], PullRequestSort.NAME)
        assert result[0].id == "2"


class TestPrintXbarPullRequestMenu:
    def test_zero_prs_prints_zero(self):
        overview = PullRequestsOverview([], [], [])
        output = capture_menu(overview)
        assert output.startswith("0 |")

    def test_zero_prs_shows_celebration(self):
        overview = PullRequestsOverview([], [], [])
        output = capture_menu(overview)
        assert "Nothing to review" in output

    def test_nonzero_prs_shows_count(self):
        pr = make_pr(overall_status=PullRequestStatus.NO_VOTE)
        overview = PullRequestsOverview([pr], [], [])
        output = capture_menu(overview)
        assert output.startswith("1 |")

    def test_exception_only_shows_question_mark(self):
        exc = PullRequestException("gitlab", "misconfigured", None, None)
        overview = PullRequestsOverview([], [], [exc])
        output = capture_menu(overview)
        assert output.startswith("? |")

    def test_exception_message_included(self):
        exc = PullRequestException("gitlab", "misconfigured", None, None)
        overview = PullRequestsOverview([], [], [exc])
        output = capture_menu(overview)
        assert "misconfigured" in output

    def test_reviewing_section_header_present(self):
        pr = make_pr()
        overview = PullRequestsOverview([pr], [], [])
        output = capture_menu(overview)
        assert "Reviewing" in output

    def test_authored_section_header_present(self):
        pr = make_pr()
        overview = PullRequestsOverview([], [pr], [])
        output = capture_menu(overview)
        assert "Authored" in output

    def test_pr_title_in_output(self):
        pr = make_pr(title="My special PR")
        overview = PullRequestsOverview([pr], [], [])
        output = capture_menu(overview)
        assert "My special PR" in output

    def test_draft_prefix(self):
        pr = make_pr(is_draft=True, title="WIP")
        overview = PullRequestsOverview([pr], [], [])
        output = capture_menu(overview)
        assert "[Draft]" in output

    def test_repo_pie_chart_image_present(self):
        pr = make_pr()
        overview = PullRequestsOverview([pr], [], [])
        output = capture_menu(overview)
        assert "image=" in output

    def test_repo_pie_chart_is_svg_base64(self):
        import base64
        pr = make_pr()
        overview = PullRequestsOverview([pr], [], [])
        output = capture_menu(overview)
        match = re.search(r'my-repo \(1\) \| href=\S+ image=(\S+)', output)
        assert match, "repo line with image not found"
        svg = base64.b64decode(match.group(1)).decode()
        assert "<svg" in svg

    def test_multiple_prs_different_statuses_pie_chart(self):
        import base64
        pr1 = make_pr(id="1", overall_status=PullRequestStatus.APPROVED)
        pr2 = make_pr(id="2", overall_status=PullRequestStatus.REJECTED)
        overview = PullRequestsOverview([pr1, pr2], [], [])
        output = capture_menu(overview)
        match = re.search(r'my-repo \(2\) \| href=\S+ image=(\S+)', output)
        assert match
        svg = base64.b64decode(match.group(1)).decode()
        assert "<path" in svg  # multiple colors → paths, not circle
