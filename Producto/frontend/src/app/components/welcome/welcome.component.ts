import { Component, OnInit, inject, ChangeDetectorRef } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router, RouterModule } from '@angular/router';
import { MinigameService, BookWithMinigames } from '../../services/minigame.service';

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

  playBookAdventure(book: BookWithMinigames): void {
    if (!book) return;
    this.router.navigate(['/games/session', book.id]);
  }

  onCoverError(event: Event): void {
    const img = event.target as HTMLImageElement;
    if (img && !img.dataset['fallbackAttempted']) {
      img.dataset['fallbackAttempted'] = 'true';
      img.src = 'assets/default_cover.jpg';
    }
  }
}
