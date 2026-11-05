/* Behaviour for the static site. No dependencies. Content is already in the HTML. */
(function () {
  'use strict';
  var $ = function (s, r) { return (r || document).querySelector(s); };
  var $$ = function (s, r) { return Array.prototype.slice.call((r || document).querySelectorAll(s)); };

  var MSG = {
    phone: 'Введите телефон полностью, например +7 (900) 123-45-67.',
    email: 'Похоже, в e-mail ошибка.',
    consent: 'Нужно согласие на обработку данных.',
    network: 'Не удалось отправить. Позвоните нам, пожалуйста.',
    sending: 'Отправляем…'
  };
  var TITLES = { order: 'Заявка на изделие', calc: 'Расчёт проекта', catalog: 'Получить каталог', callback: 'Перезвоните мне' };

  /* ---------- header: burger + models dropdown ---------- */
  var nav = $('#nav'), burger = $('.burger');
  if (burger && nav) {
    burger.addEventListener('click', function () {
      var open = nav.classList.toggle('is-open');
      burger.setAttribute('aria-expanded', String(open));
      burger.setAttribute('aria-label', open ? 'Закрыть меню' : 'Открыть меню');
    });
  }
  $$('.has-sub').forEach(function (li) {
    var b = $('.nav__btn', li);
    function set(v) { li.classList.toggle('is-open', v); b.setAttribute('aria-expanded', String(v)); }
    b.addEventListener('click', function (e) { e.stopPropagation(); set(!li.classList.contains('is-open')); });
    li.addEventListener('mouseenter', function () { if (matchMedia('(hover:hover) and (min-width:901px)').matches) set(true); });
    li.addEventListener('mouseleave', function () { if (matchMedia('(hover:hover) and (min-width:901px)').matches) set(false); });
    document.addEventListener('click', function (e) { if (!li.contains(e.target)) set(false); });
    li.addEventListener('keydown', function (e) { if (e.key === 'Escape') { set(false); b.focus(); } });
  });

  /* ---------- side dock ---------- */
  var dock = $('.dock');
  if (dock) {
    var t = $('.dock__t', dock);
    t.addEventListener('click', function () {
      var min = dock.classList.toggle('is-min');
      t.setAttribute('aria-expanded', String(!min));
      t.setAttribute('aria-label', min ? 'Развернуть панель связи' : 'Свернуть панель связи');
    });
  }
  $$('[data-top]').forEach(function (a) {
    a.addEventListener('click', function (e) { e.preventDefault(); window.scrollTo({ top: 0, behavior: 'smooth' }); });
  });

  /* ---------- product sliders ---------- */
  $$('[data-slider]').forEach(function (s) {
    var slides = $$('.slide', s), thumbs = $$('.thumb', s), cur = 0;
    function go(i) {
      cur = (i + slides.length) % slides.length;
      slides.forEach(function (el, k) { el.classList.toggle('is-on', k === cur); });
      thumbs.forEach(function (el, k) { el.classList.toggle('is-on', k === cur); el.setAttribute('aria-current', String(k === cur)); });
    }
    $$('[data-dir]', s).forEach(function (b) { b.addEventListener('click', function () { go(cur + Number(b.dataset.dir)); }); });
    thumbs.forEach(function (b) { b.addEventListener('click', function () { go(Number(b.dataset.go)); }); });
    s.addEventListener('keydown', function (e) {
      if (e.key === 'ArrowLeft') go(cur - 1);
      if (e.key === 'ArrowRight') go(cur + 1);
    });
  });

  /* ---------- dialogs ---------- */
  function openDialog(d) { if (d.showModal) d.showModal(); else d.setAttribute('open', ''); }
  function closeDialog(d) { if (d.close) d.close(); else d.removeAttribute('open'); }
  $$('dialog').forEach(function (d) {
    d.addEventListener('click', function (e) {
      if (e.target === d) closeDialog(d); /* click on the backdrop */
      if (e.target.closest && e.target.closest('[data-close]')) closeDialog(d);
    });
    d.addEventListener('close', function () {
      var body = $('#viewer-body'); if (d.id === 'viewer' && body) body.innerHTML = '';
    });
  });

  /* ---------- viewer: photo lightbox + video ---------- */
  var viewer = $('#viewer'), vbody = $('#viewer-body');
  $$('[data-view-img]').forEach(function (b) {
    b.addEventListener('click', function () {
      var im = document.createElement('img');
      im.src = b.dataset.viewImg; im.alt = ($('img', b) || {}).alt || '';
      vbody.innerHTML = ''; vbody.appendChild(im); openDialog(viewer);
    });
  });
  $$('[data-view-video]').forEach(function (b) {
    b.addEventListener('click', function () {
      var url = b.dataset.viewVideo; vbody.innerHTML = '';
      var ok = /^https:\/\/(www\.)?(youtube(-nocookie)?\.com|player\.vimeo\.com|rutube\.ru|vk\.com)\//.test(url || '');
      if (ok) {
        var f = document.createElement('iframe');
        f.src = url; f.allow = 'autoplay; fullscreen; picture-in-picture'; f.allowFullscreen = true;
        f.title = 'Видео'; f.referrerPolicy = 'strict-origin-when-cross-origin';
        vbody.appendChild(f);
      } else {
        var p = document.createElement('p'); p.className = 'viewer__empty';
        p.textContent = 'Видео пока не подключено. Добавьте ссылку в content.json (поле url), и здесь появится плеер.';
        vbody.appendChild(p);
      }
      openDialog(viewer);
    });
  });

  /* ---------- lead forms ---------- */
  var epMeta = $('meta[name="lead-endpoint"]');
  var endpoint = epMeta ? epMeta.content : '/api/lead'; /* empty = demo build: nothing is sent */
  var lead = $('#lead');

  function formatPhone(v) {
    var d = v.replace(/\D/g, '');
    if (d[0] === '8') d = '7' + d.slice(1);
    if (d[0] !== '7') d = '7' + d;
    d = d.slice(0, 11);
    var o = '+7';
    if (d.length > 1) o += ' (' + d.slice(1, 4);
    if (d.length >= 4) o += ')';
    if (d.length > 4) o += ' ' + d.slice(4, 7);
    if (d.length > 7) o += '-' + d.slice(7, 9);
    if (d.length > 9) o += '-' + d.slice(9, 11);
    return o;
  }
  function digits(v) { return v.replace(/\D/g, ''); }

  function openLead(mode, product) {
    var f = $('form', lead);
    reset(f);
    $('#lead-title').textContent = TITLES[mode] || TITLES.order;
    $('#lead-prod').textContent = product || '';
    f.elements.source.value = mode || 'order';
    f.elements.product.value = product || '';
    var em = $('[data-catalog-only]', f);
    if (em) em.hidden = mode !== 'catalog';
    $('.ok', lead).hidden = true; f.hidden = false;
    $('.ok__cat', lead).hidden = mode !== 'catalog';
    openDialog(lead);
    setTimeout(function () { var n = f.elements.name; if (n) n.focus(); }, 30);
  }
  $$('[data-lead-open]').forEach(function (b) {
    b.addEventListener('click', function () { openLead(b.dataset.leadOpen, b.dataset.product || ''); });
  });

  function reset(f) {
    $('.err', f).textContent = '';
    $$('input', f).forEach(function (i) { i.removeAttribute('aria-invalid'); });
    var btn = $('button[type=submit]', f); btn.disabled = false;
    if (btn.dataset.label) $('.btn__t', btn).textContent = btn.dataset.label;
  }

  $$('form[data-lead]').forEach(function (f) {
    var phone = f.elements.phone;
    phone.addEventListener('input', function () { phone.value = digits(phone.value).length ? formatPhone(phone.value) : ''; });
    phone.addEventListener('focus', function () { if (!phone.value) phone.value = '+7'; });
    phone.addEventListener('blur', function () { if (digits(phone.value).length <= 1) phone.value = ''; });
    f.addEventListener('submit', function (e) { e.preventDefault(); submit(f); });
  });

  function fail(f, field, text) {
    $('.err', f).textContent = text;
    if (field) { field.setAttribute('aria-invalid', 'true'); field.focus(); }
  }

  function submit(f) {
    var els = f.elements, btn = $('button[type=submit]', f), label = $('.btn__t', btn);
    $$('input', f).forEach(function (i) { i.removeAttribute('aria-invalid'); });
    $('.err', f).textContent = '';
    if (digits(els.phone.value).length !== 11) return fail(f, els.phone, MSG.phone);
    var emailEl = els.email;
    if (emailEl && emailEl.value && !(emailEl.offsetParent === null) && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(emailEl.value)) return fail(f, emailEl, MSG.email);
    if (!els.consent.checked) return fail(f, els.consent, MSG.consent);

    btn.dataset.label = label.textContent; btn.disabled = true; label.textContent = MSG.sending;
    if (!endpoint) { setTimeout(function () { done(f, true); }, 350); return; }
    var src = els.source.value || f.dataset.source || 'form';
    var data = {
      name: els.name.value.trim(), phone: els.phone.value, email: emailEl && emailEl.offsetParent !== null ? emailEl.value.trim() : '',
      source: src, product: els.product.value, website: els.website.value, page: location.pathname, consent: true
    };
    fetch(endpoint, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(data) })
      .then(function (r) { if (!r.ok) throw new Error(String(r.status)); return r.json(); })
      .then(function () { done(f); })
      .catch(function () { btn.disabled = false; label.textContent = btn.dataset.label; $('.err', f).textContent = MSG.network; });
  }

  function done(f, demo) {
    var box = f.closest('dialog') ? $('.ok', f.closest('dialog')) : f.parentNode.querySelector('.ok');
    if (demo && box) { var note = $('.ok__t', box) || $('p', box); if (note) note.textContent = 'Это демонстрационная версия: заявка никуда не отправляется.'; var cat = $('.ok__cat', box); if (cat) cat.hidden = true; }
    f.reset();
    f.hidden = true; if (box) { box.hidden = false; var h = $('h2,h3', box); if (h) { h.setAttribute('tabindex', '-1'); h.focus(); } }
    var btn = $('button[type=submit]', f); btn.disabled = false; if (btn.dataset.label) $('.btn__t', btn).textContent = btn.dataset.label;
  }
})();
