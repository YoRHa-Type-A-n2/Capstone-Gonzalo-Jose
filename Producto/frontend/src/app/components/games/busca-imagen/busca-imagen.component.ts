import { Component, OnInit, OnDestroy, Input, Output, EventEmitter } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ActivatedRoute, Router } from '@angular/router';
import { MinigameService } from '../../../services/minigame.service';

export interface LevelConfig {
  id: number;
  storyTitle: string;
  textSnippet: string;
  targetObjectName: string;
  imageUrl: string;
  targetArea: {
    top: number;
    left: number;
    width: number;
    height: number;
  };
}

@Component({
  selector: 'app-busca-imagen',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './busca-imagen.component.html',
  styleUrls: ['./busca-imagen.component.scss']
})
export class BuscaImagenComponent implements OnInit, OnDestroy {
  @Input() bookId: string = '';
  @Input() gameData: any = null;
  @Output() completed = new EventEmitter<boolean>();

  gameState: 'intro' | 'playing' | 'result' = 'intro';
  resultType: 'success' | 'wrong' | 'timeout' = 'success';

  readonly TIME_LIMIT_MS: number = 5000;
  timeLeftMs: number = 5000;
  timerProgress: number = 100;
  private timerInterval: any;

  currentLevelIndex: number = 0;
  levels: LevelConfig[] = [];

  devMode: boolean = false;
  lastDevCoords: string = '';
  devTop: number = 50;
  devLeft: number = 50;
  devWidth: number = 12;
  devHeight: number = 12;

  isLoading: boolean = true;
  hasError: boolean = false;

  constructor(
    private router: Router,
    private route: ActivatedRoute,
    private minigameService: MinigameService
  ) {}

  get currentLevel(): LevelConfig {
    return this.levels[this.currentLevelIndex] || {
      id: 0,
      storyTitle: '',
      textSnippet: '',
      targetObjectName: '',
      imageUrl: '',
      targetArea: { top: 50, left: 50, width: 12, height: 12 }
    };
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

  ngOnDestroy(): void {
    this.stopTimer();
  }

  processGameData(data: any[]): void {
    this.isLoading = true;
    this.hasError = false;

    if (Array.isArray(data) && data.length > 0) {
      this.levels = data.flatMap((item) => {
        const config = item.config_data || {};
        const rawLevels = config.levels || (Array.isArray(config) ? config : [config]);

        return rawLevels.map((l: any, idx: number) => {
          const ta = l.targetArea || l.target_area || {};
          return {
            id: l.id || idx + 1,
            storyTitle: l.storyTitle || l.story_title || '',
            textSnippet: l.textSnippet || l.text_snippet || '',
            targetObjectName: l.targetObjectName || l.target_object_name || '',
            imageUrl: l.imageUrl || l.image_url || '',
            targetArea: {
              top: ta.top ?? 50,
              left: ta.left ?? 50,
              width: ta.width ?? 12,
              height: ta.height ?? 12
            }
          };
        });
      });

      if (this.levels.length > 0) {
        this.hasError = false;
        this.currentLevelIndex = 0;
        this.syncDevWithCurrentLevel();
        this.scrollToTopIfMobile();
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

    this.minigameService.getMinigameByCode(this.bookId, 'busca_imagen').subscribe({
      next: (data) => this.processGameData(data),
      error: (err) => {
        console.error('Error cargando minijuego busca_imagen:', err);
        this.hasError = true;
        this.isLoading = false;
      }
    });
  }

  startGame(): void {
    this.gameState = 'playing';
    this.scrollToTopIfMobile();
    
    if (!this.devMode) {
      this.startTimer();
    }
  }

  startTimer(): void {
    this.stopTimer();
    this.timeLeftMs = this.TIME_LIMIT_MS;
    this.timerProgress = 100;

    const stepMs = 50;
    this.timerInterval = setInterval(() => {
      this.timeLeftMs -= stepMs;
      this.timerProgress = Math.max(0, (this.timeLeftMs / this.TIME_LIMIT_MS) * 100);

      if (this.timeLeftMs <= 0) {
        this.stopTimer();
        this.handleResult('timeout');
      }
    }, stepMs);
  }

  stopTimer(): void {
    if (this.timerInterval) {
      clearInterval(this.timerInterval);
      this.timerInterval = null;
    }
  }

  onTargetClick(event: MouseEvent): void {
    event.stopPropagation();
    if (this.devMode) {
      this.captureDevCoordinates(event);
      return;
    }
    if (this.gameState !== 'playing') return;
    this.stopTimer();
    this.handleResult('success');
  }

  onImageMissClick(event: MouseEvent): void {
    if (this.devMode) {
      this.captureDevCoordinates(event);
      return;
    }
    if (this.gameState !== 'playing') return;
    this.stopTimer();
    this.handleResult('wrong');
  }

  handleResult(type: 'success' | 'wrong' | 'timeout'): void {
    this.resultType = type;
    this.gameState = 'result';
    this.scrollToTopIfMobile();

    // Si falla o se acaba el tiempo en el último nivel (o en general), evaluamos derrota
    if (type === 'wrong' || type === 'timeout') {
      if (this.currentLevelIndex >= this.levels.length - 1) {
        this.completed.emit(false); // ❌ Derrota (0 puntos)
      }
    }
  }

  nextLevel(): void {
    if (this.currentLevelIndex < this.levels.length - 1) {
      this.currentLevelIndex++;
      this.syncDevWithCurrentLevel();
      this.gameState = 'intro';
      this.scrollToTopIfMobile();
    } else {
      // Si llega aquí con éxito en el último nivel
      if (this.resultType === 'success') {
        this.completed.emit(true); // 🟢 Victoria (10 puntos)[cite: 10]
      } else {
        this.completed.emit(false); // ❌ Derrota (0 puntos)
      }
    }
  }

  openIntroModal(): void {
    this.stopTimer();
    this.gameState = 'intro';
    this.scrollToTopIfMobile();
  }

  toggleDevMode(): void {
    this.devMode = !this.devMode;
    if (this.devMode) {
      this.syncDevWithCurrentLevel();
    }
  }

  adjustDevSize(delta: number): void {
    this.devWidth = Math.max(4, Math.min(40, this.devWidth + delta));
    this.devHeight = Math.max(4, Math.min(40, this.devHeight + delta));
    this.updateDevCoordsString();
  }

  captureDevCoordinates(event: MouseEvent): void {
    const target = event.target as HTMLElement;
    const container = target.classList.contains('image-wrapper') 
      ? target 
      : target.closest('.image-wrapper') as HTMLElement;

    if (!container) return;

    const rect = container.getBoundingClientRect();
    
    const clickX = event.clientX - rect.left;
    const clickY = event.clientY - rect.top;

    this.devLeft = Math.round((clickX / rect.width) * 100);
    this.devTop = Math.round((clickY / rect.height) * 100);

    this.updateDevCoordsString();
  }

  private syncDevWithCurrentLevel(): void {
    const area = this.currentLevel.targetArea;
    this.devTop = area.top;
    this.devLeft = area.left;
    this.devWidth = area.width;
    this.devHeight = area.height;
    this.updateDevCoordsString();
  }

  private updateDevCoordsString(): void {
    this.lastDevCoords = `targetArea: { top: ${this.devTop}, left: ${this.devLeft}, width: ${this.devWidth}, height: ${this.devHeight} }`;
  }

  selectInputText(event: Event): void {
    const input = event.target as HTMLInputElement;
    if (input) {
      input.select();
    }
  }

  exitGame(): void {
    this.stopTimer();
    this.router.navigate(['/']);
  }

  private scrollToTopIfMobile(): void {
    if (typeof window !== 'undefined' && window.innerWidth <= 768) {
      window.scrollTo(0, 0);
    }
  }
}