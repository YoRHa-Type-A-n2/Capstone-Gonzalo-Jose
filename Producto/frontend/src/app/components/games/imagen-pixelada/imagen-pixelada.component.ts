import { Component, OnInit, OnDestroy, ViewChild, ElementRef, Input, Output, EventEmitter } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ActivatedRoute, Router } from '@angular/router';
import { MinigameService } from '../../../services/minigame.service';

interface PixelChallenge {
  id: number;
  correctCharacter: string;
  imageSrc: string;
  fallbackEmoji: string;
  options: string[];
  totalTime: number;
}

@Component({
  selector: 'app-imagen-pixelada',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './imagen-pixelada.component.html',
  styleUrls: ['./imagen-pixelada.component.scss']
})
export class ImagenPixeladaComponent implements OnInit, OnDestroy {
  @ViewChild('pixelCanvas', { static: false }) canvasRef!: ElementRef<HTMLCanvasElement>;

  @Input() bookId: string = '';
  @Input() gameData: any = null;
  @Output() completed = new EventEmitter<boolean>();

  challenges: PixelChallenge[] = [];
  currentIndex: number = 0;
  score: number = 0;

  TOTAL_TIME: number = 15;
  elapsedTime: number = 0;
  timerInterval: any = null;
  currentPotentialPoints: number = 100;

  imgElement: HTMLImageElement | null = null;
  imageLoaded: boolean = false;
  hasImageError: boolean = false;
  offCanvas: HTMLCanvasElement | null = null;

  answered: boolean = false;
  selectedOption: string | null = null;
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
      this.challenges = data.flatMap((item, idx) => {
        const config = item.config_data || {};
        const itemsList = config.challenges || [config];
        const globalTime = config.total_time || config.totalTime;

        return itemsList.map((c: any, subIdx: number) => {
          // 1. Obtenemos las opciones originales de la API
          let rawOptions = c.options || [];
          
          // 2. Mezclamos las opciones al azar para que no queden fijas en la misma posición
          let shuffledOptions = this.shuffleArray(rawOptions);

          return {
            id: c.id || idx * 10 + subIdx,
            correctCharacter: c.correct_character || c.correctCharacter,
            imageSrc: c.image_src || c.imageSrc,
            fallbackEmoji: c.fallback_emoji || c.fallbackEmoji || '❓',
            options: shuffledOptions, // Asignamos las opciones barajadas
            totalTime: c.total_time || c.totalTime || globalTime || 15
          };
        });
      });

      if (this.challenges.length > 0) {
        this.hasError = false;
        this.isLoading = false;
        this.loadChallenge();
      } else {
        this.hasError = true;
        this.isLoading = false;
      }
    } else {
      console.warn('No se encontraron datos para pixelado en el libro seleccionado.');
      this.hasError = true;
      this.isLoading = false;
    }
  }

  // Función auxiliar para barajar arreglos al azar (Algoritmo Fisher-Yates)
  private shuffleArray(array: string[]): string[] {
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

    this.minigameService.getMinigameByCode(this.bookId, 'imagen_pixelada').subscribe({
      next: (data) => this.processGameData(data),
      error: (err) => {
        console.error('Error cargando minijuego pixelado:', err);
        this.hasError = true;
        this.isLoading = false;
      }
    });
  }

  ngOnDestroy(): void {
    this.clearTimer();
  }

  loadChallenge() {
    this.clearTimer();
    this.answered = false;
    this.selectedOption = null;
    this.isCorrect = false;
    this.hasImageError = false;
    this.imageLoaded = false;
    this.elapsedTime = 0;
    this.currentPotentialPoints = 100;

    if (this.challenges.length === 0) return;

    const currentChallenge = this.challenges[this.currentIndex];
    this.TOTAL_TIME = currentChallenge.totalTime || 15;

    this.imgElement = new Image();
    this.imgElement.src = currentChallenge.imageSrc;

    this.imgElement.onload = () => {
      this.imageLoaded = true;
      this.startTimerAndRendering();
    };

    this.imgElement.onerror = () => {
      this.hasImageError = true;
      this.startTimerAndRendering();
    };
  }

  startTimerAndRendering() {
    this.renderFrame();

    this.timerInterval = setInterval(() => {
      if (this.elapsedTime < this.TOTAL_TIME && !this.answered) {
        this.elapsedTime += 0.1;
        const progress = Math.min(this.elapsedTime / this.TOTAL_TIME, 1);
        this.currentPotentialPoints = Math.max(1, Math.round(100 * (1 - progress)));
        this.renderFrame();
      } else if (this.elapsedTime >= this.TOTAL_TIME && !this.answered) {
        this.currentPotentialPoints = 1;
        this.renderFrame();
      }
    }, 100);
  }

  renderFrame() {
    if (this.hasImageError || !this.imageLoaded || !this.canvasRef) return;

    const canvas = this.canvasRef.nativeElement;
    const ctx = canvas.getContext('2d');
    if (!ctx || !this.imgElement) return;

    const progress = Math.min(this.elapsedTime / this.TOTAL_TIME, 1);
    const pixelScale = 0.03 + (0.97 * Math.pow(progress, 2));

    const canvasWidth = canvas.width;
    const canvasHeight = canvas.height;

    const scaledWidth = Math.max(4, Math.floor(canvasWidth * pixelScale));
    const scaledHeight = Math.max(4, Math.floor(canvasHeight * pixelScale));

    if (!this.offCanvas) {
      this.offCanvas = document.createElement('canvas');
    }
    this.offCanvas.width = scaledWidth;
    this.offCanvas.height = scaledHeight;

    const offCtx = this.offCanvas.getContext('2d');
    if (offCtx) {
      offCtx.imageSmoothingEnabled = true;
      offCtx.drawImage(this.imgElement, 0, 0, scaledWidth, scaledHeight);

      ctx.imageSmoothingEnabled = false;
      ctx.clearRect(0, 0, canvasWidth, canvasHeight);
      ctx.drawImage(this.offCanvas, 0, 0, scaledWidth, scaledHeight, 0, 0, canvasWidth, canvasHeight);
    }
  }

  selectOption(option: string) {
    if (this.answered) return;

    this.clearTimer();
    this.answered = true;
    this.selectedOption = option;

    const correct = this.challenges[this.currentIndex].correctCharacter;
    this.isCorrect = (option === correct);

    if (this.isCorrect) {
      this.score += this.currentPotentialPoints;
    }

    this.elapsedTime = this.TOTAL_TIME;
    this.renderFrame();
  }

  nextChallenge() {
    this.currentIndex++;
    if (this.currentIndex >= this.challenges.length) {
      this.gameOver = true;
      if (this.score > 0) {
        this.completed.emit(true);  // 🟢 Victoria (10 puntos)[cite: 16]
      } else {
        this.completed.emit(false); // ❌ Derrota (0 puntos)
      }
    } else {
      this.loadChallenge();
    }
  }

  restartGame() {
    this.currentIndex = 0;
    this.score = 0;
    this.gameOver = false;
    this.loadChallenge();
  }

  clearTimer() {
    if (this.timerInterval) {
      clearInterval(this.timerInterval);
      this.timerInterval = null;
    }
  }

  exitGame() {
    this.clearTimer();
    this.router.navigate(['/']);
  }
}