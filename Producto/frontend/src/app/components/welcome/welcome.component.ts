import { Component, OnInit, inject, ChangeDetectorRef } from '@angular/core';
import { CommonModule } from '@angular/common';
import { HttpParams } from '@angular/common/http';
import { Router, RouterModule } from '@angular/router';
import { MinigameService, BookWithMinigames } from '../../services/minigame.service';
import { ApiService } from '../../core/services/api.service';

@Component({
  selector: 'app-welcome',
  standalone: true,
  imports: [CommonModule, RouterModule],
  templateUrl: './welcome.component.html',
  styleUrls: ['./welcome.component.scss']
})
export class WelcomeComponent implements OnInit {
  private router = inject(Router);
  private minigameService = inject(MinigameService);
  private cdr = inject(ChangeDetectorRef);

  private api = inject(ApiService);
  isLoadingBooks: boolean = false;
  booksWithMinigames: BookWithMinigames[] = [];

  ngOnInit(): void {
    // Pre-cargar los libros con minijuegos en segundo plano
    this.loadBooks();
  }

  loadBooks(): void {
    this.isLoadingBooks = true;
    this.minigameService.getBooksWithMinigames().subscribe({
      next: (books) => {
        this.booksWithMinigames = books;
        this.isLoadingBooks = false;
        this.cdr.markForCheck();
      },
      error: (err) => {
        console.error('❌ [WelcomeComponent] Error cargando libros con minijuegos:', err);
        this.isLoadingBooks = false;
        this.cdr.markForCheck();
      }
    });
  }

  /**
   * Si el usuario ya tiene el libro en su biblioteca -> abre la lectura.
   * Si no lo tiene -> abre la pantalla de detalles y compra (/book/:slug), igual que el catálogo.
   */
  playBookAdventure(book: BookWithMinigames): void {
    if (!book) return;

    this.api.get<any>('library/inventory/').subscribe({
      next: (inventoryRes: any) => {
        const ownedItem = this.findOwnedItem(inventoryRes, book);
        if (ownedItem?.id) {
          this.router.navigate(['/reader', ownedItem.id]);
        } else {
          this.goToBookDetail(book);
        }
      },
      // Si falla la consulta del inventario, se trata como libro no adquirido.
      error: () => this.goToBookDetail(book)
    });
  }

  /** Busca el libro en el inventario del usuario por id (o por slug si viene). */
  private findOwnedItem(inventoryRes: any, book: BookWithMinigames): any | undefined {
    const items = Array.isArray(inventoryRes) ? inventoryRes : (inventoryRes?.results || []);
    return items.find((item: any) => {
      const itemBookId = item.book_id || item.edition?.book?.id || item.edition?.book_id;
      const itemSlug = item.book_slug || item.edition?.book?.slug;
      return (itemBookId && String(itemBookId) === String(book.id)) ||
             (!!book.slug && itemSlug === book.slug);
    });
  }

  /**
   * getBooksWithMinigames() no siempre trae el slug del libro, así que si falta se consulta
   * el catálogo (el mismo endpoint que usa la pantalla de exploración) y se toma el slug real.
   */
  private goToBookDetail(book: BookWithMinigames): void {
    if (book.slug) {
      this.router.navigate(['/book', book.slug]);
      return;
    }

    // Se busca por título con un tamaño de página grande: así el libro aparece aunque no esté
    // en la primera página del catálogo, y se identifica con el id (no con el título).
    const params = new HttpParams()
      .set('search', book.title)
      .set('page_size', '50');

    this.api.get<any>('catalog/books/', params).subscribe({
      next: (catalogRes: any) => {
        const catalogBooks = Array.isArray(catalogRes) ? catalogRes : (catalogRes?.results || []);
        const match =
          catalogBooks.find((b: any) => String(b.id) === String(book.id)) ||
          catalogBooks.find((b: any) => this.slugify(b.title) === this.slugify(book.title));
        this.router.navigate(['/book', match?.slug || this.fallbackSlug(book)]);
      },
      error: () => this.router.navigate(['/book', this.fallbackSlug(book)])
    });
  }

  /** Último recurso: slug armado desde el título (puede no coincidir con el real). */
  private fallbackSlug(book: BookWithMinigames): string {
    console.warn(`⚠️ [WelcomeComponent] No se encontró el slug de "${book.title}" en el catálogo; se usa uno generado.`);
    return this.slugify(book.title);
  }

  private slugify(text: string): string {
    return (text || '')
      .toLowerCase()
      .normalize('NFD')
      .replace(/[\u0300-\u036f]/g, '')
      .replace(/[^a-z0-9]+/g, '-')
      .replace(/^-|-$/g, '');
  }

  onCoverError(event: Event): void {
    const img = event.target as HTMLImageElement;
    if (img && !img.dataset['fallbackAttempted']) {
      img.dataset['fallbackAttempted'] = 'true';
      img.src = 'assets/default_cover.jpg';
    }
  }
}