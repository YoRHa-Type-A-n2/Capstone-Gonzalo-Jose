import { Component, OnInit, OnDestroy, Input, Output, EventEmitter } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ActivatedRoute, Router } from '@angular/router';
import { MinigameService } from '../../../services/minigame.service';

interface Statement {
  text: string;
  isTrue: boolean;
}

interface StatementResult {
  text: string;
  isTrue: boolean;
  userChoice: boolean | null;
  isCorrect: boolean;
}

@Component({
  selector: 'app-rafaga-vf',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './rafaga-vf.component.html',
  styleUrls: ['./rafaga-vf.component.scss']
})
export class RafagaVfComponent implements OnInit, OnDestroy {
  @Input() bookId: string = '';
  @Input() gameData: any = null;
  @Input() isLastGame: boolean = false; 
  // Cambiamos el EventEmitter de boolean a number para enviar el puntaje exacto
  @Output() completed = new EventEmitter<number>();

  passageText: string = '';
  statements: Statement[] = [];
  timeLimitPerQuestion: number = 3;

  currentIndex: number = 0;
  score: number = 0;
  timeLeft: number = 3;
  timerInterval: any;
  gameStarted: boolean = false;
  gameOver: boolean = false;
  
  buttonsDisabled: boolean = true;
  selectedAnswer: boolean | null = null;
  initialLockTimeout: any;

  statementResults: StatementResult[] = [];

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
      const item = data[0];
      const config = item.config_data || {};
      
      this.passageText = config.passage_text || config.passageText || 'Lee con atención las afirmaciones a continuación.';
      this.timeLimitPerQuestion = config.time_per_statement || config.time_limit_per_question || 3;
      this.timeLeft = this.timeLimitPerQuestion;
      
      this.statements = (config.statements || []).map((s: any) => ({
        text: s.text,
        isTrue: s.is_true ?? s.isTrue
      }));

      if (this.statements.length > 0) {
        this.hasError = false;
      } else {
        this.hasError = true;
      }
    } else {
      console.warn('No se encontraron datos para rafaga-vf en el libro seleccionado.');
      this.hasError = true;
    }
    this.isLoading = false;
  }

  loadGameData(): void {
    this.isLoading = true;
    this.hasError = false;

    this.minigameService.getMinigameByCode(this.bookId, 'rafaga_vf').subscribe({
      next: (data) => this.processGameData(data),
      error: (err) => {
        console.error('Error al cargar datos del minijuego:', err);
        this.hasError = true;
        this.isLoading = false;
      }
    });
  }

  startGame() {
    if (this.statements.length === 0) return;
    this.gameStarted = true;
    this.currentIndex = 0;
    this.score = 0;
    this.statementResults = [];
    this.gameOver = false;
    this.loadNewQuestion();
  }

  loadNewQuestion() {
    this.selectedAnswer = null;
    this.buttonsDisabled = true;

    clearTimeout(this.initialLockTimeout);
    this.initialLockTimeout = setTimeout(() => {
      if (!this.gameOver) {
        this.buttonsDisabled = false;
      }
    }, 1000);

    this.startTimer();
  }

  startTimer() {
    this.timeLeft = this.timeLimitPerQuestion;
    clearInterval(this.timerInterval);
    this.timerInterval = setInterval(() => {
      this.timeLeft--;
      if (this.timeLeft <= 0) {
        clearInterval(this.timerInterval);
        this.processAnswer(null);
      }
    }, 1000);
  }

  answer(userChoice: boolean) {
    if (this.buttonsDisabled) return;
    this.buttonsDisabled = true;
    clearInterval(this.timerInterval);
    this.selectedAnswer = userChoice;

    setTimeout(() => {
      this.processAnswer(userChoice);
    }, 300);
  }

  processAnswer(userChoice: boolean | null) {
    clearInterval(this.timerInterval);
    const current = this.statements[this.currentIndex];

    const isCorrect = (userChoice !== null && userChoice === current.isTrue);

    if (isCorrect) {
      this.score += 5; // Suma 5 puntos por cada respuesta correcta
    }

    this.statementResults.push({
      text: current.text,
      isTrue: current.isTrue,
      userChoice: userChoice,
      isCorrect: isCorrect
    });

    this.currentIndex++;

    if (this.currentIndex < this.statements.length) {
      this.loadNewQuestion();
    } else {
      this.endGame();
    }
  }

  endGame() {
    this.gameOver = true;
    clearInterval(this.timerInterval);
  }

  goNext() {
    // Emitimos el puntaje total acumulado (ej: 0, 5, 10 o 15 puntos)
    this.completed.emit(this.score);
  }

  exitGame() {
    clearInterval(this.timerInterval);
    clearTimeout(this.initialLockTimeout);
    this.router.navigate(['/']);
  }

  ngOnDestroy(): void {
    clearInterval(this.timerInterval);
    clearTimeout(this.initialLockTimeout);
  }
}