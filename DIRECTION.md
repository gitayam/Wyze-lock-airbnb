# Direction: Wyze-lock-airbnb

A Python script that sets and removes Wyze lock access codes from Airbnb iCal bookings,
with email confirmations. It is a single-host CLI or systemd service for the owner's
rentals.

Status: dormant (last change 2024-07-18). 37 commits, all from 2024-06-02 to 2024-07-18.

## Where it is heading
- Nothing since July 2024. The last work was the Wyze SDK-only client, TOTP login, and
  email confirmations over SMTP. (00e91f6, e80a469, b6f369c)
- Smart-lock automation for the same use case now lives in the OpenBNB repo
  (short_term_land_lord), which uses Seam (Schlage/Yale/August), not Wyze. The repo itself
  doesn't say it was superseded. (inferred; that repo's SMART_LOCK_AUTOMATION.md)

## Priorities
Unchecked items on the README roadmap, if work resumes:
1. Keypad support. It is blocked on an upstream wyze-sdk issue linked from the README.
2. Delete the code when a stay is cancelled or deleted.
3. Check on a schedule within a time window around check-in.
4. A web UI, and support for other lock brands. (README.md "Roadmap")

## Non-goals and constraints
- Python 3 with `wyze_sdk`. Credentials and per-home settings come from `.env`
  (`.env-template`). Tokens are obtained once with `get-access_refresh_token.py`.
  (README.md, 85ad7c0)
- The access code comes from the last 4 digits of the Airbnb calendar event. (README.md
  roadmap, ede21a7)
- The script stops if required variables are undefined. (e355e42)

## Decisions
- 2024-07-14: Use only the Wyze SDK. (00e91f6)
- 2024-07-13: Add TOTP login and an SMTP email confirmation. (b6f369c, e80a469)
- 2024-06-02: Process codes every 15 minutes so late bookings are caught. (4d85029)

## Open questions for the owner
1. Is this repo superseded by OpenBNB's lock automation, and should it be archived? If
   not, what would resuming need (Wyze devices still in use, the SDK issue resolved)?

## Related documents
- README.md (roadmap checklist and setup)
