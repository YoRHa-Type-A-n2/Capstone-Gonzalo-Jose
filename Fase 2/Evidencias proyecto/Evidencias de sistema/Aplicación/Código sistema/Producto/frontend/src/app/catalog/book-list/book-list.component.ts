import { Component, OnInit, Input, ViewChild, ElementRef, inject, DestroyRef } from '@angular/core';
import { ApiService } from '../../core/services/api.service';
import { HttpParams } from '@angular/common/http';
import { Router, ActivatedRoute } from '@angular/router';
import { Subject, of } from 'rxjs';
import { debounceTime, distinctUntilChanged, switchMap, catchError } from 'rxjs/operators';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';

// Tipos adaptados al BookListSerializer de Django
export interface Book {
  id: string;
  title: string;
  slug: string;
  synopsis: string;
  is_featured: boolean;
  cover_image: string | null;
  created_at: string;
  author_name?: string;
  genre_name?: string;
  chapters_count?: number;
  level_badge?: string;
}

interface PaginatedResponse {
  count: number;
  next: string | null;
  previous: string | null;
  results: Book[];
}

export interface CategoryPill {
  name: string;
  icon: string;
}

export interface SortOption {
  key: string;
  label: string;
}

@Component({
  selector: 'app-book-list',
  templateUrl: './book-list.component.html',
  styleUrl: './book-list.component.css'
})
export class BookListComponent implements OnInit {
  private api = inject(ApiService);
  private router = inject(Router);
  private route = inject(ActivatedRoute);
  private destroyRef = inject(DestroyRef);

  @Input() isHome: boolean = false;
  @ViewChild('pillsRail') pillsRail?: ElementRef<HTMLDivElement>;

  books: Book[] = [];
  featuredAdventures: Book[] = [];
  isLoading = true;
  errorMsg = '';
  totalCount = 0;
  currentPage = 1;
  searchTerm = '';
  activeCategory: string | null = null;
  selectedOrdering: string = 'popularity';
  isPlayableOnly = false;

  brokenCovers = new Set<string>();

  sortOptions: SortOption[] = [
    { key: 'popularity', label: '🔥 Populares' },
    { key: 'recent', label: '✨ Nuevos' },
    { key: 'alphabetical', label: '🔤 A—Z' }
  ];

  private search$ = new Subject<string>();
  private load$ = new Subject<void>();

  get hasFilters(): boolean {
    return !!(this.activeCategory || this.searchTerm || this.isPlayableOnly);
  }

  get pageSize(): number {
    return this.hasFilters ? 50 : 24;
  }

  get totalPages(): number {
    return Math.max(1, Math.ceil(this.totalCount / this.pageSize));
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

  // Iconos filtrados para público infantil (7 a 14 años)
  categoryIcons: Record<string, string> = {
    'Acción y aventura': '🗺️',
    'Antologías': '📚',
    'Ciencia ficción': '🚀',
    'Cuentos': '📖',
    'Fantasía': '🧙‍♂️',
    'Ficción clásica': '📜',
    'Ficción contemporánea': '📚',
    'Ficción histórica': '🏛️',
    'Mitos, leyendas y sagas': '🐉',
    'Novela corta': '📖',
    'Poesía': '🌸',
    'Policíaca, negra y suspense': '🔍',
    'Teatro': '🎭',
    'Terror': '👻',
    'Biografías, diarios y hechos reales': '🖋️',
    'Ensayos': '💡',
    'Filosofía': '📜',
    'Historia': '🏛️',
    'Psicología': '🧠',
    'Sociedad y ciencias sociales': '👥'
  };

  genreDbMap: Record<string, string> = {
    'Acción y aventura': 'Acción y aventura',
    'Antologías': 'Antologías',
    'Ciencia ficción': 'Ciencia ficción',
    'Cuentos': 'Cuentos',
    'Fantasía': 'Fantasía',
    'Ficción clásica': 'Ficción clásica',
    'Ficción contemporánea': 'Ficción contemporánea',
    'Ficción histórica': 'Ficción histórica',
    'Mitos, leyendas y sagas': 'Mitos, leyendas y sagas',
    'Novela corta': 'Novela corta',
    'Poesía': 'Poesía',
    'Policíaca, negra y suspense': 'Policíaca, negra y suspense',
    'Teatro': 'Teatro',
    'Terror': 'Terror',
    'Biografías, diarios y hechos reales': 'Biografías, Diarios Y Hechos Reales',
    'Ensayos': 'Ensayos',
    'Filosofía': 'Filosofía',
    'Historia': 'Historia',
    'Psicología': 'Psicología',
    'Sociedad y ciencias sociales': 'Sociedad Y Ciencias Sociales'
  };

  categories = [
    {
      name: 'Literatura y ficción',
      sub: [
        'Acción y aventura', 'Antologías', 'Ciencia ficción', 'Cuentos', 'Fantasía',
        'Ficción clásica', 'Ficción contemporánea', 'Ficción histórica',
        'Mitos, leyendas y sagas', 'Novela corta', 'Poesía', 'Policíaca, negra y suspense',
        'Teatro', 'Terror'
      ]
    },
    {
      name: 'No ficción',
      sub: [
        'Biografías, diarios y hechos reales', 'Ensayos', 'Filosofía',
        'Historia', 'Psicología', 'Sociedad y ciencias sociales'
      ]
    }
  ];

  allSubcategories: CategoryPill[] = [];

  ngOnInit(): void {
    const rawSubs: string[] = [];
    this.categories.forEach(cat => rawSubs.push(...cat.sub));
    this.allSubcategories = rawSubs.map(subName => ({
      name: subName,
      icon: this.categoryIcons[subName] || '📖'
    }));

    // Búsqueda reactiva con debounce de 400ms
    this.search$.pipe(
      debounceTime(400),
      distinctUntilChanged(),
      takeUntilDestroyed(this.destroyRef)
    ).subscribe(term => {
      this.searchTerm = term;
      this.currentPage = 1;
      this.load$.next();
    });

    // Escucha query params (ej. playable=true)
    this.route.queryParams.pipe(
      takeUntilDestroyed(this.destroyRef)
    ).subscribe(params => {
      this.isPlayableOnly = params['playable'] === 'true';
      this.currentPage = 1;
      this.load$.next();
    });

    // Canal de carga con switchMap para cancelar peticiones anteriores
    this.load$.pipe(
      switchMap(() => {
        this.isLoading = true;
        this.errorMsg = '';

        let params = new HttpParams();
        if (this.searchTerm) {
          params = params.set('search', this.searchTerm);
        }
        if (this.activeCategory) {
          const dbName = this.genreDbMap[this.activeCategory] || this.activeCategory;
          params = params.set('genres__name', dbName);
        }
        if (this.isPlayableOnly) {
          params = params.set('playable', 'true');
        }

        params = params.set('page_size', this.pageSize.toString());
        params = params.set('page', this.currentPage.toString());

        const orderingMap: Record<string, string> = {
          popularity: '-is_featured,-created_at',
          recent: '-created_at',
          alphabetical: 'title'
        };
        const ordering = orderingMap[this.selectedOrdering] || '-is_featured,-created_at';
        params = params.set('ordering', ordering);

        return this.api.get<PaginatedResponse>('catalog/books/', params).pipe(
          catchError(err => {
            console.error('Error al cargar libros:', err);
            this.errorMsg = 'No pudimos cargar la biblioteca. Por favor, revisa tu conexión.';
            this.isLoading = false;
            return of(null);
          })
        );
      }),
      takeUntilDestroyed(this.destroyRef)
    ).subscribe(response => {
      if (response) {
        this.books = response.results || [];
        this.totalCount = response.count ?? this.books.length;

        this.featuredAdventures = this.books.filter(b => b.is_featured).slice(0, 4);
        if (this.featuredAdventures.length === 0) {
          this.featuredAdventures = this.books.slice(0, 4);
        }
        this.isLoading = false;
      }
    });

    // Petición inicial
    this.load$.next();
  }

  onSearch(event: Event): void {
    const target = event.target as HTMLInputElement;
    const value = target ? target.value.trim() : '';
    this.search$.next(value);
  }

  setCategory(cat: string): void {
    this.activeCategory = this.activeCategory === cat ? null : (cat || null);
    this.currentPage = 1;
    this.load$.next();
  }

  onOrderingChange(ordering: string): void {
    this.selectedOrdering = ordering;
    this.currentPage = 1;
    this.load$.next();
  }

  resetSearch(): void {
    this.searchTerm = '';
    this.activeCategory = null;
    this.currentPage = 1;
    this.load$.next();
  }

  retryFetch(): void {
    this.load$.next();
  }

  goToPage(page: number | string): void {
    if (typeof page !== 'number') return;
    if (page < 1 || page > this.totalPages || page === this.currentPage) return;
    this.currentPage = page;
    this.load$.next();
    window.scrollTo({ top: 0, behavior: 'smooth' });
  }

  goToBook(slug: string): void {
    if (slug) {
      this.router.navigate(['/book', slug]);
    }
  }

  onCoverError(book: Book): void {
    if (book?.id) {
      this.brokenCovers.add(book.id);
    }
  }

  hasCover(book: Book): boolean {
    return !!(book?.cover_image && !this.brokenCovers.has(book.id));
  }

  scrollPills(direction: 1 | -1): void {
    if (this.pillsRail?.nativeElement) {
      const el = this.pillsRail.nativeElement;
      el.scrollBy({ left: direction * el.clientWidth * 0.7, behavior: 'smooth' });
    }
  }
}
