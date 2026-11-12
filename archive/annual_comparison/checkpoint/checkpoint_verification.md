# Checkpoint requirement verification

Reviewed November 4, 2026 against the full assignment text supplied in the user’s latest attachment, including its Checkpoint Submission section. Scientific validation and local Chrome tests were rerun successfully during this audit; see [scientific test results](../data/validation.json) and [browser test results](test_report.json).

**Verdict: the analysis and presentation assets are prepared, but the checkpoint submission is not yet complete. A final team identity and a recorded narrated MP4 are still required.**

## Five required content items

| Assignment requirement | Evidence | Status |
|---|---|---|
| Team name and team members | Slide 1 and the opening of checkpoint_script.md list Sadhana Tadepalli and Saahithi Myneedu. | Incomplete: [TEAM NAME] remains; confirm the full registered roster. |
| Dataset chosen, with the aspects being used | Slide 2 and narration identify CMIP6 CanESM5-CanOE, monthly near-surface air temperature, historical and three scenario runs, baseline and area-weighted latitude bands. The slide names all three SSPs and the shared member/grid. | Verified in prepared materials. |
| Five or six exploratory graphs that lead to the question | Slides 3–8 embed six actual 2560 × 1440 PNG figures. The narration now explicitly connects the observed regional patterns and scenario separation to the research question. | Verified in prepared materials. All six must be visible in the recording. |
| Visualization title and intended question | Slide 1 and opening narration state the full project title and the question about regional warming and the scenario gap through 2100. | Verified in prepared materials. |
| Current progress on the final dynamic graph | Slide 9 embeds the working D3 prototype; slide 10 describes completed analysis and next steps. Narration names the implemented controls and calculated summary. | Verified locally; demonstrate the actual controls during recording. |

## Recording and submission rules

| Assignment rule | Audit result |
|---|---|
| Submit an MP4 no longer than two minutes | No MP4 exists in the workspace. Record and check the exported file’s actual duration: at most 120 seconds; aim for 115 seconds. |
| Include audio/voiceover | A 238-word script is prepared, but there is no recorded audio to verify. Listen to the exported MP4. |
| Not every member must appear in the recording | One narrator can record the demonstration. Still list all actual members. |
| Submit one video per team and add every member to Gradescope | Submission and membership on Gradescope cannot be verified from these local files. |
| Checkpoint deadline: Thursday November 5, 11:59 PM | Submit by November 5, 2026, 11:59 PM in the course’s submission timezone; the client context is America/Los_Angeles. |

The storyboard allocates 1:55, but a storyboard and word count cannot establish actual runtime. Speaking long model/scenario names and demonstrating controls can take longer than the nominal count suggests. Rehearse with the exported video timing.

## Whole-project requirements relevant to this checkpoint

- **Approved dataset:** actual CMIP6 model simulation output, with exact cloud paths and transformations in [provenance](../data/provenance.md). Historical simulations are not observations.
- **Interactive implementation:** website plotting uses D3.js; the website reads local static JSON and needs no custom backend. Offline checkpoint images use Matplotlib, as authorized in the original user request. The checkpoint instructions allow static or dynamic exploratory graphs; they do not separately specify the tooling for those static images. The D3-only requirement is satisfied by the interactive website.
- **Scientific checks:** all 1,668 records are finite and unique, year coverage is complete, historical baseline means are zero within rounding tolerance, and independent area-weighted recomputation agrees with every saved regional annual value. All six PNGs exist at the expected resolution. Prior independent checks against raw monthly fields for 1995 and 2100 also passed; see [remote sample validation](../data/remote_validation.json).
- **Interactive checks:** all 15 local Chrome checks passed again, covering filters, hover, keyboard inspection, year controls, empty selections, reset, mobile layout, slide navigation and linked assets. No page errors or failed HTTP asset requests occurred in that run.
- **Team registration:** the assignment specifies 3–4 students. Only two names have been supplied. Confirm the full registered team or an instructor-approved exception. Registration status and the earlier team formation submission are not verified.
- **Public GitHub Pages prototype:** not deployed. The assignment sets this as the final prototype deliverable for November 11, 2026, 11:59 PM; the checkpoint section asks for current progress and does not require an already published URL.
- **Final write-up:** a linked draft covers design, alternatives, interactions, transformations, limitations and development. Actual contributions, total people-hours and the team’s own development account remain incomplete. The rubric explicitly evaluates the authenticity and quality of that account; the current generated draft must be reviewed and rewritten by the team to reflect actual work. These are final-project requirements, not additional checkpoint video content items.

## Corrections made during this audit

1. Added an explicit explanation of how the exploratory patterns led to the regional/scenario research question.
2. Made Celsius units explicit in the narrated findings.
3. Corrected the storyboard’s claim about screenshots: the deck has a live prototype; screenshots are separate files.
4. Updated the narration count to 238 words and clarified that actual recording duration remains unverified.

## Before submitting

1. Replace [TEAM NAME] in the script, first slide and supporting materials. Update the generator if using it again, so it does not restore the placeholder.
2. Confirm all registered member names and the team-size arrangement.
3. Open slides.html through the local HTTP server, rehearse the storyboard and record all six figures plus the live prototype with narration.
4. Export MP4; play it to confirm audible narration, readable figures and duration at most 120 seconds.
5. Submit that one MP4 on Gradescope before the checkpoint deadline and attach every actual member.
