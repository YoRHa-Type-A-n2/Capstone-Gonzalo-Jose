// src/app/models/minigame.ts
export interface Minigame {
  id?: number;
  code: string;         // Ej: 'completa_dialogo', 'imagen_pixelada'
  title: string;
  description: string;
  config?: any;         // Datos específicos del minijuego para este libro
  route?: string;
}