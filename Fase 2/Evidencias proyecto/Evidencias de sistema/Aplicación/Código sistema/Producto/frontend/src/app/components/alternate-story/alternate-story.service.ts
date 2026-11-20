import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';
import { ApiService } from '../../core/services/api.service';
import { BookEventResponse, UseItemResponse } from './alternate-story.models';

/**
 * Habla con la app Django "mochila".
 * Usa el mismo ApiService que el reader, así que hereda la URL base y los tokens.
 */
@Injectable({ providedIn: 'root' })
export class AlternateStoryService {
  private api = inject(ApiService);

  /** Eventos del libro para los objetos que el usuario posee (sin el texto alterno). */
  getEvent(bookId: string): Observable<BookEventResponse> {
    return this.api.get<BookEventResponse>(`mochila/books/${bookId}/event/`);
  }

  /** El servidor verifica posesión y libro, y devuelve el HTML del final alterno. */
  useItem(bookId: string, itemId: string): Observable<UseItemResponse> {
    return this.api.post<UseItemResponse>(`mochila/books/${bookId}/items/${itemId}/use/`, {});
  }
}