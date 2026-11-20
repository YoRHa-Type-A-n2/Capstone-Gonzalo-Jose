import { ComponentFixture, TestBed } from '@angular/core/testing';

import { MinigameSessionComponent } from './minigame-session.component';

describe('MinigameSessionComponent', () => {
  let component: MinigameSessionComponent;
  let fixture: ComponentFixture<MinigameSessionComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [MinigameSessionComponent]
    })
    .compileComponents();
    
    fixture = TestBed.createComponent(MinigameSessionComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
