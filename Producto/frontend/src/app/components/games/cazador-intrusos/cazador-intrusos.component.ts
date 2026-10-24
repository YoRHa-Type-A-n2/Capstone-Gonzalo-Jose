import { Component, OnInit, ElementRef, ViewChild, inject, PLATFORM_ID, Input, Output, EventEmitter } from '@angular/core';
import { CommonModule, isPlatformBrowser } from '@angular/common';
import { ActivatedRoute, Router } from '@angular/router';
import { HttpClient } from '@angular/common/http';
import { MinigameService } from '../../../services/minigame.service';
import { environment } from '../../../../environments/environment';

export interface SceneItem {
  id: string;
  name: string;
  imageUrl: string;
  isIntruder: boolean;
  x: number;
  y: number;
}

export interface LevelData {
  id: number;
  title: string;
  storyTag: string;
  textDescription: string;
  bgImageUrl: string;
  items: SceneItem[];
}

@Component({
  selector: 'app-cazador-intrusos',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './cazador-intrusos.component.html',
  styleUrls: ['./cazador-intrusos.component.scss']
})
export class CazadorIntrusosComponent implements OnInit {
  @ViewChild('stageStage') stageStage!: ElementRef<HTMLDivElement>;

  @Input() bookId: string = '';
  @Input() gameData: any = null;
  @Output() completed = new EventEmitter<boolean>();

  private router = inject(Router);
  private route = inject(ActivatedRoute);
  private minigameService = inject(MinigameService);
  private http = inject(HttpClient);
  private platformId = inject(PLATFORM_ID);
  private apiUrl = environment.apiUrl || 'http://localhost:8000/api/v1';

  levels: LevelData[] = [];
  bookMinigameId: string = '';
  minigameId: string = '';

  currentLevelIndex: number = 0;
  currentLevel: LevelData | null = null;
  activeItems: SceneItem[] = [];

  lives: number = 2;
  score: number = 0;

  gameStatus: 'introText' | 'playing' | 'feedback' | 'finished' = 'introText';
  feedbackMessage: string = '';
  isLastCheckSuccess: boolean = false;

  draggedItem: SceneItem | null = null;
  dragOffset = { x: 0, y: 0 };

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

      this.levels = data.flatMap((item) => {
        const config = item.config_data || {};
        const rawLevels = config.levels || (Array.isArray(config) ? config : [config]);

        return rawLevels.map((l: any, idx: number) => ({
          id: l.id || idx + 1,
          title: l.title || 'Cazador de Intrusos',
          storyTag: l.storyTag || l.story_tag || '',
          textDescription: l.textDescription || l.text_description || '',
          bgImageUrl: l.bgImageUrl || l.bg_image_url || '',
          items: (l.items || []).map((it: any, itemIdx: number) => ({
            id: String(it.id || `item-${itemIdx + 1}`),
            name: it.name || '',
            imageUrl: it.imageUrl || it.image_url || '',
            isIntruder: it.isIntruder ?? it.is_intruder ?? false,
            x: 0,
            y: 0
          }))
        }));
      });

      if (this.levels.length > 0) {
        this.hasError = false;
        this.loadLevel(0);
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

    this.minigameService.getMinigameByCode(this.bookId, 'cazador_intrusos').subscribe({
      next: (data) => this.processGameData(data),
      error: (err) => {
        console.error('Error cargando minijuego cazador_intrusos:', err);
        this.hasError = true;
        this.isLoading = false;
      }
    });
  }

  loadLevel(index: number): void {
    if (this.levels.length === 0) return;

    this.currentLevelIndex = index;
    this.currentLevel = this.levels[index];
    this.lives = 2;
    this.activeItems = this.getRandomizedItems(this.currentLevel.items);
    this.gameStatus = 'introText';
  }

  private getRandomizedItems(originalItems: SceneItem[]): SceneItem[] {
    const items: SceneItem[] = JSON.parse(JSON.stringify(originalItems));
    const minDistanceX = 15;
    const minDistanceY = 20;
    const minX = 6;
    const maxX = 78;
    const minY = 6;
    const maxY = 70;

    const placedCoords: { x: number; y: number }[] = [];

    for (const item of items) {
      let x = 0;
      let y = 0;
      let overlaps = true;
      let attempts = 0;

      while (overlaps && attempts < 120) {
        attempts++;
        x = Math.floor(Math.random() * (maxX - minX + 1)) + minX;
        y = Math.floor(Math.random() * (maxY - minY + 1)) + minY;

        overlaps = placedCoords.some(coord =>
          Math.abs(coord.x - x) < minDistanceX && Math.abs(coord.y - y) < minDistanceY
        );
      }

      placedCoords.push({ x, y });
      item.x = x;
      item.y = y;
    }

    return items;
  }

  closeModalStartGame(): void {
    this.gameStatus = 'playing';
  }

  onMouseDown(event: MouseEvent | TouchEvent, item: SceneItem): void {
    if (this.gameStatus !== 'playing') return;

    this.draggedItem = item;
    const clientX = 'touches' in event ? event.touches[0].clientX : event.clientX;
    const clientY = 'touches' in event ? event.touches[0].clientY : event.clientY;

    this.dragOffset = { x: clientX, y: clientY };
  }

  onMouseMove(event: MouseEvent | TouchEvent): void {
    if (!this.draggedItem || !this.stageStage || this.gameStatus !== 'playing') return;

    const stageRect = this.stageStage.nativeElement.getBoundingClientRect();
    const clientX = 'touches' in event ? event.touches[0].clientX : event.clientX;
    const clientY = 'touches' in event ? event.touches[0].clientY : event.clientY;

    const deltaX = ((clientX - this.dragOffset.x) / stageRect.width) * 100;
    const deltaY = ((clientY - this.dragOffset.y) / stageRect.height) * 100;

    this.draggedItem.x += deltaX;
    this.draggedItem.y += deltaY;

    this.dragOffset = { x: clientX, y: clientY };
  }

  onMouseUp(): void {
    this.draggedItem = null;
  }

  private getItemStageOverlapPercentage(itemId: string): number {
    if (!isPlatformBrowser(this.platformId)) return 0;

    const itemElem = document.getElementById(itemId);
    const stageElem = this.stageStage?.nativeElement;

    if (!itemElem || !stageElem) return 0;

    const itemRect = itemElem.getBoundingClientRect();
    const stageRect = stageElem.getBoundingClientRect();

    const xOverlap = Math.max(0, Math.min(itemRect.right, stageRect.right) - Math.max(itemRect.left, stageRect.left));
    const yOverlap = Math.max(0, Math.min(itemRect.bottom, stageRect.bottom) - Math.max(itemRect.top, stageRect.top));

    const overlapArea = xOverlap * yOverlap;
    const itemArea = itemRect.width * itemRect.height;

    return itemArea > 0 ? overlapArea / itemArea : 0;
  }

  checkSolution(): void {
    if (this.gameStatus !== 'playing') return;

    let errorsFound = false;

    for (const item of this.activeItems) {
      const overlap = this.getItemStageOverlapPercentage(item.id);
      const isInside = overlap >= 0.7;

      if (item.isIntruder && isInside) {
        errorsFound = true;
      } else if (!item.isIntruder && !isInside) {
        errorsFound = true;
      }
    }

    if (!errorsFound) {
      this.isLastCheckSuccess = true;
      this.score += 200;
      this.feedbackMessage = '¡Perfecto! Has identificado correctamente todos los elementos.';
      this.gameStatus = 'feedback';
    } else {
      this.isLastCheckSuccess = false;
      this.lives--;

      if (this.lives <= 0) {
        this.feedbackMessage = `Te has quedado sin vidas.`;
        this.gameStatus = 'finished';
        this.sendResultToBackend('lost', 0);
      } else {
        this.feedbackMessage = `Te queda ${this.lives} vida.`;
        this.gameStatus = 'feedback';
      }
    }
  }

  resumeGameFromFeedback(): void {
    if (this.lives <= 0) {
      this.gameStatus = 'finished';
      this.sendResultToBackend('lost', 0);
    } else {
      this.gameStatus = 'playing';
    }
  }

  nextLevelOrRestart(): void {
    if (this.hasNextLevel) {
      this.loadLevel(this.currentLevelIndex + 1);
    } else {
      this.gameStatus = 'finished';
      this.sendResultToBackend('won', this.score);
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
        console.error('❌ Error registrando cazador_intrusos en la API:', err);
        this.completed.emit(result === 'won');
      }
    });
  }

  restartGame(): void {
    this.score = 0;
    if (this.levels.length > 0) {
      this.loadLevel(0);
    }
  }

  exitGame(): void {
    this.router.navigate(['/']);
  }

  get hasNextLevel(): boolean {
    return this.currentLevelIndex + 1 < this.levels.length;
  }
}