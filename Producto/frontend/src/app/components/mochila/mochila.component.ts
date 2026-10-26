import { Component, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { HttpClient } from '@angular/common/http';
import { MatDialogRef, MatDialogModule } from '@angular/material/dialog';
import { environment } from '../../../environments/environment';

@Component({
  selector: 'app-mochila',
  standalone: true,
  imports: [CommonModule, MatDialogModule],
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
  
  currentView: 'inventory' | 'shop' = 'inventory';
  isLoading: boolean = true;

  ngOnInit() {
    this.loadBackpackData();
  }

  /**
   * Limpia barras duplicadas (ej: "v1//mochila" -> "v1/mochila")
   * preservando el protocolo "http://"
   */
  private buildUrl(path: string): string {
    const rawUrl = `${this.apiUrl}/${path}`;
    return rawUrl.replace(/([^:]\/)\/+/g, '$1');
  }

  loadBackpackData() {
    this.isLoading = true;
    this.http.get(this.buildUrl('mochila/')).subscribe({
      next: (data: any) => {
        this.backpackData = data;
        
        // 1. Extraer los IDs de los objetos que el usuario posee en su inventario
        this.ownedItemIds = new Set(
          data.items?.map((bItem: any) => bItem.item?.id || bItem.item_id) || []
        );

        // 2. Asignar el catálogo completo proveniente de la base de datos
        this.allAvailableItems = data.all_items || [];

        this.isLoading = false;
      },
      error: (err) => {
        console.error('❌ Error al cargar la mochila:', err);
        this.isLoading = false;
      }
    });
  }

  loadAllItemsCatalog() {
    this.http.get(this.buildUrl('mochila/items/')).subscribe({
      next: (items: any) => {
        this.allAvailableItems = items;
        this.isLoading = false;
      },
      error: (err) => {
        console.warn('⚠️ Endpoint /mochila/items/ no encontrado. Usando ítems de la mochila como respaldo.', err);
        
        // Respaldo: Usar los ítems que retornó el endpoint principal de la mochila
        this.allAvailableItems = this.backpackData?.items?.map((bItem: any) => bItem.item) || [];
        this.isLoading = false;
      }
    });
  }

  isItemOwned(itemId: string): boolean {
    return this.ownedItemIds.has(itemId);
  }

  openShop() {
    this.currentView = 'shop';
    this.loadShopCatalog();
  }

  loadShopCatalog() {
    this.isLoading = true;
    this.http.get(this.buildUrl('mochila/shop/')).subscribe({
      next: (data: any) => {
        this.shopItems = data;
        this.isLoading = false;
      },
      error: (err) => {
        console.error('❌ Error al cargar la tienda:', err);
        this.isLoading = false;
      }
    });
  }

  buyItem(itemId: string) {
    this.http.post(this.buildUrl(`mochila/shop/${itemId}/purchase/`), {}).subscribe({
      next: (res: any) => {
        alert(res.message || '¡Objeto comprado con éxito!');
        this.loadBackpackData(); 
        this.loadShopCatalog();  
      },
      error: (err) => {
        alert(err.error?.detail || 'Error al comprar el objeto');
      }
    });
  }

  readonly defaultItemIcon = 'assets/images/default-item.png';

  getItemIcon(iconPath: string | null | undefined): string {
    if (!iconPath) {
      return this.defaultItemIcon;
    }
    const trimmed = iconPath.trim();
    if (trimmed.startsWith('http://') || trimmed.startsWith('https://') || trimmed.startsWith('data:')) {
      return trimmed;
    }

    const backendBase = (environment.apiUrl || 'http://localhost:8000/api/v1')
      .replace(/\/api\/v1\/?$/, '')
      .replace(/\/api\/?$/, '');

    if (trimmed.startsWith('/media/') || trimmed.startsWith('/static/')) {
      return `${backendBase}${trimmed}`;
    }
    if (trimmed.startsWith('media/') || trimmed.startsWith('static/')) {
      return `${backendBase}/${trimmed}`;
    }
    if (trimmed.startsWith('assets/')) {
      return trimmed;
    }
    return `${backendBase}/media/${trimmed}`;
  }

  onImageError(event: Event): void {
    const imgElement = event.target as HTMLImageElement;
    if (imgElement) {
      imgElement.onerror = null;
      imgElement.src = this.defaultItemIcon;
    }
  }

  close() {
    this.dialogRef.close();
  }
}