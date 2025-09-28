import { Component, Inject, OnInit } from '@angular/core';
import {
  MatDialogModule,
  MatDialogRef,
  MAT_DIALOG_DATA,
} from '@angular/material/dialog';
import { MatButtonModule } from '@angular/material/button';

@Component({
  selector: 'app-log-detail-dialog',
  standalone: true,
  imports: [MatDialogModule, MatButtonModule],
  templateUrl: './log-detail-dialog.html',
  styleUrls: ['./log-detail-dialog.scss'],
})
export class LogDetailDialogComponent implements OnInit {
  public formattedData: string;

  constructor(
    public dialogRef: MatDialogRef<LogDetailDialogComponent>,
    @Inject(MAT_DIALOG_DATA) public data: string
  ) {
    // Initialize with the raw data as a fallback
    this.formattedData = data;
  }

  ngOnInit(): void {
    try {
      // If the data is an empty string or not valid JSON, this will fail
      const jsonData = JSON.parse(this.data);
      // Re-stringify the parsed object with an indent of 2 spaces
      this.formattedData = JSON.stringify(jsonData, null, 2);
    } catch (error) {
      // If parsing fails, just display the original data.
      // No action needed, as we already set it as the default.
      console.warn('Data passed to dialog is not valid JSON:', this.data);
    }
  }

  onClose(): void {
    this.dialogRef.close();
  }
}