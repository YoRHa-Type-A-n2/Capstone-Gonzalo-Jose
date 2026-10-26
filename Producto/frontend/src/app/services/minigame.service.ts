import { Injectable } from '@angular/core';
import { HttpClient, HttpErrorResponse } from '@angular/common/http';
import { Observable, throwError } from 'rxjs';
import { tap, catchError, map } from 'rxjs/operators';
import { Minigame } from '../models/minigame';
import { environment } from '../../environments/environment';

export interface BookWithMinigames {
  id: string;
  title: string;
  author_name: string;
  cover_image: string;
  synopsis?: string;
}

@Injectable({
  providedIn: 'root'
})
export class MinigameService {
  private apiUrl = environment.apiUrl ? `${environment.apiUrl.replace(/\/$/, '')}/games` : 'http://localhost:8000/api/v1/games';

  constructor(private http: HttpClient) {}

  /**
   * Obtiene la lista de libros disponibles que contienen minijuegos asociados.
   * Resuelve las URLs relativas de las portadas a URLs completas o assets por defecto.
   */
  getBooksWithMinigames(): Observable<BookWithMinigames[]> {
    const url = `${this.apiUrl}/books/`;
    return this.http.get<BookWithMinigames[]>(url).pipe(
      map(books => books.map(book => ({
        ...book,
        cover_image: this.resolveCoverUrl(book.cover_image)
      }))),
      tap(books => {
        console.log(`✅ [MinigameService] Libros con minijuegos obtenidos (${books.length}):`, books);
      }),
      catchError((error: HttpErrorResponse) => {
        console.error(`❌ [MinigameService] Error al obtener libros con minijuegos:`, error);
        return throwError(() => error);
      })
    );
  }

  private resolveCoverUrl(url?: string | null): string {
    if (!url) {
      return 'assets/default_cover.jpg';
    }
    if (url.startsWith('http://') || url.startsWith('https://')) {
      return url;
    }
    const backendBase = (environment.apiUrl || 'http://localhost:8000/api/v1/').replace(/\/api\/v1\/?$/, '');
    const cleanPath = url.startsWith('/') ? url : `/${url}`;
    return `${backendBase}${cleanPath}`;
  }


  /**
   * Obtiene la lista de los 5 minijuegos aleatorios para un libro específico con logs de diagnóstico.
   */
  getMinigamesSession(bookId: string): Observable<Minigame[]> {
    const url = `${this.apiUrl}/books/${bookId}/minigames/?random=true&limit=5`;
    console.log(`🔍 [MinigameService DIAGNÓSTICO] URL solicitada: ${url}`);
    console.log(`🔑 [MinigameService DIAGNÓSTICO] Valor recibido como bookId/inventoryId: "${bookId}"`);

    return this.http.get<Minigame[]>(url).pipe(
      tap(response => {
        console.log(`✅ [MinigameService DIAGNÓSTICO] ¡Petición exitosa! Minijuegos recibidos:`, response);
      }),
      catchError((error: HttpErrorResponse) => {
        console.error(`❌ [MinigameService DIAGNÓSTICO] Error HTTP ${error.status} (${error.statusText})`);
        console.error(`📌 Detalle del error de red/servidor:`, error.error);
        return throwError(() => error);
      })
    );
  }

  /**
   * Obtiene la configuración de un minijuego individual por su código y libro con logs.
   */
  getMinigameByCode(bookId: string, gameCode: string): Observable<any> {
    const url = `${this.apiUrl}/books/${bookId}/minigames/${gameCode}/`;
    console.log(`🔍 [MinigameService DIAGNÓSTICO] Solicitando minijuego individual: ${url}`);
    
    return this.http.get<any>(url).pipe(
      tap(res => console.log(`✅ [MinigameService DIAGNÓSTICO] Datos del juego ${gameCode}:`, res)),
      catchError(err => {
        console.error(`❌ [MinigameService DIAGNÓSTICO] Error al cargar minijuego ${gameCode}:`, err);
        return throwError(() => err);
      })
    );
  }
}