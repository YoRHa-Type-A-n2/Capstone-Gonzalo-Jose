import { Component, OnInit, inject } from '@angular/core';
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
export class MinigameSessionComponent implements OnInit {
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

  // Control del Popup de Instrucciones Iniciales
  showInstructionsModal: boolean = false;

  // Desglose de puntajes
  gameScoreDetails: GameScoreSummary[] = [];

  // Popup de Objeto Desbloqueado al volver a biblioteca
  showUnlockedItemModal: boolean = false;
  unlockedItem: any = null;

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

  loadSpecificGameSession(gameCode: string) {
    this.isLoading = true;
    this.minigameService.getMinigameByCode(this.bookId, gameCode).subscribe({
      next: (games: any[]) => {
        this.playlist = games;
        this.isLoading = false;
        this.showInstructionsModal = true; // Forzar apertura del modal instructivo
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
        this.showInstructionsModal = true; // Forzar apertura del modal instructivo
      },
      error: (err) => {
        console.error('❌ [MinigameSession] Error en la petición HTTP de la sesión:', err);
        this.isLoading = false;
      }
    });
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
    console.log(`[MinigameSession] Evento 'completed' recibido. Resultado:`, result);
    
    const currentGameCode = this.getCurrentGameCode();
    const currentName = this.getGameDisplayNameByCode(currentGameCode);

    let pointsToAdd = 0;
    if (typeof result === 'number') {
      pointsToAdd = result;
    } 
    else if (result === true) {
      pointsToAdd = 10;
    } 
    else {
      pointsToAdd = 0;
    }

    this.score += pointsToAdd;

    this.gameScoreDetails.push({
      name: currentName,
      points: pointsToAdd
    });

    if (this.currentIndex < this.playlist.length - 1) {
      this.currentIndex++;
    } else {
      this.sessionFinished = true;
    }
  }

  returnToLibrary() {
    if (!this.bookId) {
      this.router.navigate(['/library']);
      return;
    }

    const url = this.buildUrl(`mochila/books/${this.bookId}/unlocked-item/`);
    this.http.get<any>(url).subscribe({
      next: (res) => {
        // Solo muestra el popup si el objeto fue recién obtenido en esta sesión (is_new)
        if (res && res.unlocked && res.is_new && res.item) {
          this.unlockedItem = res.item;
          this.showUnlockedItemModal = true;
        } else {
          this.router.navigate(['/library']);
        }
      },
      error: (err) => {
        console.warn('⚠️ No se pudo verificar el objeto desbloqueado:', err);
        this.router.navigate(['/library']);
      }
    });
  }

  closeUnlockedModal() {
    this.showUnlockedItemModal = false;
    this.router.navigate(['/library']);
  }
}