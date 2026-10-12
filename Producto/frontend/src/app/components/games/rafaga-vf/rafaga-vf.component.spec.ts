import { ComponentFixture, TestBed } from '@angular/core/testing';

import { RafagaVfComponent } from './rafaga-vf.component';

describe('RafagaVfComponent', () => {
  let component: RafagaVfComponent;
  let fixture: ComponentFixture<RafagaVfComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [RafagaVfComponent]
    })
    .compileComponents();
    
    fixture = TestBed.createComponent(RafagaVfComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
