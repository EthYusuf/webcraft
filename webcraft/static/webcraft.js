/*!
 * WebCraft.js v0.1.0
 * Declarative component library for building modern websites from a JSON spec.
 * Used standalone in the browser or driven by the `webcraft` Python package.
 * MIT License
 */
(function (global) {
  'use strict';

  const VERSION = '0.1.0';
  const registry = Object.create(null);

  // ------------------------------------------------------------------
  // Theme presets
  // ------------------------------------------------------------------
  const themes = {
    light: {
      primary: '#4f46e5', secondary: '#06b6d4', background: '#ffffff', surface: '#f8fafc',
      text: '#0f172a', muted: '#64748b', border: '#e2e8f0', font: 'Inter',
    },
    dark: {
      primary: '#818cf8', secondary: '#22d3ee', background: '#0b1120', surface: '#131c31',
      text: '#e2e8f0', muted: '#94a3b8', border: '#1e293b', font: 'Inter',
    },
    ocean: {
      primary: '#0ea5e9', secondary: '#14b8a6', background: '#f0f9ff', surface: '#ffffff',
      text: '#0c4a6e', muted: '#4b7a96', border: '#bae6fd', font: 'Poppins',
    },
    sunset: {
      primary: '#f97316', secondary: '#ec4899', background: '#fff7ed', surface: '#ffffff',
      text: '#431407', muted: '#9a5b3c', border: '#fed7aa', font: 'Poppins',
    },
    forest: {
      primary: '#16a34a', secondary: '#ca8a04', background: '#f7fee7', surface: '#ffffff',
      text: '#14280f', muted: '#5b7052', border: '#d9f99d', font: 'Nunito',
    },
    midnight: {
      primary: '#a855f7', secondary: '#f472b6', background: 'linear-gradient(160deg, #0f0c29 0%, #1e1b4b 50%, #0f0c29 100%)',
      background_color: '#120f2e', surface: 'rgba(255,255,255,0.05)', text: '#ede9fe', muted: '#a5a3c9',
      border: 'rgba(255,255,255,0.1)', font: 'Space Grotesk',
    },
    minimal: {
      primary: '#111111', secondary: '#555555', background: '#fafafa', surface: '#ffffff',
      text: '#111111', muted: '#6b6b6b', border: '#e5e5e5', font: 'DM Sans', radius: '4px',
    },
  };

  const THEME_VARS = {
    primary: '--wc-primary',
    secondary: '--wc-secondary',
    background_color: '--wc-bg',
    surface: '--wc-surface',
    text: '--wc-text',
    muted: '--wc-muted',
    border: '--wc-border',
    radius: '--wc-radius',
    max_width: '--wc-max-width',
    font_size: '--wc-font-size',
  };

  const SYSTEM_FONTS = [
    'system-ui', 'sans-serif', 'serif', 'monospace', 'arial', 'helvetica', 'georgia',
    'times new roman', 'verdana', 'tahoma', 'courier new', 'segoe ui',
  ];

  // ------------------------------------------------------------------
  // Helpers
  // ------------------------------------------------------------------
  function h(tag, attrs, ...children) {
    const el = document.createElement(tag);
    if (attrs) {
      for (const key in attrs) {
        const value = attrs[key];
        if (value == null || value === false) continue;
        if (key === 'class') el.className = value;
        else if (key === 'style' && typeof value === 'object') Object.assign(el.style, value);
        else if (key === 'html') el.innerHTML = value;
        else if (key.startsWith('on') && typeof value === 'function') el.addEventListener(key.slice(2), value);
        else el.setAttribute(key, value === true ? '' : value);
      }
    }
    children.forEach((child) => append(el, child));
    return el;
  }

  function append(parent, child) {
    if (child == null || child === false) return;
    if (Array.isArray(child)) return child.forEach((c) => append(parent, c));
    parent.appendChild(child.nodeType ? child : document.createTextNode(String(child)));
  }

  function escapeHtml(str) {
    return String(str)
      .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;').replace(/'/g, '&#39;');
  }

  function safeUrl(url) {
    if (url == null) return '#';
    const s = String(url).trim();
    return /^(javascript|vbscript|data:text\/html)/i.test(s) ? '#' : s;
  }

  /** Escapes text, then applies a tiny markdown subset: **bold**, *italic*, `code`, [link](url). */
  function rich(str) {
    if (str == null) return '';
    let out = escapeHtml(str);
    out = out.replace(/`([^`]+)`/g, '<code>$1</code>');
    out = out.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>');
    out = out.replace(/\*([^*]+)\*/g, '<em>$1</em>');
    out = out.replace(/\[([^\]]+)\]\(([^)\s]+)\)/g, (_, text, href) => `<a href="${escapeHtml(safeUrl(href))}">${text}</a>`);
    return out.replace(/\n/g, '<br>');
  }

  function richEl(tag, text, cls) {
    return h(tag, { class: cls, html: rich(text) });
  }

  function paragraphs(text, cls) {
    return String(text).split(/\n\s*\n/).map((p) => richEl('p', p, cls));
  }

  function container(...children) {
    return h('div', { class: 'wc-container' }, ...children);
  }

  function sectionHeader(p) {
    if (!p.title && !p.subtitle) return null;
    return h('div', { class: 'wc-section-header' },
      p.title ? richEl('h2', p.title, 'wc-section-title') : null,
      p.subtitle ? richEl('p', p.subtitle, 'wc-section-subtitle') : null);
  }

  function button(b, extraClass) {
    if (!b) return null;
    if (typeof b === 'string') b = { text: b };
    const style = b.style || 'primary';
    return h('a', {
      class: `wc-btn wc-btn-${style}${extraClass ? ' ' + extraClass : ''}`,
      href: safeUrl(b.href || '#'),
      target: b.new_tab ? '_blank' : null,
      rel: b.new_tab ? 'noopener noreferrer' : null,
    }, b.icon ? h('span', { class: 'wc-btn-icon' }, b.icon) : null, b.text);
  }

  function gridStyle(columns) {
    return columns ? { '--wc-cols': String(columns) } : null;
  }

  function isCssImageOrGradient(value) {
    return /(gradient\(|url\()/i.test(String(value));
  }

  function loadFont(name) {
    if (!name || SYSTEM_FONTS.includes(String(name).toLowerCase())) return;
    if (document.querySelector(`link[data-wc-font="${CSS.escape(name)}"]`)) return;
    const link = document.createElement('link');
    link.rel = 'stylesheet';
    link.href = `https://fonts.googleapis.com/css2?family=${encodeURIComponent(name).replace(/%20/g, '+')}:wght@400;500;600;700;800&display=swap`;
    link.setAttribute('data-wc-font', name);
    document.head.appendChild(link);
  }

  function fontStack(name) {
    return `'${String(name).replace(/'/g, '')}', system-ui, -apple-system, 'Segoe UI', sans-serif`;
  }

  // ------------------------------------------------------------------
  // Theme engine
  // ------------------------------------------------------------------
  function resolveTheme(theme) {
    theme = theme || {};
    const base = themes[theme.preset] || themes.light;
    const merged = Object.assign({}, base, theme);
    // An explicit background overrides the preset's solid fallback colour too.
    if (theme.background && !theme.background_color && !isCssImageOrGradient(theme.background)) {
      merged.background_color = theme.background;
    }
    if (!merged.background_color) {
      merged.background_color = isCssImageOrGradient(merged.background) ? (base.background_color || '#ffffff') : merged.background;
    }
    return merged;
  }

  function applyTheme(theme, root) {
    const t = resolveTheme(theme);
    const style = (root || document.documentElement).style;
    for (const key in THEME_VARS) {
      if (t[key] != null) style.setProperty(THEME_VARS[key], String(t[key]));
    }
    style.setProperty('--wc-page-bg', t.background);
    if (t.background_image) {
      style.setProperty('--wc-page-bg', `${t.background_overlay ? `linear-gradient(${t.background_overlay}, ${t.background_overlay}), ` : ''}url("${t.background_image}") center / cover fixed, ${t.background_color}`);
    }
    if (t.font) { loadFont(t.font); style.setProperty('--wc-font', fontStack(t.font)); }
    const heading = t.heading_font || t.font;
    if (heading) { loadFont(heading); style.setProperty('--wc-heading-font', fontStack(heading)); }
    if (t.dark != null) document.documentElement.classList.toggle('wc-dark', !!t.dark);
    return t;
  }

  // ------------------------------------------------------------------
  // Component registry
  // ------------------------------------------------------------------
  function register(name, renderFn) {
    if (typeof renderFn !== 'function') throw new TypeError('WebCraft.register: renderFn must be a function');
    registry[name] = renderFn;
  }

  function renderComponent(node) {
    if (!node || !node.type) return null;
    const fn = registry[node.type];
    if (!fn) {
      console.warn(`[WebCraft] Unknown component "${node.type}"`);
      return null;
    }
    const props = node.props || {};
    const el = fn(props, node);
    return el ? decorate(el, props) : null;
  }

  /** Applies props shared by every component: id, background, color, padding, animation, class. */
  function decorate(el, p) {
    if (p.id) el.id = p.id;
    if (p.class) el.classList.add(...String(p.class).split(/\s+/).filter(Boolean));
    if (p.background) {
      if (isCssImageOrGradient(p.background)) el.style.background = p.background;
      else el.style.backgroundColor = p.background;
    }
    if (p.color) el.style.color = p.color;
    if (p.padding != null) {
      const pad = typeof p.padding === 'number' ? `${p.padding}px` : p.padding;
      el.style.paddingTop = pad; el.style.paddingBottom = pad;
    }
    if (p.align) el.style.textAlign = p.align;
    const anim = p.animate === undefined ? el.dataset.wcDefaultAnim : p.animate;
    if (anim && anim !== 'none') el.setAttribute('data-wc-animate', anim);
    if (p.style && typeof p.style === 'object') Object.assign(el.style, p.style);
    return el;
  }

  function block(...children) {
    const el = h('section', { class: 'wc-block' }, container(...children));
    el.dataset.wcDefaultAnim = 'fade-up';
    return el;
  }

  // ------------------------------------------------------------------
  // Built-in components
  // ------------------------------------------------------------------
  register('navbar', (p) => {
    const links = h('nav', { class: 'wc-nav-links' },
      (p.links || []).map((l) => h('a', { href: safeUrl(l.href) }, l.text)),
      p.cta ? button(p.cta, 'wc-btn-sm') : null);
    const logo = h('a', { class: 'wc-logo', href: safeUrl(p.logo_href || '#') },
      p.logo_image ? h('img', { src: p.logo_image, alt: p.logo || 'logo' }) : null,
      p.logo ? h('span', null, p.logo) : null);
    const bar = h('header', { class: `wc-navbar${p.sticky === false ? '' : ' wc-sticky'}${p.transparent ? ' wc-transparent' : ''}` });
    const toggle = h('button', {
      class: 'wc-nav-toggle', type: 'button', 'aria-label': 'Menu',
      onclick: () => bar.classList.toggle('wc-open'),
    }, h('span'), h('span'), h('span'));
    links.addEventListener('click', (e) => { if (e.target.closest('a')) bar.classList.remove('wc-open'); });
    append(bar, h('div', { class: 'wc-container wc-nav-inner' }, logo, links, toggle));
    if (p.sticky !== false) {
      const onScroll = () => bar.classList.toggle('wc-scrolled', window.scrollY > 8);
      window.addEventListener('scroll', onScroll, { passive: true });
      onScroll();
    }
    return bar;
  });

  register('hero', (p) => {
    const align = p.align || 'center';
    const content = h('div', { class: 'wc-hero-content' },
      p.badge ? h('span', { class: 'wc-badge' }, p.badge) : null,
      richEl('h1', p.title || '', 'wc-hero-title'),
      p.subtitle ? richEl('p', p.subtitle, 'wc-hero-subtitle') : null,
      p.buttons && p.buttons.length ? h('div', { class: 'wc-btn-row' }, p.buttons.map((b) => button(b))) : null);
    const media = p.image ? h('div', { class: 'wc-hero-media' }, h('img', { src: p.image, alt: p.image_alt || '' })) : null;
    const hero = h('section', { class: `wc-hero wc-hero-${align}${media ? ' wc-hero-split' : ''}${p.full_height ? ' wc-hero-full' : ''}` },
      h('div', { class: 'wc-hero-glow', 'aria-hidden': 'true' }),
      container(h('div', { class: 'wc-hero-grid' }, content, media)));
    if (p.background_image) {
      const overlay = p.overlay || 'rgba(0,0,0,0.55)';
      hero.style.background = `linear-gradient(${overlay}, ${overlay}), url("${p.background_image}") center / cover`;
      hero.classList.add('wc-hero-photo');
    }
    hero.dataset.wcDefaultAnim = 'fade-up';
    return hero;
  });

  register('heading', (p) => {
    const level = Math.min(Math.max(parseInt(p.level, 10) || 2, 1), 6);
    return block(
      richEl(`h${level}`, p.text || '', 'wc-heading'),
      p.subtitle ? richEl('p', p.subtitle, 'wc-section-subtitle') : null);
  });

  register('text', (p) => {
    const el = block(h('div', { class: `wc-text${p.size ? ` wc-text-${p.size}` : ''}` }, paragraphs(p.text || '')));
    el.classList.add('wc-block-tight');
    return el;
  });

  register('button', (p) => {
    const el = block(h('div', { class: 'wc-btn-row' }, button(p)));
    el.classList.add('wc-block-tight');
    return el;
  });

  register('image', (p) => block(h('figure', { class: `wc-figure${p.rounded === false ? '' : ' wc-rounded'}` },
    h('img', { src: p.src, alt: p.alt || '', loading: 'lazy', style: p.width ? { maxWidth: typeof p.width === 'number' ? `${p.width}px` : p.width } : null }),
    p.caption ? richEl('figcaption', p.caption) : null)));

  register('video', (p) => {
    let src = String(p.src || '');
    const yt = src.match(/(?:youtube\.com\/(?:watch\?v=|embed\/|shorts\/)|youtu\.be\/)([\w-]{6,})/);
    const vimeo = src.match(/vimeo\.com\/(\d+)/);
    let media;
    if (yt) src = `https://www.youtube-nocookie.com/embed/${yt[1]}`;
    else if (vimeo) src = `https://player.vimeo.com/video/${vimeo[1]}`;
    if (yt || vimeo) {
      media = h('iframe', { src, title: p.title || 'video', allow: 'accelerometer; autoplay; clipboard-write; encrypted-media; picture-in-picture', allowfullscreen: true, loading: 'lazy' });
    } else {
      media = h('video', { src, controls: true, playsinline: true, poster: p.poster });
    }
    return block(sectionHeader(p), h('div', { class: 'wc-video' }, media));
  });

  register('features', (p) => block(
    sectionHeader(p),
    h('div', { class: 'wc-grid', style: gridStyle(p.columns || 3) }, (p.items || []).map((it, i) => h('article', {
      class: 'wc-card wc-feature', style: { '--wc-i': i },
    },
    it.image ? h('img', { class: 'wc-card-img', src: it.image, alt: it.title || '', loading: 'lazy' }) : null,
    it.icon ? h('div', { class: 'wc-feature-icon' }, it.icon) : null,
    it.title ? richEl('h3', it.title) : null,
    it.text ? richEl('p', it.text, 'wc-muted') : null,
    it.link ? button(Object.assign({ style: 'link' }, it.link)) : null)))));

  register('stats', (p) => block(
    sectionHeader(p),
    h('div', { class: 'wc-stats', style: gridStyle(p.columns || Math.min((p.items || []).length, 4)) },
      (p.items || []).map((s) => h('div', { class: 'wc-stat' },
        h('div', { class: 'wc-stat-value', 'data-wc-count': s.value }, s.value),
        h('div', { class: 'wc-stat-label' }, s.label))))));

  register('gallery', (p) => block(
    sectionHeader(p),
    h('div', { class: 'wc-gallery', style: gridStyle(p.columns || 3) }, (p.images || []).map((img) => {
      if (typeof img === 'string') img = { src: img };
      return h('a', { class: 'wc-gallery-item', href: img.src, target: '_blank', rel: 'noopener' },
        h('img', { src: img.src, alt: img.alt || '', loading: 'lazy' }),
        img.caption ? h('span', { class: 'wc-gallery-caption' }, img.caption) : null);
    }))));

  register('testimonials', (p) => block(
    sectionHeader(p),
    h('div', { class: 'wc-grid', style: gridStyle(p.columns || 3) }, (p.items || []).map((t) => h('figure', { class: 'wc-card wc-testimonial' },
      h('div', { class: 'wc-stars', 'aria-hidden': 'true' }, '★'.repeat(t.rating || 5)),
      richEl('blockquote', t.quote || ''),
      h('figcaption', null,
        t.avatar
          ? h('img', { class: 'wc-avatar', src: t.avatar, alt: t.name || '' })
          : h('span', { class: 'wc-avatar wc-avatar-initials' }, (t.name || '?').split(/\s+/).map((w) => w[0]).slice(0, 2).join('')),
        h('div', null, h('strong', null, t.name || ''), t.role ? h('span', { class: 'wc-muted' }, t.role) : null)))))));

  register('pricing', (p) => block(
    sectionHeader(p),
    h('div', { class: 'wc-grid wc-pricing', style: gridStyle(p.columns || (p.plans || []).length || 3) }, (p.plans || []).map((plan) => h('div', {
      class: `wc-card wc-plan${plan.highlight ? ' wc-plan-highlight' : ''}`,
    },
    plan.highlight ? h('span', { class: 'wc-plan-tag' }, typeof plan.highlight === 'string' ? plan.highlight : 'Popular') : null,
    h('h3', null, plan.name || ''),
    h('div', { class: 'wc-plan-price' }, h('span', null, plan.price || ''), plan.period ? h('small', null, plan.period) : null),
    plan.description ? richEl('p', plan.description, 'wc-muted') : null,
    h('ul', { class: 'wc-plan-features' }, (plan.features || []).map((f) => h('li', { html: rich(f) }))),
    button(Object.assign({ style: plan.highlight ? 'primary' : 'outline' }, plan.button || { text: 'Choose' }), 'wc-btn-block'))))));

  register('faq', (p) => block(
    sectionHeader(p),
    h('div', { class: 'wc-faq' }, (p.items || []).map((it) => h('details', { class: 'wc-faq-item' },
      h('summary', null, it.question),
      h('div', { class: 'wc-faq-answer' }, paragraphs(it.answer || '')))))));

  register('cta', (p) => {
    const el = h('section', { class: 'wc-block' }, container(h('div', { class: 'wc-cta' },
      richEl('h2', p.title || ''),
      p.text ? richEl('p', p.text) : null,
      p.buttons && p.buttons.length ? h('div', { class: 'wc-btn-row' }, p.buttons.map((b) => button(Object.assign({ style: 'light' }, b)))) : null)));
    el.dataset.wcDefaultAnim = 'zoom';
    return el;
  });

  register('contact', (p) => {
    const fields = p.fields || [
      { name: 'name', label: 'Name', type: 'text' },
      { name: 'email', label: 'Email', type: 'email' },
      { name: 'message', label: 'Message', type: 'textarea' },
    ];
    const status = h('p', { class: 'wc-form-status', role: 'status' });
    const form = h('form', { class: 'wc-card wc-form', action: p.action || null, method: p.action ? 'POST' : null },
      fields.map((f) => h('label', { class: 'wc-field' },
        h('span', null, f.label || f.name),
        f.type === 'textarea'
          ? h('textarea', { name: f.name, rows: f.rows || 5, required: f.required !== false, placeholder: f.placeholder || '' })
          : h('input', { name: f.name, type: f.type || 'text', required: f.required !== false, placeholder: f.placeholder || '' }))),
      h('button', { class: 'wc-btn wc-btn-primary wc-btn-block', type: 'submit' }, p.button || 'Send'),
      status);
    form.addEventListener('submit', (e) => {
      if (p.action) return; // Real endpoint (e.g. Formspree) handles it.
      e.preventDefault();
      const data = new FormData(form);
      if (p.email) {
        const body = fields.map((f) => `${f.label || f.name}: ${data.get(f.name) || ''}`).join('\n');
        window.location.href = `mailto:${p.email}?subject=${encodeURIComponent(p.subject || document.title)}&body=${encodeURIComponent(body)}`;
      }
      status.textContent = p.success || 'Thanks! Your message is ready to send.';
      form.reset();
    });
    return block(sectionHeader(p), h('div', { class: 'wc-contact' },
      p.info && p.info.length ? h('div', { class: 'wc-contact-info' }, p.info.map((i) => h('div', { class: 'wc-contact-line' },
        i.icon ? h('span', { class: 'wc-feature-icon' }, i.icon) : null,
        h('div', null, h('strong', null, i.label || ''), h('div', { html: rich(i.value || '') }))))) : null,
      form));
  });

  register('section', (p, node) => {
    const el = h('section', { class: `wc-section${p.full_width ? ' wc-section-full' : ''}` });
    const inner = h('div', { class: 'wc-section-inner' }, (node.children || []).map(renderComponent));
    append(el, p.full_width ? inner : container(sectionHeader(p), inner));
    if (p.full_width && (p.title || p.subtitle)) inner.prepend(container(sectionHeader(p)));
    return el;
  });

  register('columns', (p, node) => {
    const cols = (node.columns || []).map((col) => h('div', { class: 'wc-column' }, (col || []).map(renderComponent)));
    const el = h('section', { class: 'wc-block' }, container(
      h('div', { class: 'wc-columns', style: Object.assign({ '--wc-cols': String(cols.length || 1) }, p.gap ? { gap: `${p.gap}px` } : {}) }, cols)));
    if (p.vertical_align) el.querySelector('.wc-columns').style.alignItems = p.vertical_align;
    return el;
  });

  register('divider', () => h('div', { class: 'wc-container' }, h('hr', { class: 'wc-divider' })));

  register('spacer', (p) => h('div', { 'aria-hidden': 'true', style: { height: typeof p.size === 'number' ? `${p.size}px` : (p.size || '48px') } }));

  register('html', (p) => h('div', { class: 'wc-html', html: p.html || '' }));

  register('footer', (p) => h('footer', { class: 'wc-footer' }, container(
    h('div', { class: 'wc-footer-inner' },
      h('div', null,
        p.logo ? h('div', { class: 'wc-logo' }, p.logo) : null,
        p.text ? richEl('p', p.text, 'wc-muted') : null),
      p.links && p.links.length ? h('nav', { class: 'wc-footer-links' }, p.links.map((l) => h('a', { href: safeUrl(l.href) }, l.text))) : null,
      p.socials && p.socials.length ? h('div', { class: 'wc-socials' }, p.socials.map((s) => h('a', {
        href: safeUrl(s.href), target: '_blank', rel: 'noopener noreferrer', 'aria-label': s.name, title: s.name,
      }, s.icon || s.name))) : null),
    p.copyright ? h('div', { class: 'wc-copyright' }, p.copyright) : null)));

  // ------------------------------------------------------------------
  // Behaviours: reveal-on-scroll + count-up stats
  // ------------------------------------------------------------------
  function countUp(el) {
    const raw = el.getAttribute('data-wc-count') || '';
    const match = raw.match(/^(\D*)([\d.,]+)(.*)$/);
    if (!match) return;
    const [, prefix, numStr, suffix] = match;
    if (/\d/.test(suffix)) return; // e.g. "24/7" — not a single number, keep as-is.
    const decimals = (numStr.split(/[.,]/)[1] || '').length;
    const usesComma = numStr.includes(',') && !numStr.includes('.');
    const target = parseFloat(numStr.replace(/,/g, usesComma && decimals ? '.' : ''));
    if (!isFinite(target)) return;
    const duration = 1400;
    const start = performance.now();
    const tick = (now) => {
      const k = Math.min((now - start) / duration, 1);
      const eased = 1 - Math.pow(1 - k, 3);
      el.textContent = prefix + (target * eased).toFixed(decimals) + suffix;
      if (k < 1) requestAnimationFrame(tick); else el.textContent = raw;
    };
    requestAnimationFrame(tick);
  }

  function setupBehaviours(root) {
    const animated = root.querySelectorAll('[data-wc-animate]');
    const counters = root.querySelectorAll('[data-wc-count]');
    const reduce = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    if (!('IntersectionObserver' in window) || reduce) {
      animated.forEach((el) => el.classList.add('wc-in'));
      return;
    }
    const io = new IntersectionObserver((entries) => {
      entries.forEach((entry) => {
        if (!entry.isIntersecting) return;
        const el = entry.target;
        if (el.hasAttribute('data-wc-count')) countUp(el); else el.classList.add('wc-in');
        io.unobserve(el);
      });
    }, { threshold: 0.12, rootMargin: '0px 0px -40px 0px' });
    animated.forEach((el) => io.observe(el));
    counters.forEach((el) => io.observe(el));
  }

  // ------------------------------------------------------------------
  // Public API
  // ------------------------------------------------------------------
  function render(spec, target) {
    spec = spec || {};
    const mount = typeof target === 'string' ? document.querySelector(target) : (target || document.body);
    if (!mount) throw new Error(`WebCraft.render: target "${target}" not found`);
    applyTheme(spec.theme);
    if (spec.title) document.title = spec.title;
    const page = h('div', { class: 'wc-page' }, (spec.components || []).map(renderComponent));
    mount.innerHTML = '';
    mount.appendChild(page);
    setupBehaviours(page);
    document.documentElement.classList.add('wc-ready');
    return page;
  }

  /** Chainable builder for using WebCraft directly from JavaScript. */
  function site(title) {
    const spec = { title: title || '', theme: {}, components: [] };
    const api = {
      spec,
      theme(nameOrObj) {
        Object.assign(spec.theme, typeof nameOrObj === 'string' ? { preset: nameOrObj } : nameOrObj);
        return api;
      },
      background(value) { spec.theme.background = value; return api; },
      font(name, headingFont) { spec.theme.font = name; if (headingFont) spec.theme.heading_font = headingFont; return api; },
      colors(obj) { Object.assign(spec.theme, obj); return api; },
      add(type, props, extra) { spec.components.push(Object.assign({ type, props: props || {} }, extra)); return api; },
      mount(target) { return render(spec, target); },
      toJSON() { return spec; },
    };
    Object.keys(registry).forEach((type) => {
      if (!(type in api)) api[type] = (props, extra) => api.add(type, props, extra);
    });
    return api;
  }

  function auto() {
    document.querySelectorAll('script[type="application/json"][data-webcraft]').forEach((node) => {
      try {
        render(JSON.parse(node.textContent), node.getAttribute('data-target') || '#app');
      } catch (err) {
        console.error('[WebCraft] Failed to render spec:', err);
      }
    });
  }

  const WebCraft = {
    version: VERSION, themes, register, render, renderComponent, applyTheme, resolveTheme, site, auto,
    utils: { h, rich, escapeHtml, safeUrl, button, block, container, sectionHeader },
    get components() { return Object.keys(registry); },
  };

  global.WebCraft = WebCraft;
  if (typeof module === 'object' && module.exports) module.exports = WebCraft;

  if (typeof document !== 'undefined') {
    if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', auto);
    else auto();
  }
})(typeof window !== 'undefined' ? window : globalThis);
