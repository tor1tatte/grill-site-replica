# Component specs (S-size site; tokens only, see tokens.css)

Button
  variants  primary (accent), ghost (surface), sizes sm 40 / md 48 / lg 56
  states    default, hover (brightness), active (1px down), focus-visible (3px accent ring), disabled/sending (label changes, aria stays)
  a11y      real <button> or <a>; min target 48px
  used on   all pages

Header + models dropdown
  black bar, 88px; dropdown is a button with aria-expanded; opens on click, hover (desktop pointer only), closes on Escape/outside click; burger below 900px
  used on   all pages

Product card
  title (prefix in text colour, name in accent), slider (arrows, thumbs, arrow keys), info card (dimensions, 3 native <details> accordions, note, price, order)
  states    accordion open/closed, slide 1/2; mobile stacks title, media, info
  used on   S03-S07

Module card  image, name, size, price, order. used on S04

Lead form / modal  native <dialog>; name, phone (mask), e-mail (catalogue only), consent, honeypot
  states    empty, error (phone/e-mail/consent/network, role=alert), sending, sent; Escape and backdrop close; focus moves to the first field, then to the success heading
  used on   S01, S03-S07, S11

Viewer  dialog with image (lightbox) or iframe for https YouTube/Vimeo/Rutube/VK URLs only; otherwise a note. used on S01, S02, S08

Side dock  4 buttons, collapsible; becomes a bottom bar under 640px. used on all pages

Stat tile, step card, team card, showcase banner, mosaic tile: presentational, see style.css.
