# Copilot Agents Demo

Use the following 3 files to setup your Copilot Agents demo. 
Paste the ISSUE.md file into a new issue in that repository. 

## What this demo shows
- Assign an issue to Copilot to start an agent task
- Monitor progress in AgentHQ
- Re-steer mid-session with a new requirement
- Review the resulting PR like a teammate’s work

## Demo files
- `ISSUE.md` contains the exact issue text to copy/paste into GitHub
- `STEER.md` contains the mid-session requirement change to paste while the agent is working

## Quick demo steps
1. Create a new GitHub Issue by copying the Title and Body from `ISSUE.md`
2. Assign the issue to Copilot to start the agent task
3. Open AgentHQ to monitor progress
4. Paste `STEER.md` into the agent session to re-steer the work
5. Review the PR diff for clarity, completeness, and constraints.
6. Verify the PR edited the README.md file by adding priority levels plus the steered examples. 

---

## Ticket Triage Policy

Use Severity to describe impact and Priority to decide order.

### Severity levels
- Low means minor annoyance with an easy workaround
- Medium means meaningful user impact but workarounds exist
- High means blocks key workflows or risks data loss

### Priority levels
- P0 — active outage, security incident, or widespread blocker; work immediately
- P1 — major customer pain or urgent business risk; start next
- P2 — important but not urgent; schedule soon
- P3 — minor issue or routine improvement; backlog

### Default Severity → Priority
| Severity | Default Priority |
| --- | --- |
| High | P1 |
| Medium | P2 |
| Low | P3 |

Use P0 only when a High severity issue is an active outage, a security incident, or blocks many customers right now.

### How to triage in 60 seconds
1. Confirm customer impact and whether a workaround exists.
2. Set Severity: Low, Medium, or High.
3. Apply the default Priority and escalate to P0 only for active, widespread emergencies.
4. Add an owner and the next action.
5. If anything is unclear, ask in triage before closing the ticket.
