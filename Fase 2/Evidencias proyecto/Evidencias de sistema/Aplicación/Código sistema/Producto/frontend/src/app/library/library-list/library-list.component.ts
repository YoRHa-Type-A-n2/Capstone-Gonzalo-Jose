import { Component, OnInit, inject, ElementRef, ViewChild } from '@angular/core';
import { ApiService } from '../../core/services/api.service';
import lottie from 'lottie-web';

@Component({
  selector: 'app-library-list',
  templateUrl: './library-list.component.html',
  styleUrls: ['./library-list.component.css']
})
export class LibraryListComponent implements OnInit {
  private api = inject(ApiService);

  inventoryItems: any[] = [];
  isLoading = true;
  errorMsg = '';

  // 👈 Nuevas variables para controlar la paginación
  currentPage = 1;
  totalPages = 1;
  hasNext = false;
  hasPrev = false;
  totalItems = 0;
  pageSize = 50;

  private _libritoContainer?: ElementRef;
  @ViewChild('libritoContainer') set libritoContainer(el: ElementRef) {
    if (el && !this._libritoContainer) {
      this._libritoContainer = el;
      lottie.loadAnimation({
        container: el.nativeElement,
        renderer: 'svg',
        loop: true,
        autoplay: true,
        path: 'assets/lottie/librito.json'
      });
    }
  }

  ngOnInit(): void {
    this.fetchInventory(1); // 👈 Cargar la página 1 al iniciar
  }

  // 👈 Modificar para aceptar el número de página como parámetro
  fetchInventory(page: number = 1): void {
    this.isLoading = true;
    this.api.get<any>(`library/inventory/?page=${page}`).subscribe({
      next: (res: any) => {
        // Manejar respuesta paginada de Django REST Framework
        if (res.results) {
          this.inventoryItems = res.results;
          this.totalItems = res.count;
          this.hasNext = !!res.next;
          this.hasPrev = !!res.previous;
          this.currentPage = page;
          this.totalPages = Math.ceil(this.totalItems / this.pageSize) || 1;
        } else {
          // Fallback por si la paginación estuviera desactivada temporalmente
          this.inventoryItems = Array.isArray(res) ? res : [];
        }
        this.isLoading = false;
      },
      error: (err) => {
        console.error(err);
        this.errorMsg = 'No pudimos cargar tu biblioteca. Intenta de nuevo más tarde.';
        this.isLoading = false;
      }
    });
  }

  // 👈 Métodos para los botones de control
  nextPage(): void {
    if (this.hasNext) {
      this.fetchInventory(this.currentPage + 1);
    }
  }

  prevPage(): void {
    if (this.hasPrev) {
      this.fetchInventory(this.currentPage - 1);
    }
  }
}