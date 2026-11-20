import { Component, OnInit, OnDestroy, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { HttpClient } from '@angular/common/http';
import { ActivatedRoute, Router } from '@angular/router';
import { MinigameService } from '../../../services/minigame.service';
import { environment } from '../../../../environments/environment';

// Importación de componentes de minijuegos
import { CompletaDialogoComponent } from '../completa-dialogo/completa-dialogo.component';
import { ImagenPixeladaComponent } from '../imagen-pixelada/imagen-pixelada.component';
import { RafagaVfComponent } from '../rafaga-vf/rafaga-vf.component';
import { EmoticonoDialogoComponent } from '../emoticono-dialogo/emoticono-dialogo.component';
import { EncuentraContradiccionComponent } from '../encuentra-contradiccion/encuentra-contradiccion.component';
import { ReconstruccionManuscritoComponent } from '../reconstruccion-manuscrito/reconstruccion-manuscrito.component';
import { TestigoOcularComponent } from '../testigo-ocular/testigo-ocular.component';
import { CazadorIntrusosComponent } from '../cazador-intrusos/cazador-intrusos.component';
import { BuscaImagenComponent } from '../busca-imagen/busca-imagen.component';
import { ComicsDesordenadosComponent } from '../comics-desordenados/comics-desordenados.component';

import { resolveItemIcon, handleItemImageError, DEFAULT_ITEM_ICON } from '../../../core/utils/item-icon.util';

interface GameScoreSummary {
  name: string;
  points: number;
}

@Component({
  selector: 'app-minigame-session',
  standalone: true,
  imports: [
    CommonModule,
    CompletaDialogoComponent,
    ImagenPixeladaComponent,
    RafagaVfComponent,
    EmoticonoDialogoComponent,
    EncuentraContradiccionComponent,
    ReconstruccionManuscritoComponent,
    TestigoOcularComponent,
    CazadorIntrusosComponent,
    BuscaImagenComponent,
    ComicsDesordenadosComponent
  ],
  templateUrl: './minigame-session.component.html',
  styleUrls: ['./minigame-session.component.scss']
})
export class MinigameSessionComponent implements OnInit, OnDestroy {
  private route = inject(ActivatedRoute);
  private router = inject(Router);
  private minigameService = inject(MinigameService);
  private http = inject(HttpClient);
  private apiUrl = environment.apiUrl || 'http://localhost:8000/api/v1';

  bookId: string = '';
  playlist: any[] = [];
  currentIndex: number = 0;
  isLoading: boolean = true;
  sessionFinished: boolean = false;
  score: number = 0;

  gamesWon: number = 0;
  showInstructionsModal: boolean = false;
  gameScoreDetails: GameScoreSummary[] = [];

  // Popup de Objeto Desbloqueado al terminar la sesión
  showUnlockedItemModal: boolean = false;
  unlockedItem: any = null;
  private readingItemChecked: boolean = false;

  ngOnInit() {
    const routeId = this.route.snapshot.paramMap.get('bookId');
    const specificGameCode = this.route.snapshot.queryParamMap.get('game');

    if (routeId) {
      this.bookId = routeId;
      
      if (specificGameCode) {
        this.loadSpecificGameSession(specificGameCode);
      } else {
        this.loadSession();
      }
    } else {
      console.error('❌ [MinigameSession] No se encontró un bookId válido en la ruta.');
      this.isLoading = false;
      this.router.navigate(['/library']);
    }
  }

  private buildUrl(path: string): string {
    const rawUrl = `${this.apiUrl}/${path}`;
    return rawUrl.replace(/([^:]\/)\/+/g, '$1');
  }

  getCleanIconUrl(iconPath: string): string {
    if (!iconPath) return 'assets/images/default-item.png';
    if (iconPath.startsWith('http')) return iconPath;
    const backendUrl = this.apiUrl.split('/api/v1/')[0];
    return `${backendUrl}/media/${iconPath}`;
  }

  loadSpecificGameSession(gameCode: string) {
    this.isLoading = true;
    this.minigameService.getMinigameByCode(this.bookId, gameCode).subscribe({
      next: (games: any[]) => {
        this.playlist = games;
        this.isLoading = false;
        this.showInstructionsModal = true;
      },
      error: (err) => {
        console.error('❌ [MinigameSession] Error al cargar el minijuego específico:', err);
        this.isLoading = false;
      }
    });
  }

  getCurrentGameDisplayName(): string {
    return this.getGameDisplayNameByCode(this.getCurrentGameCode());
  }

  getGameDisplayNameByCode(code: string): string {
    const namesMap: { [key: string]: string } = {
      'cazador_intrusos': 'Cazador de Intrusos',
      'busca_imagen': 'Busca en la Imagen',
      'comics_desordenados': 'Cómics Desordenados',
      'completa_dialogo': 'Completa el Diálogo',
      'emoticono_dialogo': 'Emoticono diálogo',
      'encuentra_contradiccion': 'Encuentra la contradicción',
      'imagen_pixelada': 'Imagen Pixelada',
      'rafaga_vf': 'Ráfaga Verdadero/Falso',
      'reconstruccion_manuscrito': 'Reconstruir Manuscrito',
      'testigo_ocular': 'Testigo Ocular'
    };
    return namesMap[code] || 'Minijuego Interactivo';
  }

  loadSession() {
    this.isLoading = true;
    this.minigameService.getMinigamesSession(this.bookId).subscribe({
      next: (games: any[]) => {
        const uniqueGamesMap = new Map();
        for (const game of games) {
          const code = game.minigame_code || game.code;
          if (code && !uniqueGamesMap.has(code)) {
            uniqueGamesMap.set(code, game);
          }
        }
        
        let uniqueList = Array.from(uniqueGamesMap.values());
        uniqueList = uniqueList.sort(() => Math.random() - 0.5);
        this.playlist = uniqueList.slice(0, 5);
        this.isLoading = false;
        this.showInstructionsModal = true;
      },
      error: (err) => {
        console.error('❌ [MinigameSession] Error en la petición HTTP de la sesión:', err);
        this.isLoading = false;
      }
    });
    // Iniciar música de los desafíos
    this.playChallengeAudio();
  }

  startSessionFromInstructions() {
    this.showInstructionsModal = false;
    
  }

  getCurrentGameCode(): string {
    if (this.playlist.length === 0 || this.currentIndex >= this.playlist.length) return '';
    const currentGame = this.playlist[this.currentIndex];
    return currentGame.minigame_code || currentGame.code || '';
  }

  onGameCompleted(result: any) {
    const currentGameCode = this.getCurrentGameCode();
    const currentName = this.getGameDisplayNameByCode(currentGameCode);

    let pointsToAdd = 0;
    if (typeof result === 'number') {
      pointsToAdd = result;
    } else if (result === true) {
      pointsToAdd = 10;
    } else {
      pointsToAdd = 0;
    }

    this.score += pointsToAdd;

    if (pointsToAdd > 0) {
      this.gamesWon++;
    }

    this.gameScoreDetails.push({
      name: currentName,
      points: pointsToAdd
    });

    if (this.currentIndex < this.playlist.length - 1) {
      this.currentIndex++;
    } else {
      this.sessionFinished = true;
      // Detener la música al finalizar todos los desafíos
      this.stopChallengeAudio();
      this.checkAndClaimReadingItem();
    }
  }

  readonly defaultItemIcon = DEFAULT_ITEM_ICON;

  getItemIcon(iconPath: string | null | undefined): string {
    return resolveItemIcon(iconPath, environment.apiUrl);
  }

  onImageError(event: Event): void {
    handleItemImageError(event);
  }

  /**
   * Al finalizar los desafíos, consultamos directamente al endpoint si hay un objeto
   * de lectura desbloqueable para este libro que el usuario haya ganado en esta sesión.
   */
  private checkAndClaimReadingItem() {
    if (this.gamesWon < 1 || this.readingItemChecked || !this.bookId) return;
    this.readingItemChecked = true;

    const url = this.buildUrl(`mochila/books/${this.bookId}/unlocked-item/`);
    this.http.get<any>(url).subscribe({
      next: (res) => {
        // Si el backend confirma que se ha ganado y existe el ítem
        if (res?.unlocked === true && res?.item) {
          this.unlockedItem = res.item;
          this.showUnlockedItemModal = true;
        } else {
          this.unlockedItem = null;
          this.showUnlockedItemModal = false;
        }
      },
      error: (err) => {
        console.warn('⚠️ No se pudo verificar el objeto desbloqueado:', err);
      }
    });
  }

  returnToLibrary() {
    this.stopChallengeAudio();
    this.router.navigate(['/library']);
  }

  closeUnlockedModal() {
    this.showUnlockedItemModal = false;
  }
  // Audio de fondo para los desafíos
  private challengeAudio: HTMLAudioElement | null = null;

  private readonly challengeAudioPath = 'assets/audio/desafio.mp3';

  private playChallengeAudio(): void {
    if (!this.challengeAudio) {
      this.challengeAudio = new Audio(this.challengeAudioPath);

      // Configuración del audio
      this.challengeAudio.loop = true;
      this.challengeAudio.volume = 0.35;
      this.challengeAudio.preload = 'auto';
    }

    this.challengeAudio.currentTime = 4;

    this.challengeAudio.play().catch(error => {
      console.warn('No se pudo reproducir el audio de los desafíos:', error);
    });
  }

  private stopChallengeAudio(): void {
    if (this.challengeAudio) {
      this.challengeAudio.pause();
      this.challengeAudio.currentTime = 0;
    }
  }

  ngOnDestroy(): void {
    this.stopChallengeAudio();
    this.challengeAudio = null;
  }
}