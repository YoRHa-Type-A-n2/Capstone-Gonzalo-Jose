import { ComponentFixture, TestBed } from '@angular/core/testing';

import { TestigoOcularComponent } from './testigo-ocular.component';

describe('TestigoOcularComponent', () => {
  let component: TestigoOcularComponent;
  let fixture: ComponentFixture<TestigoOcularComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [TestigoOcularComponent]
    })
    .compileComponents();
    
    fixture = TestBed.createComponent(TestigoOcularComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
