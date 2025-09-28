// src/app/key-management/key-create/key-create.component.ts

import { Component } from '@angular/core';
import { FormBuilder, FormGroup, Validators, ReactiveFormsModule } from '@angular/forms';
import { Router } from '@angular/router';
import { CommonModule, Location } from '@angular/common';

// Angular Material Modules
import { MatCardModule } from '@angular/material/card';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatSelectModule } from '@angular/material/select';
import { MatButtonModule } from '@angular/material/button';
import { MatSlideToggleModule } from '@angular/material/slide-toggle';
import { MatRadioModule } from '@angular/material/radio';

// Custom Service & Model
import { KeyManagementService, CreateKeyRequest } from '../key-management.service';
import { Key } from '../key.model';
import { NotificationService } from '../../../core/notification.service';

/**
 * Component for creating a new cryptographic key.
 * It provides a form to specify key properties like provider, region, usage, and more.
 */
@Component({
  selector: 'app-key-create',
  standalone: true,
  imports: [
    CommonModule,
    ReactiveFormsModule,
    MatCardModule,
    MatFormFieldModule,
    MatInputModule,
    MatSelectModule,
    MatButtonModule,
    MatSlideToggleModule,
    MatRadioModule
  ],
  templateUrl: './key-create.component.html',
  styleUrls: ['./key-create.component.scss']
})
export class KeyCreateComponent {
  /** The reactive form group for the key creation form. */
  keyForm: FormGroup;
  /** Available cloud providers for key creation. */
  providers: Key['cloud_provider'][] = ['aws', 'azure', 'gcp'];
  /** Available key usage purposes. */
  purposes: Key['usage'][] = ['ENCRYPT_DECRYPT', 'SIGN_VERIFY'];
  /** Available protection levels for the key. */
  protectionLevels: Key['protection_level'][] = ['SOFTWARE', 'HSM'];

  constructor(
    private fb: FormBuilder,
    private keyService: KeyManagementService,
    private router: Router,
    private location: Location,
    private notificationService: NotificationService
  ) {
    // Initialize the form with controls, default values, and validators.
    this.keyForm = this.fb.group({
      description: ['', Validators.required],
      cloud_provider: ['', Validators.required],
      region: ['', Validators.required],
      algorithm: ['AES_256', Validators.required],
      purpose: ['ENCRYPT_DECRYPT', Validators.required],
      protection_level: ['SOFTWARE', Validators.required],
      labels: [''], // Example format: "env:prod, team:backend"
      rotation_enabled: [false],
      rotation_days: [365],
    });
  }

  /**
   * Handles the key creation form submission.
   * Validates the form, constructs the request payload, and calls the key management service.
   */
  createKey() {
    if (this.keyForm.invalid) {
      this.keyForm.markAllAsTouched(); // Mark fields to show validation errors
      // **ADDED**: Notify user that the form is invalid.
      this.notificationService.showError('Please fill out all required fields.');
      return;
    }
    
    const formValue = this.keyForm.value;
    const requestPayload: CreateKeyRequest = {
      ...formValue,
      labels: this.parseLabels(formValue.labels)
    };

    this.keyService.createKey(requestPayload).subscribe({
      next: () => {
        // **ADDED**: Success notification on successful key creation.
        this.notificationService.showSuccess('Key created successfully!');
        this.router.navigate(['/app/key-management']);
      },
      error: (err) => {
        const errorMessage = err.error?.message || 'An unknown error occurred.';
        this.notificationService.showError(`Error creating key: ${errorMessage}`);
      }
    });
  }

  /**
   * Parses a comma-separated string of "key:value" pairs into a record object.
   * @param labelsStr The string containing the labels to parse.
   * @returns A Record<string, string> object representing the labels.
   */
  private parseLabels(labelsStr: string): Record<string, string> {
    if (!labelsStr) return {};
    const labels: Record<string, string> = {};
    labelsStr.split(',').forEach(pair => {
      const [key, value] = pair.split(':');
      if (key && value) {
        labels[key.trim()] = value.trim();
      }
    });
    return labels;
  }
  
  /**
   * Navigates to the previous page in the browser's history.
   */
  goBack(): void {
    this.location.back();
  }
}