/**
 * Contrato con el backend (app Django "mochila"), tal como lo exponen
 * BookEventView y UseItemView.
 *
 *   GET  mochila/books/{bookId}/event/                 -> BookEventResponse
 *   POST mochila/books/{bookId}/items/{itemId}/use/    -> UseItemResponse
 */

/** Resumen del final alterno: nunca incluye su texto. */
export interface AlternateStorySummary {
  id: string;
  title: string;
  chapter_index: number;
  trigger_phrase: string;
}

/** ItemSerializer: un objeto que el usuario posee y que sirve en este libro. */
export interface AlternateItem {
  id: string;
  book: string;
  book_title: string;
  name: string;
  description: string;
  /** URL absoluta de la imagen (el serializer recibe el request), o null. */
  icon: string | null;
  unlock_method: 'reading' | 'purchase';
  points_cost: number | null;
  is_active: boolean;
  alternate_story: AlternateStorySummary | null;
}

/** Objetos agrupados por capítulo y frase de activación. */
export interface AlternateEvent {
  chapter_index: number;
  /** Último párrafo antes del cambio: el punto donde se lanza el evento. */
  trigger_phrase: string;
  usable_items: AlternateItem[];
}

export interface BookEventResponse {
  has_event: boolean;
  events: AlternateEvent[];
}

export interface UseItemResponse {
  item_id: string;
  /** HTML del final alterno. Solo llega cuando el usuario elige el objeto. */
  alternate_ending: string;
  title: string;
  chapter_index: number;
}

/** Objetos que comparten el mismo punto de disparo en el texto. */
export interface TriggerGroup {
  /** Frase normalizada (sin tildes, espacios ni puntuación). */
  key: string;
  chapterIndex: number;
  items: AlternateItem[];
  /** Bloque del DOM donde está la frase. null mientras no se haya renderizado. */
  element: HTMLElement | null;
}

export type AlternateState = 'idle' | 'armed' | 'swapping' | 'done';