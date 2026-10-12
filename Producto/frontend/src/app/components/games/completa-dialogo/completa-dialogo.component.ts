import { Component, ElementRef, ViewChild, ViewChildren, QueryList, OnInit, OnDestroy, Input, Output, EventEmitter } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ActivatedRoute, Router } from '@angular/router';
import { DragDropModule, CdkDrag, CdkDragEnd } from '@angular/cdk/drag-drop';
import { MinigameService } from '../../../services/minigame.service';

interface DialogLevel {
  id: number;
  textBefore: string;
  textAfter: string;
  correctWord: string;
  options: string[];
  timeLeft?: number;
}

@Component({
  selector: 'app-completa-dialogo',
  standalone: true,
  imports: [CommonModule, DragDropModule],
  templateUrl: './completa-dialogo.component.html',
  styleUrls: ['./completa-dialogo.component.scss']
})
export class CompletaDialogoComponent implements OnInit, OnDestroy {
  @ViewChild('targetSlot') targetSlot!: ElementRef;
  @ViewChildren(CdkDrag) dragElements!: QueryList<CdkDrag>;

  @Input() bookId: string = '';
  @Input() gameData: any = null;
  @Output() completed = new EventEmitter<boolean>();

  levels: DialogLevel[] = [];

  currentLevelIndex: number = 0;
  currentLevel!: DialogLevel;
  availableOptions: string[] = [];
  droppedWord: string | null = null;

  score: number = 0;
  timeLeft: number = 7.0;
  timerInterval: any = null;

  levelResults: boolean[] = [];

  gameStatus: 'intro' | 'playing' | 'success' | 'error' | 'timeout' | 'finished' = 'intro';

  isLoading: boolean = true;
  hasError: boolean = false;

  constructor(
    private router: Router,
    private route: ActivatedRoute,
    private minigameService: MinigameService
  ) {}

  ngOnDestroy(): void {
    this.clearTimer();
  }

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
      this.levels = data.flatMap((item) => {
        const config = item.config_data || {};
        const rawLevels = config.levels || [config];

        return rawLevels.map((l: any, idx: number) => ({
          id: l.id || idx + 1,
          textBefore: l.text_before || l.textBefore || '',
          textAfter: l.text_after || l.textAfter || '',
          correctWord: l.correct_word || l.correctWord || '',
          options: l.options || [],
          timeLeft: l.time_left || l.timeLeft || 7.0
        }));
      });

      if (this.levels.length > 0) {
        this.hasError = false;
        this.loadLevel(this.currentLevelIndex, false);
      } else {
        this.hasError = true;
      }
    } else {
      console.warn('No se encontraron datos para completa_dialogo en el libro seleccionado.');
      this.hasError = true;
    }
    this.isLoading = false;
  }

  loadGameData(): void {
    this.isLoading = true;
    this.hasError = false;

    this.minigameService.getMinigameByCode(this.bookId, 'completa_dialogo').subscribe({
      next: (data) => this.processGameData(data),
      error: (err) => {
        console.error('Error cargando minijuego completa_dialogo:', err);
        this.hasError = true;
        this.isLoading = false;
      }
    });
  }

  loadLevel(index: number, autoStart: boolean = false): void {
    this.clearTimer();
    this.resetPositions();
    if (this.levels.length === 0) return;

    this.currentLevelIndex = index;
    this.currentLevel = this.levels[index];
    this.availableOptions = [...this.currentLevel.options].sort(() => Math.random() - 0.5);
    this.droppedWord = null;
    this.timeLeft = this.currentLevel.timeLeft || 7.0;

    if (autoStart) {
      this.gameStatus = 'playing';
      this.startTimer();
    } else {
      this.gameStatus = 'intro';
    }
  }

  startGameplay(): void {
    this.gameStatus = 'playing';
    this.startTimer();
  }

  startTimer(): void {
    const stepMs = 100;
    this.timerInterval = setInterval(() => {
      this.timeLeft = Math.max(0, +(this.timeLeft - 0.1).toFixed(1));
      if (this.timeLeft <= 0) {
        this.clearTimer();
        if (this.gameStatus === 'playing') {
          this.gameStatus = 'timeout';
          this.levelResults[this.currentLevelIndex] = false;
        }
      }
    }, stepMs);
  }

  clearTimer(): void {
    if (this.timerInterval) {
      clearInterval(this.timerInterval);
      this.timerInterval = null;
    }
  }

  onDragEnded(event: CdkDragEnd, option: string): void {
    if (this.gameStatus !== 'playing' || !this.targetSlot) return;

    const dragRect = event.source.getRootElement().getBoundingClientRect();
    const targetRect = this.targetSlot.nativeElement.getBoundingClientRect();

    const overlapPercentage = this.calculateOverlapPercentage(dragRect, targetRect);

    if (overlapPercentage >= 0.30) {
      this.clearTimer();
      this.droppedWord = option;

      if (option === this.currentLevel.correctWord) {
        this.gameStatus = 'success';
        this.score += 100 + Math.round(this.timeLeft * 20);
        this.levelResults[this.currentLevelIndex] = true;
      } else {
        this.gameStatus = 'error';
        this.levelResults[this.currentLevelIndex] = false;
      }
    }
  }

  private calculateOverlapPercentage(rect1: DOMRect, rect2: DOMRect): number {
    const xOverlap = Math.max(0, Math.min(rect1.right, rect2.right) - Math.max(rect1.left, rect2.left));
    const yOverlap = Math.max(0, Math.min(rect1.bottom, rect2.bottom) - Math.max(rect1.top, rect2.top));
    
    const overlapArea = xOverlap * yOverlap;
    const draggedArea = rect1.width * rect1.height;

    if (draggedArea === 0) return 0;
    return overlapArea / draggedArea;
  }

  resetPositions(): void {
    if (this.dragElements) {
      this.dragElements.forEach(drag => drag.reset());
    }
  }

  nextLevel(): void {
    if (this.currentLevelIndex + 1 < this.levels.length) {
      this.loadLevel(this.currentLevelIndex + 1, true);
    } else {
      this.gameStatus = 'finished';
      this.completed.emit(true);
    }
  }

  restartGame(): void {
    this.score = 0;
    this.levelResults = [];
    this.loadLevel(0, false);
  }

  exitGame(): void {
    this.router.navigate(['/']);
  }

  get timerPercentage(): number {
    const totalTime = this.currentLevel?.timeLeft || 7.0;
    return (this.timeLeft / totalTime) * 100;
  }
}