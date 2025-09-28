import { Injectable } from '@angular/core';
import { MatSnackBar } from '@angular/material/snack-bar';

@Injectable({
  providedIn: 'root'
})
export class NotificationService {

  constructor(private snackBar: MatSnackBar) {}

  /**
   * Shows an error notification in the top-right corner.
   * @param message The error message to display.
   */
  showError(message: string): void {
    this.snackBar.open(message, 'Close', {
      duration: 5000,
      horizontalPosition: 'right',
      verticalPosition: 'top',
      panelClass: ['error-snackbar']
    });
  }

  /**
   * Shows a success notification in the top-right corner.
   * @param message The success message to display.
   */
  showSuccess(message: string): void {
    this.snackBar.open(message, 'OK', {
      duration: 3000, // A shorter duration for success messages
      horizontalPosition: 'right',
      verticalPosition: 'top',
      panelClass: ['success-snackbar'] // A custom class for success styling
    });
  }
}