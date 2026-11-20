import { ComponentFixture, TestBed } from '@angular/core/testing';

import { EmoticonoDialogoComponent } from './emoticono-dialogo.component';

describe('EmoticonoDialogoComponent', () => {
  let component: EmoticonoDialogoComponent;
  let fixture: ComponentFixture<EmoticonoDialogoComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [EmoticonoDialogoComponent]
    })
    .compileComponents();
    
    fixture = TestBed.createComponent(EmoticonoDialogoComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
