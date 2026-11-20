import { ComponentFixture, TestBed } from '@angular/core/testing';

import { ImagenPixeladaComponent } from './imagen-pixelada.component';

describe('ImagenPixeladaComponent', () => {
  let component: ImagenPixeladaComponent;
  let fixture: ComponentFixture<ImagenPixeladaComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [ImagenPixeladaComponent]
    })
    .compileComponents();
    
    fixture = TestBed.createComponent(ImagenPixeladaComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
