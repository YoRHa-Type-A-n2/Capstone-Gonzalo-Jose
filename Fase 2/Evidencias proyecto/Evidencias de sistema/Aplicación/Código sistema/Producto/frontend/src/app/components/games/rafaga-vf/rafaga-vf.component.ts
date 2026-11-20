import { Component, OnInit, OnDestroy, Input, Output, EventEmitter, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ActivatedRoute, Router } from '@angular/router';
import { HttpClient } from '@angular/common/http';
import { MinigameService } from '../../../services/minigame.service';
import { environment } from '../../../../environments/environment';

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
  @Output() completed = new EventEmitter<number>();

  private router = inject(Router);
  private route = inject(ActivatedRoute);
  private minigameService = inject(MinigameService);
  private http = inject(HttpClient);
  private apiUrl = environment.apiUrl || 'http://localhost:8000/api/v1';

  passageText: string = '';
  statements: Statement[] = [];
  timeLimitPerQuestion: number = 3;

  bookMinigameId: string = '';
  minigameId: string = '';

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
      const item = data[0];
      this.bookMinigameId = item.id || item.book_minigame_id || '';
      this.minigameId = item.minigame_id || '';

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
      this.score += 5; 
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

    // Determinar si ganó o perdió (en ráfaga V/F, definimos victoria si el score > 0)
    const result = this.score > 0 ? 'won' : 'lost';
    this.sendResultToBackend(result, this.score);
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
        // Actualizamos el score con lo que respondió la API si aplica
      },
      error: (err) => {
        console.error('❌ Error registrando rafaga_vf en la API:', err);
      }
    });
  }

  goNext() {
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