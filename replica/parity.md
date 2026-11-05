## Parity: 78.7 / 100

features 89.9  (38 counted, must-haves 24 of 27 done)
layout   33.7  (3 screens compared)

Not shippable yet: 3 must-have features are not done.

## By area, weakest first
- content                        0.0  (2 features)
- backend                        0.0  (1 features)
- blog                          50.0  (1 features)
- legal                         50.0  (1 features)
- leads                         75.0  (2 features)
- shell                         89.3  (5 features)
- home                          93.5  (9 features)
- catalog                      100.0  (12 features)
- portfolio                    100.0  (1 features)
- partners                     100.0  (1 features)
- contacts                     100.0  (1 features)
- seo                          100.0  (1 features)
- quality                      100.0  (1 features)

## Missing, in build order
- [must] leads: Lead delivery to e-mail or Telegram, partial  (server.py stores leads to leads.jsonl; forwarding to e-mail/Telegram/CRM not wired (needs your credentials))
- [must] legal: Legal pages (privacy + consent), partial  (pages exist but text is a template stub: a lawyer must replace it)
- [must] shell: Header phone + e-mail + social icons, partial  (built; contact data are placeholders)
- [should] blog: Video blog list (9) with modal player, partial  (player works for YouTube/Vimeo/Rutube/VK embed URLs; no URLs set yet (shows a note))
- [should] home: Download catalogue form (e-mail + phone), partial  (form + e-mail validation + stored lead work; no catalogue file is actually sent (no PDF exists yet))
- [could] backend: Their CRM and lead inbox, no  (private)
- [could] content: Brand name / logo / product names, no  (not cloneable: replaced in replica-brand)
- [could] content: Real photos and video, no  (not cloneable: owned by the company)
- [could] home: Team / masters block, partial  (built with placeholder names and an icon avatar)

## Screens
- replica/clone-screens/same-viewport/S01-home-desktop.png  26.9
- replica/clone-screens/same-viewport/S04-grill-zona-desktop.png  35.5
- replica/clone-screens/same-viewport/S03-grill-station-desktop.png  38.7

## Fix in the matrix
- line 37: priority 'skip' is not must/should/could, counted as could
- line 38: priority 'skip' is not must/should/could, counted as could
- line 39: priority 'skip' is not must/should/could, counted as could

## Layout score, honestly
27 / 39 / 36 on home / grill-station / grill-zona at 1440 wide: all "DIFFERENT". Section order and card structure follow the original, so I do not read this as a structural failure. Two likely reasons, only the first was tested: (1) vertical rhythm: matching header, hero, model banner and stat-tile heights lifted the two catalogue pages by +10 and +5 but not the home page; (2) the pictures differ by design (illustrated placeholders vs real photos), and the score compares edges. Not chased further: pixel parity with the original is its trade dress and is meant to change.

## Behaviour differences
| flow | original does | clone does | fix or keep |
| --- | --- | --- | --- |
| F01/F02 lead form | name + phone (+ e-mail on some), consent line | same fields, phone mask + validation, 5 error/success states | keep |
| F03 catalogue | form, then catalogue arrives | form + stored lead, no file sent | fix: add a PDF + mail send |
| F04 video | plays video | player ready, no URLs | fix: add embed URLs in content.json |
| F06 side dock | 4 buttons | 4 buttons, collapsible; bottom bar on phones | keep |
| product slider | arrows + thumbs | arrows + thumbs + arrow keys, no swipe | fix later: swipe |

Clicks on the main path: hero CTA, phone, submit = 3 (same as the original's best case).

## Verdict
**Not shippable yet**, by the skill's rule (3 must-haves partial). All three are outside code: lead forwarding needs your e-mail/Telegram credentials, legal text needs a lawyer, contacts need your real data. Feature parity 89.9; 43 automated browser checks pass; contrast 13 pairs, 0 AA failures; 450 internal links and assets resolve.

## Build next (top 5)
1. Real brand, phones, e-mail, addresses in src/content.json (replica-brand).
2. Wire lead delivery (Telegram bot or e-mail) in server.py, or point the form at your CRM.
3. Real photos/video: drop files into the site and replace the scene() calls.
4. Lawyer-reviewed privacy and consent texts.
5. Catalogue PDF and video URLs.
