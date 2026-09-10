import base64
import datetime
import json
import os
import requests

from google import genai


_GITHUB_API = "https://api.github.com"


def _gh_put(token, repo, branch, path, content, message):
    hdrs = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    encoded = base64.b64encode(content.encode()).decode()
    url = f"{_GITHUB_API}/repos/{repo}/contents/{path}"
    r = requests.get(url, headers=hdrs, params={"ref": branch})
    sha = r.json().get("sha") if r.status_code == 200 else None
    body = {"message": message, "content": encoded, "branch": branch}
    if sha:
        body["sha"] = sha
    r = requests.put(url, headers=hdrs, json=body)
    r.raise_for_status()


def main():
    with open("relay_result.json") as f:
        data = json.load(f)

    request_id = data.pop("_relay_request_id", "unknown")

    client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
    result = client.models.generate_content(
        model="gemini-BROKEN-for-testing",
        contents=(
            "You are an ML experiment assistant. "
            "Analyze this training result and give a brief, actionable observation "
            "(2-4 sentences). Focus on what the numbers suggest and one concrete next step.\n\n"
            f"Result:\n{json.dumps(data, indent=2)}"
        ),
    )

    now = datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
    response = (
        f"<!-- request_id: {request_id} -->\n"
        f"# AI Relay Response\n\n"
        f"**{now}**\n\n"
        f"{result.text}\n"
    )

    token = os.environ["GITHUB_TOKEN"]
    repo = os.environ["RELAY_REPO"]
    branch = os.environ.get("RELAY_BRANCH", "relay-data")

    _gh_put(token, repo, branch, "relay_response.md", response,
            f"relay: response for {request_id}")


if __name__ == "__main__":
    main()
