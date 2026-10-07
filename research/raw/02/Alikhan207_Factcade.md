# Factcade

AI operations copilot for small factories. When one machine stops, Factcade shows what the whole
factory is about to lose in rupees, proposes a plan, and applies it once the owner approves.

    machine fails -> cascade analysis -> loss per hour -> AI action plan -> owner approves -> recovery

## Architecture

| Piece | AWS service | Job |
|---|---|---|
| Frontend | Amplify Hosting | Live factory line, loss counter, plan and approval |
| API | API Gateway (HTTP API) | `/state /fail /plan /approve /repair /reset` |
| Logic | Lambda | Cascade and loss maths (plain Python, no AI), plan validation |
| AI copilot | Amazon Bedrock (Nova Pro) through the Strands Agents SDK | Reads the cascade with tools and proposes actions |
| State | DynamoDB | One item holding machines, incident and events |
| Events | EventBridge -> Lambda | Failure / approval / repair events; notifier logs who to alert |

The AI never computes money. The cascade is deterministic; the agent gets read-only tools over that result,
and every action it returns is checked against the real machines and orders. If it fails or times out, a
rule-based plan is used and the UI says so.

## Deploy (AWS CloudShell, region us-east-1, about 10 minutes)

1. Open CloudShell in your AWS account, switch region to **us-east-1**.
2. Upload this zip (Actions, Upload file), then `unzip factcade-aws.zip && cd factcade`.
3. `python3 tests/test_backend.py` should end with `all passed`.
4. `bash deploy.sh`. It builds the dependency layer, packages, deploys the stack and prints the API URL.
5. Check it: `curl -s <API URL>/state | head -c 300`.
6. Frontend: download `site.zip` from CloudShell (Actions, Download file). In the Amplify console choose
   **Create new app, Deploy without Git**, upload `site.zip`. You get an `https://...amplifyapp.com` URL.
7. If `/plan` returns a fallback plan, open Bedrock in us-east-1 and make sure Amazon Nova Pro access is enabled.

Demo without any backend: open `frontend/index.html` in a browser. It runs on built-in sample data and says so
in a banner. Add `?api=<API URL>` to point the same file at your deployed API.

## Before recording the video

- Click **Simulate failure** once and wait for the plan, so Lambda is warm (first call after idle is slower).
- Press **Reset demo**, then record.
- CloudWatch log group of the notifier (see stack output `NotifierLogGroup`) shows the EventBridge
  notifications, a good second screen for the "where AWS fits" part.

## Honest limits

- The factory is a modeled example. Loss per hour = idle cost of the failed machine + idle cost of downstream
  stages scaled by the output actually lost. The 60% recovery after rerouting (`RECOVERY` in `factory.py`)
  is an assumption. Replace both with a real factory's numbers when you have them.
- The notifier writes the alert to logs. Sending SMS / WhatsApp / email is the next step, not built.
- One shared state item: fine for a demo, not for many simultaneous users.

## Tests

`python tests/test_backend.py` runs offline: cascade values, plan validation, retry and fallback paths,
every API route including error cases, and the notifier. No AWS calls.
