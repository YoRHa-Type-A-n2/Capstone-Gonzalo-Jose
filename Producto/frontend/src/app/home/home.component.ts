import { Component, OnInit, OnDestroy, AfterViewInit, PLATFORM_ID, Inject, inject, ChangeDetectorRef, ElementRef, ViewChild } from '@angular/core';
import { Subject } from 'rxjs';
import { isPlatformBrowser } from '@angular/common';
import { ApiService } from '../core/services/api.service';
import { AuthService } from '../core/services/auth.service';
import { Router } from '@angular/router';
import lottie from 'lottie-web';

export interface Book {
  id: string;
  title: string;
  slug: string;
  synopsis: string;
  is_featured: boolean;
  cover_image: string | null;
  tags?: { name: string; slug: string }[];
  genres?: any[];
  price?: number;
  author_name?: string;
  ai_character_count?: number;
}

export interface DemoAvatar {
  id: number;
  name: string;
  description: string;
  avatar_image_url: string | null;
  chat_count: number;
  book_title?: string;
  book_slug?: string;
}

export interface DemoChatMessage {
  role: 'user' | 'assistant';
  content: string;
}

@Component({
  selector: 'app-home',
  templateUrl: './home.component.html',
  styleUrls: ['./home.component.css']
})
export class HomeComponent implements OnInit, OnDestroy, AfterViewInit {
  private api = inject(ApiService);
  public auth = inject(AuthService);
  private router = inject(Router);
  private cdr = inject(ChangeDetectorRef);
  private platformId = inject(PLATFORM_ID);
  private destroy$ = new Subject<void>();

  // State
  allBooks: Book[] = [];
  trendingBooks: Book[] = [];
  recommendedBooks: Book[] = [];
  discoveryBooks: Book[] = [];
  randomDiscoveryBooks: Book[] = [];
  totalBooksCount: number = 1854;
  isHowItWorksAnimated: boolean = false;

  // ── GAMIFICACIÓN: HISTORIAS COLECCIONABLES (SECCIÓN 1) ──
  featuredCollectibleStories: any[] = [
    {
      id: 'b1',
      title: 'Peter Pan y Wendy',
      author: 'J. M. Barrie',
      genre: 'Aventura',
      level: 'Nivel 1',
      chaptersCount: 17,
      progress: 0,
      cover: '/media/books/peter-pan-y-wendy-j-m-barrie/cover.jpg',
      slug: 'peter-pan-y-wendy-j-m-barrie'
    },
    {
      id: 'b2',
      title: 'Las Aventuras de Alicia en el País de las Maravillas',
      author: 'Lewis Carroll',
      genre: 'Fantasía',
      level: 'Nivel 1',
      chaptersCount: 12,
      progress: 0,
      cover: '/media/books/las-aventuras-de-alicia-en-el-pais-de-las-maravillas-carroll-lewis/cover.jpg',
      slug: 'las-aventuras-de-alicia-en-el-pais-de-las-maravillas-carroll-lewis'
    },
    {
      id: 'b3',
      title: 'Las Aventuras de Tom Sawyer',
      author: 'Mark Twain',
      genre: 'Aventura',
      level: 'Nivel 2',
      chaptersCount: 35,
      progress: 0,
      cover: '/media/books/las-aventuras-de-tom-sawyer-mark-twain/cover.jpg',
      slug: 'las-aventuras-de-tom-sawyer-mark-twain'
    },
    {
      id: 'b4',
      title: 'El Principito',
      author: 'Antoine de Saint-Exupéry',
      genre: 'Fantasía',
      level: 'Nivel 1',
      chaptersCount: 27,
      progress: 0,
      cover: '/media/books/el-principito-antoine-de-saint-exupery/cover.jpg',
      slug: 'el-principito-antoine-de-saint-exupery'
    }
  ];

  // ── GAMIFICACIÓN: PERSONAJES JUGABLES (SECCIÓN 2) ──
  featuredGameCharacters = [
    {
      id: 1,
      name: 'Sherlock Holmes',
      role: 'Detective Astuto',
      description: 'Resuelve misterios arcanos utilizando la deducción y la lógica.',
      avatarUrl: 'assets/default_avatar.jpg',
      slug: 'sherlock-holmes'
    },
    {
      id: 2,
      name: 'Alicia',
      role: 'Exploradora de Maravillas',
      description: 'Curiosa y valiente ante los enigmas del mundo subterráneo.',
      avatarUrl: 'assets/default_avatar.jpg',
      slug: 'alicia'
    },
    {
      id: 3,
      name: 'El Principito',
      role: 'Soñador Estelar',
      description: 'Viajero de asteroides que ve lo esencial con el corazón.',
      avatarUrl: 'assets/default_avatar.jpg',
      slug: 'el-principito'
    },
    {
      id: 4,
      name: 'Don Quijote',
      role: 'Caballero Andante',
      description: 'Defensor de ideales nobles que convierte molinos en gigantes.',
      avatarUrl: 'assets/default_avatar.jpg',
      slug: 'don-quijote'
    }
  ];

  // ── GAMIFICACIÓN: ESTADO "TU AVENTURA" (SECCIÓN 3) ──
  userAdventureState = {
    level: 3,
    levelTitle: 'Explorador de Leyendas',
    currentXp: 120,
    maxXp: 250,
    xpPercentage: 48,
    badgesCount: 5,
    storiesRead: 3,
    chatsCount: 14
  };

  // ── GAMIFICACIÓN: RUTA DE LA HISTORIA (SECCIÓN 4) ──
  storyTrailNodes = [
    { chapter: 1, title: 'El Comienzo del Viaje', type: 'reading', status: 'completed', icon: '📖' },
    { chapter: 2, title: 'El Encuentro con el Sabio', type: 'chat', status: 'completed', icon: '💬' },
    { chapter: 3, title: 'La Encrucijada de Sombras', type: 'decision', status: 'current', icon: '🧭' },
    { chapter: 4, title: 'El Desafío en el Templo', type: 'challenge', status: 'locked', icon: '🔒' },
    { chapter: 5, title: 'El Final de la Aventura', type: 'reward', status: 'locked', icon: '⭐' }
  ];

  // ── GAMIFICACIÓN: INSIGNIAS Y LOGROS (SECCIÓN 5) ──
  achievementsList = [
    { id: 'a1', title: 'Primera Aventura', description: 'Comenzaste tu primer viaje lector', icon: '🏆', unlocked: true },
    { id: 'a2', title: 'Lector Curioso', description: 'Completaste 3 capítulos seguidos', icon: '📚', unlocked: true },
    { id: 'a3', title: 'Explorador de Mundos', description: 'Descubriste 5 palabras de Lore', icon: '🗺️', unlocked: true },
    { id: 'a4', title: 'Maestro de Diálogos', description: 'Conversaste con 3 personajes IA', icon: '💬', unlocked: true },
    { id: 'a5', title: 'Final Desbloqueado', description: 'Completa una historia completa', icon: '⭐', unlocked: false }
  ];

  // Avatars showcase (from API)
  showcaseAvatars: DemoAvatar[] = [];
  avatarsLoading = false;

  // Demo Chat state
  demoMessages: DemoChatMessage[] = [
    { role: 'user', content: '¿Por qué luchas contra molinos?' },
    { role: 'assistant', content: 'Porque donde otros ven molinos, yo veo gigantes. El valor no reside en la victoria, sino en no bajar la espada.' }
  ];
  demoInput = '';
  demoSending = false;
  demoRemainingMessages = 3;
  demoChatLimitReached = false;
  demoAvatarName = 'Don Quijote';
  demoAvatarImage: string | null = null;

  // Libros con personajes IA activos (se carga dinámicamente)
  featuredWithCharacters: any[] = [];

  activeCharacterIndex = 0;
  private charCarouselInterval: any;

  @ViewChild('avatarsCarousel') avatarsCarousel!: ElementRef;

  private _readingContainer?: ElementRef;
  @ViewChild('readingContainer') set readingContainer(el: ElementRef) {
    if (el && !this._readingContainer) {
      this._readingContainer = el;
      lottie.loadAnimation({
        container: el.nativeElement,
        renderer: 'svg',
        loop: true,
        autoplay: true,
        path: 'assets/lottie/magic.json'
      });
    }
  }

  private _saludoContainer?: ElementRef;
  @ViewChild('saludoContainer') set saludoContainer(el: ElementRef) {
    if (el && !this._saludoContainer) {
      this._saludoContainer = el;
      lottie.loadAnimation({
        container: el.nativeElement,
        renderer: 'svg',
        loop: true,
        autoplay: true,
        path: 'assets/lottie/saludo.json'
      });
    }
  }

  private _closingContainer?: ElementRef;
  @ViewChild('closingContainer') set closingContainer(el: ElementRef) {
    if (el && !this._closingContainer) {
      this._closingContainer = el;
      lottie.loadAnimation({
        container: el.nativeElement,
        renderer: 'svg',
        loop: true,
        autoplay: true,
        path: 'assets/lottie/magic.json'
      });
    }
  }

  isLoading = true;
  errorMsg = '';

  private scrollIntervals: any[] = [];

  ngOnInit(): void {
    if (isPlatformBrowser(this.platformId)) {
      this.loadBooks();
      this.loadAIBooks();
      this.loadShowcaseAvatars();
    }
  }

  ngAfterViewInit(): void {
    this.initRevealObserver();
  }

  // ─── Avatar Showcase ─────────────────────────────────────────────────────────

  private loadShowcaseAvatars(): void {
    this.avatarsLoading = true;
    this.api.get<any>('ai/hub/avatars/?sort=popularity').subscribe({
      next: (response: any) => {
        const avatars = Array.isArray(response) ? response : (response.results || []);
        this.showcaseAvatars = avatars.slice(0, 8);
        this.avatarsLoading = false;
      },
      error: () => {
        this.avatarsLoading = false;
      }
    });
  }

  goToCharactersHub(): void {
    this.router.navigate(['/characters']);
  }

  goToCharacterChat(avatar: DemoAvatar): void {
    if (!avatar) return;

    if (!this.auth.isLoggedIn()) {
      this.router.navigate(['/demo-chat', avatar.id]);
      return;
    }

    if (!avatar.book_slug) {
      this.router.navigate(['/demo-chat', avatar.id]);
      return;
    }

    // Si está logueado, verificar propiedad
    this.api.get<any>(`library/inventory/check/?slug=${avatar.book_slug}`).subscribe({
      next: (res: any) => {
        if (res.owned) {
          // Va al lector con el chat IA abierto
          this.router.navigate(['/reader', res.inventory_id], { 
            queryParams: { chatWith: avatar.id } 
          });
        } else {
          // Va a la página del libro para adquirir it
          this.router.navigate(['/book', avatar.book_slug]);
        }
      },
      error: () => {
        // Fallback
        this.router.navigate(['/book', avatar.book_slug]);
      }
    });
  }

  scrollCarousel(direction: number): void {
    if (this.avatarsCarousel) {
      const el = this.avatarsCarousel.nativeElement;
      const scrollAmount = 320 * direction; // width of card (220px) + gap (24px) approx
      el.scrollBy({ left: scrollAmount, behavior: 'smooth' });
    }
  }

  // ─── Demo Chat ───────────────────────────────────────────────────────────────

  sendDemoMessage(): void {
    const msg = this.demoInput.trim();
    if (!msg || this.demoSending || this.demoChatLimitReached) return;

    this.demoMessages.push({ role: 'user', content: msg });
    this.demoInput = '';
    this.demoSending = true;

    this.api.post<any>('ai/demo-chat/', { message: msg }).subscribe({
      next: (res: any) => {
        this.demoMessages.push({ role: 'assistant', content: res.reply });
        this.demoRemainingMessages = res.remaining_messages ?? 0;
        if (res.avatar_name) this.demoAvatarName = res.avatar_name;
        if (res.avatar_image) this.demoAvatarImage = res.avatar_image;
        if (this.demoRemainingMessages <= 0) {
          this.demoChatLimitReached = true;
        }
        this.demoSending = false;
        setTimeout(() => this.scrollDemoToBottom(), 50);
      },
      error: (err: any) => {
        const errData = err?.error;
        if (errData?.error === 'DEMO_LIMIT_REACHED') {
          this.demoChatLimitReached = true;
          this.demoRemainingMessages = 0;
          this.demoMessages.push({
            role: 'assistant',
            content: errData.message || 'Has alcanzado el límite de mensajes de prueba. ¡Regístrate para continuar!'
          });
        } else {
          this.demoMessages.push({
            role: 'assistant',
            content: 'El viento sopla fuerte hoy y mi conexión es débil. Intenta de nuevo en un momento.'
          });
        }
        this.demoSending = false;
        setTimeout(() => this.scrollDemoToBottom(), 50);
      }
    });
  }

  onDemoKeydown(event: KeyboardEvent): void {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault();
      this.sendDemoMessage();
    }
  }

  private scrollDemoToBottom(): void {
    const el = document.querySelector('.demo-chat-messages');
    if (el) el.scrollTop = el.scrollHeight;
  }

  goToRegister(): void {
    this.router.navigate(['/register']);
  }

  // ─── Existing logic ───────────────────────────────────────────────────────────

  private initRevealObserver(): void {
    const revealObserver = new IntersectionObserver(
      (entries) => entries.forEach(e => {
        if (e.isIntersecting) {
          e.target.classList.add('visible');
          revealObserver.unobserve(e.target);
        }
      }),
      { threshold: 0.05 }
    );
    document.querySelectorAll('.reveal-section:not(.visible)').forEach(el => revealObserver.observe(el));

    // Observador para animar el camino naranja de ¿Cómo funciona?
    if (typeof window !== 'undefined' && window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
      this.isHowItWorksAnimated = true;
    } else {
      const howEl = document.querySelector('.how-it-works-section');
      if (howEl) {
        const howObserver = new IntersectionObserver(
          (entries) => entries.forEach(e => {
            if (e.isIntersecting) {
              this.isHowItWorksAnimated = true;
              this.cdr.detectChanges();
              howObserver.unobserve(e.target);
            }
          }),
          { threshold: 0.15 }
        );
        howObserver.observe(howEl);
      }
    }

    const statsEl = document.querySelector('.stats-section');
    if (statsEl) {
      const statsObserver = new IntersectionObserver(
        (entries) => entries.forEach(e => {
          if (e.isIntersecting) {
            this.animateCounters();
            statsObserver.unobserve(e.target);
          }
        }),
        { threshold: 0.3 }
      );
      statsObserver.observe(statsEl);
    }
  }

  private animateCounters(): void {
    const counters = [
      { id: 'stat-books', target: this.totalBooksCount },
      { id: 'stat-chars', target: 25 },
      { id: 'stat-convs', target: 150 },
      { id: 'stat-authors', target: 10 }
    ];
    counters.forEach(({ id, target }) => {
      const el = document.getElementById(id);
      if (!el) return;
      const duration = 1800;
      const start = performance.now();
      const update = (now: number) => {
        const progress = Math.min((now - start) / duration, 1);
        const ease = 1 - Math.pow(1 - progress, 3);
        el.textContent = Math.floor(ease * target).toLocaleString('es-CL');
        if (progress < 1) requestAnimationFrame(update);
      };
      requestAnimationFrame(update);
    });
  }

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
    this.scrollIntervals.forEach(interval => clearInterval(interval));
    if (this.charCarouselInterval) clearInterval(this.charCarouselInterval);
  }

  goToCharBook(slug: string): void {
    this.router.navigate(['/book', slug]);
  }

  setCharacterSlide(index: number): void {
    this.activeCharacterIndex = index;
  }

  private loadBooks(): void {
    this.isLoading = true;
    this.api.get<any>('catalog/books/?ordering=-is_featured,-created_at&page_size=50').subscribe({
      next: (response: any) => {
        if (this.destroy$.isStopped) {
          return;
        }
        this.allBooks = response.results || response;
        this.buildSections();
        this.isLoading = false;
        setTimeout(() => {
          if (this.destroy$.isStopped) return;
          this.initAutoScroll();
          this.initRevealObserver();
        }, 100);
      },
      error: (error) => {
        if (this.destroy$.isStopped) return;
        console.error('Error cargando libros', error);
        this.isLoading = false;
      }
    });

    this.api.get<any>('catalog/books/recommendations/').subscribe({
      next: (response) => {
        this.recommendedBooks = response.results || response;
        setTimeout(() => {
          if (!this.destroy$.isStopped) {
            this.initRevealObserver();
            this.initAutoScroll();
          }
        }, 100);
      },
      error: () => {
        // Fallback silently if recommendations fail
        this.recommendedBooks = [];
      }
    });
  }

  private loadAIBooks(): void {
    this.api.get<any>('catalog/books/?has_ai_avatars=true&ordering=-ai_character_count&page_size=10').subscribe({
      next: (response: any) => {
        if (this.destroy$.isStopped) return;
        const booksWithCharacters = response.results || response;
        console.log("AI Books Response:", booksWithCharacters);
        this.featuredWithCharacters = booksWithCharacters.map((b: any) => ({
          slug: b.slug,
          title: b.title,
          author: b.author_name || 'Desconocido',
          cover: b.cover_image || 'assets/default_cover.jpg',
          genre: (b.genres && b.genres.length > 0) ? b.genres[0].name : 'Ficción',
          characterCount: b.ai_character_count || 0
        })).sort((a: any, b: any) => b.characterCount - a.characterCount);
        console.log("Mapped featuredWithCharacters:", this.featuredWithCharacters);
        this.cdr.detectChanges();
      },
      error: (error) => {
        console.error('Error cargando libros con IA', error);
      }
    });
  }

  private initAutoScroll(): void {
    const tracks = document.querySelectorAll('.trending-track:not(.scroll-init), .recommended-track:not(.scroll-init)');
    tracks.forEach((track: any) => {
      track.classList.add('scroll-init');
      let isInteracting = false;

      track.addEventListener('mouseenter', () => isInteracting = true);
      track.addEventListener('mouseleave', () => isInteracting = false);
      track.addEventListener('touchstart', () => isInteracting = true, { passive: true });
      track.addEventListener('touchend', () => { setTimeout(() => isInteracting = false, 2000); }, { passive: true });

      const interval = setInterval(() => {
        if (!isInteracting) {
          const cardWidth = track.firstElementChild ? track.firstElementChild.clientWidth + 24 : 250;
          if (track.scrollLeft + track.clientWidth >= track.scrollWidth - 10) {
            track.scrollTo({ left: 0, behavior: 'smooth' });
          } else {
            track.scrollBy({ left: cardWidth, behavior: 'smooth' });
          }
        }
      }, 4000);

      this.scrollIntervals.push(interval);
    });
  }

  private buildSections(): void {
    this.trendingBooks = this.allBooks.filter(b => b.is_featured).slice(0, 20);
    if (this.trendingBooks.length === 0) {
      this.trendingBooks = this.allBooks.slice(0, 20);
    }

    const sampleWithCovers = this.allBooks.filter(b => b.cover_image && b.cover_image.length > 0).slice(0, 4);
    if (sampleWithCovers.length > 0) {
      this.featuredCollectibleStories = sampleWithCovers.map((b, idx) => ({
        id: b.id,
        title: b.title,
        author: b.author_name || 'Autor Clásico',
        genre: (b.genres && b.genres.length > 0) ? (typeof b.genres[0] === 'string' ? b.genres[0] : (b.genres[0].name || 'Clásico')) : 'Clásico',
        level: `Nivel ${(idx % 3) + 1}`,
        chaptersCount: 10 + (idx * 4),
        progress: 0,
        cover: b.cover_image || 'assets/default_cover.jpg',
        slug: b.slug
      }));
    }

    const trendingSlugs = new Set(this.trendingBooks.map(b => b.slug));
    this.discoveryBooks = this.allBooks.filter(b => !trendingSlugs.has(b.slug));
    this.randomDiscoveryBooks = [...this.allBooks].sort(() => 0.5 - Math.random());
  }

  scrollToCatalog(): void {
    document.getElementById('catalogo')?.scrollIntoView({ behavior: 'smooth' });
  }

  goToBook(slug: string): void {
    this.router.navigate(['/book', slug]);
  }

  trackBySlug(_: number, book: Book): string {
    return book.slug;
  }

  trackById(_: number, avatar: DemoAvatar): number {
    return avatar.id;
  }
}
