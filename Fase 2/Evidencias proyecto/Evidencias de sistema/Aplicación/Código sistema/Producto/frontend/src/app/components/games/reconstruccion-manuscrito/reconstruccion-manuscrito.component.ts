import { Component, OnInit, ElementRef, ViewChildren, QueryList, Input, Output, EventEmitter, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ActivatedRoute, Router } from '@angular/router';
import { HttpClient } from '@angular/common/http';
import { DragDropModule, CdkDrag, CdkDragEnd } from '@angular/cdk/drag-drop';
import { MinigameService } from '../../../services/minigame.service';
import { environment } from '../../../../environments/environment';

export interface StoryFragment {
  id: number;
  text: string;
}

export interface Challenge {
  id: number;
  title: string;
  fragments: StoryFragment[];
}

@Component({
  selector: 'app-reconstruccion-manuscrito',
  standalone: true,
  imports: [CommonModule, DragDropModule],
  templateUrl: './reconstruccion-manuscrito.component.html',
  styleUrls: ['./reconstruccion-manuscrito.component.scss']
})
export class ReconstruccionManuscritoComponent implements OnInit {
  @ViewChildren(CdkDrag) dragElements!: QueryList<CdkDrag>;
  @ViewChildren('slotZone') slotZones!: QueryList<ElementRef>;

  @Input() bookId: string = '';
  @Input() gameData: any = null;
  @Output() completed = new EventEmitter<boolean>();

  private router = inject(Router);
  private route = inject(ActivatedRoute);
  private minigameService = inject(MinigameService);
  private http = inject(HttpClient);
  private apiUrl = environment.apiUrl || 'http://localhost:8000/api/v1';

  challenges: Challenge[] = [];
  bookMinigameId: string = '';
  minigameId: string = '';

  currentIndex: number = 0;
  score: number = 0;
  attemptsRemaining: number = 2;
  
  pool: StoryFragment[] = [];
  slots: StoryFragment[][] = [[], [], [], [], []];

  isVerified: boolean = false;
  isCorrect: boolean = false;
  gameOver: boolean = false;

  isLoading: boolean = true;
  hasError: boolean = false;

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

  private buildUrl(path: string): string {
    const rawUrl = `${this.apiUrl}/${path}`;
    return rawUrl.replace(/([^:]\/)\/+/g, '$1');
  }

  processGameData(data: any[]): void {
    this.isLoading = true;
    this.hasError = false;

    if (Array.isArray(data) && data.length > 0) {
      const firstItem = data[0];
      this.bookMinigameId = firstItem.id || firstItem.book_minigame_id || '';
      this.minigameId = firstItem.minigame_id || '';

      this.challenges = data.flatMap((item) => {
        const config = item.config_data || {};
        const rawChallenges = config.challenges || [config];

        return rawChallenges.map((c: any, idx: number) => ({
          id: c.id || idx + 1,
          title: c.title || 'Manuscrito',
          fragments: (c.fragments || []).map((f: any) => ({
            id: f.id,
            text: f.text
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
      this.hasError = true;
    }
    this.isLoading = false;
  }

  loadGameData(): void {
    this.isLoading = true;
    this.hasError = false;

    this.minigameService.getMinigameByCode(this.bookId, 'reconstruccion_manuscrito').subscribe({
      next: (data) => this.processGameData(data),
      error: (err) => {
        console.error('Error cargando minijuego reconstruccion_manuscrito:', err);
        this.hasError = true;
        this.isLoading = false;
      }
    });
  }

  loadChallenge(index: number): void {
    this.isVerified = false;
    this.isCorrect = false;
    this.attemptsRemaining = 2;
    this.slots = [[], [], [], [], []];
    
    if (this.challenges.length === 0) return;

    const original = [...this.challenges[index].fragments];
    this.pool = this.shuffleArray(original);
  }

  private shuffleArray(array: StoryFragment[]): StoryFragment[] {
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

  onDragEnded(event: CdkDragEnd, fragment: StoryFragment): void {
    if (this.isVerified && this.isCorrect) return;

    this.removeFromSlots(fragment);

    const bubbleRect = event.source.getRootElement().getBoundingClientRect();
    let bestSlotIndex = -1;
    let maxRatio = 0;

    this.slotZones.forEach((slotRef, index) => {
      const slotRect = slotRef.nativeElement.getBoundingClientRect();
      const ratio = this.calculateOverlapRatio(bubbleRect, slotRect);
      
      if (ratio >= 0.80 && ratio > maxRatio) {
        maxRatio = ratio;
        bestSlotIndex = index;
      }
    });

    if (bestSlotIndex !== -1) {
      this.slots[bestSlotIndex].push(fragment);
    }
  }

  private calculateOverlapRatio(bubbleRect: DOMRect, slotRect: DOMRect): number {
    const xOverlap = Math.max(0, Math.min(bubbleRect.right, slotRect.right) - Math.max(bubbleRect.left, slotRect.left));
    const yOverlap = Math.max(0, Math.min(bubbleRect.bottom, slotRect.bottom) - Math.max(bubbleRect.top, slotRect.top));
    const intersectionArea = xOverlap * yOverlap;
    const bubbleArea = bubbleRect.width * bubbleRect.height;

    return bubbleArea > 0 ? intersectionArea / bubbleArea : 0;
  }

  private removeFromSlots(fragment: StoryFragment): void {
    for (let i = 0; i < this.slots.length; i++) {
      this.slots[i] = this.slots[i].filter(f => f.id !== fragment.id);
    }
  }

  get isAllSlotsFilled(): boolean {
    return this.slots.every(slot => slot.length === 1);
  }

  verifyOrder(): void {
    if (!this.isAllSlotsFilled) return;

    let correct = true;
    for (let i = 0; i < this.slots.length; i++) {
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
    this.slots = [[], [], [], [], []];
    this.resetPositions();
  }

  nextChallenge(): void {
    this.resetPositions();

    if (!this.isCorrect && this.attemptsRemaining === 0) {
      this.gameOver = true;
      this.sendResultToBackend('lost', 0);
      return;
    }

    if (this.currentIndex + 1 < this.challenges.length) {
      this.currentIndex++;
      this.loadChallenge(this.currentIndex);
    } else {
      this.gameOver = true;
      const isWin = this.isCorrect || this.score > 0;
      const finalResult = isWin ? 'won' : 'lost';
      this.sendResultToBackend(finalResult, this.score);
    }
  }

  private sendResultToBackend(result: 'won' | 'lost', score: number): void {
    const payload: any = {
      book_id: this.bookId,
      result: result,
      score: score
    };

    if (this.bookMinigameId) {
      payload.book_minigame_id = this.bookMinigameId;
    }
    if (this.minigameId) {
      payload.minigame_id = this.minigameId;
    }

    this.http.post(this.buildUrl('mochila/minigames/record/'), payload).subscribe({
      next: (res: any) => {
        this.completed.emit(result === 'won');
      },
      error: (err) => {
        console.error('❌ Error registrando reconstruccion_manuscrito en la API:', err);
        this.completed.emit(result === 'won');
      }
    });
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