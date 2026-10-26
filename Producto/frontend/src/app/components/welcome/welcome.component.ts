import { Component, OnInit, inject, ChangeDetectorRef } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router, RouterModule } from '@angular/router';
import { MinigameService, BookWithMinigames } from '../../services/minigame.service';

export interface WelcomeGame {
  code: string;
  title: string;
  description: string;
  icon: string;
  comingSoon?: boolean;
}

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

  isModalOpen: boolean = false;
  selectedGame: WelcomeGame | null = null;
  isLoadingBooks: boolean = false;
  booksWithMinigames: BookWithMinigames[] = [];

  readonly minigames: WelcomeGame[] = [
    {
      code: 'cazador_intrusos',
      title: 'Cazador de Intrusos',
      description: 'Encuentra objetos anacrónicos o fuera de lugar en la escena histórica.',
      icon: '🕵️',
      comingSoon: false
    },
    {
      code: 'busca_imagen',
      title: 'Busca en la Imagen',
      description: 'Localiza detalles clave ocultos en la ilustración del capítulo.',
      icon: '🔍',
      comingSoon: false
    },
    {
      code: 'comics_desordenados',
      title: 'Cómics Desordenados',
      description: 'Ordena la secuencia narrativa para reconstruir la historia.',
      icon: '🧩',
      comingSoon: false
    },
    {
      code: 'completa_dialogo',
      title: 'Completa el Diálogo',
      description: 'Selecciona la frase correcta dicha por cada personaje.',
      icon: '💬',
      comingSoon: false
    },
    {
      code: 'emoticono_dialogo',
      title: 'Emoticono y Diálogo',
      description: 'Asocia las emociones con las citas emblemáticas del texto.',
      icon: '🎭',
      comingSoon: false
    },
    {
      code: 'encuentra_contradiccion',
      title: 'Encuentra Contradicción',
      description: 'Detecta afirmaciones que chocan con los hechos de la obra.',
      icon: '⚡',
      comingSoon: false
    },
    {
      code: 'imagen_pixelada',
      title: 'Imagen Pixelada',
      description: 'Adivina qué personaje o escena se oculta tras los píxeles.',
      icon: '👾',
      comingSoon: false
    },
    {
      code: 'rafaga_vf',
      title: 'Ráfaga V/F',
      description: 'Contesta rápidamente si las afirmaciones son verdaderas o falsas.',
      icon: '⚡',
      comingSoon: false
    },
    {
      code: 'reconstruccion_manuscrito',
      title: 'Reconstruir Manuscrito',
      description: 'Rellena los fragmentos faltantes en el manuscrito antiguo.',
      icon: '📜',
      comingSoon: false
    },
    {
      code: 'testigo_ocular',
      title: 'Testigo Ocular',
      description: 'Pon a prueba tu memoria visual respondiendo preguntas sobre la escena.',
      icon: '👁️',
      comingSoon: false
    }
  ];

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

  openGameModal(game: WelcomeGame): void {
    if (game.comingSoon) return;
    this.selectedGame = game;
    this.isModalOpen = true;

    if (this.booksWithMinigames.length === 0) {
      this.loadBooks();
    }
  }

  closeGameModal(): void {
    this.isModalOpen = false;
    this.selectedGame = null;
  }

  selectBookAndPlay(book: BookWithMinigames): void {
    if (!book || !this.selectedGame) return;

    const gameCode = this.selectedGame.code;
    const targetBookId = book.id;

    this.closeGameModal();

    this.router.navigate(['/games/session', targetBookId], {
      queryParams: { game: gameCode }
    });
  }

  onCoverError(event: Event): void {
    const img = event.target as HTMLImageElement;
    if (img && !img.dataset['fallbackAttempted']) {
      img.dataset['fallbackAttempted'] = 'true';
      img.src = 'assets/default_cover.jpg';
    }
  }
}
