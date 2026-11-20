import { Component, OnInit, inject, OnDestroy, ChangeDetectorRef, HostListener, ViewChild, ElementRef } from '@angular/core';
import { Subject } from 'rxjs';
import { debounceTime, takeUntil } from 'rxjs/operators';
import { ApiService } from '../../core/services/api.service';
import { AudioService } from '../../core/services/audio.service';
import { ActivatedRoute, Router } from '@angular/router';
import { DomSanitizer, SafeHtml } from '@angular/platform-browser';
import lottie from 'lottie-web';
import { environment } from '../../../environments/environment';
import { KokoroTtsService } from '../../core/services/kokoro-tts.service';
import { ChatService } from '../../core/services/chat.service';
import { SpeechRecognitionService } from '../../core/services/speech-recognition.service';
import { trigger, state, style, transition, animate } from '@angular/animations';
import { WasmTtsService } from '../../core/services/wasm-tts.service';
import { NativeTtsService } from '../../core/services/native-tts.service';
import { StatusBar } from '@capacitor/status-bar';
import { NavigationBar } from '@hugotomazi/capacitor-navigation-bar';
import { Capacitor } from '@capacitor/core';

export interface ProgressData {
  percentage: number;
  wordId: string;
  timestamp: number;
  scrollPercent?: number;
}

@Component({
  selector: 'app-reader',
  templateUrl: './reader.component.html',
  styleUrl: './reader.component.css',
  animations: [
    trigger('slideFromRight', [
      state('in',  style({ transform: 'translateX(0%)' })),
      state('out', style({ transform: 'translateX(100%)' })),
      transition('in <=> out', animate('350ms ease-in-out')),
    ]),
    trigger('slideFromLeft', [
      state('in',  style({ transform: 'translateX(0%)' })),
      state('out', style({ transform: 'translateX(-100%)' })),
      transition('in <=> out', animate('350ms ease-in-out')),
    ]),
  ]
})
export class ReaderComponent implements OnInit, OnDestroy {
  private api = inject(ApiService);
  public audioService = inject(AudioService);
  private route = inject(ActivatedRoute);
  private router = inject(Router);
  private sanitizer = inject(DomSanitizer);
  private cdr = inject(ChangeDetectorRef);
  public kokoroVoice = inject(KokoroTtsService);
  public chatService = inject(ChatService);
  public speechService = inject(SpeechRecognitionService);
  public wasmVoice = inject(WasmTtsService);
  public nativeTts = inject(NativeTtsService);

  inventoryId: string = '';
  currentPage: number = 1;
  totalPages: number = 1;
  chapters: any[] = [];
  safeChapterHtml: SafeHtml = '';
  chapterTitle: string = 'Cargando libro...';
  bookTitle: string = 'Cargando...';
  bookSlug: string = '';
  hasPremiumNarration: boolean = false;
  progressId: number | null = null;

  fontSize: number = 18;
  currentTheme: 'dark' | 'light' | 'sepia' | 'nocturno' = 'dark';
  currentFontFamily: 'sans' | 'serif' | 'dyslexic' | 'medieval' | 'garamond' | 'georgia' | 'palatino' | 'opensans' | 'helvetica' = 'serif';
  isTocOpen: boolean = false;
  lastScrollTop: number = 0;
  isToolbarHidden: boolean = false;
  hideProgressOnScroll: boolean = false;
  bionicReadingActive: boolean = false;
  tapToScrollActive: boolean = false;
  showSceneImages: boolean = true;

  isCharPanelOpen: boolean = false;
  avatars: any[] = [];
  selectedAvatar: any = null;
  showCharProfile: boolean = false;
  isKokoroProcessing = false;
  engineMode$ = this.kokoroVoice.engineMode$;
  kokoroDownloading$ = this.kokoroVoice.isDownloadingModel$;
  kokoroProgress$ = this.kokoroVoice.downloadProgress$;

  showMinigameSelectorModal: boolean = false;

  // Listado oficial de los 10 minijuegos disponibles
  availableMinigamesList = [
    { code: 'cazador_intrusos', name: '🕵️ Cazador de Intrusos' },
    { code: 'busca_imagen', name: '🔍 Busca en la Imagen' },
    { code: 'comics_desordenados', name: '🧩 Cómics Desordenados' },
    { code: 'completa_dialogo', name: '💬 Completa el Diálogo' },
    { code: 'emoticono_dialogo', name: '🎭 Emoticono y Diálogo' },
    { code: 'encuentra_contradiccion', name: '⚡ Encuentra Contradicción' },
    { code: 'imagen_pixelada', name: '👾 Imagen Pixelada' },
    { code: 'rafaga_vf', name: '⚡ Ráfaga Verdadero/Falso' },
    { code: 'reconstruccion_manuscrito', name: '📜 Reconstruir Manuscrito' },
    { code: 'testigo_ocular', name: '👁️ Testigo Ocular' }
  ];

  toggleKokoroEngine() {
    if (this.kokoroVoice.engineMode$.value === 'local') {
      this.kokoroVoice.setRemoteEngine();
    } else {
      const confirmed = window.confirm('⚠️ Nota: La voz neuronal local descarga un modelo de IA en tu navegador.\n\nSe recomienda tener un equipo con tarjeta gráfica dedicada (GPU) para evitar lentitud. ¿Estás seguro de que deseas continuar y activar el motor local?');
      if (confirmed) {
        this.kokoroVoice.downloadLocalEngine();
      }
    }
  }

  toggleSceneImages() {
    this.showSceneImages = !this.showSceneImages;
    localStorage.setItem('reader-show-images', String(this.showSceneImages));
  }

  setAudioMode(mode: 'native' | 'pro' | 'kokoro' | 'wasm' | 'native-android') {
    if (this.currentAudioMode !== mode) {
      this.stopAudio(true);
      this.currentAudioMode = mode;
    }
  }

  get authorAvatar(): any {
    return this.avatars.find(a => a.is_author) || null;
  }
  get characterAvatars(): any[] {
    return this.avatars.filter(a => !a.is_author);
  }

  isChatOpen: boolean = false;
  chatSession: any = null;
  chatMessages: any[] = [];
  chatInput: string = '';
  isSendingMessage: boolean = false;
  inkBalance: number = 0;

  currentAudioMode: 'native' | 'pro' | 'kokoro' | 'wasm' | 'native-android' = 'native';
  currentWordIndex: number = -1;
  isAudioLoading: boolean = false;
  wasmVoices = [
    { id: 'Xenova/mms-tts-spa', name: 'MMS Español (Meta) - Pesado' }
  ];

  isMobile: boolean = /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent);

  chapterId: string | null = null;
  isAudioPanelOpen: boolean = false;
  currentChapterPlainText: string = '';
  proErrorMessage: string = '';  
  isFullyRendered: boolean = false; 

  readonly PREMIUM_VOICE_INK_COST = 200;  
  isUnlocking: boolean = false;          

  parsedBlocks: Array<{
    tag: string;
    tokens: Array<any>;
    sentences?: Array<{
      idx: number;
      tokens: Array<{
        text: string;
        isWord: boolean;
        isImg: boolean;
        isBr?: boolean;
        idx: number;
        src?: string;
        alt?: string;
        bionicBold?: string;
        bionicNormal?: string;
      }>;
    }>;
  }> = [];
  renderedBlocks: typeof this.parsedBlocks = [];
  titleTokens: any[] = [];
  private totalWordCount: number = 0;

  isCallMode: boolean = false;
  audioLevel: number = 0;
  partialTranscript: string = '';

  private saveProgressSubject = new Subject<number>();
  private destroy$ = new Subject<void>();
  private savedProgressData: ProgressData | null = null;
  
  chapterScrollPercent: number = 0;
  isNearEnd: boolean = false;
  showBookmarkToast: boolean = false;

  showImageModal: boolean = false;
  modalImageSrc: string = '';

  showRestartModal: boolean = false;
  lastAudioWordIndex: number = 0;

  @ViewChild('avatarVideo') avatarVideoElement!: ElementRef<HTMLVideoElement>;
  showVideoAvatar: boolean = false;
  isVideoSpeaking: boolean = false;
  activeTalkingFrame: number = 1;
  activeThinkingFrame: number = 1;
  private talkingInterval: any;
  private thinkingInterval: any;

  aiProvider: string = 'gemini'; 
  aiStatus: 'ok' | 'warning' | 'error' = 'ok';

  isInitialDataLoaded = false;
  isLoadingInitialData = false;
  isOverlayActive = true;

  private wakeLock: any = null;
  private handleVisibilityChange = async () => {
    if (document.visibilityState === 'visible') {
      await this.requestWakeLock();
    }
  };

  private _loadingLottieContainer?: ElementRef;
  @ViewChild('loadingLottie') set loadingLottie(el: ElementRef) {
    if (el && !this._loadingLottieContainer) {
      this._loadingLottieContainer = el;
      lottie.loadAnimation({
        container: el.nativeElement,
        renderer: 'svg',
        loop: true,
        autoplay: true,
        path: 'assets/lottie/right left.json'
      });
    }
  }

  ngOnInit() {
    this.inventoryId = this.route.snapshot.paramMap.get('id') || '';

    this.requestWakeLock();
    document.addEventListener('visibilitychange', this.handleVisibilityChange);

    this.toggleImmersiveMode(true);

    this.saveProgressSubject.pipe(debounceTime(3000)).subscribe(p => this.syncProgressToBackend(p));

    this.loadInitialData();
    this.loadInkBalance();

    const savedFont = localStorage.getItem('reader-font-family');
    const validFonts = ['sans', 'serif', 'dyslexic', 'medieval', 'garamond', 'georgia', 'palatino', 'opensans', 'helvetica'];
    if (savedFont && validFonts.includes(savedFont)) {
      this.currentFontFamily = savedFont as any;
    }

    const savedTheme = localStorage.getItem('reader-theme');
    const validThemes = ['dark', 'light', 'sepia', 'nocturno'];
    if (savedTheme && validThemes.includes(savedTheme)) {
      this.currentTheme = savedTheme as any;
    }

    const savedFontSize = localStorage.getItem('reader-font-size');
    if (savedFontSize) {
      const parsedSize = parseInt(savedFontSize, 10);
      if (!isNaN(parsedSize) && parsedSize >= 12 && parsedSize <= 32) {
        this.fontSize = parsedSize;
      }
    }

    this.applyTheme();
    this.applyFontSize();

    const savedHide = localStorage.getItem('reader-hide-progress');
    if (savedHide !== null) {
      this.hideProgressOnScroll = savedHide === 'true';
    }

    const savedBionic = localStorage.getItem('reader-bionic-reading');
    if (savedBionic !== null) {
      this.bionicReadingActive = savedBionic === 'true';
    }

    const savedShowImages = localStorage.getItem('reader-show-images');
    if (savedShowImages !== null) {
      this.showSceneImages = savedShowImages === 'true';
    }

    this.route.queryParams.pipe(takeUntil(this.destroy$)).subscribe(params => {
      const avatarId = params['chatWith'];
      if (avatarId) {
        const checkAvatars = setInterval(() => {
          if (this.avatars && this.avatars.length > 0) {
            clearInterval(checkAvatars);
            const avatar = this.avatars.find(a => String(a.id) === String(avatarId));
            if (avatar) {
              this.startChat(avatar);
            } else {
              console.warn(`Avatar con ID ${avatarId} no encontrado.`);
            }
          }
        }, 200);
        setTimeout(() => clearInterval(checkAvatars), 10000);
      }
    });

    this.audioService.currentWordIndex$.pipe(takeUntil(this.destroy$)).subscribe(idx => {
      if (this.currentAudioMode === 'native') {
        this.currentWordIndex = idx;
        if (idx !== -1) {
          this.lastAudioWordIndex = idx;
          this.saveAudioPosition();
        }
        this.cdr.detectChanges(); 
        if (idx !== -1) this.scrollWordIntoView(idx);
      }
    });

    this.wasmVoice.currentWordIndex$.pipe(takeUntil(this.destroy$)).subscribe(idx => {
      if (this.currentAudioMode === 'wasm') {
        this.currentWordIndex = idx;
        if (idx !== -1) {
          this.lastAudioWordIndex = idx;
          this.saveAudioPosition();
        }
        this.cdr.detectChanges();
        if (idx !== -1) this.scrollWordIntoView(idx);
      }
    });

    this.speechService.transcript$.pipe(takeUntil(this.destroy$)).subscribe(text => {
      if (text) {
        this.chatInput = text;
        this.sendMessage();
      }
    });

    this.speechService.partialTranscript$.pipe(takeUntil(this.destroy$)).subscribe(text => {
      this.partialTranscript = text;
      this.cdr.detectChanges();
    });

    this.speechService.audioLevel$.pipe(takeUntil(this.destroy$)).subscribe(level => {
      this.audioLevel = level;
      this.cdr.detectChanges();
    });

    this.kokoroVoice.isProcessing$.pipe(takeUntil(this.destroy$)).subscribe(isProc => {
      this.isKokoroProcessing = isProc;
      this.cdr.detectChanges();
    });

    this.kokoroVoice.isSpeaking$.pipe(takeUntil(this.destroy$)).subscribe(isSpeaking => {
      this.isVideoSpeaking = isSpeaking;
      if (isSpeaking) {
        if (!this.talkingInterval) {
          this.talkingInterval = setInterval(() => {
            this.activeTalkingFrame = Math.floor(Math.random() * 3) + 1;
            this.cdr.detectChanges();
          }, 2000); 
        }
      } else {
        if (this.talkingInterval) {
          clearInterval(this.talkingInterval);
          this.talkingInterval = null;
        }
      }
      
      if (this.isCallMode && this.avatarVideoElement?.nativeElement) {
         const video = this.avatarVideoElement.nativeElement;
         if (isSpeaking) {
           video.currentTime = 1;
           video.play();
           video.ontimeupdate = () => {
             if (video.currentTime >= 6) video.currentTime = 1;
           };
         } else {
           video.pause();
           video.currentTime = 0;
           video.ontimeupdate = null;
         }
      }
      this.cdr.detectChanges();
    });

    this.kokoroVoice.currentWordIndex$.pipe(takeUntil(this.destroy$)).subscribe(idx => {
      if (this.currentAudioMode === 'kokoro' && !this.isChatOpen) {
        this.currentWordIndex = idx;
        if (idx !== -1) {
          this.lastAudioWordIndex = idx;
          this.saveAudioPosition();
        }
        this.cdr.detectChanges();
        if (idx !== -1) this.scrollWordIntoView(idx);
      }
    });

    this.nativeTts.currentWordIndex$.pipe(takeUntil(this.destroy$)).subscribe(idx => {
      if (this.currentAudioMode === 'native-android' && !this.isChatOpen) {
        this.currentWordIndex = idx;
        if (idx !== -1) {
          this.lastAudioWordIndex = idx;
          this.saveAudioPosition();
        }
        this.cdr.detectChanges();
        if (idx !== -1) this.scrollWordIntoView(idx);
      }
    });

    this.chatService.inkBalance$.pipe(takeUntil(this.destroy$)).subscribe(balance => {
      this.inkBalance = balance;
      this.cdr.detectChanges();
    });

    this.audioService.chapterEnd$.pipe(takeUntil(this.destroy$)).subscribe(() => {
      this.lastAudioWordIndex = 0;
      this.saveAudioPosition(); 
      if (this.currentPage < this.totalPages) {
        setTimeout(() => {
          this.currentPage++;
          this.parseAndRenderChapter();
          this.saveProgressSubject.next(this.currentPage - 1);
          setTimeout(() => this.playAudio(), 600);
        }, 500);
      }
    });

    window.addEventListener('beforeunload', () => this.saveAudioPosition());
  }

  bookUuid: string = ''; // Nueva propiedad para guardar el UUID real del libro

  loadInitialData() {
    if (this.isInitialDataLoaded || this.isLoadingInitialData) return;
    this.isLoadingInitialData = true;

    this.api.get<any>(`library/inventory/${this.inventoryId}/`).subscribe({
      next: (inventory) => {
        this.isLoadingInitialData = false;
        this.isInitialDataLoaded = true;
        if (inventory && inventory.progress) {
          this.bookTitle = inventory.book_title || inventory.edition?.book?.title || 'Libro';
          this.currentPage = inventory.progress.current_page || 1;
          this.progressId = inventory.progress.id;
          this.bookSlug = inventory.book_slug;

          this.bookUuid = inventory.book_id || inventory.edition?.book?.id || inventory.edition?.book_id || '';
          
          if (inventory.progress.current_cfi) {
            try {
              this.savedProgressData = JSON.parse(inventory.progress.current_cfi);
            } catch (e) {}
          }
        }
        this.loadChapters();
      },
      error: (err) => {
        console.error('Error cargando inventario', err);
        this.router.navigate(['/catalog']);
      }
    });
  }

  ngOnDestroy() {
    this.releaseWakeLock();
    document.removeEventListener('visibilitychange', this.handleVisibilityChange);
    this.audioService.stop();
    this.stopCallMode();
    this.kokoroVoice.stop();
    this.saveAudioPosition();
    this.stopThinkingAnimation();

    this.toggleImmersiveMode(false);
    this.destroy$.next();
    this.destroy$.complete();
  }

  private async requestWakeLock() {
    try {
      if ('wakeLock' in navigator) {
        this.wakeLock = await (navigator as any).wakeLock.request('screen');
        this.wakeLock.addEventListener('release', () => {});
      }
    } catch (err: any) {}
  }

  private releaseWakeLock() {
    if (this.wakeLock !== null) {
      this.wakeLock.release().catch(() => {}).finally(() => {
        this.wakeLock = null;
      });
    }
  }

  onCanvasScroll(event: any) {
    if (!this.isFullyRendered) return; 
    
    const el = event.target;
    const currentScrollTop = el.scrollTop;
    
    if (currentScrollTop > this.lastScrollTop && currentScrollTop > 50) {
      if (!this.isToolbarHidden) {
        this.isToolbarHidden = true;
      }
    } else {
      if (this.isToolbarHidden) {
        this.isToolbarHidden = false;
      }
    }
    this.lastScrollTop = currentScrollTop;

    const scrollHeight = el.scrollHeight - el.clientHeight;
    const scrollPercent = scrollHeight > 0 ? currentScrollTop / scrollHeight : 0;
    
    this.chapterScrollPercent = Math.min(100, Math.max(0, scrollPercent * 100));
    this.isNearEnd = scrollPercent >= 0.98 || (scrollHeight - currentScrollTop) < 50 || scrollHeight <= 50;

    const exactPage = (this.currentPage - 1) + scrollPercent;
    this.saveProgressSubject.next(exactPage);
  }

  checkIfNearEnd() {
    const el = document.querySelector('.reading-canvas');
    if (el) {
      const scrollHeight = el.scrollHeight - el.clientHeight;
      this.isNearEnd = (scrollHeight <= 50) || ((scrollHeight - el.scrollTop) < 50);
    }
  }

  async toggleImmersiveMode(active: boolean) {
    if (Capacitor.isNativePlatform()) {
      try {
        if (active) {
          await StatusBar.setOverlaysWebView({ overlay: true });
          await StatusBar.hide();
          await NavigationBar.hide();
        } else {
          await StatusBar.show();
          await StatusBar.setOverlaysWebView({ overlay: false });
          await NavigationBar.show();
        }
      } catch (err) {}
    }
    
    try {
      if (active && !document.fullscreenElement) {
         await document.documentElement.requestFullscreen();
      } else if (!active && document.fullscreenElement) {
         await document.exitFullscreen();
      }
    } catch (e) { }
  }

  onCanvasClick(event: MouseEvent) {
    const target = event.target as HTMLElement;
    if (target.closest('.word') || target.closest('img') || target.closest('button')) {
      return; 
    }

    if (!this.tapToScrollActive) {
      return;
    }
    
    const el = document.querySelector('.reading-canvas') as HTMLElement;
    if (el) {
      const scrollHeight = el.scrollHeight - el.clientHeight;
      if (el.scrollTop < scrollHeight - 10) {
         const canvasRect = el.getBoundingClientRect();
         const blocks = Array.from(el.querySelectorAll('p, h1, h2, h3, figure'));
         let targetBlock: HTMLElement | null = null;
         
         for (let i = blocks.length - 1; i >= 0; i--) {
           const rect = blocks[i].getBoundingClientRect();
           if (rect.top < canvasRect.bottom - 20) {
             targetBlock = blocks[i] as HTMLElement;
             break;
           }
         }

         let wordsToHighlight: HTMLElement[] = [];
         if (targetBlock) {
             const words = Array.from(targetBlock.querySelectorAll('.word')) as HTMLElement[];
             let lastVisibleWord: HTMLElement | null = null;
             
             for (let i = words.length - 1; i >= 0; i--) {
                 const rect = words[i].getBoundingClientRect();
                 if (rect.bottom < canvasRect.bottom - 10) {
                     lastVisibleWord = words[i];
                     break;
                 }
             }
             
             if (lastVisibleWord) {
                 const lineTop = lastVisibleWord.getBoundingClientRect().top;
                 wordsToHighlight = words.filter(w => Math.abs(w.getBoundingClientRect().top - lineTop) < 15);
             }
         }

         el.scrollBy({ top: el.clientHeight * 0.9, behavior: 'smooth' });

         if (wordsToHighlight.length > 0) {
           el.querySelectorAll('.tap-highlight-fade').forEach(w => w.classList.remove('tap-highlight-fade'));
           wordsToHighlight.forEach(w => w.classList.add('tap-highlight-fade'));
           setTimeout(() => {
             wordsToHighlight.forEach(w => w.classList.remove('tap-highlight-fade'));
           }, 2500);
         }
      }
    }
  }

  changeFontSize(delta: number) {
    this.fontSize = Math.min(Math.max(this.fontSize + delta, 12), 32);
    this.applyFontSize();
    localStorage.setItem('reader-font-size', this.fontSize.toString());
  }

  setFontFamily(font: 'sans' | 'serif' | 'dyslexic' | 'medieval' | 'garamond' | 'georgia' | 'palatino' | 'opensans' | 'helvetica') {
    this.currentFontFamily = font;
    localStorage.setItem('reader-font-family', font);
  }

  setTheme(theme: 'dark' | 'light' | 'sepia' | 'nocturno') {
    this.currentTheme = theme;
    this.applyTheme();
    localStorage.setItem('reader-theme', theme);
  }

  setHideProgress(value: boolean) {
    this.hideProgressOnScroll = value;
    localStorage.setItem('reader-hide-progress', String(value));
  }

  setBionicReading(value: boolean) {
    this.bionicReadingActive = value;
    localStorage.setItem('reader-bionic-reading', String(value));
  }

  isAlphanumeric(c: string): boolean {
    const code = c.charCodeAt(0);
    return (code >= 48 && code <= 57) || 
           (code >= 65 && code <= 90) || 
           (code >= 97 && code <= 122) || 
           code >= 128; 
  }

  getBionicSplit(word: string): { bold: string; normal: string } {
    if (!word) return { bold: '', normal: '' };
    const len = word.length;
    
    let start = 0;
    while (start < len && !this.isAlphanumeric(word[start])) {
      start++;
    }
    
    let end = len - 1;
    while (end >= start && !this.isAlphanumeric(word[end])) {
      end--;
    }
    
    if (start > end) {
      return { bold: word, normal: '' };
    }
    
    const prefix = word.substring(0, start);
    const cleanWord = word.substring(start, end + 1);
    const suffix = word.substring(end + 1);
    
    const cleanLen = cleanWord.length;
    let boldLength = 1;
    if (cleanLen === 1 || cleanLen === 2) {
      boldLength = 1;
    } else if (cleanLen === 3) {
      boldLength = 2;
    } else {
      boldLength = Math.ceil(cleanLen * 0.45);
    }
    
    return {
      bold: prefix + cleanWord.substring(0, boldLength),
      normal: cleanWord.substring(boldLength) + suffix
    };
  }

  private applyFontSize() {
    document.documentElement.style.setProperty('--font-size-reader', `${this.fontSize}px`);
  }

  private applyTheme() {
    document.body.classList.remove('theme-dark', 'theme-light', 'theme-sepia', 'theme-nocturno');
    document.body.classList.add(`theme-${this.currentTheme}`);
  }

  toggleToc() {
    this.isTocOpen = !this.isTocOpen;
    if (this.isTocOpen) this.isCharPanelOpen = false;
  }

  goToChapter(index: number) {
    this.currentPage = index + 1;
    this.renderCurrentChapter();
    this.saveProgressSubject.next(index);
    this.isTocOpen = false;
    this.loadAvatars();
  }

  loadChapters() {
    if (this.chapters && this.chapters.length > 0) return;
    this.api.get(`library/inventory/${this.inventoryId}/chapters/`).subscribe({
      next: (res: any) => {
        if (res && res.chapters && res.chapters.length > 0) {
          this.chapters = res.chapters;
          this.hasPremiumNarration = res.has_premium_narration;
          this.totalPages = res.chapters.length;
          if (this.currentPage > this.totalPages) { this.currentPage = this.totalPages; } else if (this.currentPage < 1) { this.currentPage = 1; }
          this.renderCurrentChapter();
          this.loadAvatars(); 
        } else {
          this.chapterTitle = 'Sin contenido';
          this.safeChapterHtml = this.sanitizer.bypassSecurityTrustHtml('<p>El libro no tiene capítulos procesados.</p>');
        }
      },
      error: (err) => {
        console.error('Error al cargar capítulos', err);
        this.chapterTitle = 'Error';
        if (err.status === 404 || err.status === 401) {
          setTimeout(() => this.router.navigate(['/catalog']), 2000);
        }
        this.safeChapterHtml = this.sanitizer.bypassSecurityTrustHtml('<p>Hubo un error cargando el contenido.</p>');
        this.isOverlayActive = false;
      }
    });
  }

  renderCurrentChapter() {
    setTimeout(() => this.parseAndRenderChapter(), 0);
  }

  isActiveSentence(sentence: any): boolean {
    if (this.currentWordIndex < 0 || !sentence || !sentence.tokens) return false;
    const words = sentence.tokens.filter((t: any) => t.isWord);
    if (words.length === 0) return false;
    const firstIdx = words[0].idx;
    const lastIdx = words[words.length - 1].idx;
    return this.currentWordIndex >= firstIdx && this.currentWordIndex <= lastIdx;
  }

  parseAndRenderChapter() {
    const chapter = this.chapters[this.currentPage - 1];
    if (!chapter) return;

    this.currentWordIndex = this.getSavedAudioWordIndex();
    this.chapterTitle = chapter.title || `Capítulo ${this.currentPage}`;

    const backendUrl = environment.apiUrl.split('/api/v1/')[0];
    const cleanHtml = chapter.content_html.replace(/src=(["'])(\/?)media\//g, `src=$1${backendUrl}/media/`);

    const tempDiv = document.createElement('div');
    tempDiv.innerHTML = cleanHtml;
    this.currentChapterPlainText = tempDiv.textContent || '';

    const parser = new DOMParser();
    const doc = parser.parseFromString(cleanHtml, 'text/html');
    const blocks: typeof this.parsedBlocks = [];
    let wordIdx = 0;

    const tokenizeInline = (node: Node): typeof this.parsedBlocks[0]['tokens'] => {
      const tokens: typeof this.parsedBlocks[0]['tokens'] = [];
      node.childNodes.forEach(child => {
        if (child.nodeType === Node.TEXT_NODE) {
          const parts = (child.textContent || '').split(/(\s+)/);
          parts.forEach(part => {
            if (part.trim().length > 0) {
              const split = this.getBionicSplit(part);
              tokens.push({
                text: part,
                isWord: true,
                isImg: false,
                isBr: false,
                idx: wordIdx++,
                bionicBold: split.bold,
                bionicNormal: split.normal
              });
            } else if (part.length > 0) {
              tokens.push({ text: part, isWord: false, isImg: false, isBr: false, idx: -1 });
            }
          });
        } else if (child.nodeType === Node.ELEMENT_NODE) {
          const el = child as Element;
          const tag = el.tagName.toLowerCase();
          if (tag === 'img') {
            const img = el as HTMLImageElement;
            tokens.push({
              text: '', isWord: false, isImg: true, isBr: false, idx: -1,
              src: img.src || img.getAttribute('src') || '', alt: img.alt || ''
            });
          } else if (tag === 'br') {
            tokens.push({ text: '', isWord: false, isImg: false, isBr: true, idx: -1 });
          } else {
            tokens.push(...tokenizeInline(child));
          }
        }
      });
      return tokens;
    };

    const blockTags = new Set(['p', 'div', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'blockquote', 'li', 'ul', 'ol', 'section', 'article', 'figure']);

    const parseNode = (node: Node) => {
      if (node.nodeType === Node.ELEMENT_NODE) {
        const el = node as Element;
        const tag = el.tagName.toLowerCase();
        
        if (tag === 'img') {
          const img = el as HTMLImageElement;
          blocks.push({
            tag: 'img-block',
            tokens: [{ text: '', isWord: false, isImg: true, idx: -1, src: img.src || img.getAttribute('src') || '', alt: img.alt || '' }]
          });
        } else if (blockTags.has(tag)) {
          let hasBlockChildren = false;
          for (let i = 0; i < el.children.length; i++) {
            if (blockTags.has(el.children[i].tagName.toLowerCase())) {
              hasBlockChildren = true;
              break;
            }
          }

          if (hasBlockChildren) {
            el.childNodes.forEach(child => parseNode(child));
          } else {
            const tokens = tokenizeInline(el);
            if (tokens.length > 0) {
              blocks.push({ tag: tag === 'div' || tag === 'figure' ? 'p' : tag, tokens });
            }
          }
        } else {
          const tokens = tokenizeInline(node);
          if (tokens.length > 0) blocks.push({ tag: 'p', tokens });
        }
      } else if (node.nodeType === Node.TEXT_NODE && node.textContent?.trim()) {
        const tokens = tokenizeInline(node);
        if (tokens.length > 0) blocks.push({ tag: 'p', tokens });
      }
    };

    doc.body.childNodes.forEach(child => parseNode(child));

    // 🛡️ FALLBACK DE SEGURIDAD: Si el parser estricto no genera bloques debido a diferencias en el HTML del libro,
    // convertimos todo el texto plano en un bloque legible para que ningún libro se quede en blanco.
    if (blocks.length === 0 && this.currentChapterPlainText.trim().length > 0) {
      const fallbackTokens = this.currentChapterPlainText.split(/(\s+)/).map(part => {
        if (part.trim().length > 0) {
          const split = this.getBionicSplit(part);
          return {
            text: part,
            isWord: true,
            isImg: false,
            isBr: false,
            idx: wordIdx++,
            bionicBold: split.bold,
            bionicNormal: split.normal
          };
        }
        return { text: part, isWord: false, isImg: false, isBr: false, idx: -1 };
      });

      blocks.push({
        tag: 'p',
        tokens: fallbackTokens,
        sentences: [{
          idx: 0,
          tokens: fallbackTokens
        }]
      });
    }

    let globalSentenceIdx = 0;
    blocks.forEach(block => {
      if (block.tag === 'img-block') return;
      
      const sentences = [];
      let currentTokens = [];
      
      for (let i = 0; i < block.tokens.length; i++) {
        const tok = block.tokens[i];
        currentTokens.push(tok);
        
        if (tok.isWord) {
          if (/[.!?]["'»”)]*$/.test(tok.text)) {
            sentences.push({ idx: globalSentenceIdx++, tokens: currentTokens });
            currentTokens = [];
          }
        } else if (tok.isBr) {
          sentences.push({ idx: globalSentenceIdx++, tokens: currentTokens });
          currentTokens = [];
        }
      }
      
      if (currentTokens.length > 0) {
        sentences.push({ idx: globalSentenceIdx++, tokens: currentTokens });
      }
      
      block.sentences = sentences;
    });

    this.parsedBlocks = blocks;
    this.titleTokens = [];

    if (this.parsedBlocks.length > 0) {
      const firstBlock = this.parsedBlocks[0];
      const titleToCompare = this.chapterTitle.toLowerCase().replace(/\s+/g, ' ').trim();
      
      let accumulatedText = '';
      let splitIndex = -1;

      for (let i = 0; i < firstBlock.tokens.length; i++) {
        accumulatedText += firstBlock.tokens[i].text;
        const normalizedAccumulated = accumulatedText.toLowerCase().replace(/\s+/g, ' ').trim();
        
        if (normalizedAccumulated === titleToCompare) {
          splitIndex = i + 1;
          break;
        }
        if (normalizedAccumulated.length > titleToCompare.length + 5) break;
      }

      if (splitIndex !== -1) {
        // Solo extraemos los tokens del título si NO vacían el bloque entero de contenido
        if (splitIndex < firstBlock.tokens.length) {
          this.titleTokens = firstBlock.tokens.splice(0, splitIndex);
          
          while (firstBlock.tokens.length > 0 && !firstBlock.tokens[0].isWord && !firstBlock.tokens[0].isImg) {
            firstBlock.tokens.shift();
          }
        } else {
          // Si el bloque solo contenía el título, se asigna como título sin alterar el resto
          this.titleTokens = [...firstBlock.tokens];
        }
      }
    }

    this.totalWordCount = wordIdx;
    this.safeChapterHtml = this.sanitizer.bypassSecurityTrustHtml(''); 

    this.chapterScrollPercent = 0;
    this.isNearEnd = false;
    this.lastScrollTop = 0;

    const viewer = document.querySelector('.reading-canvas');
    if (viewer) viewer.scrollTop = 0;

    this.renderedBlocks = [];
    
    let targetBlockIndex = 0;
    let needsFullRender = false;
    
    if (this.savedProgressData) {
      if (this.savedProgressData.wordId) {
        const targetIdx = parseInt(this.savedProgressData.wordId.split('-')[1]);
        if (!isNaN(targetIdx)) {
          targetBlockIndex = this.parsedBlocks.findIndex(b => b.tokens.some((t: any) => t.idx === targetIdx));
        }
      } else if (this.savedProgressData.scrollPercent) {
        needsFullRender = true; 
      }
    } else if (this.currentWordIndex > 0) {
      targetBlockIndex = this.parsedBlocks.findIndex(b => b.tokens.some((t: any) => t.idx === this.currentWordIndex));
    }
    
    if (targetBlockIndex === -1) targetBlockIndex = 0;
    let lottieDismissed = false;

    const renderChunks = (startIndex: number) => {
      const chunkSize = (startIndex <= targetBlockIndex || needsFullRender) ? 50 : 15;
      const chunk = this.parsedBlocks.slice(startIndex, startIndex + chunkSize);
      
      if (chunk.length > 0) {
        this.renderedBlocks = [...this.renderedBlocks, ...chunk];
        this.cdr.detectChanges();
        
        const nextIndex = startIndex + chunkSize;
        const reachedTarget = needsFullRender ? (nextIndex >= this.parsedBlocks.length) : (nextIndex > targetBlockIndex);
        
        if (reachedTarget && !lottieDismissed) {
          lottieDismissed = true;
          setTimeout(() => {
            if (this.savedProgressData) {
              if (this.savedProgressData.wordId) {
                const idx = parseInt(this.savedProgressData.wordId.split('-')[1]);
                if (!isNaN(idx)) this.scrollWordIntoView(idx, true);
              } else if (this.savedProgressData.scrollPercent && viewer) {
                viewer.scrollTop = this.savedProgressData.scrollPercent * (viewer.scrollHeight - viewer.clientHeight);
              }
              this.savedProgressData = null;
            } else if (this.currentWordIndex > 0) {
              this.scrollWordIntoView(this.currentWordIndex, true);
            }
            
            this.isOverlayActive = false;
            this.checkIfNearEnd();
            this.cdr.detectChanges();
          }, 50);
        }
        
        if (nextIndex < this.parsedBlocks.length) {
          setTimeout(() => renderChunks(nextIndex), 16);
        } else {
          this.isFullyRendered = true;
        }
      } else {
        if (!lottieDismissed) {
          lottieDismissed = true;
          this.isOverlayActive = false;
          this.checkIfNearEnd();
          this.cdr.detectChanges();
        }
        this.isFullyRendered = true;
      }
    };
    
    this.isFullyRendered = false; 
    renderChunks(0);
  }

  processContentForAudio(html: string): string {
    const parser = new DOMParser();
    const doc = parser.parseFromString(html, 'text/html');
    let wordCount = 0;

    const traverse = (node: Node) => {
      if (node.nodeType === Node.TEXT_NODE) {
        const text = node.textContent || '';
        const words = text.split(/(\s+)/); 
        const fragment = document.createDocumentFragment();

        words.forEach(w => {
          if (w.trim().length > 0) {
            const span = document.createElement('span');
            span.className = 'word';
            span.id = `word-${wordCount}`;
            span.textContent = w;
            fragment.appendChild(span);
            wordCount++;
          } else {
            fragment.appendChild(document.createTextNode(w));
          }
        });

        node.parentNode?.replaceChild(fragment, node);
      } else {
        node.childNodes.forEach(child => traverse(child));
      }
    };

    traverse(doc.body);
    return doc.body.innerHTML;
  }

  toggleAudioPanel() {
    this.isAudioPanelOpen = !this.isAudioPanelOpen;
  }

  toggleTapToScroll() {
    this.tapToScrollActive = !this.tapToScrollActive;
  }

  isFullscreenActive: boolean = false;

  toggleImmersiveButton() {
    this.isFullscreenActive = !this.isFullscreenActive;
    this.toggleImmersiveMode(this.isFullscreenActive);
  }

  purchaseNarration() {
    if (this.isUnlocking || !this.bookSlug) return;
    
    if (this.inkBalance < this.PREMIUM_VOICE_INK_COST) {
      alert(`No tienes tinta suficiente. Necesitas ${this.PREMIUM_VOICE_INK_COST} Ink.`);
      return;
    }

    this.isUnlocking = true;
    this.api.post(`catalog/books/${this.bookSlug}/purchase_narration/`, {}).subscribe({
      next: (res: any) => {
        this.isUnlocking = false;
        this.hasPremiumNarration = true;
        this.inkBalance = res.ink_balance;
        alert('¡Narración premium desbloqueada para todo el libro!');
      },
      error: (err) => {
        this.isUnlocking = false;
        console.error('Error al comprar narración', err);
        alert(err.error?.message || 'Error al procesar la compra.');
      }
    });
  }

  getFirstVisibleWordIndex(): number {
    const words = document.querySelectorAll('.word');
    for (let i = 0; i < words.length; i++) {
      const w = words[i];
      const rect = w.getBoundingClientRect();
      if (rect.top >= 80 && rect.top <= window.innerHeight) {
        const idStr = w.getAttribute('id');
        if (idStr) {
          return parseInt(idStr.replace('word-', ''), 10);
        }
      }
    }
    return -1;
  }

  resumeAudio() {
    this.isAudioPanelOpen = false;
    const savedWordEl = document.getElementById(`word-${this.lastAudioWordIndex}`);
    if (savedWordEl) {
      const savedRect = savedWordEl.getBoundingClientRect();
      if (savedRect.bottom <= 80 || savedRect.top >= window.innerHeight) {
        this.stopAudio(true);
        setTimeout(() => this.playAudio(), 100);
        return;
      }
    }

    if (this.currentAudioMode === 'kokoro') {
      this.kokoroVoice.resume();
    } else if (this.currentAudioMode === 'native-android') {
      const startWord = this.lastAudioWordIndex >= 0 ? this.lastAudioWordIndex : 0;
      this.nativeTts.speak(this.currentChapterPlainText, startWord);
    } else {
      this.audioService.resume();
    }
  }

  playAudio() {
    this.isAudioPanelOpen = false;
    this.stopAudio(true); 
    this.proErrorMessage = ''; 
    const chapter = this.chapters[this.currentPage - 1];

    const savedWordEl = document.getElementById(`word-${this.lastAudioWordIndex}`);
    if (savedWordEl) {
      const savedRect = savedWordEl.getBoundingClientRect();
      if (savedRect.bottom <= 80 || savedRect.top >= window.innerHeight) {
        const visibleIdx = this.getFirstVisibleWordIndex();
        if (visibleIdx !== -1) {
          this.lastAudioWordIndex = visibleIdx;
          this.currentWordIndex = visibleIdx;
        }
      }
    } else {
       const visibleIdx = this.getFirstVisibleWordIndex();
       if (visibleIdx !== -1) {
         this.lastAudioWordIndex = visibleIdx;
         this.currentWordIndex = visibleIdx;
       }
    }

    const startWord = this.lastAudioWordIndex >= 0 ? this.lastAudioWordIndex : 0;

    if (this.currentAudioMode === 'native') {
      this.audioService.playNative(this.currentChapterPlainText, startWord);
    } else if (this.currentAudioMode === 'wasm') {
      this.audioService.playWasm(this.currentChapterPlainText);
    } else if (this.currentAudioMode === 'kokoro') {
      this.kokoroVoice.speak(this.currentChapterPlainText, this.authorAvatar?.id || 1, startWord);
    } else if (this.currentAudioMode === 'native-android') {
      this.nativeTts.speak(this.currentChapterPlainText, startWord);
    } else {
      if (!this.hasPremiumNarration) {
        this.proErrorMessage = '🔒 Debes desbloquear "Otras opciones" para escuchar la voz grabada.';
        this.currentAudioMode = 'native';
        return;
      }

      this.isAudioLoading = true;
      
      if (chapter && chapter.audios && chapter.audios.length > 0) {
        const audio = chapter.audios[0];
        this.audioService.playRecorded(audio.audio_url, audio.alignment_data).subscribe({
          next: () => this.isAudioLoading = false,
          error: (err) => {
            this.isAudioLoading = false;
            this.proErrorMessage = 'Error al reproducir el audio de la base de datos.';
          }
        });
        return;
      }

      const backendUrl = environment.apiUrl.split('/api/v1/')[0];
      const chapterOrder = chapter?.order ?? this.currentPage;
      const capNumStr = chapterOrder.toString().padStart(2, '0');
      let fallbackAudioUrl = '';

      if (this.bookSlug === 'el-extrano-caso-del-dr-jekyll-y-mr-hyde' || this.bookSlug?.includes('jekyll')) {
        fallbackAudioUrl = `${backendUrl}/media/audio_narrations/El_extraño_caso/Capitulo_${capNumStr}.mp3`;
      } else if (this.bookSlug === 'el-principe-feliz' || this.bookSlug?.includes('principe')) {
        fallbackAudioUrl = `${backendUrl}/media/audio_narrations/Principe_Feliz/Capitulo_${capNumStr}.mp3`;
      } else if (this.bookSlug === 'el-principito' || this.bookSlug?.includes('principito')) {
        fallbackAudioUrl = `${backendUrl}/media/audio_narrations/principito/Capitulo_${capNumStr}.mp3`;
      }

      if (fallbackAudioUrl) {
        this.audioService.playRecorded(fallbackAudioUrl).subscribe({
          next: () => {
            this.isAudioLoading = false;
            this.currentWordIndex = -1;
          },
          error: (err) => {
            this.isAudioLoading = false;
            this.proErrorMessage = '🔒 Audio no encontrado para este capítulo.';
            this.currentAudioMode = 'native';
          }
        });
      } else {
        this.isAudioLoading = false;
        this.proErrorMessage = '🔒 La voz grabada no está disponible para este libro aún.';
        this.currentAudioMode = 'native';
      }
    }
  }

  stopAudio(preventScroll: boolean = false) {
    this.audioService.stop();
    this.kokoroVoice.stop();
    this.nativeTts.stop();
    this.currentWordIndex = -1;

    if (!preventScroll) {
      const canvas = document.querySelector('.reading-canvas');
      if (canvas) {
        canvas.scrollTo({ top: 0, behavior: 'smooth' });
      }
    }
  }

  onWordClick(wordIdx: number) {
    if (this.tapToScrollActive) return;

    if (this.currentAudioMode === 'pro') {
      this.audioService.seekToWord(wordIdx, this.currentChapterPlainText);
    }
    this.currentWordIndex = wordIdx;
  }

  getSavedAudioWordIndex(): number {
    if (!this.inventoryId) return 0;
    try {
      const saved = localStorage.getItem(`audio_pos_${this.inventoryId}`);
      if (saved) {
        const data = JSON.parse(saved);
        if (data.page === this.currentPage && typeof data.wordIndex === 'number' && data.wordIndex >= 0) {
          this.lastAudioWordIndex = data.wordIndex;
          return data.wordIndex;
        }
      }
    } catch (e) {}
    this.lastAudioWordIndex = 0;
    return 0;
  }

  confirmRestartAudio() {
    this.showRestartModal = true;
  }

  closeRestartModal() {
    this.showRestartModal = false;
  }

  toggleAudioFromFab() {
    if (this.currentAudioMode === 'kokoro') {
      if (this.kokoroVoice.isSpeaking$.value) {
        this.kokoroVoice.stop();
        this.isAudioPanelOpen = true;
      } else {
        this.playAudio();
      }
    } else if (this.currentAudioMode === 'native-android') {
      if (this.nativeTts.isSpeaking$.value) {
        this.nativeTts.stop();
        this.isAudioPanelOpen = true;
      } else {
        this.playAudio();
      }
    } else {
      if (this.audioService.isPlaying) {
        this.audioService.pause();
        this.isAudioPanelOpen = true;
      } else if (this.audioService.isPaused) {
        this.resumeAudio();
      } else {
        this.playAudio();
      }
    }
  }

  stopAudioFromFab() {
    this.stopAudio();
    this.isAudioPanelOpen = true;
  }

  restartAudio() {
    this.showRestartModal = false;
    this.stopAudio();
    this.currentWordIndex = 0;
    this.lastAudioWordIndex = 0;
    this.saveAudioPosition();
    setTimeout(() => {
      this.playAudio();
    }, 100);
  }

  private saveAudioPosition() {
    if (this.inventoryId) {
      localStorage.setItem(`audio_pos_${this.inventoryId}`, JSON.stringify({
        page: this.currentPage,
        wordIndex: this.lastAudioWordIndex
      }));
    }
  }

  private scrollWordIntoView(idx: number, highlightBookmark: boolean = false) {
    const el = document.getElementById(`word-${idx}`);
    if (el) {
      const rect = el.getBoundingClientRect();
      const safeTop = window.innerHeight * 0.2;
      const safeBottom = window.innerHeight * 0.8;
      
      if (rect.top < safeTop || rect.bottom > safeBottom) {
        el.scrollIntoView({ behavior: 'smooth', block: 'center', inline: 'nearest' });
      }
    }
  }

  private highlightWord(index: number) {
    if (this.currentWordIndex !== -1) {
      const prevWord = document.getElementById(`word-${this.currentWordIndex}`);
      if (prevWord) prevWord.classList.remove('active-word', 'kokoro-active');
    }

    if (index !== -1) {
      const currentWord = document.getElementById(`word-${index}`);
      if (currentWord) {
        if (this.currentAudioMode === 'kokoro') {
          currentWord.classList.add('kokoro-active');
        } else {
          currentWord.classList.add('active-word');
        }
        currentWord.scrollIntoView({ behavior: 'smooth', block: 'center', inline: 'nearest' });
      }
    }
  }

  nextPage() {
    if (this.currentPage < this.totalPages) {
      this.currentPage++;
      this.renderCurrentChapter();
      this.saveProgressSubject.next(this.currentPage - 1);
      this.loadAvatars();
    }
  }

  previousPage() {
    if (this.currentPage > 1) {
      this.currentPage--;
      this.renderCurrentChapter();
      this.saveProgressSubject.next(this.currentPage - 1);
      this.loadAvatars();
    }
  }

  /**
   * Método que lanza la sesión de minijuegos al llegar al final del libro
   */
  launchMinigameSession() {
    const targetId = this.bookUuid; // Usamos el UUID real del libro que coincide con la BD
    if (!targetId) {
      console.error('No se encontró el UUID del libro para iniciar los minijuegos.');
      return;
    }
    this.router.navigate(['/games/session', targetId]);
  }

  toggleCharPanel() {
    this.isCharPanelOpen = !this.isCharPanelOpen;
    if (this.isCharPanelOpen) {
      this.isTocOpen = false;
      if (this.avatars.length === 0) this.loadAvatars();
    }
    if (!this.isCharPanelOpen) {
      this.showCharProfile = false;
      if (this.isChatOpen) {
        this.isChatOpen = false;
        this.stopCallMode();
      }
    }
  }

  loadAvatars() {
    this.api.get(`ai/avatars/?inventory_id=${this.inventoryId}`).subscribe({
      next: (res: any) => { this.avatars = res; },
      error: (err) => console.warn('No hay personajes para este libro:', err)
    });
  }

  openCharProfile(avatar: any) {
    this.selectedAvatar = avatar;
    this.showCharProfile = true;
    this.isChatOpen = false;
  }

  closeCharProfile() {
    this.showCharProfile = false;
    this.selectedAvatar = null;
  }

  toggleVideoAvatar() {
    this.showVideoAvatar = !this.showVideoAvatar;
    setTimeout(() => this.scrollChatToBottom(), 150);
  }

  startChat(avatar: any) {
    if (!avatar.is_unlocked) return;
    this.selectedAvatar = avatar;
    this.showCharProfile = false;

    this.api.get(`ai/sessions/?avatar_id=${avatar.id}`).subscribe({
      next: (session: any) => {
        this.chatSession = session;
        this.loadChatHistory(session.id);
        this.isChatOpen = true;
        this.isCharPanelOpen = true; 
        this.showVideoAvatar = false; 
        setTimeout(() => this.scrollChatToBottom(), 200);
      },
      error: (err) => console.error('Error iniciando sesión de chat', err)
    });
  }

  loadChatHistory(sessionId: number) {
    this.api.get(`ai/sessions/${sessionId}/messages/`).subscribe({
      next: (msgs: any) => { 
        this.chatMessages = msgs; 
        setTimeout(() => this.scrollChatToBottom(), 150);
      },
      error: (err) => console.error('Error cargando historial', err)
    });
  }

  sendMessage() {
    if (!this.chatInput.trim() || this.isSendingMessage || !this.chatSession) return;
    if (this.inkBalance <= 0) return;

    const content = this.chatInput.trim();
    this.chatInput = '';
    this.isSendingMessage = true;

    this.startThinkingAnimation();

    this.chatMessages.push({
      role: 'user',
      content,
      created_at: new Date().toISOString()
    });

    this.api.post('ai/chat/', {
      session_id: this.chatSession.id,
      message: content
    }).subscribe({
      next: (res: any) => {
        this.chatMessages.push({
          role: 'assistant',
          content: res.reply,
          created_at: res.timestamp
        });
        
        if (res.ink_balance !== undefined) {
          this.inkBalance = res.ink_balance;
          this.chatService.updateInkBalance(res.ink_balance);
        }

        this.aiProvider = res.ai_provider || 'gemini';
        this.aiStatus = res.ai_status || 'ok';
        
        this.isSendingMessage = false;
        this.stopThinkingAnimation();
        setTimeout(() => this.scrollChatToBottom(), 50);

        this.speakChatReply(res.reply);
      },
      error: (err) => {
        console.error('Error en el chat', err);
        this.isSendingMessage = false;
        this.stopThinkingAnimation();
        this.aiStatus = 'error';
        this.chatMessages.pop();
        this.chatInput = content;
      }
    });
  }

  formatMessage(text: string): string {
    if (!text) return '';
    return text.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
  }

  private startThinkingAnimation() {
    if (this.thinkingInterval) return;
    this.activeThinkingFrame = 1;
    this.thinkingInterval = setInterval(() => {
      this.activeThinkingFrame = this.activeThinkingFrame === 1 ? 2 : 1;
      this.cdr.detectChanges();
    }, 2000);
  }

  private stopThinkingAnimation() {
    if (this.thinkingInterval) {
      clearInterval(this.thinkingInterval);
      this.thinkingInterval = null;
    }
    this.activeThinkingFrame = 1;
  }

  get isMuted() {
    return this.kokoroVoice.isMuted$.value;
  }

  toggleMute() {
    this.kokoroVoice.toggleMute();
  }

  playMessageAudio(msg: any) {
    if (!msg || !msg.content) return;
    const wasMuted = this.kokoroVoice.isMuted$.value;
    if (wasMuted) {
      this.kokoroVoice.isMuted$.next(false);
    }
    
    this.speakChatReply(msg.content);
    
    if (wasMuted) {
       setTimeout(() => this.kokoroVoice.isMuted$.next(true), 100);
    }
  }

  stopCallMode() {
    this.isCallMode = false;
    this.speechService.stopListening();
    this.kokoroVoice.stop();
  }

  toggleCallMode() {
    this.isCallMode = !this.isCallMode;
    if (this.isCallMode) {
      this.speechService.startListening();
    } else {
      this.stopCallMode();
      setTimeout(() => this.scrollChatToBottom(), 100);
    }
  }

  closeChat() {
    this.isChatOpen = false;
    this.stopCallMode();
  }

  private scrollChatToBottom() {
    const chatBody = document.querySelector('.chat-messages-area');
    if (chatBody) {
      chatBody.scrollTop = chatBody.scrollHeight;
    }
  }

  private async speakChatReply(text: string) {
    const charName = this.selectedAvatar?.name || 'Unknown';
    const nameLower = charName.toLowerCase();
    
    let voiceId = 'ef_dora'; 
    
    if (nameLower.includes('alcalde') || nameLower.includes('rey') || nameLower.includes('padre') || nameLower.includes('señor')) {
      voiceId = 'em_santa';
    } 
    else if (nameLower.includes('príncipe') || nameLower.includes('principe') || nameLower.includes('autor') || nameLower.includes('joven') || nameLower.includes('niño')) {
      voiceId = 'em_alex'; 
    }

    this.kokoroVoice.speak(text, this.chatSession?.avatar_id || this.authorAvatar?.id || 1, 0, voiceId);
    
    this.kokoroVoice.isSpeaking$.pipe(takeUntil(this.destroy$)).subscribe(speaking => {
      this.isVideoSpeaking = speaking;
      if (speaking) {
        this.activeTalkingFrame = Math.floor(Math.random() * 3) + 1;
        if (this.avatarVideoElement?.nativeElement) {
          const video = this.avatarVideoElement.nativeElement;
          video.currentTime = 1;
          video.play();
          video.ontimeupdate = () => {
            if (video.currentTime >= 6) video.currentTime = 1;
          };
        }
      } else {
        if (this.avatarVideoElement?.nativeElement) {
          this.avatarVideoElement.nativeElement.pause();
          this.avatarVideoElement.nativeElement.currentTime = 0;
        }
      }
      this.cdr.detectChanges();
    });
  }

  private loadInkBalance() {
    this.chatService.loadInitialInk();
  }

  trackByBlock(index: number, block: any): number {
    return index;
  }

  trackByToken(index: number, token: any): number {
    return token.idx >= 0 ? token.idx : -(index + 1);
  }

  showWordMenu: boolean = false;
  wordMenuX: number = 0;
  wordMenuY: number = 0;
  selectedText: string = '';
  isMenuBelow: boolean = false;

  showDictionaryModal: boolean = false;
  dictionaryResult: any = null;
  isDictionaryLoading: boolean = false;

  @HostListener('document:selectionchange', ['$event'])
  onSelectionChange() {
    const selection = window.getSelection();
    if (selection && selection.toString().trim().length > 0) {
      const anchorNode = selection.anchorNode;
      const readingCanvas = document.querySelector('.reading-canvas');
      if (anchorNode && readingCanvas && !readingCanvas.contains(anchorNode)) {
         this.showWordMenu = false;
         return;
      }

      setTimeout(() => {
        if (selection.rangeCount === 0) return;
        const range = selection.getRangeAt(0);
        const rect = range.getBoundingClientRect();
        this.selectedText = selection.toString().trim();
        
        this.wordMenuX = rect.left + (rect.width / 2);
        
        if (rect.top < 80) {
          this.wordMenuY = rect.bottom + 15;
          this.isMenuBelow = true;
        } else {
          this.wordMenuY = rect.top - 15;
          this.isMenuBelow = false;
        }
        
        this.showWordMenu = true;
      }, 50);
    } else {
      this.showWordMenu = false;
      this.selectedText = '';
    }
  }

  askCharacter() {
    if (!this.selectedText || this.characterAvatars.length === 0) {
      alert('No hay texto seleccionado o personajes disponibles.');
      return;
    }
    const defaultAvatar = this.characterAvatars[0];
    this.startChat(defaultAvatar);
    this.chatInput = `¿Qué significa esto en la historia?\n\n"${this.selectedText}"`;
    this.showWordMenu = false;
  }

  saveBookmark() {
    if (!this.selectedText) return;

    const selection = window.getSelection();
    let wordId = '';
    
    if (selection && selection.rangeCount > 0) {
      const node = selection.anchorNode?.parentElement;
      const wordSpan = node?.closest('.word');
      if (wordSpan && wordSpan.id) {
        wordId = wordSpan.id;
      }
    }

    const viewer = document.querySelector('.reading-canvas');
    let exactPage = this.currentPage - 1;
    if (viewer) {
      const scrollHeight = viewer.scrollHeight - viewer.clientHeight;
      const scrollPercent = scrollHeight > 0 ? viewer.scrollTop / scrollHeight : 0;
      exactPage += scrollPercent;
    }

    this.syncProgressToBackend(exactPage, wordId);
    
    this.showBookmarkToast = true;
    setTimeout(() => {
      this.showBookmarkToast = false;
    }, 2500);

    this.showWordMenu = false;
  }

  playAudioFromSelection() {
    if (!this.selectedText) return;
    
    const selection = window.getSelection();
    let wordIdx = -1;
    
    if (selection && selection.rangeCount > 0) {
      const node = selection.anchorNode?.parentElement;
      const wordSpan = node?.closest('.word');
      if (wordSpan && wordSpan.id) {
        wordIdx = parseInt(wordSpan.id.replace('word-', ''), 10);
      }
    }

    this.showWordMenu = false;
    
    if (wordIdx !== -1 && !isNaN(wordIdx)) {
      this.lastAudioWordIndex = wordIdx;
      this.currentWordIndex = wordIdx;
      this.saveAudioPosition();
      this.stopAudio(true);
      
      setTimeout(() => {
        if (!this.isAudioPanelOpen) this.isAudioPanelOpen = true;
        this.playAudio();
      }, 150);
    } else {
      if (!this.isAudioPanelOpen) this.isAudioPanelOpen = true;
      this.playAudio();
    }
  }

  defineWord() {
    if (!this.selectedText) return;
    
    this.showWordMenu = false;
    this.showDictionaryModal = true;
    this.isDictionaryLoading = true;
    this.dictionaryResult = null;

    const wordToSearch = this.selectedText.split(/\s+/)[0].replace(/[^\w\sáéíóúÁÉÍÓÚñÑ]/g, '');

    fetch(`https://api.dictionaryapi.dev/api/v2/entries/es/${encodeURIComponent(wordToSearch.toLowerCase())}`)
      .then(res => {
        if (!res.ok) throw new Error('No encontrado');
        return res.json();
      })
      .then(data => {
        this.dictionaryResult = data[0];
        this.isDictionaryLoading = false;
      })
      .catch(err => {
        this.dictionaryResult = { error: 'No se encontró una definición exacta para esta palabra.' };
        this.isDictionaryLoading = false;
      });
  }

  closeDictionary() {
    this.showDictionaryModal = false;
    this.dictionaryResult = null;
  }

  private syncProgressToBackend(exactPage: number, wordId: string = '') {
    if (!this.progressId || this.totalPages === 0) return;

    const percentage = Math.round((exactPage / this.totalPages) * 100);
    const safePercentage = Math.min(Math.max(percentage, 0), 100); 
    const intPage = Math.min(Math.floor(exactPage) + 1, this.totalPages); 
    
    const scrollPercent = exactPage - Math.floor(exactPage);

    const progressData: ProgressData = {
      percentage: safePercentage,
      wordId: wordId,
      timestamp: Date.now(),
      scrollPercent: scrollPercent
    };

    this.api.patch(`library/progress/${this.progressId}/`, { 
      current_page: intPage,
      completion_percentage: safePercentage,
      current_cfi: JSON.stringify(progressData)
    }).subscribe({
      next: () => console.log(`✅ Progreso guardado: Cap ${intPage} (${safePercentage}%), Palabra: ${wordId}`),
      error: (err) => console.error('Error guardando progreso', err)
    });
  }

  openImageModal(src?: string) {
    if (!src) return;
    this.modalImageSrc = src;
    this.showImageModal = true;
  }

  closeImageModal() {
    this.showImageModal = false;
    this.modalImageSrc = '';
  }

  get isAudioSessionActive(): boolean {
    return this.lastAudioWordIndex >= 0 || this.isKokoroProcessing;
  }

  get showFloatingAudioControl(): boolean {
    return false; 
  }

  getMangaFrameUrl(): string {
    if (!this.selectedAvatar || !this.selectedAvatar.avatar_image_url) {
      return '';
    }
    const url = this.selectedAvatar.avatar_image_url;
    if (!url.includes('manga_assets')) {
      return url; 
    }
    
    let base = url;
    if (base.endsWith('calm.webp') || base.endsWith('calm.png')) {
      base = base.substring(0, base.lastIndexOf('/') + 1);
    } else {
      if (!base.endsWith('/')) base += '/';
    }

    if (this.isSendingMessage) {
      return this.activeThinkingFrame === 1 ? base + 'thinking.webp' : base + 'calm.webp';
    } else if (this.isVideoSpeaking) {
      return base + `talking_${this.activeTalkingFrame}.webp`;
    }
    return base + 'calm.webp'; 
  }

  openMinigameSelector() {
    if (!this.bookUuid) {
      console.error('No se encontró el UUID del libro.');
      return;
    }
    this.showMinigameSelectorModal = true;
  }

  closeMinigameSelector() {
    this.showMinigameSelectorModal = false;
  }

  selectAndLaunchMinigame(gameCode: string) {
    if (!this.bookUuid) return;
    this.showMinigameSelectorModal = false;
    
    // Esto enviará el código exacto a la ruta de la sesión
    this.router.navigate(['/games/session', this.bookUuid], { 
      queryParams: { game: gameCode } 
    });
  }
}