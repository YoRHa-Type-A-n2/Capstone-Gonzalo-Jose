import { Component, OnInit, inject } from '@angular/core';
import { Router } from '@angular/router';
import { ApiService } from '../core/services/api.service';

export interface Category {
  id?: string;
  name: string;
  slug: string;
  icon?: string;
  image: string;
  description: string;
  color: string;
  bookCount?: number;
}

export interface FeaturedAuthor {
  id?: string;
  name: string;
  slug: string;
  photo?: string | null;
  bio?: string | null;
  role?: string;
  origin?: string | null;
  era?: string | null;
  bookCount?: number | null;
  genres?: string[] | null;
}

@Component({
  selector: 'app-categories',
  templateUrl: './categories.component.html',
  styleUrls: ['./categories.component.css']
})
export class CategoriesComponent implements OnInit {
  private router = inject(Router);
  private api = inject(ApiService);

  searchTerm = '';
  isLoading = true;
  errorMsg = '';
  activeCategorySlug: string | null = null;
  featuredAuthor: FeaturedAuthor | null = null;
  isLoadingAuthor = true;

  // Lista de exclusión de géneros no aptos para público infantil/juvenil (7 a 14 años)
  readonly excludedGenreSlugs: Set<string> = new Set([
    'ficcion-erotica',
    'erotica',
    'romantica-erotica',
    'erotismo'
  ]);

  categories: Category[] = [];
  skeletonCards = Array(8).fill(0);

  private categoryIconsMap: Record<string, string> = {
    'accion-y-aventura': '🗺️',
    'antologias': '📚',
    'biografias-diarios-y-hechos-reales': '🖋️',
    'ciencia-ficcion': '🚀',
    'clasicos': '📜',
    'cuentos': '📖',
    'ensayos': '💡',
    'fantasia': '🧙',
    'ficcion': '📖',
    'ficcion-clasica': '📚',
    'ficcion-contemporanea': '📖',
    'ficcion-historica': '🏛️',
    'filosofia': '📜',
    'historia': '🏛️',
    'infantil': '🧸',
    'mitos-leyendas-y-sagas': '🐉',
    'novela-corta': '📖',
    'poesia': '🌸',
    'policiaca-negra-y-suspense': '🔍',
    'psicologia': '🧠',
    'sociedad-y-ciencias-sociales': '👥',
    'teatro': '🎭',
    'terror': '👻'
  };

  // Paleta oficial de Literatus Novelist
  private categoryColorsMap: string[] = [
    '#1f7a5c', // verde principal
    '#f5a25d', // naranja cálido
    '#17604a', // verde oscuro
    '#d97706', // ámbar
    '#2d3b36'  // tinta
  ];

  normalizeText(text: string): string {
    return (text || '')
      .toLowerCase()
      .normalize('NFD')
      .replace(/[\u0300-\u036f]/g, '')
      .trim();
  }

  get filteredCategories(): Category[] {
    if (!this.searchTerm.trim()) {
      return this.categories;
    }
    const cleanTerm = this.normalizeText(this.searchTerm);
    return this.categories.filter(c =>
      this.normalizeText(c.name).includes(cleanTerm) ||
      this.normalizeText(c.description).includes(cleanTerm)
    );
  }

  ngOnInit(): void {
    this.loadGenres();
    this.loadFeaturedAuthor();
  }

  loadFeaturedAuthor(): void {
    this.isLoadingAuthor = true;
    this.api.get<any>('catalog/authors/?page_size=1').subscribe({
      next: (countRes) => {
        const totalCount = countRes?.count || 1;
        const pageSize = 5;
        const totalPages = Math.max(1, Math.ceil(totalCount / pageSize));

        const now = new Date();
        const startOfYear = new Date(now.getFullYear(), 0, 0);
        const dayOfYear = Math.floor((now.getTime() - startOfYear.getTime()) / (1000 * 60 * 60 * 24));

        const targetPage = (dayOfYear % totalPages) + 1;

        this.api.get<any>(`catalog/authors/?page=${targetPage}&page_size=${pageSize}`).subscribe({
          next: (pageRes) => {
            const authors = pageRes?.results || (Array.isArray(pageRes) ? pageRes : []);
            if (authors && authors.length > 0) {
              const chosen = authors.find((a: any) => (a.bio && a.bio.trim().length > 15) || a.photo) || authors[0];
              this.featuredAuthor = {
                id: chosen.id,
                name: chosen.full_name || chosen.name || 'Autor de la Biblioteca',
                slug: chosen.slug || chosen.id,
                photo: chosen.photo || null,
                bio: chosen.bio || null,
                role: 'Escritor',
                origin: chosen.nationality || null,
                era: chosen.birth_year ? `${chosen.birth_year}${chosen.death_year ? ' — ' + chosen.death_year : ''}` : null,
                bookCount: chosen.book_count ?? (chosen.author_books ? chosen.author_books.length : null)
              };
            } else {
              this.featuredAuthor = null;
            }
            this.isLoadingAuthor = false;
          },
          error: (err) => {
            console.warn('Error al cargar autor del día:', err);
            this.featuredAuthor = null;
            this.isLoadingAuthor = false;
          }
        });
      },
      error: (err) => {
        console.warn('Error al consultar conteo de autores:', err);
        this.featuredAuthor = null;
        this.isLoadingAuthor = false;
      }
    });
  }

  goToAuthor(slug?: string): void {
    if (slug) {
      this.router.navigate(['/author', slug]);
    } else {
      this.router.navigate(['/authors']);
    }
  }

  getAuthorInitial(name?: string): string {
    if (!name) return '✍️';
    return name.trim().charAt(0).toUpperCase() || '✍️';
  }

  loadGenres(): void {
    this.isLoading = true;
    this.errorMsg = '';

    this.api.get<any>('catalog/genres/?page_size=100').subscribe({
      next: (res) => {
        const genres = Array.isArray(res) ? res : (res.results || []);
        if (genres && genres.length > 0) {
          const validGenres = genres.filter((g: any) => {
            const isExcluded = this.excludedGenreSlugs.has(g.slug);
            const count = g.book_count ?? 0;
            return !isExcluded && count > 0;
          });

          this.categories = validGenres.map((g: any, idx: number) => {
            const icon = this.categoryIconsMap[g.slug] || '📖';
            const color = this.categoryColorsMap[idx % this.categoryColorsMap.length];
            return {
              id: g.id,
              name: g.name,
              slug: g.slug,
              icon: icon,
              image: g.cover_image || 'assets/default_cover.jpg',
              description: g.description || `Explora historias y libros en la categoría de ${g.name}.`,
              color: color,
              bookCount: g.book_count ?? 0
            };
          });
        } else {
          this.categories = [];
        }
        this.isLoading = false;
      },
      error: (err) => {
        console.error('Error cargando categorías de la API:', err);
        this.isLoading = false;
        this.errorMsg = 'No pudimos cargar las categorías. Comprueba tu conexión e inténtalo nuevamente.';
      }
    });
  }

  retryLoad(): void {
    this.loadGenres();
    if (!this.featuredAuthor) {
      this.loadFeaturedAuthor();
    }
  }

  goToCategory(slug: string): void {
    this.activeCategorySlug = slug;
    this.router.navigate(['/categories', slug]);
  }

  onSearch(event: any): void {
    this.searchTerm = event?.target?.value || '';
  }

  clearSearch(): void {
    this.searchTerm = '';
  }

  goToBook(slug: string): void {
    this.router.navigate(['/book', slug]);
  }
}
