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
const TAIL_ATTR = 'data-alt-tail';
const REOPEN_CLASS = 'as-reopen-btn';
/** Puntuación de cierre que se queda pegada a la frase (el "!" de "...ventanas!"). */
const CLOSING_PUNCT = /[.!?\u2026\u00bb\u201d\u2019)\]"']/;
const BLOCK_TAGS = new Set(['p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'blockquote', 'figure']);

const textCache = new WeakMap<Element, string>();

/** Deja solo letras y números, sin tildes ni mayúsculas. Tolera espacios, saltos de línea y puntuación. */
export function normalize(text: string): string {
  return (text || '')
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .toLowerCase()
    .replace(/\s+/g, ' ') // 👈 Colapsa cualquier combinación de saltos de línea y espacios múltiples en un espacio simple
    .replace(/[^a-z0-9 ]/g, '') // Mantiene espacios normalizados
    .trim();
}

/** Primer bloque del lector cuyo texto contiene la frase (ya normalizada y tolerante a saltos de línea). */
export function findTriggerBlock(canvas: HTMLElement, normalizedPhrase: string): HTMLElement | null {
  if (!normalizedPhrase) return null;
  const blocks = Array.from(canvas.querySelectorAll<HTMLElement>(BLOCK_SELECTOR));
  for (const el of blocks) {
    if (el.closest(`[${ALT_ATTR}]`)) continue;
    let text = textCache.get(el);
    if (text === undefined) {
      // Usamos innerText en lugar de textContent para respetar saltos de línea visuales del lector si los hubiera
      text = normalize(el.innerText || el.textContent || '');
      if (text) textCache.set(el, text);
    }
    // Verificamos si el bloque contiene la frase clave normalizada
    if (text && text.includes(normalizedPhrase)) return el;
  }
  return null;
}

/** Una letra o número, sin tildes ni mayúsculas ('' si el carácter no cuenta). */
function compactChar(ch: string): string {
  return ch
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .toLowerCase()
    .replace(/[^a-z0-9]/g, '');
}

/** Texto que sobra en el mismo bloque después de la frase de disparo. */
export interface TailCut {
  /** Elementos con el texto sobrante (para animarlos antes de ocultarlos). */
  targets: HTMLElement[];
  /** Borde inferior, en coordenadas de pantalla, de la última línea que se conserva (0 si no se pudo medir). */
  anchorBottom: number;
  /** Oculta el texto sobrante. */
  hide(): void;
  /** Devuelve el bloque exactamente como lo pintó el reader. */
  restore(): void;
}

/**
 * La frase de disparo casi nunca es el párrafo completo: suele terminar a mitad de párrafo.
 * Ocultar los bloques que vienen DESPUÉS no basta, porque el resto de ese mismo párrafo
 * se quedaría en pantalla. Esta función localiza dónde termina la frase dentro del bloque
 * y marca todo lo que sigue (texto suelto, spans, <br>...) para poder ocultarlo.
 *
 *  - Trabaja sobre las letras y números (sin espacios ni puntuación), igual que la búsqueda
 *    del bloque, así que tolera tildes, saltos de línea, guiones y comillas distintas.
 *  - No borra nada: parte el nodo de texto en el corte y envuelve el sobrante en <span>.
 *    restore() los desenvuelve y vuelve a unir el texto.
 *  - Devuelve null si la frase ya cierra el bloque (no hay nada que recortar).
 */
export function cutAfterPhrase(trigger: HTMLElement, normalizedPhrase: string): TailCut | null {
  const key = (normalizedPhrase || '').replace(/ /g, '');
  if (!key) return null;

  // 1. Texto del bloque sin espacios ni puntuación, recordando de qué nodo sale cada letra.
  const map: Array<{ node: Text; offset: number }> = [];
  let flat = '';
  const walker = document.createTreeWalker(trigger, NodeFilter.SHOW_TEXT);
  for (let n = walker.nextNode(); n; n = walker.nextNode()) {
    const node = n as Text;
    if (node.parentElement?.closest(`.${REOPEN_CLASS}`)) continue;
    for (let i = 0; i < node.data.length; i++) {
      const c = compactChar(node.data[i]);
      for (let k = 0; k < c.length; k++) {
        flat += c[k];
        map.push({ node, offset: i });
      }
    }
  }

  const from = flat.indexOf(key);
  if (from < 0) return null;
  const end = from + key.length; // posición (exclusiva) de la última letra de la frase
  if (end >= flat.length) return null; // la frase ya termina el bloque
  const last = map[end - 1];

  // 2. Punto de corte: justo después de la última letra, más la puntuación de cierre pegada a ella.
  const head = last.node;
  let cut = last.offset + 1;
  while (cut < head.data.length && /[\u0300-\u036f]/.test(head.data[cut])) cut++;
  while (cut < head.data.length && CLOSING_PUNCT.test(head.data[cut])) cut++;
  const tailText = cut < head.data.length ? head.splitText(cut) : null;

  const mergeSplit = () => {
    if (tailText && head.nextSibling === tailText) {
      head.appendData(tailText.data);
      tailText.remove();
    }
  };

  // 3. Todo lo que queda después del corte dentro del bloque (también en niveles anidados).
  const roots: Node[] = [];
  for (let cur: Node | null = head; cur && cur !== trigger; cur = cur.parentNode) {
    for (let sib = cur.nextSibling; sib; sib = sib.nextSibling) roots.push(sib);
  }

  const targets: HTMLElement[] = [];
  const wrappers: HTMLElement[] = [];
  for (const node of roots) {
    if (node.nodeType === Node.TEXT_NODE) {
      if (!(node as Text).data.trim()) continue;
      const span = document.createElement('span');
      span.setAttribute(TAIL_ATTR, '1');
      node.parentNode!.insertBefore(span, node);
      span.appendChild(node);
      targets.push(span);
      wrappers.push(span);
    } else if (node instanceof HTMLElement && !node.classList.contains(REOPEN_CLASS)) {
      targets.push(node);
    }
  }
  if (!targets.length) {
    mergeSplit();
    return null;
  }

  // Borde inferior de la última línea que se conserva (la altura de lo que se va se calcula desde aquí).
  let anchorBottom = 0;
  if (head.data.length > 0) {
    const range = document.createRange();
    range.setStart(head, head.data.length - 1);
    range.setEnd(head, head.data.length);
    const rect = range.getBoundingClientRect();
    if (rect.height > 0) anchorBottom = rect.bottom;
  }

  const previousDisplay = new Map<HTMLElement, string>();
  return {
    targets,
    anchorBottom,
    hide() {
      for (const el of targets) {
        previousDisplay.set(el, el.style.display);
        el.setAttribute(HIDDEN_ATTR, '1');
        el.style.display = 'none';
      }
    },
    restore() {
      for (const el of targets) {
        el.removeAttribute(HIDDEN_ATTR);
        if (previousDisplay.has(el)) el.style.display = previousDisplay.get(el)!;
      }
      for (const span of wrappers) span.replaceWith(...Array.from(span.childNodes));
      mergeSplit();
    },
  };
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
  /** Frase de disparo normalizada: sirve para recortar lo que sigue a la frase dentro del mismo párrafo. */
  triggerKey: string;
}

export interface SwapResult {
  wrapper: HTMLElement;
  hidden: HTMLElement[];
  /** Texto del párrafo del disparo que se ocultó (null si la frase cerraba el párrafo). */
  tailCut: TailCut | null;
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
  const { canvas, trigger, newBlocks, reduceMotion, useBlur, triggerKey } = opts;
  const hidden: HTMLElement[] = [];

  // Si la frase termina a mitad de párrafo, el resto de ese párrafo también es texto original que sigue.
  const tailCut = cutAfterPhrase(trigger, triggerKey);

  try {
    const old = blocksAfter(canvas, trigger).filter(el => !el.hasAttribute(HIDDEN_ATTR));
    const viewport = canvas.getBoundingClientRect();
    const visible = old.filter(el => {
      const r = el.getBoundingClientRect();
      return r.bottom > viewport.top && r.top < viewport.bottom;
    });
    const offscreen = old.filter(el => !visible.includes(el));

    // Altura que ocupaba el texto original desde el punto de corte, para que el scroll no salte al reemplazarlo.
    const triggerBottom = trigger.getBoundingClientRect().bottom;
    const cutBottom = tailCut && tailCut.anchorBottom > 0 ? tailCut.anchorBottom : triggerBottom;
    const lastOld = old[old.length - 1];
    const endBottom = lastOld ? lastOld.getBoundingClientRect().bottom : triggerBottom;
    const heldHeight = Math.max(0, endBottom - cutBottom);

    // Lo que está fuera de pantalla se oculta ya: nadie lo ve.
    offscreen.forEach(el => {
      hide(el);
      hidden.push(el);
    });

    // 1. Disolución del texto original visible (primero lo que sobra del párrafo, luego los bloques siguientes).
    const dissolving: HTMLElement[] = [...(tailCut?.targets ?? []), ...visible];
    if (!reduceMotion && dissolving.length) {
      const stagger = Math.min(70, 600 / dissolving.length);
      const outs = dissolving.map((el, i) =>
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
    tailCut?.hide();

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
      return { wrapper, hidden, tailCut };
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

    return { wrapper, hidden, tailCut };
  } catch (err) {
    // Si algo falla a medias, el párrafo del disparo vuelve a como estaba.
    tailCut?.restore();
    throw err;
  }
}

/** Devuelve el texto original: quita el final alterno y muestra de nuevo lo que se ocultó. */
export function restoreOriginal(
  wrapper: HTMLElement | null,
  hidden: HTMLElement[],
  canvas: HTMLElement | null,
  tailCut?: TailCut | null
) {
  wrapper?.remove();
  tailCut?.restore();
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