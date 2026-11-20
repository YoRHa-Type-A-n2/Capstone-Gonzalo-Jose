/**
 * Resolución de íconos de objetos (mochila, tienda, final alterno, popup de objeto desbloqueado).
 *
 * En la BD el ícono se guarda como "assets/images/items/delantal.png". Si el campo es un ImageField,
 * el serializer de Django lo devuelve como URL ABSOLUTA del backend:
 *     http://localhost:8000/media/assets/images/items/delantal.png      <-- ese archivo no existe en el backend
 * La imagen real vive en el frontend (src/assets/images/items), así que cualquier ruta que contenga
 * "assets/images/items/<archivo>" se redirige a esa carpeta, venga como venga (relativa o URL completa).
 */

export const DEFAULT_ITEM_ICON = 'assets/images/default-item.png';
const LOCAL_ITEMS_DIR = 'assets/images/items';
const DEFAULT_API_URL = 'http://localhost:8000/api/v1';

function backendBase(apiUrl?: string): string {
  return (apiUrl || DEFAULT_API_URL)
    .replace(/\/api\/v1\/?$/, '')
    .replace(/\/api\/?$/, '');
}

/**
 * @param iconPath ruta o URL que entrega el backend
 * @param apiUrl   environment.apiUrl (solo se usa para íconos subidos al backend vía /media/)
 */
export function resolveItemIcon(iconPath: string | null | undefined, apiUrl?: string): string {
  const trimmed = (iconPath || '').trim();
  if (!trimmed) return DEFAULT_ITEM_ICON;
  if (trimmed.startsWith('data:')) return trimmed;

  // 1) Imágenes del frontend: va ANTES que el chequeo de "http", porque el backend puede
  //    devolverlas como URL absoluta (.../media/assets/images/items/x.png).
  const local = trimmed.match(/assets\/images\/items\/([^/?#]+)/i);
  if (local) return `${LOCAL_ITEMS_DIR}/${local[1]}`;

  // 2) Otras URLs completas (por ejemplo, un ícono subido desde el admin de Django): se respetan.
  if (/^https?:\/\//i.test(trimmed)) return trimmed;

  // 3) Otras rutas del frontend ("assets/..." o "/assets/...").
  if (/^\/?assets\//i.test(trimmed)) return trimmed.replace(/^\//, '');

  // 4) Rutas relativas del backend (/media/..., media/..., items/x.png).
  const base = backendBase(apiUrl);
  if (trimmed.startsWith('/media/') || trimmed.startsWith('/static/')) return `${base}${trimmed}`;
  if (trimmed.startsWith('media/') || trimmed.startsWith('static/')) return `${base}/${trimmed}`;
  return `${base}/media/${trimmed}`;
}

/**
 * Para usar en (error) de la <img>. Si la imagen falla:
 *  1. prueba una sola vez la carpeta local assets/images/items/<mismo archivo>
 *  2. si tampoco existe, muestra la imagen por defecto (sin entrar en bucle).
 */
export function handleItemImageError(event: Event): void {
  const img = event.target as HTMLImageElement | null;
  if (!img) return;

  const current = img.getAttribute('src') || '';
  if (current.endsWith(DEFAULT_ITEM_ICON)) return; // ya es la imagen de respaldo

  if (!img.dataset['itemFallbackTried'] && !current.includes('assets/images/')) {
    img.dataset['itemFallbackTried'] = '1';
    const file = current.split(/[?#]/)[0].split('/').pop();
    if (file) {
      img.src = `${LOCAL_ITEMS_DIR}/${file}`;
      return;
    }
  }
  img.src = DEFAULT_ITEM_ICON;
}