import { ComponentFixture, TestBed } from '@angular/core/testing';

import { ReconstruccionManuscritoComponent } from './reconstruccion-manuscrito.component';

describe('ReconstruccionManuscritoComponent', () => {
  let component: ReconstruccionManuscritoComponent;
  let fixture: ComponentFixture<ReconstruccionManuscritoComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [ReconstruccionManuscritoComponent]
    })
    .compileComponents();
    
    fixture = TestBed.createComponent(ReconstruccionManuscritoComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
