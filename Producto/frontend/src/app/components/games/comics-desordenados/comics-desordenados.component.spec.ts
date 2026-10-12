import { ComponentFixture, TestBed } from '@angular/core/testing';

import { ComicsDesordenadosComponent } from './comics-desordenados.component';

describe('ComicsDesordenadosComponent', () => {
  let component: ComicsDesordenadosComponent;
  let fixture: ComponentFixture<ComicsDesordenadosComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [ComicsDesordenadosComponent]
    })
    .compileComponents();
    
    fixture = TestBed.createComponent(ComicsDesordenadosComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
