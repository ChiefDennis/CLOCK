// Import necessary modules from Angular's core and common libraries
import { Component, OnInit } from '@angular/core';
import { FormBuilder, FormGroup, ReactiveFormsModule, Validators } from '@angular/forms';
import { CommonModule } from '@angular/common';

// Import RxJS operators for handling asynchronous data streams
import { Observable } from 'rxjs';
import { map } from 'rxjs/operators';

// Import the services and models created for this feature
import { KeyManagementService } from '../key-management/key-management.service';
import { Key } from '../key-management/key.model';
import { NotificationService } from '../../core/notification.service';

// Import all the required Angular Material modules for the template
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatSelectModule } from '@angular/material/select';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatRadioModule } from '@angular/material/radio';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';

/**
 * CryptoToolsComponent provides a UI for performing encryption and decryption
 * operations using the available cryptographic keys.
 */
@Component({
  selector: 'app-crypto-tools',
  standalone: true,
  imports: [
    CommonModule, ReactiveFormsModule, MatFormFieldModule, MatInputModule,
    MatSelectModule, MatButtonModule, MatIconModule, MatRadioModule,
    MatProgressSpinnerModule
  ],
  templateUrl: './crypto-tools.component.html',
  styleUrls: ['./crypto-tools.component.scss']
})
export class CryptoToolsComponent implements OnInit {
  // An observable that will hold the list of keys for the dropdown
  keys$!: Observable<Key[]>;
  // The main reactive form for the component
  cryptoForm: FormGroup;
  // A boolean to track the loading state for API calls
  isLoading = false;

  constructor(
    private fb: FormBuilder, // Injected FormBuilder to create the reactive form
    private keyService: KeyManagementService, // Injected service for API calls
    private notificationService: NotificationService // Injected service for showing snackbars
  ) {
    // Initialize the form with its controls, validators, and default values
    this.cryptoForm = this.fb.group({
      key: [null, Validators.required], // Dropdown to select the key
      operation: ['encrypt', Validators.required], // Radio buttons for 'encrypt' or 'decrypt'
      inputText: ['', Validators.required], // Textarea for user input
      outputText: [{ value: '', disabled: true }] // Read-only textarea for the result
    });
  }

  /**
   * On component initialization, fetch the list of keys from the service.
   */
  ngOnInit(): void {
    // This call will use the service's cache if the keys have already been fetched
    this.keys$ = this.keyService.listLocalKeys().pipe(
      // Use the map operator to filter the array of keys
      map(keys => keys.filter(key => key.status === 'Enabled'))
    );
  }

  /**
   * Main function to handle form submission. It checks the selected operation
   * and calls the appropriate service method.
   */
  performOperation(): void {
    // If the form is invalid, mark all fields as touched to show validation errors
    if (this.cryptoForm.invalid) {
      this.cryptoForm.markAllAsTouched();
      return;
    }

    this.isLoading = true;
    const { key, operation, inputText } = this.cryptoForm.value;

    // Delegate to the correct service method based on the selected radio button
    if (operation === 'encrypt') {
      this.keyService.encrypt(key.cloud_provider, key.key_id, inputText).subscribe({
        next: (res) => this.handleSuccess(res.ciphertext, 'Encryption successful!'),
        error: (err) => this.handleError(err)
      });
    } else {
      this.keyService.decrypt(key.cloud_provider, key.key_id, inputText).subscribe({
        next: (res) => this.handleSuccess(res.plaintext, 'Decryption successful!'),
        error: (err) => this.handleError(err)
      });
    }
  }

  /**
   * A private helper method to handle successful API responses.
   * @param resultText The text to display in the output textarea.
   * @param message The message to show in the success snackbar.
   */
  private handleSuccess(resultText: string, message: string): void {
    this.cryptoForm.get('outputText')?.setValue(resultText);
    this.isLoading = false;
    this.notificationService.showSuccess(message);
  }

  /**
   * A private helper method to handle API errors.
   * @param error The error object from the API call.
   */
  private handleError(error: any): void {
    const errorMessage = error.error?.message || 'An unknown error occurred.';
    this.notificationService.showError(errorMessage);
    this.isLoading = false;
  }

  /**
   * Copies the content of the output textarea to the user's clipboard.
   * Includes a fallback method for insecure (non-HTTPS) environments.
   */
  copyToClipboard(): void {
    const outputText = this.cryptoForm.get('outputText')?.value;
    if (!outputText) return;

    // Use the modern Clipboard API if it's available (requires HTTPS or localhost)
    if (navigator.clipboard) {
      navigator.clipboard.writeText(outputText).then(() => {
        this.notificationService.showSuccess('Copied to clipboard!');
      }).catch(err => {
        this.notificationService.showError('Could not copy text.');
      });
    } else {
      // Fallback for insecure contexts (like http://) using the obsolete execCommand
      const textArea = document.createElement('textarea');
      textArea.value = outputText;
      textArea.style.position = 'fixed'; // Prevents scrolling
      textArea.style.left = '-9999px';
      document.body.appendChild(textArea);
      textArea.focus();
      textArea.select();
      try {
        document.execCommand('copy');
        this.notificationService.showSuccess('Copied to clipboard!');
      } catch (err) {
        this.notificationService.showError('Could not copy text.');
      }
      document.body.removeChild(textArea);
    }
  }

  /**
   * Resets the form to its initial state.
   */
  clearForm(): void {
    this.cryptoForm.reset({
      key: null,
      operation: 'encrypt',
      inputText: '',
      outputText: ''
    });
    // The outputText control is disabled, so we explicitly clear its value as well
    this.cryptoForm.get('outputText')?.setValue('');
  }
}