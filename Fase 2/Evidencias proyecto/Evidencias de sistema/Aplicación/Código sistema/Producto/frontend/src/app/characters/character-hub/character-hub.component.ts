import { Component, OnInit, inject, DestroyRef } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Router } from '@angular/router';
import { Subject, of } from 'rxjs';
import { debounceTime, distinctUntilChanged, switchMap, catchError } from 'rxjs/operators';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { ChatService } from '../../core/services/chat.service';
import { ApiService } from '../../core/services/api.service';
import { AuthService } from '../../core/services/auth.service';

export interface CharacterAvatar {
  id: number;
  name: string;
  book_title: string | null;
  book_slug: string | null;
  description: string | null;
  avatar_image_url: string | null;
  book_cover_url: string | null;
  is_major_character?: boolean;
  is_author?: boolean;
  tags?: string[];
  trend_level?: number;
  chat_count?: number;
  genre?: string;
  sample_dialogue?: string;
}

export interface FilterOption {
  key: string;
  label: string;
  icon: string;
}

export interface SortOption {
  key: string;
  label: string;
}

@Component({
  selector: 'app-character-hub',
  templateUrl: './character-hub.component.html',
  styleUrls: ['./character-hub.component.css']
})
export class CharacterHubComponent implements OnInit {
  private chatService = inject(ChatService);
  private api = inject(ApiService);
  private router = inject(Router);
  private auth = inject(AuthService);
  private destroyRef = inject(DestroyRef);

  // Estados principales
  characters: CharacterAvatar[] = [];
  featuredCharacters: CharacterAvatar[] = [];
  isLoading = true;
  isLoadingFeatured = true;
  errorMsg = '';
  totalCount = 0;

  // Parámetros de consulta
  currentPage = 1;
  readonly pageSize = 24;
  searchQuery = '';
  activeFilter = 'all'; // 'all' | 'protagonists' | 'authors'
  selectedSort = 'popularity'; // 'popularity' | 'name'

  // Opciones de configuración
  filterOptions: FilterOption[] = [
    { key: 'all', label: 'Todos los personajes', icon: '✨' },
    { key: 'protagonists', label: 'Protagonistas', icon: '⭐' },
    { key: 'authors', label: 'Escritores/as', icon: '✍️' }
  ];

  sortOptions: SortOption[] = [
    { key: 'popularity', label: '🔥 Más populares' },
    { key: 'name', label: '🔤 Nombre A—Z' }
  ];

  // Control de imágenes rotas
  brokenAvatars = new Set<number>();
  brokenCovers = new Set<number>();

  // Skeletons para estado de carga
  skeletonCards = Array(8).fill(0);

  // Canales reactivos
  private search$ = new Subject<string>();
  private load$ = new Subject<void>();

  // Getters para paginación y visibilidad
  get totalPages(): number {
    return Math.max(1, Math.ceil(this.totalCount / this.pageSize));
  }

  get showFeaturedSection(): boolean {
    return this.currentPage === 1 && !this.searchQuery.trim() && this.activeFilter === 'all';
  }

  get visiblePages(): (number | string)[] {
    const total = this.totalPages;
    const current = this.currentPage;

    if (total <= 7) {
      return Array.from({ length: total }, (_, i) => i + 1);
    }

    const pages: (number | string)[] = [];
    const left = Math.max(2, current - 1);
    const right = Math.min(total - 1, current + 1);

    pages.push(1);
    if (left > 2) {
      pages.push('…');
    }
    for (let p = left; p <= right; p++) {
      pages.push(p);
    }
    if (right < total - 1) {
      pages.push('…');
    }
    pages.push(total);

    return pages;
  }

  ngOnInit(): void {
    // Pipeline para búsqueda con debounce
    this.search$.pipe(
      debounceTime(400),
      distinctUntilChanged(),
      takeUntilDestroyed(this.destroyRef)
    ).subscribe(term => {
      this.searchQuery = term;
      this.currentPage = 1;
      this.load$.next();
    });

    // Pipeline reactivo para cargar personajes paginados
    this.load$.pipe(
      switchMap(() => {
        this.isLoading = true;
        this.errorMsg = '';

        const filterParam = this.activeFilter === 'all' ? '' : this.activeFilter;

        return this.chatService.getGlobalAvatars(
          this.searchQuery,
          this.selectedSort,
          this.currentPage,
          this.pageSize,
          filterParam
        ).pipe(
          catchError(err => {
            console.error('Error cargando avatares:', err);
            this.errorMsg = 'Nuestros personajes están descansando. Comprueba tu conexión e inténtalo de nuevo.';
            return of({ count: 0, results: [] });
          })
        );
      }),
      takeUntilDestroyed(this.destroyRef)
    ).subscribe((response: any) => {
      this.isLoading = false;
      if (response && Array.isArray(response.results)) {
        this.characters = response.results;
        this.totalCount = response.count || 0;
      } else if (Array.isArray(response)) {
        this.characters = response;
        this.totalCount = response.length;
      } else {
        this.characters = [];
        this.totalCount = 0;
      }
    });

    // Cargar sección independiente de destacados
    this.loadFeaturedTop();

    // Disparar primera carga del catálogo paginado
    this.load$.next();
  }

  loadFeaturedTop(): void {
    this.isLoadingFeatured = true;
    this.chatService.getGlobalAvatars('', 'popularity', 1, 4).pipe(
      catchError(err => {
        console.warn('No se pudieron cargar personajes destacados:', err);
        return of({ count: 0, results: [] });
      }),
      takeUntilDestroyed(this.destroyRef)
    ).subscribe((response: any) => {
      this.isLoadingFeatured = false;
      if (response && Array.isArray(response.results)) {
        this.featuredCharacters = response.results.slice(0, 4);
      } else if (Array.isArray(response)) {
        this.featuredCharacters = response.slice(0, 4);
      } else {
        this.featuredCharacters = [];
      }
    });
  }

  onSearchInput(value: string): void {
    this.search$.next(value);
  }

  clearSearch(): void {
    this.searchQuery = '';
    this.currentPage = 1;
    this.load$.next();
  }

  setFilter(filterKey: string): void {
    if (this.activeFilter === filterKey) return;
    this.activeFilter = filterKey;
    this.currentPage = 1;
    this.load$.next();
  }

  setSort(sortKey: string): void {
    if (this.selectedSort === sortKey) return;
    this.selectedSort = sortKey;
    this.currentPage = 1;
    this.load$.next();
  }

  goToPage(page: number | string): void {
    if (typeof page !== 'number' || page === this.currentPage || page < 1 || page > this.totalPages) {
      return;
    }
    this.currentPage = page;
    this.load$.next();

    const gridAnchor = document.getElementById('characters-grid-anchor');
    if (gridAnchor) {
      gridAnchor.scrollIntoView({ behavior: 'smooth', block: 'start' });
    } else {
      window.scrollTo({ top: 350, behavior: 'smooth' });
    }
  }

  retryLoad(): void {
    this.load$.next();
    if (this.featuredCharacters.length === 0) {
      this.loadFeaturedTop();
    }
  }

  handleAvatarError(charId: number): void {
    this.brokenAvatars.add(charId);
  }

  handleCoverError(charId: number): void {
    this.brokenCovers.add(charId);
  }

  isAvatarBroken(charId: number): boolean {
    return this.brokenAvatars.has(charId);
  }

  isCoverBroken(charId: number): boolean {
    return this.brokenCovers.has(charId);
  }

  getDeterministicBg(name: string): string {
    const friendlyPalette = [
      '#e3f1ec',
      '#fef2d6',
      '#fde8d7',
      '#e0e7ff',
      '#dcfce7',
      '#fae8ff',
      '#ffedd5'
    ];
    if (!name) return friendlyPalette[0];
    let hash = 0;
    for (let i = 0; i < name.length; i++) {
      hash = name.charCodeAt(i) + ((hash << 5) - hash);
    }
    const index = Math.abs(hash) % friendlyPalette.length;
    return friendlyPalette[index];
  }

  getInitial(name: string): string {
    if (!name) return '🎭';
    const clean = name.trim();
    return clean.charAt(0).toUpperCase() || '🎭';
  }

  getRoleBadge(char: CharacterAvatar): { label: string; icon: string; cssClass: string } {
    if (char.is_author) {
      return { label: 'Escritor/a', icon: '✍️', cssClass: 'badge-author' };
    }
    if (char.is_major_character) {
      return { label: 'Protagonista', icon: '⭐', cssClass: 'badge-protagonist' };
    }
    return { label: 'Personaje', icon: '🎭', cssClass: 'badge-character' };
  }

  openChat(character: CharacterAvatar): void {
    if (!character) return;

    if (!this.auth.isLoggedIn()) {
      this.router.navigate(['/demo-chat', character.id]);
      return;
    }

    if (!character.book_slug) {
      this.router.navigate(['/demo-chat', character.id]);
      return;
    }

    this.api.get<any>(`library/inventory/check/?slug=${character.book_slug}`).subscribe({
      next: (res: any) => {
        if (res && res.owned) {
          this.router.navigate(['/reader', res.inventory_id], { 
            queryParams: { chatWith: character.id } 
          });
        } else {
          this.router.navigate(['/book', character.book_slug]);
        }
      },
      error: (err: any) => {
        console.error('Error verificando propiedad:', err);
        this.router.navigate(['/book', character.book_slug]);
      }
    });
  }

  goToBook(slug?: string | null): void {
    if (slug) {
      this.router.navigate(['/book', slug]);
    } else {
      this.router.navigate(['/catalog']);
    }
  }
}
