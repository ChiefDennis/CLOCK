import { Component, Inject } from '@angular/core';
import { MatDialogModule, MatDialogRef, MAT_DIALOG_DATA } from '@angular/material/dialog';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { CommonModule } from '@angular/common';

// Defines the shape of the data that this dialog expects
export interface DeleteKeyDialogData {
  key_id: string;
}

@Component({
  selector: 'app-delete-key-dialog',
  standalone: true,
  imports: [
    CommonModule,
    MatDialogModule,
    MatButtonModule,
    MatIconModule
  ],
  template: `
    <h2 mat-dialog-title>Confirm Schedule Deletion</h2>
    <mat-dialog-content>
      <p>Are you sure you want to schedule key <strong>{{ data.key_id }}</strong> for deletion?</p>
      <p>This action cannot be undone.</p>
    </mat-dialog-content>
    <mat-dialog-actions align="end">
      <button mat-button mat-dialog-close>Cancel</button>
      <button mat-raised-button color="warn" [mat-dialog-close]="true" cdkFocusInitial>
        <mat-icon>delete_forever</mat-icon>
        Schedule Deletion
      </button>
    </mat-dialog-actions>
  `,
})
export class DeleteKeyDialogComponent {
  constructor(
    public dialogRef: MatDialogRef<DeleteKeyDialogComponent>,
    @Inject(MAT_DIALOG_DATA) public data: DeleteKeyDialogData
  ) {}
}