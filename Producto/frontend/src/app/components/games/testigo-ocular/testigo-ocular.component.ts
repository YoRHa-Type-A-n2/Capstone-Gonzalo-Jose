import { Component, OnInit, OnDestroy, AfterViewInit, Input, Output, EventEmitter } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ActivatedRoute, Router } from '@angular/router';
import { MinigameService } from '../../../services/minigame.service';

interface Question {
  id: number;
  prompt: string;
  correctOption: string;
  options: string[];
}

interface DemoLevel {
  id: number;
  title: string;
  storyTag: string;
  imageUrl: string;
  questions: Question[];
}

@Component({
  selector: 'app-testigo-ocular',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './testigo-ocular.component.html',
  styleUrls: ['./testigo-ocular.component.scss']
})
export class TestigoOcularComponent implements OnInit, OnDestroy, AfterViewInit {
  @Input() bookId: string = '';
  @Input() gameData: any = null;
  @Output() completed = new EventEmitter<boolean>();

  levels: DemoLevel[] = [];

  currentLevelIndex: number = 0;
  currentQuestionIndex: number = 0;
  currentLevel!: DemoLevel;
  currentQuestion!: Question;

  score: number = 0;
  lives: number = 2;
  timeLeft: number = 5.0;
  timerInterval: any = null;

  questionResults: boolean[][] = [];

  gameStatus: 'intro' | 'answering' | 'questionFeedback' | 'finished' = 'intro';

  feedbackMessage: string = '';
  isLastAttemptCorrect: boolean = false;

  isLoading: boolean = true;
  hasError: boolean = false;

  constructor(
    private router: Router,
    private route: ActivatedRoute,
    private minigameService: MinigameService
  ) {}

  ngOnInit(): void {
    window.scrollTo({ top: 0, left: 0, behavior: 'instant' });
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
        const rawLevels = config.levels || (Array.isArray(config) ? config : [config]);

        return rawLevels.map((l: any, idx: number) => ({
          id: l.id || idx + 1,
          title: l.title || 'Testigo Ocular',
          storyTag: l.storyTag || l.story_tag || '',
          imageUrl: l.imageUrl || l.image_url || '',
          questions: (l.questions || []).map((q: any, qIdx: number) => ({
            id: q.id || qIdx + 1,
            prompt: q.prompt || '',
            correctOption: q.correctOption || q.correct_option || '',
            options: q.options || []
          }))
        }));
      });

      if (this.levels.length > 0) {
        this.hasError = false;
        this.restartGame();
      } else {
        this.hasError = true;
      }
    } else {
      console.warn('No se encontraron datos para testigo_ocular en el libro seleccionado.');
      this.hasError = true;
    }
    this.isLoading = false;
  }

  ngAfterViewInit(): void {
    setTimeout(() => {
      window.scrollTo({ top: 0, left: 0, behavior: 'instant' });
    }, 0);
  }

  ngOnDestroy(): void {
    this.clearTimer();
  }

  loadGameData(): void {
    this.isLoading = true;
    this.hasError = false;

    this.minigameService.getMinigameByCode(this.bookId, 'testigo_ocular').subscribe({
      next: (data) => this.processGameData(data),
      error: (err) => {
        console.error('Error cargando minijuego testigo_ocular:', err);
        this.hasError = true;
        this.isLoading = false;
      }
    });
  }

  loadLevel(index: number): void {
    this.clearTimer();
    if (this.levels.length === 0) return;

    this.currentLevelIndex = index;
    this.currentLevel = this.levels[index];
    this.currentQuestionIndex = 0;
    this.currentQuestion = this.currentLevel.questions[0];
    this.lives = 2;
    this.gameStatus = 'intro';
  }

  startAnsweringPhase(): void {
    this.gameStatus = 'answering';
    this.currentQuestion = this.currentLevel.questions[this.currentQuestionIndex];
    this.startTimer();
  }

  startTimer(): void {
    this.clearTimer();
    this.timeLeft = 5.0;
    const stepMs = 100;
    
    this.timerInterval = setInterval(() => {
      this.timeLeft = Math.max(0, +(this.timeLeft - 0.1).toFixed(1));
      if (this.timeLeft <= 0) {
        this.clearTimer();
        this.handleTimeout();
      }
    }, stepMs);
  }

  clearTimer(): void {
    if (this.timerInterval) {
      clearInterval(this.timerInterval);
      this.timerInterval = null;
    }
  }

  handleTimeout(): void {
    this.lives--;
    this.isLastAttemptCorrect = false;

    if (this.lives > 0) {
      this.feedbackMessage = `¡Tiempo agotado! Te queda 1 vida para esta imagen.`;
    } else {
      this.markRemainingQuestionsOfLevelAsFailed();
      this.feedbackMessage = '¡Tiempo agotado y sin vidas para esta imagen!';
    }
    this.gameStatus = 'questionFeedback';
  }

  selectOption(option: string): void {
    if (this.gameStatus !== 'answering') return;

    this.clearTimer();

    if (option === this.currentQuestion.correctOption) {
      this.score += 100 + Math.round(this.timeLeft * 20);
      this.isLastAttemptCorrect = true;
      this.registerResult(true);
      this.feedbackMessage = '¡Excelente memoria! Respuesta correcta.';
      this.gameStatus = 'questionFeedback';
    } else {
      this.lives--;
      this.isLastAttemptCorrect = false;

      if (this.lives > 0) {
        this.feedbackMessage = `Incorrecto. Te queda 1 vida para esta imagen.`;
      } else {
        this.markRemainingQuestionsOfLevelAsFailed();
        this.feedbackMessage = '¡Respuesta incorrecta! Te has quedado sin vidas para esta imagen.';
      }
      this.gameStatus = 'questionFeedback';
    }
  }

  registerResult(isCorrect: boolean): void {
    if (!this.questionResults[this.currentLevelIndex]) {
      this.questionResults[this.currentLevelIndex] = [];
    }
    this.questionResults[this.currentLevelIndex][this.currentQuestionIndex] = isCorrect;
  }

  markRemainingQuestionsOfLevelAsFailed(): void {
    if (!this.questionResults[this.currentLevelIndex]) {
      this.questionResults[this.currentLevelIndex] = [];
    }
    for (let q = 0; q < this.currentLevel.questions.length; q++) {
      if (this.questionResults[this.currentLevelIndex][q] === undefined) {
        this.questionResults[this.currentLevelIndex][q] = false;
      }
    }
  }

  nextQuestionOrLevel(): void {
    if (this.lives <= 0) {
      this.gameStatus = 'finished';
      return;
    }

    if (this.isLastAttemptCorrect) {
      if (this.currentQuestionIndex + 1 < this.currentLevel.questions.length) {
        this.currentQuestionIndex++;
        this.startAnsweringPhase();
      } else {
        this.gameStatus = 'finished';
      }
    } else {
      this.startAnsweringPhase();
    }
  }

  nextLevelOrRestart(): void {
    if (this.hasNextLevel) {
      this.loadLevel(this.currentLevelIndex + 1);
    } else {
      this.completed.emit(true);
    }
  }

  restartGame(): void {
    this.score = 0;
    this.questionResults = [];
    if (this.levels.length > 0) {
      this.loadLevel(0);
    }
  }

  exitGame(): void {
    this.clearTimer();
    this.router.navigate(['/']);
  }

  get timerPercentage(): number {
    return (this.timeLeft / 5.0) * 100;
  }

  get hasNextLevel(): boolean {
    return this.currentLevelIndex + 1 < this.levels.length;
  }
}