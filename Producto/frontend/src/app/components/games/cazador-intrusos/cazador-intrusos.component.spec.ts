import { ComponentFixture, TestBed } from '@angular/core/testing';

import { CazadorIntrusosComponent } from './cazador-intrusos.component';

describe('CazadorIntrusosComponent', () => {
  let component: CazadorIntrusosComponent;
  let fixture: ComponentFixture<CazadorIntrusosComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [CazadorIntrusosComponent]
    })
    .compileComponents();
    
    fixture = TestBed.createComponent(CazadorIntrusosComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
