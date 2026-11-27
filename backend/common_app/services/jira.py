import base64
import logging
import os
from dataclasses import dataclass, field
from datetime import date, timedelta
from typing import Any

import requests

logger = logging.getLogger(__name__)

# Jira Cloud accepts at most 50 issues per bulk create request.
BULK_CREATE_LIMIT = 50


@dataclass(frozen=True)
class IssueData:
    date: date
    jira_team_id: str | None
    jira_account_id: str | None


@dataclass
class BulkCreateResult:
    """Outcome per input index: either a created issue key or an error message."""

    keys: dict[int, str] = field(default_factory=dict)
    errors: dict[int, str] = field(default_factory=dict)


def format_jira_error(body: Any, fallback: str = "Unknown Jira error") -> str:
    """Turn a Jira ErrorCollection ({errorMessages, errors}) into one line."""
    if not isinstance(body, dict):
        return fallback
    messages = list(body.get("errorMessages") or [])
    messages += [f"{k}: {v}" for k, v in (body.get("errors") or {}).items()]
    return "; ".join(messages) or fallback


def _response_error(response: requests.Response) -> str:
    try:
        body = response.json()
    except ValueError:
        body = None
    return format_jira_error(
        body, fallback=f"Jira returned HTTP {response.status_code}: {response.text}"
    )


class JiraService:
    def __init__(self):
        self.base_url = os.environ.get("JIRA_BASE_URL")
        self.project_key = os.environ.get("JIRA_PROJECT_KEY")
        self.parent_issue_key = os.environ.get("JIRA_PARENT_ISSUE_KEY")
        token = base64.b64encode(
            f"{os.environ.get('JIRA_EMAIL')}:{os.environ.get('JIRA_API_TOKEN')}".encode()
        ).decode()
        self.session = requests.Session()
        self.session.headers.update(
            {"Content-Type": "application/json", "Authorization": f"Basic {token}"}
        )

    def build_issue_payload(self, issue: IssueData) -> dict:
        return {
            "fields": {
                "project": {"key": self.project_key},
                "issuetype": {"id": "10506"},
                "summary": f"Регресс {issue.date}",
                "assignee": {"accountId": issue.jira_account_id},
                "customfield_10839": {"id": issue.jira_team_id},
                "customfield_10382": {"accountId": issue.jira_account_id},
                "customfield_10015": str(issue.date),
                "duedate": str(issue.date + timedelta(days=1)),
                "timetracking": {"originalEstimate": "6h", "remainingEstimate": "6h"},
            },
            "update": {
                "issuelinks": [
                    {
                        "add": {
                            "type": {"name": "Consist"},
                            "outwardIssue": {"key": self.parent_issue_key},
                        }
                    }
                ]
            },
        }

    def bulk_create_issues(self, issues: list[IssueData]) -> BulkCreateResult:
        """Create issues in chunks of BULK_CREATE_LIMIT.

        Never raises for Jira-side failures: every input index ends up either in
        ``result.keys`` or in ``result.errors``, so issues created in earlier
        chunks are not lost when a later chunk fails.
        """
        result = BulkCreateResult()
        jira_url = f"{self.base_url}/rest/api/3/issue/bulk"
        for start in range(0, len(issues), BULK_CREATE_LIMIT):
            chunk = issues[start : start + BULK_CREATE_LIMIT]
            payload = {"issueUpdates": [self.build_issue_payload(i) for i in chunk]}
            try:
                self._create_chunk(jira_url, payload, len(chunk), start, result)
            except requests.RequestException as e:
                logger.exception("Jira bulk create failed for chunk at %s", start)
                for offset in range(len(chunk)):
                    result.errors[start + offset] = str(e)
        return result

    def _create_chunk(
        self,
        jira_url: str,
        payload: dict,
        size: int,
        start: int,
        result: BulkCreateResult,
    ) -> None:
        response = self.session.post(url=jira_url, json=payload)
        # 201: at least one issue created; 400: all failed (same body shape).
        if response.status_code not in (201, 400):
            raise requests.HTTPError(_response_error(response))
        body = response.json()
        if "issues" not in body or "errors" not in body:
            raise requests.HTTPError(_response_error(response))

        failed = {
            e["failedElementNumber"]: format_jira_error(e.get("elementErrors"))
            for e in body["errors"]
        }
        created = body["issues"]
        if len(created) + len(failed) != size:
            raise requests.HTTPError(
                f"Unexpected Jira bulk response: {len(created)} created, "
                f"{len(failed)} failed, {size} requested"
            )
        # Jira returns created issues in request order, skipping failed elements.
        created_iter = iter(created)
        for offset in range(size):
            if offset in failed:
                result.errors[start + offset] = failed[offset]
            else:
                result.keys[start + offset] = next(created_iter)["key"]

    def update_issue(
        self, issue_key: str, jira_team_id: str | None, jira_account_id: str | None
    ) -> None:
        jira_url = f"{self.base_url}/rest/api/3/issue/{issue_key}"
        ticket_payload = {
            "fields": {
                "assignee": {"accountId": jira_account_id},
                "customfield_10839": {"id": jira_team_id},
            }
        }
        answer = self.session.put(url=jira_url, json=ticket_payload)
        if answer.status_code not in (200, 201, 204):
            raise requests.HTTPError(_response_error(answer))
