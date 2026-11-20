import { Component, ElementRef, ViewChild, ViewChildren, QueryList, OnInit, Input, Output, EventEmitter, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ActivatedRoute, Router } from '@angular/router';
import { HttpClient } from '@angular/common/http';
import { DragDropModule, CdkDrag, CdkDragEnd } from '@angular/cdk/drag-drop';
import { MinigameService } from '../../../services/minigame.service';
import { environment } from '../../../../environments/environment';

interface DialogueOption {
  id: number;
  character: string;
  text: string;
  isCorrect: boolean;
}

interface Challenge {
  emotionTitle: string;
  emotionImage: string;
  fallbackEmoji: string;
  dialogues: DialogueOption[];
  explanation: string;
}

@Component({
  selector: 'app-emoticono-dialogo',
  standalone: true,
  imports: [CommonModule, DragDropModule],
  templateUrl: './emoticono-dialogo.component.html',
  styleUrls: ['./emoticono-dialogo.component.scss']
})
export class EmoticonoDialogoComponent implements OnInit {
  @ViewChild('targetZone') targetZone!: ElementRef;
  @ViewChildren(CdkDrag) dragElements!: QueryList<CdkDrag>;

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
  
  droppedOption: DialogueOption | null = null;
  hasImageError: boolean = false;
  answered: boolean = false;
  isCorrectDrop: boolean = false;
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
        const itemsList = config.challenges || [config];

        return itemsList.map((c: any) => {
          let dialoguesList: DialogueOption[] = (c.dialogues || []).map((d: any, index: number) => ({
            id: d.id ?? index,
            character: d.character || '',
            text: d.text,
            isCorrect: d.is_correct ?? d.isCorrect ?? false
          }));

          dialoguesList = this.shuffleArray(dialoguesList);

          return {
            emotionTitle: c.emotion_title || c.emotionTitle || 'Emoción',
            emotionImage: c.emotion_image || c.emotionImage || '',
            fallbackEmoji: c.fallback_emoji || c.fallbackEmoji || '💬',
            explanation: c.explanation || '',
            dialogues: dialoguesList
          };
        });
      });

      if (this.challenges.length > 0) {
        this.hasError = false;
      } else {
        this.hasError = true;
      }
    } else {
      this.hasError = true;
    }
    this.isLoading = false;
  }

  private shuffleArray(array: any[]): any[] {
    const arr = [...array];
    for (let i = arr.length - 1; i > 0; i--) {
      const j = Math.floor(Math.random() * (i + 1));
      [arr[i], arr[j]] = [arr[j], arr[i]];
    }
    return arr;
  }

  loadGameData(): void {
    this.isLoading = true;
    this.hasError = false;

    this.minigameService.getMinigameByCode(this.bookId, 'emoticono_dialogo').subscribe({
      next: (data) => this.processGameData(data),
      error: (err) => {
        console.error('Error cargando juego emoticono_dialogo:', err);
        this.hasError = true;
        this.isLoading = false;
      }
    });
  }

  onImageError() {
    this.hasImageError = true;
  }

  onDragEnded(event: CdkDragEnd, option: DialogueOption) {
    if (this.answered || !this.targetZone) return;

    const dragRect = event.source.getRootElement().getBoundingClientRect();
    const targetRect = this.targetZone.nativeElement.getBoundingClientRect();

    if (this.isOverlapping(dragRect, targetRect)) {
      this.droppedOption = option;
      this.answered = true;
      this.isCorrectDrop = option.isCorrect;

      if (this.isCorrectDrop) {
        this.score += 20;
      }
    }
  }

  private isOverlapping(rect1: DOMRect, rect2: DOMRect): boolean {
    return !(
      rect1.right < rect2.left ||
      rect1.left > rect2.right ||
      rect1.bottom < rect2.top ||
      rect1.top > rect2.bottom
    );
  }

  nextChallenge() {
    this.resetPositions();
    this.answered = false;
    this.droppedOption = null;
    this.hasImageError = false;
    this.isCorrectDrop = false;
    this.currentIndex++;

    if (this.currentIndex >= this.challenges.length) {
      this.gameOver = true;
      
      const isWin = this.score > 0;
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
        console.error('❌ Error registrando emoticono_dialogo en la API:', err);
        this.completed.emit(result === 'won');
      }
    });
  }

  restartGame() {
    this.resetPositions();
    this.currentIndex = 0;
    this.score = 0;
    this.answered = false;
    this.droppedOption = null;
    this.hasImageError = false;
    this.isCorrectDrop = false;
    this.gameOver = false;
  }

  private resetPositions() {
    if (this.dragElements) {
      this.dragElements.forEach(drag => drag.reset());
    }
  }

  exitGame() {
    this.router.navigate(['/']);
  }
}