import base64
import logging
import os
from datetime import date, timedelta

import requests

logger = logging.getLogger(__name__)


class JiraService:
    def __init__(self):
        self.base_url = os.environ.get("JIRA_BASE_URL")
        self.project_key = os.environ.get("JIRA_PROJECT_KEY")
        self.parent_issue_key = os.environ.get("JIRA_PARENT_ISSUE_KEY")
        self.session = requests.Session()
        token = base64.b64encode(
            f"{os.environ.get('JIRA_EMAIL')}:{os.environ.get('JIRA_API_TOKEN')}".encode()
        ).decode()
        self.session.headers.update(
            {"Content-Type": "application/json", "Authorization": f"Basic {token}"}
        )

    def create_issue(
        self, date: date, jira_team_id: str | None, jira_account_id: str | None
    ) -> str:
        jira_url = f"{self.base_url}/rest/api/3/issue"
        ticket_payload = {
            "fields": {
                "project": {"key": self.project_key},
                "issuetype": {"id": "10506"},
                "summary": f"Регресс {date}",
                "assignee": {"accountId": jira_account_id},
                "customfield_10839": {"id": jira_team_id},
                "customfield_10382": {"accountId": jira_account_id},
                "customfield_10015": str(date),
                "duedate": str(date + timedelta(days=1)),
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
        answer = self.session.post(url=jira_url, json=ticket_payload)
        logger.info((jira_url, self.session.headers))
        if answer.status_code != 201:
            raise Exception(answer.text)
        issue_key = answer.json()["key"]
        return issue_key

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
            raise Exception(answer.text)
