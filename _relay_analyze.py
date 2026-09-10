import datetime
import json
import os
import subprocess

from google import genai


def main():
    with open("relay_result.json") as f:
        data = json.load(f)

    request_id = data.pop("_relay_request_id", "unknown")

    client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
    result = client.models.generate_content(
        model="gemini-2.5-flash",
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

    with open("relay_response.md", "w") as f:
        f.write(response)

    subprocess.run(["git", "config", "user.email", "relay-bot@github-actions"], check=True)
    subprocess.run(["git", "config", "user.name", "AI Relay"], check=True)
    subprocess.run(["git", "add", "relay_response.md"], check=True)
    subprocess.run(["git", "commit", "-m", f"relay: response for {request_id}"], check=True)
    subprocess.run(["git", "push"], check=True)


if __name__ == "__main__":
    main()
