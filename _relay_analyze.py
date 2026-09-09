import datetime
import json
import os
import subprocess

import anthropic


def main():
    with open("relay_result.json") as f:
        data = json.load(f)

    request_id = data.pop("_relay_request_id", "unknown")

    client = anthropic.Anthropic()
    msg = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=1024,
        messages=[{
            "role": "user",
            "content": (
                "You are an ML experiment assistant. "
                "Analyze this training result and give a brief, actionable observation "
                "(2-4 sentences). Focus on what the numbers suggest and one concrete next step.\n\n"
                f"Result:\n{json.dumps(data, indent=2)}"
            ),
        }],
    )

    now = datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
    response = (
        f"<!-- request_id: {request_id} -->\n"
        f"# AI Relay Response\n\n"
        f"**{now}**\n\n"
        f"{msg.content[0].text}\n"
    )

    with open("relay_response.md", "w") as f:
        f.write(response)

    subprocess.run(["git", "config", "user.email", "relay-bot@github-actions"], check=True)
    subprocess.run(["git", "config", "user.name", "AI Relay"], check=True)
    subprocess.run(["git", "add", "relay_response.md"], check=True)
    subprocess.run(["git", "commit", "-m", f"relay: response for {request_id}"], check=True)
    subprocess.run(["git", "push"], check=True)


if __name__ == "__main__":
    main()
