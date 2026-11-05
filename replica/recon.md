# Recon map: bestmangal.pro (clean-room)

Date: 2026-11-05. Sources: public pages only, read at human pace (home + 9 pages, sitemap.xml, robots.txt), plus 2 headless reference screenshots. No JS bundles read, no network/API inspection, no logins.

## 1. Scope

- **App:** bestmangal.pro, a marketing + catalog site of a Russian manufacturer of custom stainless-steel grill stations, BBQ complexes and outdoor kitchens. Web, desktop + mobile.
- **Slice:** the whole public site (10 pages). There is no cart or checkout: every "Заказать" opens a lead form. The core loop is **visitor browses models, sees a price, leaves a phone number**.
- **Who it is for:** assumed to be a rebuild for a client in the same niche, so brand, copy and photos are replaced (clean-room). All text and image paths live in one content file so the owner can drop in their own.

## 2. Sources

| source | URL | gives |
| --- | --- | --- |
| sitemap | https://bestmangal.pro/sitemap.xml | 10 URLs, the full page list |
| home | https://bestmangal.pro/ | positioning, section order, stats, lead forms |
| model pages | /grill-station /grill-zona /grill-na-kolesah /kuhni-nerjaveika /kupeli | product cards, price, spec accordions |
| portfolio | /portfolio | project gallery with prices |
| video blog | /blog | list of video cards |
| partners | /partner | B2B terms, how to apply |
| contacts | /contact | two sites (factory + showroom) |

## 3. Screen inventory

| ID | screen | route | purpose | key components | states |
| --- | --- | --- | --- | --- | --- |
| S01 | Home | / | pitch and funnel to models | header, hero, trust badges, about + stats, gallery mosaic, models showcase, "not sure?" CTA, process steps, team, expert-consult form, footer, side dock | desktop, mobile, modal open |
| S02 | Portfolio | /portfolio | proof by completed projects | gallery grid, project card (title, spec line, price) | desktop |
| S03 | Grill stations | /grill-station | catalog of "Джин" family (6 cards) | hero banner, product card with slider, spec accordion, price, order button | accordion open/closed, slider |
| S04 | Grill zones | /grill-zona | BBQ complexes (4) + modules (7, with sizes) | same product card, module card | desktop |
| S05 | Portable | /grill-na-kolesah | wheeled grills (4 items) | product card | desktop |
| S06 | Steel kitchens | /kuhni-nerjaveika | premium kitchens A-Mini..Ultra + bars | product card, grouped | desktop |
| S07 | Tubs / grill tables | /kupeli | hearths, grill table, hot tubs | product card, grouped | desktop |
| S08 | Video blog | /blog | 9 video entries | video card, modal player | desktop |
| S09 | Partners | /partner | B2B terms | text blocks, numbered steps, phone | desktop |
| S10 | Contacts | /contact | where to find them | two address blocks | desktop |
| S11 | Lead modal | overlay | "Заказать" / "Рассчитать" / callback | name, phone, (email), consent, submit | empty, error, sent |
| S12 | Legal pages | /regulation.html /consent.html | personal-data docs | plain text | n/a |

Not in the sitemap but linked: S12 only. There are no individual product detail pages: details live in accordions on the category page.

## 4. Flows

```
F01 Visitor leaves a request from the home hero
    S01 hero "Рассчитать стоимость проекта" -> S11 modal -> sent
    edge: empty phone, no consent ticked, double submit
    clicks to beat: 3 (CTA, type phone, submit)

F02 Visitor picks a model and orders
    S01 models showcase -> S03..S07 category page -> read card, open accordion -> "Заказать" -> S11 -> sent
    edge: slider left/right, accordion open/close, price formatting

F03 Visitor downloads the catalogue
    S01 "Скачать каталог" -> S11 (email + phone) -> sent
    (original gives a file after submit; clone shows a "check your inbox" state)

F04 Visitor reviews proof
    S01 gallery mosaic -> S02 portfolio, or video card -> play video

F05 Business partner applies
    S09 -> reads steps -> e-mail or phone (no on-site form)

F06 Visitor contacts quickly
    side dock (Telegram / VK / call / up) from any page
```

## 5. Components

| component | variants / states | used on |
| --- | --- | --- |
| Header | black bar, logo, nav, dropdown "Модели", social icons, phone + email; burger on mobile | all |
| Models dropdown | hover/click, 5 items | all |
| Button | primary red, secondary grey with play icon, hover, disabled | all |
| Hero | full-bleed photo + headline + CTA + badge strip | S01, S03 |
| Section label | small grey label + hairline | S01 |
| Stat tile | red or black rounded tile, big number + caption | S01 |
| Gallery mosaic | mixed photo/video tiles, lightbox | S01, S02 |
| Product card | title (white + red part), image slider with thumbs, spec list, accordions, price, order button | S03..S07 |
| Accordion row | "+" to "−", 3 per card | S03..S07 |
| Showcase banner | big dark image card, text right, 2 buttons, "PREMIUM" stamp | S01 |
| Step card | numbered process | S01 |
| Team card | photo, name, role | S01 |
| Lead form | name / phone / email, consent checkbox | S11, S01 |
| Modal | close, overlay | S11, video |
| Side dock | 4 vertical buttons, collapsible | all |
| Footer | contacts, two addresses, legal entity, hours, links | all |
| Cookie / consent line | none seen | none |

## 6. Inferred data model

```
Product   id, category (station|zone|portable|kitchen|tub), name, subtitle,
          dims_closed, dims_open, color, price_rub, images[], badge,
          groups: { work_zones[], functional[], services[] }
          evidence: S03 cards   confidence: high
Project   id, title, spec_line, price_rub, image, kind (photo|video)
          evidence: S02          confidence: high
Video     id, title, thumbnail, url   evidence: S08   confidence: high
Lead      id, name, phone, email?, source (hero|model:<id>|catalog|consult),
          consent_at, created_at, status
          evidence: S11 fields, labels   confidence: medium (no backend seen)
Contact   site (factory|showroom), address, phones[], hours   confidence: high
```

Everything except Lead is static content. Lead needs a place to land (e-mail, Telegram bot or a CRM webhook).

## 7. Feature matrix

See `features.csv`.

## 8. What cannot be cloned

| item | why |
| --- | --- |
| Photos, 3D renders, videos, logo, team portraits | owned by the company; replaced with original placeholders |
| Marketing copy, product names, "Джин", "Чебурашка" etc. | their text and trade names; rewritten and renamed |
| Company facts: 3500 projects, founded 2014, "lifetime warranty", INN, addresses | facts about them, not us; placeholders in the clone |
| Their CRM / lead delivery | private; the clone gets its own endpoint |
| SEO position and domain | not transferable |

## 9. Size

- Screens: 12 (10 real pages + modal + legal). Flows: 6. Entities: 5 (4 static).
- Hard parts: (1) the product card with slider + accordion + thumbs that repeats ~30 times from data, (2) lead delivery (spam protection, consent log), (3) video lightbox without embedding their channel.
- Out of scope: payments, accounts, a CMS (content in a data file).
- Size: **S** (a weekend). Static site + one small form endpoint.

Next step: `/replica-architect`.
