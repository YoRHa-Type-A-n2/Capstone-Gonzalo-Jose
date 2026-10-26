import {
  ChangeDetectorRef,
  Component,
  HostListener,
  Input,
  NgZone,
  OnChanges,
  OnDestroy,
  SecurityContext,
  SimpleChanges,
  ViewEncapsulation,
  inject,
} from '@angular/core';
import { CommonModule } from '@angular/common';
import { DomSanitizer } from '@angular/platform-browser';
import { Subscription } from 'rxjs';
import { Capacitor } from '@capacitor/core';
import { environment } from '../../../environments/environment';

import { AlternateStoryService } from './alternate-story.service';
import {
  AlternateEvent,
  AlternateItem,
  AlternateState,
  TriggerGroup,
  UseItemResponse,
} from './alternate-story.models';
import {
  buildAlternateBlocks,
  findTriggerBlock,
  hideStrayBlocks,
  normalize,
  playSwap,
  restoreOriginal,
} from './alternate-story.dom';

/**
 * Capa independiente del reader. Se coloca una vez en reader.component.html:
 *
 *   <app-alternate-story-layer [bookId]="bookUuid"></app-alternate-story-layer>
 *
 * Qué hace:
 *  1. Pide al backend los objetos de la mochila que sirven en este libro.
 *  2. Busca en el DOM del lector el párrafo con la frase de disparo.
 *  3. Cuando ese párrafo cruza la mitad de la pantalla, abre el popup.
 *  4. Si el lector elige un objeto, reemplaza el texto posterior con un desvanecimiento.
 *
 * El texto original nunca se borra: se oculta, y vuelve al reabrir el libro.
 */
@Component({
  selector: 'app-alternate-story-layer',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './alternate-story-layer.component.html',
  styleUrl: './alternate-story-layer.component.scss',
  // Sin encapsulación: el corte y el pill viven dentro del DOM del reader.
  encapsulation: ViewEncapsulation.None,
})
export class AlternateStoryLayerComponent implements OnChanges, OnDestroy {
  @Input() bookId = '';

  private service = inject(AlternateStoryService);
  private sanitizer = inject(DomSanitizer);
  private zone = inject(NgZone);
  private cdr = inject(ChangeDetectorRef);

  // Estado que usa la plantilla
  state: AlternateState = 'idle';
  popupOpen = false;
  popupLeaving = false;
  isUsing = false;
  errorMsg = '';
  activeTitle = '';
  activeGroup: TriggerGroup | null = null;
  appliedGroup: TriggerGroup | null = null;
  selectedItem: AlternateItem | null = null;

  // Estado interno
  private groups: TriggerGroup[] = [];
  private canvas: HTMLElement | null = null;
  private loadedFor = '';
  private sub?: Subscription;
  private pollTimer?: ReturnType<typeof setInterval>;
  private locateTimer?: ReturnType<typeof setTimeout>;
  private mutationObserver?: MutationObserver;
  private intersectionObserver?: IntersectionObserver;
  private wrapper: HTMLElement | null = null;
  private hidden: HTMLElement[] = [];
  private appliedTrigger: HTMLElement | null = null;

  ngOnChanges(changes: SimpleChanges) {
    // bookUuid del reader llega vacío y se llena cuando carga el inventario.
    if (changes['bookId'] && this.bookId && this.bookId !== this.loadedFor) {
      this.load();
    }
  }

  ngOnDestroy() {
    this.teardown();
  }

  @HostListener('document:keydown.escape')
  onEscape() {
    if (this.popupOpen && !this.isUsing) this.cancel();
  }

  // ---------------------------------------------------------------------------
  // Carga y armado del evento
  // ---------------------------------------------------------------------------

  private load() {
    this.loadedFor = this.bookId;
    this.teardown();
    this.sub = this.service.getEvent(this.bookId).subscribe({
      next: res => this.setup(res?.events ?? []),
      // Sin evento (o sin sesión): el reader sigue funcionando igual.
      error: () => undefined,
    });
  }

  private setup(events: AlternateEvent[]) {
    // El backend ya agrupa por (capítulo, frase); aquí solo se unifican frases equivalentes.
    const byKey = new Map<string, TriggerGroup>();
    for (const event of events) {
      const key = normalize(event.trigger_phrase || '');
      if (!key) continue;
      if (!byKey.has(key)) {
        byKey.set(key, { key, chapterIndex: event.chapter_index, items: [], element: null });
      }
      const group = byKey.get(key)!;
      for (const item of event.usable_items ?? []) {
        if (!group.items.some(i => i.id === item.id)) group.items.push(item);
      }
    }
    this.groups = Array.from(byKey.values()).filter(g => g.items.length > 0);
    if (!this.groups.length) return;

    this.state = 'armed';
    this.waitForCanvas();
  }

  /** El canvas puede no existir todavía (el reader lo muestra tras cargar). */
  private waitForCanvas() {
    this.zone.runOutsideAngular(() => {
      const tryAttach = () => {
        const el = document.querySelector<HTMLElement>('.reading-canvas');
        if (!el) return false;
        this.canvas = el;
        this.startObservers();
        return true;
      };
      if (tryAttach()) return;
      this.pollTimer = setInterval(() => {
        if (tryAttach()) clearInterval(this.pollTimer);
      }, 300);
    });
  }

  private startObservers() {
    if (!this.canvas) return;

    // Una franja fina en el centro del canvas: -45% arriba y abajo deja el 10% central.
    this.intersectionObserver = new IntersectionObserver(
      entries => {
        for (const entry of entries) {
          if (!entry.isIntersecting) continue;
          const group = this.groups.find(g => g.element === entry.target);
          if (group && this.state === 'armed' && !this.popupOpen) {
            this.zone.run(() => this.openPopup(group));
            break;
          }
        }
      },
      { root: this.canvas, rootMargin: '-45% 0px -45% 0px', threshold: 0 }
    );

    // El reader pinta el texto por tandas: hay que seguir mirando hasta encontrar la frase.
    this.mutationObserver = new MutationObserver(() => this.scheduleLocate());
    this.mutationObserver.observe(this.canvas, { childList: true, subtree: true });

    this.locate();
  }

  private scheduleLocate() {
    clearTimeout(this.locateTimer);
    this.locateTimer = setTimeout(() => this.locate(), 120);
  }

  private locate() {
    if (!this.canvas) return;

    for (const group of this.groups) {
      // El reader volvió a pintar (cambio de capítulo, etc.) y el bloque ya no existe.
      if (group.element && !group.element.isConnected) {
        this.intersectionObserver?.unobserve(group.element);
        if (this.appliedTrigger === group.element) {
          this.zone.run(() => this.resetApplied());
        }
        group.element = null;
      }
      if (!group.element) {
        const el = findTriggerBlock(this.canvas, group.key);
        if (el) {
          group.element = el;
          this.intersectionObserver?.observe(el);
        }
      }
    }

    // Si ya hay un final alterno aplicado, lo que el reader siga pintando después se oculta.
    if (this.state === 'done' && this.appliedTrigger) {
      hideStrayBlocks(this.canvas, this.appliedTrigger, this.hidden);
    }
  }

  // ---------------------------------------------------------------------------
  // Popup
  // ---------------------------------------------------------------------------

  openPopup(group: TriggerGroup | null) {
    if (!group) return;
    this.activeGroup = group;
    this.selectedItem = null;
    this.errorMsg = '';
    this.popupLeaving = false;
    this.popupOpen = true;
    // Por si el reader quiere pausar el audio sin que haya que editarlo ahora.
    window.dispatchEvent(new CustomEvent('alternate-story:open'));
    this.cdr.markForCheck();
  }

  select(item: AlternateItem) {
    if (this.isUsing) return;
    this.selectedItem = item;
    this.errorMsg = '';
  }

  cancel() {
    this.selectedItem = null;
    this.errorMsg = '';
    this.closePopup();
  }

  private closePopup() {
    this.popupLeaving = true;
    setTimeout(() => {
      this.popupOpen = false;
      this.popupLeaving = false;
      this.cdr.markForCheck();
    }, 220);
  }

  // ---------------------------------------------------------------------------
  // Usar el objeto y cambiar el texto
  // ---------------------------------------------------------------------------

  confirmUse() {
    if (!this.selectedItem || this.isUsing) return;
    this.isUsing = true;
    this.errorMsg = '';
    this.service.useItem(this.bookId, this.selectedItem.id).subscribe({
      next: res => this.zone.run(() => this.applyEnding(res)),
      error: () => {
        this.isUsing = false;
        this.errorMsg = 'No se pudo usar el objeto. Inténtalo de nuevo.';
        this.cdr.markForCheck();
      },
    });
  }

  private applyEnding(res: UseItemResponse) {
    const group = this.activeGroup;
    const canvas = this.canvas;
    const trigger = group?.element;

    if (!group || !canvas || !trigger || !trigger.isConnected) {
      this.isUsing = false;
      this.errorMsg = 'El punto de la historia ya no está en pantalla.';
      return;
    }

    // Angular ya limpia scripts y atributos peligrosos; el backend es la primera defensa.
    const safeHtml = this.sanitizer.sanitize(SecurityContext.HTML, res.alternate_ending) || '';
    const newBlocks = buildAlternateBlocks(safeHtml, canvas, trigger);
    if (!newBlocks.length) {
      this.isUsing = false;
      this.errorMsg = 'Este final no tiene texto.';
      return;
    }

    // Cambiar de objeto estando ya uno aplicado: primero vuelve el texto original.
    if (this.state === 'done') this.silentRestore();

    this.activeTitle = res.title;
    this.state = 'swapping';
    this.closePopup();
    window.dispatchEvent(new CustomEvent('alternate-story:applied', { detail: { title: res.title } }));

    const reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    const useBlur = !reduceMotion && !Capacitor.isNativePlatform();

    this.zone.runOutsideAngular(async () => {
      try {
        await new Promise(resolve => setTimeout(resolve, 260)); // el popup termina de desvanecerse
        const result = await playSwap({ canvas, trigger, newBlocks, reduceMotion, useBlur });
        this.zone.run(() => {
          this.wrapper = result.wrapper;
          this.hidden = result.hidden;
          this.appliedTrigger = trigger;
          this.appliedGroup = group;
          this.state = 'done';
          this.isUsing = false;
          this.cdr.markForCheck();
        });
        this.scheduleLocate();
      } catch (err) {
        console.error('[alternate-story] No se pudo aplicar el final alterno', err);
        this.zone.run(() => {
          this.state = 'armed';
          this.isUsing = false;
          this.cdr.markForCheck();
        });
      }
    });
  }

  /** Vuelve al final original desde el popup. */
  revertToOriginal() {
    if (this.state !== 'done') return;
    restoreOriginal(this.wrapper, this.hidden, this.canvas);
    this.resetApplied();
    this.activeTitle = '';
    this.closePopup();
    window.dispatchEvent(new CustomEvent('alternate-story:reverted'));
  }

  private silentRestore() {
    restoreOriginal(this.wrapper, this.hidden, null);
    this.resetApplied();
  }

  private resetApplied() {
    this.wrapper = null;
    this.hidden = [];
    this.appliedTrigger = null;
    this.appliedGroup = null;
    if (this.state === 'done') this.state = 'armed';
    this.cdr.markForCheck();
  }

  // ---------------------------------------------------------------------------

  private teardown() {
    this.sub?.unsubscribe();
    clearInterval(this.pollTimer);
    clearTimeout(this.locateTimer);
    this.mutationObserver?.disconnect();
    this.intersectionObserver?.disconnect();
    this.mutationObserver = undefined;
    this.intersectionObserver = undefined;
    this.groups = [];
    this.canvas = null;
    this.wrapper = null;
    this.hidden = [];
    this.appliedTrigger = null;
    this.appliedGroup = null;
    this.activeGroup = null;
    this.selectedItem = null;
    this.popupOpen = false;
    this.state = 'idle';
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
}