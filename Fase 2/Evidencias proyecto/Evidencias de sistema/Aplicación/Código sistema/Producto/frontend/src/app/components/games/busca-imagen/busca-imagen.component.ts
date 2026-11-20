import { Component, OnInit, OnDestroy, Input, Output, EventEmitter, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ActivatedRoute, Router } from '@angular/router';
import { HttpClient } from '@angular/common/http';
import { MinigameService } from '../../../services/minigame.service';
import { environment } from '../../../../environments/environment';

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

  private router = inject(Router);
  private route = inject(ActivatedRoute);
  private minigameService = inject(MinigameService);
  private http = inject(HttpClient);
  private apiUrl = environment.apiUrl || 'http://localhost:8000/api/v1';

  gameState: 'intro' | 'playing' | 'result' = 'intro';
  resultType: 'success' | 'wrong' | 'timeout' = 'success';

  readonly TIME_LIMIT_MS: number = 5000;
  timeLeftMs: number = 5000;
  timerProgress: number = 100;
  private timerInterval: any;

  currentLevelIndex: number = 0;
  levels: LevelConfig[] = [];
  bookMinigameId: string = '';
  minigameId: string = '';

  // --- MODO DESARROLLADOR ---
  devMode: boolean = false;
  lastDevCoords: string = '';
  devTop: number = 50;
  devLeft: number = 50;
  devWidth: number = 12;
  devHeight: number = 12;

  isLoading: boolean = true;
  hasError: boolean = false;

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

    if (type === 'wrong' || type === 'timeout') {
      if (this.currentLevelIndex >= this.levels.length - 1) {
        this.sendResultToBackend('lost', 0);
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
      if (this.resultType === 'success') {
        this.sendResultToBackend('won', 10);
      } else {
        this.sendResultToBackend('lost', 0);
      }
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
        const isWin = result === 'won';
        this.completed.emit(isWin);
      },
      error: (err) => {
        console.error('❌ Error al registrar resultado en la API:', err);
        this.completed.emit(result === 'won');
      }
    });
  }

  openIntroModal(): void {
    this.stopTimer();
    this.gameState = 'intro';
    this.scrollToTopIfMobile();
  }

  // --- MÉTODOS DEL MODO DESARROLLADOR ---

  toggleDevMode(): void {
    this.devMode = !this.devMode;
    if (this.devMode) {
      this.stopTimer();
      this.gameState = 'playing'; // Entramos directo a la pantalla de juego
      // CORRECCIÓN: Al activar el modo dev, forzamos la carga de TODOS los elementos de busca_imagen desde la API[cite: 26, 27, 28]
      this.loadGameData();
    } else {
      // Al salir del modo dev, restauramos el juego original de la sesión si existía[cite: 28]
      if (this.gameData) {
        this.processGameData([this.gameData]);
      } else {
        this.loadGameData();
      }
    }
  }

  devPrevLevel(): void {
    if (this.currentLevelIndex > 0) {
      this.currentLevelIndex--;
      this.syncDevWithCurrentLevel();
    }
  }

  devNextLevel(): void {
    if (this.currentLevelIndex < this.levels.length - 1) {
      this.currentLevelIndex++;
      this.syncDevWithCurrentLevel();
    }
  }

  adjustDevSize(delta: number): void {
    this.devWidth = Math.max(2, Math.min(60, this.devWidth + delta));
    this.devHeight = Math.max(2, Math.min(60, this.devHeight + delta));
    this.saveCurrentLevelTargetArea();
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

    this.saveCurrentLevelTargetArea();
    this.updateDevCoordsString();
  }

  private saveCurrentLevelTargetArea(): void {
    if (this.levels[this.currentLevelIndex]) {
      this.levels[this.currentLevelIndex].targetArea = {
        top: this.devTop,
        left: this.devLeft,
        width: this.devWidth,
        height: this.devHeight
      };
    }
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
    this.lastDevCoords = `"targetArea": {\n  "top": ${this.devTop},\n  "left": ${this.devLeft},\n  "width": ${this.devWidth},\n  "height": ${this.devHeight}\n}`;
  }

  copyCoordsToClipboard(): void {
    if (navigator.clipboard) {
      navigator.clipboard.writeText(this.lastDevCoords).then(() => {
        console.log('✅ Coordenadas copiadas al portapapeles.');
      });
    }
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