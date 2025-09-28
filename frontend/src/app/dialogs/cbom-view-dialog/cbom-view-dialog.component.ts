import { Component, Inject } from '@angular/core';
import { CommonModule, JsonPipe } from '@angular/common';
import { MatDialogModule, MatDialogRef, MAT_DIALOG_DATA } from '@angular/material/dialog';
import { MatButtonModule } from '@angular/material/button';

@Component({
  selector: 'app-cbom-view-dialog',
  standalone: true,
  imports: [CommonModule, MatDialogModule, MatButtonModule, JsonPipe],
  template: `
    <h2 mat-dialog-title>Full CBOM Report</h2>
    <mat-dialog-content class="cbom-content">
      <pre><code>{{ data | json }}</code></pre>
    </mat-dialog-content>
    <mat-dialog-actions align="end">
      <button mat-button mat-dialog-close cdkFocusInitial>Close</button>
    </mat-dialog-actions>
  `,
  styles: [`
    .cbom-content {
      background-color: var(--mat-sys-surface-container-highest);
      border-radius: 8px;
      padding: 1rem;
    }
    pre {
      margin: 0;
    }
  `]
})
export class CbomViewDialogComponent {
  constructor(
    public dialogRef: MatDialogRef<CbomViewDialogComponent>,
    @Inject(MAT_DIALOG_DATA) public data: any
  ) {}
}