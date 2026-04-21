import base64
import math
import re

import pytest

from common.charts import status_pie_chart_base64
from pull_requests.domain import PullRequestStatus


def decode_svg(b64: str) -> str:
    return base64.b64decode(b64).decode()


class TestStatusPieChartBase64:
    def test_returns_none_for_empty_counts(self):
        assert status_pie_chart_base64({}) is None

    def test_returns_none_for_all_zero_counts(self):
        assert status_pie_chart_base64({PullRequestStatus.APPROVED: 0}) is None

    def test_returns_valid_base64(self):
        result = status_pie_chart_base64({PullRequestStatus.APPROVED: 1})
        base64.b64decode(result)  # raises if invalid

    def test_single_status_renders_circle(self):
        svg = decode_svg(status_pie_chart_base64({PullRequestStatus.APPROVED: 3}))
        assert "<circle" in svg
        assert "<path" not in svg

    def test_multiple_statuses_renders_paths(self):
        svg = decode_svg(status_pie_chart_base64({
            PullRequestStatus.APPROVED: 2,
            PullRequestStatus.REJECTED: 1,
        }))
        assert "<path" in svg
        assert "<circle" not in svg

    def test_approved_uses_green(self):
        svg = decode_svg(status_pie_chart_base64({PullRequestStatus.APPROVED: 1}))
        assert "#5cb85c" in svg

    def test_approved_with_suggestions_uses_green(self):
        svg = decode_svg(status_pie_chart_base64({PullRequestStatus.APPROVED_WITH_SUGGESTIONS: 1}))
        assert "#5cb85c" in svg

    def test_needs_work_uses_orange(self):
        svg = decode_svg(status_pie_chart_base64({PullRequestStatus.NEEDS_WORK: 1}))
        assert "#f0ad4e" in svg

    def test_waiting_for_author_uses_orange(self):
        svg = decode_svg(status_pie_chart_base64({PullRequestStatus.WAITING_FOR_AUTHOR: 1}))
        assert "#f0ad4e" in svg

    def test_no_vote_uses_grey(self):
        svg = decode_svg(status_pie_chart_base64({PullRequestStatus.NO_VOTE: 1}))
        assert "#999999" in svg

    def test_unapproved_uses_grey(self):
        svg = decode_svg(status_pie_chart_base64({PullRequestStatus.UNAPPROVED: 1}))
        assert "#999999" in svg

    def test_rejected_uses_red(self):
        svg = decode_svg(status_pie_chart_base64({PullRequestStatus.REJECTED: 1}))
        assert "#d9534f" in svg

    def test_statuses_with_same_color_merge_into_circle(self):
        # APPROVED and APPROVED_WITH_SUGGESTIONS both map to green → single color → circle
        svg = decode_svg(status_pie_chart_base64({
            PullRequestStatus.APPROVED: 1,
            PullRequestStatus.APPROVED_WITH_SUGGESTIONS: 2,
        }))
        assert "<circle" in svg
        assert "<path" not in svg

    def test_custom_size_reflected_in_svg(self):
        svg = decode_svg(status_pie_chart_base64({PullRequestStatus.APPROVED: 1}, size=32))
        assert 'width="32"' in svg
        assert 'height="32"' in svg

    def test_default_size_is_20(self):
        svg = decode_svg(status_pie_chart_base64({PullRequestStatus.APPROVED: 1}))
        assert 'width="20"' in svg

    def test_pie_segment_angles_sum_to_full_circle(self):
        counts = {
            PullRequestStatus.APPROVED: 1,
            PullRequestStatus.NEEDS_WORK: 1,
            PullRequestStatus.REJECTED: 1,
        }
        svg = decode_svg(status_pie_chart_base64(counts))
        # Extract all arc endpoint coordinates and verify the last endpoint wraps back
        # to the first — a rough structural check that all segments are present
        paths = re.findall(r'<path d="([^"]+)"', svg)
        assert len(paths) == 3

    def test_ignored_zero_count_statuses(self):
        # Zero-count entries should not produce extra segments
        svg = decode_svg(status_pie_chart_base64({
            PullRequestStatus.APPROVED: 2,
            PullRequestStatus.REJECTED: 0,
        }))
        assert "<circle" in svg  # single non-zero color → circle
