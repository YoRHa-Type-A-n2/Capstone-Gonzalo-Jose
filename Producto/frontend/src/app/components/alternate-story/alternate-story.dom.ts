/**
 * Utilidades de DOM para el final alterno.
 *
 * Todo trabaja sobre el DOM que ya renderizó el reader, sin tocar su código:
 *  - Los bloques viejos NO se eliminan (Angular los sigue controlando): se ocultan
 *    con display:none y se marcan para poder restaurarlos.
 *  - El texto nuevo va en un contenedor propio (data-alt-story) que Angular no conoce.
 */

/** Mismos bloques que el reader usa para el tap-to-scroll, más algunos de respaldo. */
export const BLOCK_SELECTOR = 'p, h1, h2, h3, h4, h5, h6, blockquote, figure';

const ALT_ATTR = 'data-alt-story';
const HIDDEN_ATTR = 'data-alt-hidden';
const BLOCK_TAGS = new Set(['p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'blockquote', 'figure']);

const textCache = new WeakMap<Element, string>();

/** Deja solo letras y números, sin tildes ni mayúsculas. Tolera espacios y comillas distintos. */
export function normalize(text: string): string {
  return text
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .toLowerCase()
    .replace(/[^a-z0-9]/g, '');
}

/** Primer bloque del lector cuyo texto contiene la frase (ya normalizada). */
export function findTriggerBlock(canvas: HTMLElement, normalizedPhrase: string): HTMLElement | null {
  if (!normalizedPhrase) return null;
  const blocks = Array.from(canvas.querySelectorAll<HTMLElement>(BLOCK_SELECTOR));
  for (const el of blocks) {
    if (el.closest(`[${ALT_ATTR}]`)) continue;
    let text = textCache.get(el);
    if (text === undefined) {
      text = normalize(el.textContent || '');
      if (text) textCache.set(el, text); // no cachear vacíos: pueden estar a medio renderizar
    }
    if (text && text.includes(normalizedPhrase)) return el;
  }
  return null;
}

/** Bloques originales que van después del punto de disparo (los que serán reemplazados). */
export function blocksAfter(canvas: HTMLElement, trigger: HTMLElement): HTMLElement[] {
  return Array.from(canvas.querySelectorAll<HTMLElement>(BLOCK_SELECTOR)).filter(
    el =>
      !el.closest(`[${ALT_ATTR}]`) &&
      !trigger.contains(el) &&
      (trigger.compareDocumentPosition(el) & Node.DOCUMENT_POSITION_FOLLOWING) !== 0
  );
}

function hide(el: HTMLElement) {
  el.setAttribute(HIDDEN_ATTR, '1');
  el.style.display = 'none';
}

function unhide(el: HTMLElement) {
  el.removeAttribute(HIDDEN_ATTR);
  el.style.display = '';
}

/**
 * Oculta bloques originales que el reader siga agregando después del corte
 * (el reader renderiza por tandas, así que pueden llegar tarde).
 */
export function hideStrayBlocks(canvas: HTMLElement, trigger: HTMLElement, hidden: HTMLElement[]) {
  for (const el of blocksAfter(canvas, trigger)) {
    if (el.hasAttribute(HIDDEN_ATTR)) continue;
    hide(el);
    hidden.push(el);
  }
}

/**
 * Convierte el HTML del final alterno (ya sanitizado) en bloques que se ven igual
 * que los del reader: copian el atributo _ngcontent-* y la clase de un bloque real
 * del mismo tipo, porque los estilos del reader están encapsulados por Angular.
 */
export function buildAlternateBlocks(safeHtml: string, canvas: HTMLElement, fallbackRef: HTMLElement): HTMLElement[] {
  const doc = new DOMParser().parseFromString(safeHtml, 'text/html');
  const sources: Array<{ tag: string; html: string }> = [];

  if (doc.body.children.length > 0) {
    for (const child of Array.from(doc.body.children)) {
      const tag = child.tagName.toLowerCase();
      if (tag === 'img') {
        sources.push({ tag: 'figure', html: child.outerHTML });
      } else if (BLOCK_TAGS.has(tag)) {
        sources.push({ tag, html: child.innerHTML });
      } else {
        sources.push({ tag: 'p', html: child.innerHTML || child.textContent || '' });
      }
    }
  } else {
    // Texto suelto sin etiquetas: un párrafo por cada línea en blanco.
    (doc.body.textContent || '')
      .split(/\n{2,}/)
      .map(t => t.trim())
      .filter(Boolean)
      .forEach(t => sources.push({ tag: 'p', html: t }));
  }

  return sources.map(({ tag, html }) => {
    const el = document.createElement(tag);
    const ref =
      Array.from(canvas.querySelectorAll<HTMLElement>(tag)).find(e => !e.closest(`[${ALT_ATTR}]`)) || fallbackRef;
    for (const attr of Array.from(ref.attributes)) {
      if (attr.name.startsWith('_ngcontent') || attr.name === 'class') {
        el.setAttribute(attr.name, attr.value);
      }
    }
    el.innerHTML = html;
    return el;
  });
}

export interface SwapOptions {
  canvas: HTMLElement;
  trigger: HTMLElement;
  newBlocks: HTMLElement[];
  /** Respeta prefers-reduced-motion: sin cascada ni desenfoque. */
  reduceMotion: boolean;
  /** El desenfoque pesa en móvil: se desactiva en la app nativa. */
  useBlur: boolean;
}

export interface SwapResult {
  wrapper: HTMLElement;
  hidden: HTMLElement[];
}

function nextFrame(): Promise<void> {
  return new Promise(resolve => requestAnimationFrame(() => resolve()));
}

function seamElement(): HTMLElement {
  const seam = document.createElement('div');
  seam.className = 'as-seam';
  seam.setAttribute('aria-hidden', 'true');
  seam.innerHTML = '<span class="as-seam-line as-seam-left"></span><i class="as-seam-gem"></i><span class="as-seam-line as-seam-right"></span>';
  return seam;
}

/**
 * La secuencia completa:
 *   1. el texto original que sigue se disuelve en cascada (como tinta que se borra),
 *   2. aparece un corte con una línea que se dibuja desde el centro,
 *   3. el final alterno emerge párrafo a párrafo.
 */
export async function playSwap(opts: SwapOptions): Promise<SwapResult> {
  const { canvas, trigger, newBlocks, reduceMotion, useBlur } = opts;
  const hidden: HTMLElement[] = [];

  const old = blocksAfter(canvas, trigger).filter(el => !el.hasAttribute(HIDDEN_ATTR));
  const viewport = canvas.getBoundingClientRect();
  const visible = old.filter(el => {
    const r = el.getBoundingClientRect();
    return r.bottom > viewport.top && r.top < viewport.bottom;
  });
  const offscreen = old.filter(el => !visible.includes(el));

  // Altura que ocupaba el texto original, para que el scroll no salte al reemplazarlo.
  const lastOld = old[old.length - 1];
  const heldHeight = lastOld
    ? Math.max(0, lastOld.getBoundingClientRect().bottom - trigger.getBoundingClientRect().bottom)
    : 0;

  // Lo que está fuera de pantalla se oculta ya: nadie lo ve.
  offscreen.forEach(el => {
    hide(el);
    hidden.push(el);
  });

  // 1. Disolución del texto original visible.
  if (!reduceMotion && visible.length) {
    const stagger = Math.min(70, 600 / visible.length);
    const outs = visible.map((el, i) =>
      el.animate(
        [
          { opacity: 1, transform: 'translateY(0)', filter: useBlur ? 'blur(0px)' : 'none' },
          { opacity: 0, transform: 'translateY(-6px)', filter: useBlur ? 'blur(5px)' : 'none' },
        ],
        { duration: 520, delay: i * stagger, easing: 'cubic-bezier(.4,0,.2,1)', fill: 'forwards' }
      )
    );
    await Promise.all(outs.map(a => a.finished.catch(() => undefined)));
    outs.forEach(a => a.cancel());
  }
  visible.forEach(el => {
    hide(el);
    hidden.push(el);
  });

  // 2. El contenedor del final alterno entra justo donde estaba el texto viejo.
  const wrapper = document.createElement('div');
  wrapper.setAttribute(ALT_ATTR, '1');
  wrapper.style.minHeight = `${heldHeight}px`;
  wrapper.style.overflowAnchor = 'none';
  const seam = seamElement();
  wrapper.append(seam, ...newBlocks);
  newBlocks.forEach(b => (b.style.opacity = '0'));
  trigger.after(wrapper);
  await nextFrame();

  if (reduceMotion) {
    newBlocks.forEach(b => (b.style.opacity = ''));
    seam.classList.add('as-seam-static');
    wrapper.style.minHeight = '0px';
    return { wrapper, hidden };
  }

  // 3. Línea del corte y aparición del nuevo texto.
  seam.classList.add('as-seam-draw');
  const n = newBlocks.length;
  const step = Math.min(160, 1800 / Math.max(n, 1));
  const ins = newBlocks.map((b, i) =>
    b.animate(
      [
        { opacity: 0, transform: 'translateY(12px)', filter: useBlur ? 'blur(6px)' : 'none' },
        { opacity: 1, transform: 'translateY(0)', filter: useBlur ? 'blur(0px)' : 'none' },
      ],
      { duration: 900, delay: 420 + i * step, easing: 'cubic-bezier(.22,1,.36,1)', fill: 'both' }
    )
  );
  await Promise.all(ins.map(a => a.finished.catch(() => undefined)));
  newBlocks.forEach(b => (b.style.opacity = ''));
  ins.forEach(a => a.cancel());

  // El espacio reservado se libera suavemente.
  wrapper.style.transition = 'min-height 600ms ease';
  wrapper.style.minHeight = '0px';

  return { wrapper, hidden };
}

/** Devuelve el texto original: quita el final alterno y muestra de nuevo lo que se ocultó. */
export function restoreOriginal(wrapper: HTMLElement | null, hidden: HTMLElement[], canvas: HTMLElement | null) {
  wrapper?.remove();
  const viewport = canvas?.getBoundingClientRect();
  hidden.forEach(el => {
    unhide(el);
    if (viewport) {
      const r = el.getBoundingClientRect();
      if (r.bottom > viewport.top && r.top < viewport.bottom) {
        el.animate([{ opacity: 0 }, { opacity: 1 }], { duration: 500, easing: 'ease-out' });
      }
    }
  });
}