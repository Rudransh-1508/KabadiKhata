# Suraksha

**Family care for an aging parent — without watching her.**

![Next.js](https://img.shields.io/badge/Next.js-15-black)
![AWS](https://img.shields.io/badge/AWS-Ship%20it-orange)
![Bedrock](https://img.shields.io/badge/Amazon-Bedrock-purple)
![Wear%20OS](https://img.shields.io/badge/Wear%20OS-Galaxy-blue)
![Cedar](https://img.shields.io/badge/Policy-Cedar-green)

> Most days, Suraksha says nothing at all. That’s the point.

Suraksha is a **hardware-first, agentic companion** for aging at home: Galaxy Watch + tablet voice + long-term memory + proactive care + consent-aware family escalation — built to **ship on AWS**.

Amma (72, Bengaluru) wears the watch and talks to Suraksha in Hindi or Hinglish. Rahul and Priya get a calm family view. They are notified only when something is actually wrong — and only the person who can show up is asked first.

**Build story + architecture diagram:** [`docs/suraksha-build-story.md`](docs/suraksha-build-story.md) · [`docs/suraksha-aws-architecture.png`](docs/suraksha-aws-architecture.png)  
**API / agent runbook:** [`ally/README.md`](ally/README.md)

---

## The problem

Adult children living in another city do not need a live feed of their parent’s day. Cameras and always-on dashboards steal independence. Silence leaves families guessing. Panic buttons only help if she can reach them and wants to press them.

Suraksha sits in between: it learns what is normal for Amma, talks to **her** first, remembers what she asked for, enforces what she said to keep private, and only then coordinates the person who can actually help.

---

## Who it’s for

| Who | What they get |
| --- | --- |
| **Parent (Amma)** | Watch + tablet companion; speak a task; almost no learning curve |
| **Family (Rahul, Priya)** | Calm home/command views; push only when needed; one-tap respond |
| **Nearby help (optional)** | Guard / neighbour path only if Cedar allows |

Suraksha is **not** an emergency service replacement. Family screens always surface **112**.

---

## What Suraksha does

| Capability | Detail |
| --- | --- |
| **Agentic voice companion** | Speak a task — reminders, check-ins, errands, health notes, consent. Tools run; it doesn’t only chat. |
| **All-in-one memory** | DynamoDB single-table facts: day log, mood, alerts, reminders, consent, audit — not a disposable chat blob. |
| **Hardware-first** | Galaxy Wear OS: wake, vitals, fall. Tablet for conversation. Put it on, talk. |
| **Fall detection** | Watch signals open investigation / scripts; family chain only after policy and judgement. |
| **Proactive care** | EventBridge every minute: due reminders, wake-window misses, investigation timeouts. |
| **Ask her first** | Missed wake or worrying signal → Suraksha checks in with Amma before looping family. |
| **Consent that blocks tools** | Spoken privacy rules → Cedar templates → `ConsentGuard` on every tool call; audit she can read. |
| **Evidence-only family Q&A** | “Did she sleep okay?” → answers only from tool-returned records, or not sure / private. |
| **Family escalation** | Step Functions: Rahul → timeout → Priya → ask about neighbour → neighbour if allowed → failsafe notify-all. |
| **Quiet by design** | Most days: no noise. Engagement is not the goal. |
| **Explore world (demo)** | 3D wardstone / gallery experience for storytelling and AWS gallery beats. |

### Example moments

| Moment | What happens | AWS |
| --- | --- | --- |
| First movement of the day | 