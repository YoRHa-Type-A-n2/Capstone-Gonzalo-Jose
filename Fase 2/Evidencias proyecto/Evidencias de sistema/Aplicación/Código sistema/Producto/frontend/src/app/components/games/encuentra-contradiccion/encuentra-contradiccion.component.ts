import { Component, OnInit, OnDestroy, Input, Output, EventEmitter, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ActivatedRoute, Router } from '@angular/router';
import { HttpClient } from '@angular/common/http';
import { MinigameService } from '../../../services/minigame.service';
import { environment } from '../../../../environments/environment';

interface ImageOption {
  id: number;
  imageSrc: string;
  altText: string;
  isContradiction: boolean;
}

interface ContradictionChallenge {
  id: number;
  premiseText: string;
  explanation: string;
  images: ImageOption[];
}

@Component({
  selector: 'app-encuentra-contradiccion',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './encuentra-contradiccion.component.html',
  styleUrls: ['./encuentra-contradiccion.component.scss']
})
export class EncuentraContradiccionComponent implements OnInit, OnDestroy {
  @Input() bookId: string = '';
  @Input() gameData: any = null;
  @Output() completed = new EventEmitter<boolean>();

  private router = inject(Router);
  private route = inject(ActivatedRoute);
  private minigameService = inject(MinigameService);
  private http = inject(HttpClient);
  private apiUrl = environment.apiUrl || 'http://localhost:8000/api/v1';

  challenges: ContradictionChallenge[] = [];
  bookMinigameId: string = '';
  minigameId: string = '';

  currentIndex: number = 0;
  score: number = 0;

  showPremiseModal: boolean = true;
  TIME_LIMIT: number = 6;
  timeRemaining: number = 6;
  timerInterval: any = null;

  answered: boolean = false;
  selectedOption: ImageOption | null = null;
  isCorrect: boolean = false;
  timeOut: boolean = false;
  gameOver: boolean = false;

  isLoading: boolean = true;
  hasError: boolean = false;

  ngOnDestroy(): void {
    this.stopTimer();
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
        if (config.timeLimit || config.time_limit) {
          this.TIME_LIMIT = config.timeLimit || config.time_limit || 6;
        }

        const rawChallenges = config.challenges || [config];
        return rawChallenges.map((c: any, idx: number) => {
          let imagesList: ImageOption[] = (c.images || []).map((img: any) => ({
            id: img.id,
            imageSrc: img.image_src || img.imageSrc || '',
            altText: img.alt_text || img.altText || '',
            isContradiction: img.is_contradiction ?? img.isContradiction ?? false
          }));

          imagesList = this.shuffleArray(imagesList);

          return {
            id: c.id || idx + 1,
            premiseText: c.premise_text || c.premiseText || '',
            explanation: c.explanation || '',
            images: imagesList
          };
        });
      });

      if (this.challenges.length > 0) {
        this.hasError = false;
        this.prepareChallenge();
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

    this.minigameService.getMinigameByCode(this.bookId, 'encuentra_contradiccion').subscribe({
      next: (data) => this.processGameData(data),
      error: (err) => {
        console.error('Error cargando minijuego encuentra_contradiccion:', err);
        this.hasError = true;
        this.isLoading = false;
      }
    });
  }

  prepareChallenge() {
    this.stopTimer();
    this.showPremiseModal = true;
    this.answered = false;
    this.selectedOption = null;
    this.isCorrect = false;
    this.timeOut = false;
    this.timeRemaining = this.TIME_LIMIT;
  }

  startTimerAndGame() {
    this.showPremiseModal = false;
    this.timeRemaining = this.TIME_LIMIT;

    this.timerInterval = setInterval(() => {
      if (this.timeRemaining > 0 && !this.answered) {
        this.timeRemaining -= 0.1;
      } else if (this.timeRemaining <= 0 && !this.answered) {
        this.handleTimeOut();
      }
    }, 100);
  }

  selectOption(option: ImageOption) {
    if (this.answered || this.showPremiseModal) return;

    this.stopTimer();
    this.answered = true;
    this.selectedOption = option;
    this.isCorrect = option.isContradiction;

    if (this.isCorrect) {
      const pointsObtained = Math.max(10, Math.round(this.timeRemaining * 15));
      this.score += pointsObtained;
    }
  }

  handleTimeOut() {
    this.stopTimer();
    this.timeRemaining = 0;
    this.answered = true;
    this.timeOut = true;
    this.isCorrect = false;
  }

  nextChallenge() {
    this.currentIndex++;
    if (this.currentIndex >= this.challenges.length) {
      this.gameOver = true;
      
      const isWin = this.score > 0;
      const finalResult = isWin ? 'won' : 'lost';
      this.sendResultToBackend(finalResult, this.score);
    } else {
      this.prepareChallenge();
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
        console.error('❌ Error registrando encuentra_contradiccion en la API:', err);
        this.completed.emit(result === 'won');
      }
    });
  }

  restartGame() {
    this.currentIndex = 0;
    this.score = 0;
    this.gameOver = false;
    this.prepareChallenge();
  }

  stopTimer() {
    if (this.timerInterval) {
      clearInterval(this.timerInterval);
      this.timerInterval = null;
    }
  }

  exitGame() {
    this.stopTimer();
    this.router.navigate(['/']);
  }
}