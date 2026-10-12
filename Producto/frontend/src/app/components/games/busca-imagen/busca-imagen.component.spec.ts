import { ComponentFixture, TestBed } from '@angular/core/testing';

import { BuscaImagenComponent } from './busca-imagen.component';

describe('BuscaImagenComponent', () => {
  let component: BuscaImagenComponent;
  let fixture: ComponentFixture<BuscaImagenComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [BuscaImagenComponent]
    })
    .compileComponents();
    
    fixture = TestBed.createComponent(BuscaImagenComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
