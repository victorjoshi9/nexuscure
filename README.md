# nexuscure — OpenClaw

Automation tool for claiming **DigitalOcean** credits from the
[GitHub Student Developer Education Pack](https://education.github.com/pack).

---

## Prerequisites

| Requirement | Notes |
|---|---|
| Python 3.8+ | [python.org](https://www.python.org/downloads/) |
| GitHub account with active student/teacher verification | [Apply here](https://education.github.com/discount_requests/application) |
| Playwright browsers | Installed automatically (see Setup) |

---

## Setup

```bash
# 1. Install Python dependencies
pip install -r requirements.txt

# 2. Install Playwright browser binaries
python -m playwright install chromium
```

---

## Usage

### Option A — command-line arguments

```bash
python claim_digitalocean.py \
  --username YOUR_GITHUB_USERNAME \
  --password YOUR_GITHUB_PASSWORD
```

### Option B — environment variables (recommended)

```bash
export GITHUB_USERNAME="your_github_username"
export GITHUB_PASSWORD="your_github_password"

python claim_digitalocean.py
```

### Headless mode (no visible browser window)

```bash
python claim_digitalocean.py --headless
```

### All options

```
--username    GitHub username  (or GITHUB_USERNAME env var)
--password    GitHub password  (or GITHUB_PASSWORD env var)
--headless    Run without a visible browser window
--slow-mo     Slow down each action by N milliseconds (default: 500)
```

---

## What the script does

1. Opens a Chromium browser and logs you into GitHub.
2. Navigates to the GitHub Education Pack offers page.
3. Locates the **DigitalOcean** offer card.
4. Clicks through to the DigitalOcean redemption page.
5. Leaves the browser open (15 seconds) so you can complete the final
   DigitalOcean account setup step manually.

> **Two-factor authentication (2FA):** If your GitHub account has 2FA
> enabled, the script will pause and prompt you to complete the 2FA step
> in the browser window before continuing.

---

## Troubleshooting

| Problem | Solution |
|---|---|
| "Could not find the DigitalOcean offer" | Ensure your GitHub account has active student/teacher verification. |
| Login error | Double-check your credentials. If using SSO, complete the SSO flow manually. |
| Redirected to login on Education Pack page | Your GitHub session may have expired; re-run the script. |
