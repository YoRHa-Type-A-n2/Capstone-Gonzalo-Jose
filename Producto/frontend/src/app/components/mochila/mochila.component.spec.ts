import { ComponentFixture, TestBed } from '@angular/core/testing';

import { MochilaComponent } from './mochila.component';

describe('MochilaComponent', () => {
  let component: MochilaComponent;
  let fixture: ComponentFixture<MochilaComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      declarations: [MochilaComponent]
    })
    .compileComponents();
    
    fixture = TestBed.createComponent(MochilaComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
