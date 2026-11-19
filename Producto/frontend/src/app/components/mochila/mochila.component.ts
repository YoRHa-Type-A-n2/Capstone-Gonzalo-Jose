import { Component, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { HttpClient } from '@angular/common/http';
import { MatDialogRef, MatDialogModule } from '@angular/material/dialog';
import { environment } from '../../../environments/environment';
import { resolveItemIcon, handleItemImageError, DEFAULT_ITEM_ICON } from '../../core/utils/item-icon.util';

@Component({
  selector: 'app-mochila',
  standalone: true,
  imports: [CommonModule, FormsModule, MatDialogModule],
  templateUrl: './mochila.component.html',
  styleUrls: ['./mochila.component.scss']
})
export class MochilaComponent implements OnInit {
  private http = inject(HttpClient);
  public dialogRef = inject(MatDialogRef<MochilaComponent>);
  private apiUrl = environment.apiUrl || 'http://localhost:8000/api';

  backpackData: any = null;
  shopItems: any[] = [];
  allAvailableItems: any[] = [];
  ownedItemIds: Set<string> = new Set();
  purchasingIds: Set<string> = new Set();
  
  currentView: 'inventory' | 'shop' = 'inventory';
  isLoading: boolean = true;

  // Filtros y propiedades para gráficos
  selectedTextFilter: string = '';
  selectedMinigameFilter: string = '';
  
  availableTexts: string[] = [];
  availableMinigames: string[] = [];

  topBooksData: any[] = [];
  maxTopBarValue: number = 1;

  textFilteredMinigames: any[] = [];
  maxTextFilteredValue: number = 1;

  minigameFilteredBooks: any[] = [];
  progressiveHistory: any[] = [];
  maxProgValue: number = 1;

  ngOnInit() {
    this.loadBackpackData();
  }

  private buildUrl(path: string): string {
    const rawUrl = `${this.apiUrl}/${path}`;
    return rawUrl.replace(/([^:]\/)\/+/g, '$1');
  }

  loadBackpackData() {
    this.isLoading = true;
    this.http.get(this.buildUrl('mochila/')).subscribe({
      next: (data: any) => {
        this.backpackData = data;
        
        this.ownedItemIds = new Set(
          (data.items || [])
            .map((bItem: any) => bItem.item?.id ?? bItem.item_id)
            .filter((id: any) => id !== undefined && id !== null)
            .map((id: any) => String(id))
        );

        this.allAvailableItems = data.all_items || [];
        
        // Inicializar listas para filtros y procesar gráficos por defecto
        this.extractFilterOptions();
        this.updateChartsData();

        this.isLoading = false;
      },
      error: (err) => {
        console.error('❌ Error al cargar la mochila:', err);
        this.isLoading = false;
      }
    });
  }

  extractFilterOptions() {
    if (!this.backpackData) return;
    
    const details = this.backpackData.detailed_history || this.backpackData.raw_history || [];
    const textsSet = new Set<string>();
    const mgSet = new Set<string>();

    details.forEach((row: any) => {
      if (row.book_title || row.text_name) textsSet.add(row.book_title || row.text_name);
      if (row.minigame__name || row.minigame_name) mgSet.add(row.minigame__name || row.minigame_name);
    });

    this.availableTexts = Array.from(textsSet);
    this.availableMinigames = Array.from(mgSet);
  }

  onFilterChange() {
    this.updateChartsData();
  }

  updateChartsData() {
    const rawHistory = this.backpackData?.detailed_history || [];

    // CASO 1: Sin filtros -> Top 3 libros con más desafíos completados
    if (!this.selectedTextFilter && !this.selectedMinigameFilter) {
      const bookMap: { [key: string]: { title: string; won: number; lost: number; total: number } } = {};
      
      rawHistory.forEach((row: any) => {
        const title = row.book_title || 'Desconocido';
        if (!bookMap[title]) bookMap[title] = { title, won: 0, lost: 0, total: 0 };
        
        const isWin = row.result === 'won';
        if (isWin) bookMap[title].won++;
        else bookMap[title].lost++;
        bookMap[title].total++;
      });

      this.topBooksData = Object.values(bookMap)
        .sort((a, b) => b.total - a.total)
        .slice(0, 3);

      this.maxTopBarValue = Math.max(...this.topBooksData.map(b => Math.max(b.won, b.lost)), 1);
    }

    // CASO 2: Filtro por Texto / Libro (Sin juego seleccionado) -> Historial por minijuego
    else if (this.selectedTextFilter && !this.selectedMinigameFilter) {
      const mgMap: { [key: string]: { minigame_name: string; won: number; lost: number } } = {};

      rawHistory
        .filter((row: any) => row.book_title === this.selectedTextFilter)
        .forEach((row: any) => {
          const mgName = row.minigame_name || 'Minijuego';
          if (!mgMap[mgName]) mgMap[mgName] = { minigame_name: mgName, won: 0, lost: 0 };

          if (row.result === 'won') mgMap[mgName].won++;
          else mgMap[mgName].lost++;
        });

      this.textFilteredMinigames = Object.values(mgMap);
      this.maxTextFilteredValue = Math.max(...this.textFilteredMinigames.map(m => Math.max(m.won, m.lost)), 1);
    }

    // CASO 3: Filtro por Minijuego (Sin texto seleccionado) -> Gráficos circulares por libro
    else if (!this.selectedTextFilter && this.selectedMinigameFilter) {
      const bookMap: { [key: string]: { book_title: string; won: number; lost: number } } = {};

      rawHistory
        .filter((row: any) => row.minigame_name === this.selectedMinigameFilter)
        .forEach((row: any) => {
          const bTitle = row.book_title || 'Desconocido';
          if (!bookMap[bTitle]) bookMap[bTitle] = { book_title: bTitle, won: 0, lost: 0 };

          if (row.result === 'won') bookMap[bTitle].won++;
          else bookMap[bTitle].lost++;
        });

      this.minigameFilteredBooks = Object.values(bookMap).map(item => {
        const total = item.won + item.lost;
        const winrate = total > 0 ? Math.round((item.won / total) * 100) : 0;
        return { ...item, winrate };
      });
    }

    // CASO 4: Ambos filtros seleccionados -> Gráfico de barras progresivas cronológicas
    else if (this.selectedTextFilter && this.selectedMinigameFilter) {
      const filtered = rawHistory
        .filter((row: any) => 
          row.book_title === this.selectedTextFilter &&
          row.minigame_name === this.selectedMinigameFilter
        )
        .sort((a: any, b: any) => new Date(a.created_at || 0).getTime() - new Date(b.created_at || 0).getTime());

      let accWins = 0;
      let accLosses = 0;

      this.progressiveHistory = filtered.map((row: any) => {
        const isWin = row.result === 'won';
        if (isWin) accWins++;
        else accLosses++;

        return {
          is_win: isWin,
          accumulated_wins: accWins,
          accumulated_losses: accLosses
        };
      });

      this.maxProgValue = Math.max(...this.progressiveHistory.map(p => Math.max(p.accumulated_wins, p.accumulated_losses)), 1);
    }
  }

  getBarHeight(val: number, max: number): number {
    return Math.min(Math.round((val / max) * 100), 100);
  }

  getProgBarHeight(val: number, max: number): number {
    return Math.min(Math.round((val / max) * 100), 100);
  }

  getPieGradient(won: number, lost: number): string {
    const total = won + lost;
    if (total === 0) return 'conic-gradient(#ccc 0deg 360deg)';
    const wonDeg = (won / total) * 360;
    return `conic-gradient(#2ecc71 0deg ${wonDeg}deg, #e74c3c ${wonDeg}deg 360deg)`;
  }

  isItemOwned(itemId: string): boolean {
    return itemId != null && this.ownedItemIds.has(String(itemId));
  }

  isShopItemOwned(item: any): boolean {
    if (!item) return false;
    return item.is_owned === true || item.owned === true || this.isItemOwned(item.id);
  }

  isPurchasing(itemId: string): boolean {
    return this.purchasingIds.has(String(itemId));
  }

  openShop() {
    this.currentView = 'shop';
    if (!this.backpackData) {
      this.loadBackpackData();
    }
    this.loadShopCatalog();
  }

  loadShopCatalog() {
    this.isLoading = true;
    this.http.get(this.buildUrl('mochila/shop/')).subscribe({
      next: (data: any) => {
        this.shopItems = Array.isArray(data) ? data : (data.results || []);
        this.isLoading = false;
      },
      error: (err) => {
        console.error('❌ Error al cargar la tienda:', err);
        this.isLoading = false;
      }
    });
  }

  buyItem(itemId: string) {
    const id = String(itemId);
    if (this.isItemOwned(id) || this.purchasingIds.has(id)) return;

    this.purchasingIds.add(id);
    this.http.post(this.buildUrl(`mochila/shop/${id}/purchase/`), {}).subscribe({
      next: (res: any) => {
        this.purchasingIds.delete(id);
        alert(res.message || '¡Objeto comprado con éxito!');
        this.loadBackpackData();
        this.loadShopCatalog();
      },
      error: (err) => {
        this.purchasingIds.delete(id);
        alert(err.error?.detail || 'Error al comprar el objeto');
        this.loadBackpackData();
      }
    });
  }

  readonly defaultItemIcon = DEFAULT_ITEM_ICON;

  getItemIcon(iconPath: string | null | undefined): string {
  return resolveItemIcon(iconPath, environment.apiUrl);
}
onImageError(event: Event): void {
  handleItemImageError(event);
}

  close() {
    this.dialogRef.close();
  }
}