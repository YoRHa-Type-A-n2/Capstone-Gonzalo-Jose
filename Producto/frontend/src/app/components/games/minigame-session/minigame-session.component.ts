import { Component, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ActivatedRoute, Router } from '@angular/router';
import { MinigameService } from '../../../services/minigame.service';
import { Minigame } from '../../../models/minigame';

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

  bookId: string = '';
  playlist: any[] = [];
  currentIndex: number = 0;
  isLoading: boolean = true;
  sessionFinished: boolean = false;
  score: number = 0;

  // Arreglo para almacenar el desglose de puntajes por minijuego
  gameScoreDetails: GameScoreSummary[] = [];

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

  loadSpecificGameSession(gameCode: string) {
    this.isLoading = true;
    this.minigameService.getMinigameByCode(this.bookId, gameCode).subscribe({
      next: (games: any[]) => {
        this.playlist = games;
        this.isLoading = false;
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
      },
      error: (err) => {
        console.error('❌ [MinigameSession] Error en la petición HTTP de la sesión:', err);
        this.isLoading = false;
      }
    });
  }

  getCurrentGameCode(): string {
    if (this.playlist.length === 0 || this.currentIndex >= this.playlist.length) return '';
    const currentGame = this.playlist[this.currentIndex];
    return currentGame.minigame_code || currentGame.code || '';
  }

  onGameCompleted(result: any) {
    console.log(`[MinigameSession] Evento 'completed' recibido. Resultado:`, result);
    
    // 1. Obtenemos el nombre amigable del minijuego actual antes de avanzar de índice
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
    console.log(`Puntos sumados en este juego: ${pointsToAdd} | Puntaje total acumulado: ${this.score}`);

    // 2. ¡IMPORTANTE! Guardamos el nombre y los puntos en el arreglo para la pantalla final
    this.gameScoreDetails.push({
      name: currentName,
      points: pointsToAdd
    });

    if (this.currentIndex < this.playlist.length - 1) {
      this.currentIndex++;
    } else {
      this.sessionFinished = true;
      console.log('🏁 [MinigameSession] Desglose final guardado:', this.gameScoreDetails);
    }
  }

  returnToLibrary() {
    this.router.navigate(['/library']);
  }
}