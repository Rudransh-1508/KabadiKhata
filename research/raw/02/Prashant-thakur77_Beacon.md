# Beacon Night Shift

**The on-call agent that fixes the 3 AM page with your voice — and the second time it happens, does not wake you at all.**

> **Two submissions live in this repository.**
> This branch (`main`, tagged [`first-commit-submission`](https://github.com/Prashant-thakur77/Beacon/tree/first-commit-submission)) is the **First Commit** entry, kept exactly as it was judged.
> The **AssemblyAI Voice Agent hackathon** entry is on the **[`assemblyai`](https://github.com/Prashant-thakur77/Beacon/tree/assemblyai)** branch — it adds the phone channel, the consent certificate, per-channel attestation and a measured latency benchmark. **If you arrived here from lablab.ai, you want that branch.**

[![CI](https://github.com/Prashant-thakur77/Beacon/actions/workflows/build.yaml/badge.svg)](https://github.com/Prashant-thakur77/Beacon/actions/workflows/build.yaml)
[![Release](https://img.shields.io/github/v/release/Prashant-thakur77/Beacon?label=release)](https://github.com/Prashant-thakur77/Beacon/releases/latest)
[![License](https://img.shields.io/badge/license-Apache--2.0-blue)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.12-3776ab)](pyproject.toml)
[![Built on AWS](https://img.shields.io/badge/built%20on-AWS-ff9900)](docs/architecture.md)

**Live console:** https://6die6lduac6ipxkeg73nxsuvpu0yzkim.lambda-url.us-east-1.on.aws/ · **Demo film:** [YouTube](https://youtu.be/a3SxZHvIkCo) · [3-minute cut](https://github.com/Prashant-thakur77/Beacon/releases/download/v0.2.0/Beacon-Night-Shift-3min.mp4) · [full cut](https://github.com/Prashant-thakur77/Beacon/releases/download/v0.2.0/Beacon-Night-Shift-full.mp4) · **Blog:** [Why the transcript is the safety artifact](https://builder.aws.com/post/3Jb5v7ouXDReILJ7WMuHrlB1leL_p/why-transcript-is-the-safety-artifactvoice-approved-aws-remediation-with-strands-and-step-functions) · **Architecture:** [docs/architecture.md](docs/architecture.md) (Mermaid) · **Try it locally:** `make setup && make local`

It is 3 AM. Payments are failing. You are alone, half-asleep, phone in hand. You need four answers: *is it real, what changed, what do I do, can I go back to sleep.*

Beacon reads the logs on Amazon Bedrock, finds the CloudTrail change that caused the outage, proves it against a golden snapshot, proposes one allowlisted fix, dry-runs it under a locked-down role, and waits for your word. You say **"approve fix one"** into your browser. A Step Functions loop applies the fix and refuses to say *recovered* until CloudWatch agrees. Then Beacon asks: *handle this myself next time?* You say yes, for a week. That sentence becomes a **Sleep Contract**: a scoped, expiring standing approval, with your own words as the record. The next time the same thing breaks, Beacon fixes it, verifies it, and emails you in the morning. Zero humans woken.

Built solo in a weekend for the AWS *First Commit* hackathon. Everything below is live code with tests, not a slide.

![Beacon Night Shift](docs/assets/landing.gif)

<table><tr>
<td><img src="docs/assets/night-board.png" alt="Night Board" /></td>
<td><img src="docs/assets/analytics.png" alt="Analytics" /></td>
</tr><tr>
<td align="center"><sub>Night Board: the incident, the conversation, the evidence</sub></td>
<td align="center"><sub>Analytics: recovery, sleep and cost across nights</sub></td>
</tr></table>

## Try it in two minutes, no AWS account

```bash
make setup            # once: uv venv, CPU torch, the package, npm ci
make local            # 