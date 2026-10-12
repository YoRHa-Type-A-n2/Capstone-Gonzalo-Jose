import { ComponentFixture, TestBed } from '@angular/core/testing';

import { CompletaDialogoComponent } from './completa-dialogo.component';

describe('CompletaDialogoComponent', () => {
  let component: CompletaDialogoComponent;
  let fixture: ComponentFixture<CompletaDialogoComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [CompletaDialogoComponent]
    })
    .compileComponents();
    
    fixture = TestBed.createComponent(CompletaDialogoComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
