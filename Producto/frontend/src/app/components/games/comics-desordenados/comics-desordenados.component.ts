import { Component, OnInit, ElementRef, ViewChildren, QueryList, Input, Output, EventEmitter } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ActivatedRoute, Router } from '@angular/router';
import { DragDropModule, CdkDrag, CdkDragEnd } from '@angular/cdk/drag-drop';
import { MinigameService } from '../../../services/minigame.service';

export interface ComicPanel {
  id: number;
  image: string;
}

export interface Challenge {
  id: number;
  title: string;
  panels: ComicPanel[];
}

@Component({
  selector: 'app-comics-desordenados',
  standalone: true,
  imports: [CommonModule, DragDropModule],
  templateUrl: './comics-desordenados.component.html',
  styleUrls: ['./comics-desordenados.component.scss']
})
export class ComicsDesordenadosComponent implements OnInit {
  @ViewChildren(CdkDrag) dragElements!: QueryList<CdkDrag>;
  @ViewChildren('slotZone') slotZones!: QueryList<ElementRef>;

  @Input() bookId: string = '';
  @Input() gameData: any = null;
  @Output() completed = new EventEmitter<boolean>();

  challenges: Challenge[] = [];

  currentIndex: number = 0;
  score: number = 0;
  attemptsRemaining: number = 2;
  
  pool: ComicPanel[] = [];
  slots: ComicPanel[][] = [[], [], [], []];

  isVerified: boolean = false;
  isCorrect: boolean = false;
  gameOver: boolean = false;

  isLoading: boolean = true;
  hasError: boolean = false;

  constructor(
    private router: Router,
    private route: ActivatedRoute,
    private minigameService: MinigameService
  ) {}

  ngOnInit(): void {
    if (!this.bookId) {
      this.bookId = this.route.snapshot.paramMap.get('bookId') || '';
    }

    if (this.gameData) {
      this.processGameData([this.gameData]);
    } else {
      this.loadGameData();
    }
  }

  processGameData(data: any[]): void {
    this.isLoading = true;
    this.hasError = false;

    if (Array.isArray(data) && data.length > 0) {
      this.challenges = data.flatMap((item) => {
        const config = item.config_data || {};
        const rawChallenges = config.challenges || (Array.isArray(config) ? config : [config]);

        return rawChallenges.map((c: any, idx: number) => ({
          id: c.id || idx + 1,
          title: c.title || 'Cómic Desordenado',
          panels: (c.panels || []).map((p: any, pIdx: number) => ({
            id: p.id || pIdx + 1,
            image: p.image || p.imageUrl || p.image_url || ''
          }))
        }));
      });

      if (this.challenges.length > 0) {
        this.hasError = false;
        this.loadChallenge(this.currentIndex);
      } else {
        this.hasError = true;
      }
    } else {
      console.warn('No se encontraron datos para comics_desordenados en el libro seleccionado.');
      this.hasError = true;
    }
    this.isLoading = false;
  }

  loadGameData(): void {
    this.isLoading = true;
    this.hasError = false;

    this.minigameService.getMinigameByCode(this.bookId, 'comics_desordenados').subscribe({
      next: (data) => this.processGameData(data),
      error: (err) => {
        console.error('Error cargando minijuego comics_desordenados:', err);
        this.hasError = true;
        this.isLoading = false;
      }
    });
  }

  loadChallenge(index: number): void {
    this.isVerified = false;
    this.isCorrect = false;
    this.attemptsRemaining = 2;
    this.slots = [[], [], [], []];
    
    if (this.challenges.length === 0) return;

    const original = [...this.challenges[index].panels];
    this.pool = this.shuffleArray(original);
  }

  private shuffleArray(array: ComicPanel[]): ComicPanel[] {
    const shuffled = [...array];
    for (let i = shuffled.length - 1; i > 0; i--) {
      const j = Math.floor(Math.random() * (i + 1));
      [shuffled[i], shuffled[j]] = [shuffled[j], shuffled[i]];
    }
    if (shuffled.every((item, idx) => item.id === idx + 1)) {
      return this.shuffleArray(array);
    }
    return shuffled;
  }

  onDragEnded(event: CdkDragEnd, panel: ComicPanel): void {
    if (this.isVerified && this.isCorrect) return;

    this.removeFromSlots(panel);

    const dragRect = event.source.getRootElement().getBoundingClientRect();
    let bestSlotIndex = -1;
    let maxRatio = 0;

    this.slotZones.forEach((slotRef, index) => {
      const slotRect = slotRef.nativeElement.getBoundingClientRect();
      const ratio = this.calculateOverlapRatio(dragRect, slotRect);
      
      if (ratio >= 0.80 && ratio > maxRatio) {
        maxRatio = ratio;
        bestSlotIndex = index;
      }
    });

    if (bestSlotIndex !== -1) {
      this.slots[bestSlotIndex].push(panel);
    }
  }

  private calculateOverlapRatio(dragRect: DOMRect, slotRect: DOMRect): number {
    const xOverlap = Math.max(0, Math.min(dragRect.right, slotRect.right) - Math.max(dragRect.left, slotRect.left));
    const yOverlap = Math.max(0, Math.min(dragRect.bottom, slotRect.bottom) - Math.max(dragRect.top, slotRect.top));
    const intersectionArea = xOverlap * yOverlap;
    const dragArea = dragRect.width * dragRect.height;

    return dragArea > 0 ? intersectionArea / dragArea : 0;
  }

  private removeFromSlots(panel: ComicPanel): void {
    for (let i = 0; i < this.slots.length; i++) {
      this.slots[i] = this.slots[i].filter(p => p.id !== panel.id);
    }
  }

  get isAllSlotsFilled(): boolean {
    return this.slots.every(slot => slot.length === 1);
  }

  verifyOrder(): void {
    if (!this.isAllSlotsFilled) return;

    let correct = true;
    for (let i = 0; i < 4; i++) {
      if (this.slots[i][0].id !== i + 1) {
        correct = false;
        break;
      }
    }

    this.isVerified = true;
    if (correct) {
      this.isCorrect = true;
      this.score += 100 * this.attemptsRemaining;
    } else {
      this.attemptsRemaining--;
      this.isCorrect = false;
    }
  }

  retryChallenge(): void {
    this.isVerified = false;
    this.slots = [[], [], [], []];
    this.resetPositions();
  }

  nextChallenge(): void {
    this.resetPositions();

    // Si se quedó sin intentos en este desafío, finalizamos el juego enviando false (derrota)
    if (!this.isCorrect && this.attemptsRemaining === 0) {
      this.gameOver = true;
      this.completed.emit(false);
      return;
    }

    if (this.currentIndex + 1 < this.challenges.length) {
      this.currentIndex++;
      this.loadChallenge(this.currentIndex);
    } else {
      this.gameOver = true;
      // Si completó todos los desafíos correctamente
      if (this.score > 0) {
        this.completed.emit(true);  // 🟢 Victoria (10 puntos)[cite: 12]
      } else {
        this.completed.emit(false); // ❌ Derrota (0 puntos)
      }
    }
  }

  restartGame(): void {
    this.resetPositions();
    this.currentIndex = 0;
    this.score = 0;
    this.gameOver = false;
    this.loadChallenge(0);
  }

  private resetPositions(): void {
    if (this.dragElements) {
      this.dragElements.forEach(drag => drag.reset());
    }
  }

  exitGame(): void {
    this.router.navigate(['/']);
  }
}