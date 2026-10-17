import { Component, ElementRef, ViewChild, ViewChildren, QueryList, OnInit, Input, Output, EventEmitter } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ActivatedRoute, Router } from '@angular/router';
import { DragDropModule, CdkDrag, CdkDragEnd } from '@angular/cdk/drag-drop';
import { MinigameService } from '../../../services/minigame.service';

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

  challenges: Challenge[] = [];
  currentIndex: number = 0;
  score: number = 0;
  
  droppedOption: DialogueOption | null = null;
  hasImageError: boolean = false;
  answered: boolean = false;
  isCorrectDrop: boolean = false;
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
        const itemsList = config.challenges || [config];

        return itemsList.map((c: any) => {
          // Mapeamos las opciones de diálogo originales del JSON
          let dialoguesList: DialogueOption[] = (c.dialogues || []).map((d: any, index: number) => ({
            id: d.id ?? index,
            character: d.character || '',
            text: d.text,
            isCorrect: d.is_correct ?? d.isCorrect ?? false
          }));

          // Mezclamos el orden de los diálogos al azar para evitar que la respuesta correcta esté siempre en la primera posición
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
      console.warn('No se encontraron datos para emoticono_dialogo en el libro seleccionado.');
      this.hasError = true;
    }
    this.isLoading = false;
  }

  // Función auxiliar para barajar un arreglo de forma aleatoria (Algoritmo Fisher-Yates)
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
      
      // Si acertó los puntos suficientes o el último fue correcto (puedes ajustar esta validación según tu criterio de éxito global)
      if (this.score > 0) {
        this.completed.emit(true);  // 🟢 Victoria (10 puntos)
      } else {
        this.completed.emit(false); // ❌ Derrota (0 puntos)
      }
    }
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