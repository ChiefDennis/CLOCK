import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { MatDialog } from '@angular/material/dialog';
import { ReportsService } from './reports.service';
import { NotificationService } from '../../core/notification.service';
import { CbomViewDialogComponent } from '../../dialogs/cbom-view-dialog/cbom-view-dialog.component';

// Angular Material Modules
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { MatDividerModule } from '@angular/material/divider';

@Component({
  selector: 'app-reports',
  standalone: true,
  imports: [
    CommonModule, MatButtonModule, MatIconModule, MatProgressSpinnerModule, MatDividerModule
  ],
  templateUrl: './reports.component.html',
  styleUrls: ['./reports.component.scss']
})
export class ReportsComponent {
  cbomData: any | null = null;
  isLoading = false;

  constructor(
    private reportsService: ReportsService,
    private notificationService: NotificationService,
    private dialog: MatDialog
  ) {}

  generateCbom(): void {
    this.isLoading = true;
    this.cbomData = null; // Clear previous data
    this.reportsService.getCbom().subscribe({
      next: (data) => {
        this.cbomData = data;
        this.isLoading = false;
        this.notificationService.showSuccess('CBOM report generated successfully.');
      },
      error: (err) => {
        this.notificationService.showError(`Failed to generate report: ${err.error?.message || 'Unknown error'}`);
        this.isLoading = false;
      }
    });
  }

  viewFullCbom(): void {
    if (!this.cbomData) return;
    this.dialog.open(CbomViewDialogComponent, {
      width: '80vw',
      maxWidth: '900px',
      data: this.cbomData
    });
  }

  downloadCbom(): void {
    if (!this.cbomData) return;
    
    // Create a JSON string with pretty printing (2-space indentation)
    const jsonString = JSON.stringify(this.cbomData, null, 2);
    const blob = new Blob([jsonString], { type: 'application/json' });
    
    // Create a temporary link to trigger the download
    const link = document.createElement('a');
    link.href = URL.createObjectURL(blob);
    link.download = `cbom-report-${new Date().toISOString()}.json`;
    link.click();
    
    // Clean up the temporary link
    URL.revokeObjectURL(link.href);
  }
}