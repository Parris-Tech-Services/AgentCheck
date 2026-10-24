# Intel iMac (2017): set up a free, secondary GitHub Actions runner using Antigravity CLI (agy)

> **Public, self-contained setup guide — 24 October 2026.** This is intended for an existing 2017 Intel iMac on macOS and an owner-authorised *private* GitHub repository. It contains no credentials, tokens, private URLs, account names, or non-public project details. Installing or registering a runner requires **local action** and owner authentication; nothing in this document establishes that a runner is already working.

## Scope and safety

- Create a **macOS x64** *self-hosted* runner named `imac2017-ci`, with an extra custom label `parris-mac-ci`. GitHub's standard labels are `self-hosted`, `macOS`, `X64`.
- Use a **repository-level runner restricted to one owner-chosen private repository**. A second machine's Linux runner should use distinct labels. Never allow untrusted forks, public pull requests, or arbitrary user-provided code to execute on a persistent personal computer.
- Do not purchase hosting, uncap any billing limit, or enable GitHub-hosted `macos-latest`/other paid jobs. Manually dispatch CI only for reviewed, trusted branches. CI execution is different from an AI agent's subscription usage; do not run agents as a CI task.
- 8 GB RAM and an older HDD are sufficient for **small, sequential lint/unit/browser checks**, but should not be expected to sustain large parallel tests. Keep at least 20 GB free after installation, keep one job/one browser worker at a time, and monitor CPU, disk and thermal load.
- First verify the current macOS version, security patches and compatibility. Old unpatched macOS releases are a security risk for an internet-connected service. Back up important data before invasive changes. Use the existing apps and services without interrupting them.
- Use a **standard non-admin macOS user dedicated to CI** with separate directories and no Keychain/iCloud/browser/personal-files access. User-account separation reduces ordinary exposure but is not a high-assurance security boundary.
- Obtain explicit approval for administrator operations, installing software, modifying system or login-service settings, changing power management, and GitHub registration.

## Step 1 — Run these read-only checks in iMac Terminal

Copy only these commands, not the prompt text or previous Terminal output:

```sh
sw_vers
uname -m
sysctl -n hw.memsize
df -h /
command -v agy || true
ls -l "$HOME/.local/bin/agy" 2>/dev/null || true
```

Expect `uname -m` to report `x86_64` on an Intel Mac. Verify actual architecture rather than guessing. If `agy` is not found, install below.

## Step 2 — Install the official Antigravity CLI (if missing)

Google's official instructions: https://antigravity.google/docs/cli/install/ and https://antigravity.google/download .

To avoid running an uninspected script directly:

```sh
curl -fsSL https://antigravity.google/cli/install.sh -o "$HOME/Downloads/agy-install.sh"
less "$HOME/Downloads/agy-install.sh"
```

Press `q` after reviewing. If the source and contents appear legitimate and you approve the changes, install:

```sh
bash "$HOME/Downloads/agy-install.sh"
export PATH="$HOME/.local/bin:$PATH"
agy --version
agy
```

Official installer targets `~/.local/bin/agy` on macOS. If the new Terminal still doesn't find it, add `$HOME/.local/bin` to `~/.zshrc` after checking for an existing PATH line.

**Do not run `agy --dangerously-skip-permissions`.** Use an **interactive** authenticated session with normal approval prompts, not unattended permissive headless execution. Authenticate through the local browser/Keychain, not an API key. Confirm no charged pay-as-you-go key has been configured.

## Step 3 — Paste this prompt into interactive `agy`

You are Google Antigravity CLI running **locally** on my 2017 Intel iMac. The other AI CLIs are unavailable due to usage limits. Please set this Mac up as a **free, secure, secondary GitHub Actions self-hosted CI runner** for **one of my private GitHub repositories**. Do all safe technical work yourself where permissions allow; stop for interactive approval whenever needed. Do not merely outline a plan, and never claim setup is verified without a real GitHub run.

1. **Audit before installing:** check `sw_vers`, architecture, RAM/CPU, disk free space and health, macOS security update status, active services, available Git/Node/Python, sleep/login behaviour, and existing runner installations. Preserve personal accounts and workloads.
2. **Protect the host:** recommend a new dedicated **non-admin macOS user** and install all runner files under that account. Restrict filesystem access. Do not grant sudo, Full Disk Access, broad Accessibility access, Docker privileges or access to personal browser sessions, iCloud, or private data. Remember macOS user separation does not make running untrusted code safe.
3. **Ask me to select the private GitHub target repository**, then use a local `gh auth login` or browser sign-in with owner permission. Do not assume public access to a private repository and never reveal it in a public document or log. Register a **repository-level** runner, not a broad organisation runner. Keep GitHub Actions enabled for self-hosted jobs but do not raise spending limits.
4. **Install the official macOS x64 self-hosted runner** following GitHub's *current generated commands* and checksum: https://docs.github.com/en/actions/how-tos/manage-runners/self-hosted-runners/configure-the-application?platform=mac . Register as `imac2017-ci` with custom label **`parris-mac-ci`**, keeping built-in macOS and X64 labels. Only obtain the short-lived registration token locally through authorised GitHub UI/CLI; do not show, commit, log or transmit it.
5. **Install required build prerequisites minimally** (Git, Node LTS, Python 3; Xcode CLI tools only if necessary). Limit to **one job**, one browser test worker and small trusted pilot runs; monitor memory/disk usage. Do not clone the entire repository fleet.
6. **Install/start the runner service using macOS `launchd`**, GitHub's supplied `./svc.sh install`, `./svc.sh start` and `./svc.sh status` where applicable, as the dedicated standard user. Avoid Linux systemd commands. Confirm runner Online/Idle, observe what happens after sleep, user logoff, idle and reboot; do not bypass macOS screen lock or change automatic login without permission.
7. **Prove with a real manual workflow run** from the selected private repository, using `runs-on: [self-hosted, macOS, X64, parris-mac-ci]`. Make a minimal read-only test if none exists. Verify GitHub shows the actual Mac runner as the worker, logs report macOS/Git/Node/Python correctly, test is green, and the runner returns Online/Idle. Do not switch to `macos-latest`, `ubuntu-latest` or any GitHub-hosted runner.
8. **After green preflight**, manually run one small **reviewed private-repository** lint/test or Playwright WebKit browser test with one worker; do not automatically run agents, external PRs, untrusted code, heavy games or new production deploys.
9. **Record real evidence in the selected private repository** — runner name, OS, access restriction, label, service status, test URL/commit, any spent GitHub-hosted minutes (should be zero for this run), and outstanding problems. Do not put account secrets, private repo existence or personal machine details into a public log.
10. **Report accurately**: VERIFIED RUNNER READY only if a live manual preflight passes; otherwise PARTIALLY COMPLETE / BLOCKED with the exact owner approval needed. Do not mark every app/game fully verified just because the runner is online.

**Additional instructions:** if the Mac's OS is unpatched/unsupported or too low on free disk, stop and explain. Do not use global `command(*)`/other blanket permission-autoallow rules to make agy run headlessly. Do not install unknown scripts or weaken branch protection. Never use an API key with usage-based charges.

## Step 4 — Example private-repo preflight workflow (only if none exists)

Create this **in your selected private repository**, not here, under `.github/workflows/macos-self-hosted-preflight.yml`. Replace labels only if the actual registered runner differs. It is manual only:

```yaml
name: macOS self-hosted runner preflight
on:
  workflow_dispatch:
permissions:
  contents: read
jobs:
  preflight:
    runs-on: [self-hosted, macOS, X64, parris-mac-ci]
    timeout-minutes: 6
    steps:
      - name: Read-only environment checks
        shell: bash
        run: |
          set -euo pipefail
          test "$(uname -s)" = Darwin
          sw_vers
          uname -m
          df -h .
          git --version
          node --version
          npm --version
          python3 --version
          echo "Preflight completed on the Mac self-hosted runner."
```

Dispatch manually from the private repository's **Actions** tab. If the job queues, inspect runner status, repo registration scope, labels, macOS session and launchd service first; don't change to a billed hosted runner.

## Notes

- A file in a **private** GitHub repository commonly returns **404** in a browser that is signed out or logged into an account without access. This guide is public, but your private project's issue, workflows and repo access will still require signing into the right GitHub account.
- GitHub macOS service troubleshooting: https://docs.github.com/en/actions/how-tos/manage-runners/self-hosted-runners/monitor-and-troubleshoot?platform=mac
- GitHub security: https://docs.github.com/en/actions/reference/security/secure-use
- GitHub self-hosted runner billing: https://docs.github.com/en/billing/concepts/product-billing/github-actions
- Antigravity CLI installation: https://antigravity.google/docs/cli/install/
