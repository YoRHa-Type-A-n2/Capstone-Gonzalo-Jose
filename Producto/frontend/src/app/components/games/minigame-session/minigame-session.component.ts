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

  ngOnInit() {
    const routeId = this.route.snapshot.paramMap.get('bookId');
    if (routeId) {
      this.bookId = routeId;
      this.loadSession();
    } else {
      console.error('❌ [MinigameSession] No se encontró un bookId válido en la ruta.');
      this.isLoading = false;
      this.router.navigate(['/library']);
    }
  }

  loadSession() {
    this.isLoading = true;
    console.log(`📡 [MinigameSession] Solicitando playlist para el bookId UUID: ${this.bookId}`);
    
    this.minigameService.getMinigamesSession(this.bookId).subscribe({
      next: (games: any[]) => {
        console.log('✅ [MinigameSession] Datos crudos devueltos por la API:', games);
        
        // 1. Filtramos para asegurar estrictamente UN SOLO minijuego por cada 'minigame_code' único
        const uniqueGamesMap = new Map();
        for (const game of games) {
          const code = game.minigame_code || game.code;
          if (code && !uniqueGamesMap.has(code)) {
            uniqueGamesMap.set(code, game);
          }
        }
        
        let uniqueList = Array.from(uniqueGamesMap.values());

        // 2. Opcional: Si quieres barajarlos y limitar la sesión a 5 minijuegos diferentes
        uniqueList = uniqueList.sort(() => Math.random() - 0.5);
        this.playlist = uniqueList.slice(0, 5); // Cambia el número si prefieres otro límite

        this.isLoading = false;
        
        if (this.playlist && this.playlist.length > 0) {
          console.log('🔍 [MinigameSession] Playlist filtrada y lista (sin repetir tipos):', this.playlist);
          console.log('🔑 [MinigameSession] Código evaluado (getCurrentGameCode):', this.getCurrentGameCode());
        } else {
          console.warn('⚠️ [MinigameSession] La playlist quedó vacía tras el filtrado.');
        }
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
    
    // Capturamos 'minigame_code' que es el nombre exacto que manda tu API Django
    const code = currentGame.minigame_code || currentGame.code || '';
    
    return code;
  }

  onGameCompleted(success: any) {
    console.log(`🎯 [MinigameSession] Evento 'completed' recibido del minijuego [${this.currentIndex}]. Resultado:`, success);
    if (success) {
      this.score += 100;
    }

    if (this.currentIndex < this.playlist.length - 1) {
      this.currentIndex++;
      console.log(`➡️ [MinigameSession] Avanzando al siguiente minijuego. Nuevo índice: ${this.currentIndex}`);
    } else {
      console.log('🏁 [MinigameSession] Todos los minijuegos de la playlist han finalizado.');
      this.sessionFinished = true;
    }
  }

  returnToLibrary() {
    this.router.navigate(['/library']);
  }
}