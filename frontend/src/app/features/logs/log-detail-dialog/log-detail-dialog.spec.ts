import { ComponentFixture, TestBed } from '@angular/core/testing';

import { LogDetailDialogComponent } from './log-detail-dialog';

describe('LogDetailDialog', () => {
  let component: LogDetailDialogComponent;
  let fixture: ComponentFixture<LogDetailDialogComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [LogDetailDialogComponent]
    })
    .compileComponents();

    fixture = TestBed.createComponent(LogDetailDialogComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
