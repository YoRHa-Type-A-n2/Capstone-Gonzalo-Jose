import { Injectable } from '@angular/core';
import { HttpClient, HttpErrorResponse } from '@angular/common/http';
import { Observable, throwError } from 'rxjs';
import { tap, catchError } from 'rxjs/operators';
import { Minigame } from '../models/minigame';

@Injectable({
  providedIn: 'root'
})
export class MinigameService {
  private apiUrl = 'http://127.0.0.1:8000/api/v1/games';

  constructor(private http: HttpClient) {}

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