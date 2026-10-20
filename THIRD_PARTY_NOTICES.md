# Provenance

KonThai is an editorial skill developed by TdoubleEN, released 2026-10-20. It consolidates selected editorial principles rather than executing other skills.

- blader/humanizer, installed v3.1.0: factual fidelity, author voice, contextual pattern review. MIT license reproduced in licenses/humanizer-MIT.txt.
- citelogics-th/thai-humanizer, v1.0.0, commit 17615e9c1946a5d80d18b2d1091d703257303b3f: Thai connectors, translated syntax and register. MIT license reproduced in licenses/thai-humanizer-MIT.txt.
- [chakrit/kien-thai](https://github.com/chakrit/kien-thai), commit `3695c889a23538e97ddae45c53e8b894730b41f5`: selected topic/condition placement, recoverable subject omission, person-role continuity and register/voice concepts, rewritten as optional contextual guidance. MIT license reproduced in licenses/kien-thai-MIT.txt. No corpus excerpts, model-routing scripts, blocklists or audit-loop implementation copied.
- hardikpandya/stop-slop: inspiration for selective filler/repetition review; no code or phrase-list files copied.
- Aboudjem/humanizer-skill: inspiration for before/after protected-data checks; the helper here is newly implemented, without copying its code or scoring system.

PyThaiNLP, Pordee, cloud humanization APIs, AI-detection scores and mandatory multi-pass loops are not dependencies. The agent's existing model service still processes text under its own configuration; local scripts make no network requests.
