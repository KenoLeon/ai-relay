import base64
import datetime
import json
import os
import time

import requests

_GITHUB_API = "https://api.github.com"


def _cfg():
    return (
        os.environ["GITHUB_TOKEN"],
        os.environ["RELAY_REPO"],
        os.environ.get("RELAY_BRANCH", "relay-data"),
    )


def _headers(token):
    return {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }


def _ensure_branch(token, repo, branch):
    hdrs = _headers(token)
    r = requests.get(f"{_GITHUB_API}/repos/{repo}/git/refs/heads/{branch}", headers=hdrs)
    if r.status_code == 200:
        return
    r = requests.get(f"{_GITHUB_API}/repos/{repo}", headers=hdrs)
    r.raise_for_status()
    default = r.json()["default_branch"]
    r = requests.get(f"{_GITHUB_API}/repos/{repo}/git/refs/heads/{default}", headers=hdrs)
    r.raise_for_status()
    sha = r.json()["object"]["sha"]
    r = requests.post(
        f"{_GITHUB_API}/repos/{repo}/git/refs",
        headers=hdrs,
        json={"ref": f"refs/heads/{branch}", "sha": sha},
    )
    r.raise_for_status()


def _put_file(token, repo, branch, path, content, message):
    hdrs = _headers(token)
    encoded = base64.b64encode(content.encode()).decode()
    url = f"{_GITHUB_API}/repos/{repo}/contents/{path}"
    r = requests.get(url, headers=hdrs, params={"ref": branch})
    sha = r.json().get("sha") if r.status_code == 200 else None
    body = {"message": message, "content": encoded, "branch": branch}
    if sha:
        body["sha"] = sha
    r = requests.put(url, headers=hdrs, json=body)
    r.raise_for_status()


def push(data: dict) -> str:
    """Commit data as relay_result.json on the relay branch. Returns the request_id."""
    token, repo, branch = _cfg()
    _ensure_branch(token, repo, branch)
    request_id = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
    payload = {"_relay_request_id": request_id, **data}
    _put_file(
        token, repo, branch,
        "relay_result.json",
        json.dumps(payload, indent=2),
        f"relay: push {request_id}",
    )
    print(f"[relay] pushed → {repo}@{branch} ({request_id})")
    return request_id


def pull(request_id: str, timeout: int = 300, poll: int = 10) -> str:
    """Poll for relay_response.md matching request_id. Fails fast if the Action errors."""
    token, repo, branch = _cfg()
    hdrs = _headers(token)
    response_url = f"{_GITHUB_API}/repos/{repo}/contents/relay_response.md"
    runs_url = f"{_GITHUB_API}/repos/{repo}/actions/runs"

    push_dt = datetime.datetime.strptime(request_id, "%Y%m%dT%H%M%SZ")
    push_iso = push_dt.strftime("%Y-%m-%dT%H:%M:%SZ")

    deadline = time.time() + timeout
    while time.time() < deadline:
        # Check for successful response
        r = requests.get(response_url, headers=hdrs, params={"ref": branch})
        if r.status_code == 200:
            text = base64.b64decode(r.json()["content"]).decode()
            if f"request_id: {request_id}" in text:
                return text

        # Check for a failed Action run triggered after this push
        r = requests.get(runs_url, headers=hdrs, params={
            "event": "push",
            "branch": branch,
            "created": f">={push_iso}",
            "per_page": 5,
        })
        if r.status_code == 200:
            for run in r.json().get("workflow_runs", []):
                if run.get("conclusion") == "failure":
                    raise RuntimeError(
                        f"[relay] Action failed — check: {run.get('html_url')}"
                    )

        remaining = int(deadline - time.time())
        print(f"[relay] waiting… ({remaining}s left)")
        time.sleep(poll)

    raise TimeoutError(f"[relay] no response for {request_id} after {timeout}s")
