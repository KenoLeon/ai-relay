# colab-relay

Push experiment results from a Colab notebook to GitHub, get AI analysis back — using only free infrastructure.

## How it works

1. Your Colab notebook calls `push(data)` → commits `relay_result.json` to a GitHub branch
2. A GitHub Action triggers → calls Gemini → writes `relay_response.md` back
3. Your notebook calls `pull(req)` → prints the AI's response

## Setup (one time)

### 1. Install

```python
!pip install colab-relay
```

### 2. Create a GitHub repo for relay data

Create a new GitHub repo (e.g. `your-username/my-relay`). It can be private.

### 3. Add the GitHub Action

Copy both files from [`action-template/`](action-template/) into your relay repo:

- `action-template/ai-relay.yml` → `.github/workflows/ai-relay.yml`
- `action-template/_relay_analyze.py` → `_relay_analyze.py`

### 4. Add secrets to your relay repo

In your relay repo → Settings → Secrets and variables → Actions:

| Secret | Value |
|--------|-------|
| `GEMINI_API_KEY` | Your Google AI Studio key ([get one free](https://aistudio.google.com)) |

### 5. Create a GitHub PAT

Create a fine-grained PAT at `github.com/settings/personal-access-tokens` scoped to your relay repo with:
- **Contents**: Read and Write
- **Actions**: Read

## Usage

```python
import os
from colab_relay import push, pull

os.environ["GITHUB_TOKEN"] = "your-pat"
os.environ["RELAY_REPO"] = "your-username/my-relay"

# Push results and get AI analysis
req = push({"epoch": 5, "loss": 0.31, "val_loss": 0.38, "accuracy": 0.89})
response = pull(req)
print(response)
```

## Configuration

| Environment variable | Required | Default | Description |
|----------------------|----------|---------|-------------|
| `GITHUB_TOKEN` | Yes | — | PAT with Contents + Actions read on relay repo |
| `RELAY_REPO` | Yes | — | `owner/repo` of your relay repo |
| `RELAY_BRANCH` | No | `relay-data` | Branch for relay data |

## License

MIT
