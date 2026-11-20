import { ComponentFixture, TestBed } from '@angular/core/testing';

import { EncuentraContradiccionComponent } from './encuentra-contradiccion.component';

describe('EncuentraContradiccionComponent', () => {
  let component: EncuentraContradiccionComponent;
  let fixture: ComponentFixture<EncuentraContradiccionComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [EncuentraContradiccionComponent]
    })
    .compileComponents();
    
    fixture = TestBed.createComponent(EncuentraContradiccionComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
