import { Component, Inject } from '@angular/core';
import { CommonModule } from '@angular/common';

import { MAT_DIALOG_DATA, MatDialogModule, MatDialogRef } from '@angular/material/dialog';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';

import { Alarm } from '../../features/alerts/alerts.model';

@Component({
  selector: 'app-alarm-detail-dialog',
  standalone: true,
  imports: [
    CommonModule,
    MatDialogModule,
    MatButtonModule,
    MatIconModule,
  ],
  templateUrl: './alarm-detail-dialog.component.html',
  styleUrls: ['./alarm-detail-dialog.component.scss']
})
export class AlarmDetailDialogComponent {
  // We inject the alarm data passed from the AlertsComponent
  constructor(
    public dialogRef: MatDialogRef<AlarmDetailDialogComponent>,
    @Inject(MAT_DIALOG_DATA) public alarm: Alarm
  ) {}

  /**
   * Closes the dialog and returns a string indicating which action to take.
   * @param action The action to perform ('acknowledge' or 'reactivate')
   */
  performAction(action: 'acknowledge' | 'reactivate'): void {
    this.dialogRef.close(action);
  }

  /**
   * Closes the dialog without performing any action.
   */
  close(): void {
    this.dialogRef.close();
  }
}