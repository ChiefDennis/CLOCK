import { Component, OnInit, TemplateRef, ViewChild } from '@angular/core';
import { ActivatedRoute, Router } from '@angular/router';
import { CommonModule, Location } from '@angular/common';
import { FormBuilder, FormGroup, FormsModule, ReactiveFormsModule, Validators } from '@angular/forms';
import { Observable, forkJoin, of } from 'rxjs';
import { tap } from 'rxjs/operators';
import { MatDialog, MatDialogModule } from '@angular/material/dialog';
import { MatCardModule } from '@angular/material/card';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { MatSlideToggleModule } from '@angular/material/slide-toggle';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatDividerModule } from '@angular/material/divider';
import { KeyManagementService } from '../key-management.service';
import { Key } from '../key.model';
import { NotificationService } from '../../../core/notification.service';

/**
 * Component to display and manage the details of a specific cryptographic key.
 * It allows for enabling/disabling the key, managing its rotation policy,
 * and scheduling it for deletion.
 */
@Component({
  selector: 'app-key-detail',
  standalone: true,
  imports: [
    CommonModule, ReactiveFormsModule, FormsModule, MatCardModule, MatButtonModule,
    MatIconModule, MatProgressSpinnerModule, MatSlideToggleModule,
    MatFormFieldModule, MatInputModule, MatDividerModule,
    MatDialogModule
  ],
  templateUrl: './key-detail.component.html',
  styleUrls: ['./key-detail.component.scss']
})
export class KeyDetailComponent implements OnInit {
  /** Observable stream for the key data. */
  key$: Observable<Key | undefined> | undefined;
  /** The current key object being displayed/edited. */
  key: Key | undefined;
  /** The reactive form group for editing key properties. */
  keyEditForm: FormGroup;
  /** Flag to indicate if a data loading or save operation is in progress. */
  isLoading = false;
  /** Holds the parsed deletion date if the key is pending deletion. */
  parsedDeletionDate: string | null = null;

  /** Reference to the delete confirmation dialog template in the component's HTML. */
  @ViewChild('deleteKeyDialog') deleteKeyDialog!: TemplateRef<any>;

  constructor(
    private route: ActivatedRoute,
    private router: Router,
    private keyService: KeyManagementService,
    private location: Location,
    private fb: FormBuilder,
    private notificationService: NotificationService,
    private dialog: MatDialog
  ) {
    // Initialize the form with default values and validators.
    this.keyEditForm = this.fb.group({
      status: [false],
      rotation_enabled: [false],
      rotation_days: [{ value: 90, disabled: true }, [Validators.required, Validators.min(1)]]
    });
  }

  /**
   * Component lifecycle hook that runs on initialization.
   * Fetches the key details based on the 'id' parameter from the URL.
   */
  ngOnInit(): void {
    const keyIdParam = this.route.snapshot.paramMap.get('id');
    if (keyIdParam) {
      const keyIdAsNumber = +keyIdParam;
      this.key$ = this.keyService.getLocalKeyById(keyIdAsNumber).pipe(
        tap(key => {
          if (key) {
            this.key = key;
            this.initializeForm(key);

            // Check if the key status indicates it's pending deletion and parse the date.
            if (key.status.startsWith('PendingDeletion|')) {
              this.parsedDeletionDate = key.status.split('|')[1];
            } else {
              this.parsedDeletionDate = null;
            }
          } else {
            // **ADDED**: If key is not found, show an error and navigate back.
            this.notificationService.showError(`Key with ID ${keyIdAsNumber} not found.`);
            this.goBack();
          }
        })
      );
    }

    // Subscribe to changes in the 'rotation_enabled' toggle to enable/disable the 'rotation_days' input.
    this.keyEditForm.get('rotation_enabled')?.valueChanges.subscribe(isEnabled => {
      const rotationDaysControl = this.keyEditForm.get('rotation_days');
      if (isEnabled) {
        rotationDaysControl?.enable();
      } else {
        rotationDaysControl?.disable();
      }
    });
  }

  /**
   * Initializes the form with data from the fetched key.
   * @param key The key object used to populate the form.
   */
  initializeForm(key: Key): void {
    this.keyEditForm.patchValue({
      status: key.status === 'Enabled',
      rotation_enabled: key.rotation_enabled,
      rotation_days: key.rotation_days || 90
    }, { emitEvent: false }); // emitEvent: false prevents valueChanges from firing immediately.

    // Manually set the enabled/disabled state for rotation_days.
    if (key.rotation_enabled) {
      this.keyEditForm.get('rotation_days')?.enable({ emitEvent: false });
    } else {
      this.keyEditForm.get('rotation_days')?.disable({ emitEvent: false });
    }

    // Mark the form as pristine, so the save button is disabled until a change is made.
    this.keyEditForm.markAsPristine();
  }

  /**
   * Saves the changes made in the form.
   * It determines which properties have changed and calls the appropriate service methods.
   */
  saveChanges(): void {
    if (!this.key || this.keyEditForm.invalid) {
      // **ADDED**: Notify user if the form is invalid on save attempt.
      this.notificationService.showError('Form is invalid. Please check the fields.');
      return;
    }
    this.isLoading = true;
    const formValues = this.keyEditForm.value;
    const updateObservables = [];

    // Check if the status (Enabled/Disabled) has changed.
    const currentStatus = this.key.status === 'Enabled';
    if (formValues.status !== currentStatus) {
      updateObservables.push(this.keyService.setEnabled(this.key.cloud_provider, this.key.key_id, formValues.status));
    }

    // Check if rotation settings have changed.
    const rotationChanged = formValues.rotation_enabled !== this.key.rotation_enabled ||
      (formValues.rotation_enabled && formValues.rotation_days !== this.key.rotation_days);
    if (rotationChanged) {
      const days = formValues.rotation_days || 90;
      updateObservables.push(this.keyService.setRotation(this.key.cloud_provider, this.key.key_id, formValues.rotation_enabled, days));
    }

    // Use forkJoin to run all update observables in parallel.
    forkJoin(updateObservables.length > 0 ? updateObservables : [of(null)]).subscribe({
      next: () => {
        // Success notification on successful update.
        this.notificationService.showSuccess('Key updated successfully!');
        this.keyEditForm.markAsPristine();
        this.isLoading = false;
        // Reload the component to fetch the latest key data.
        this.router.navigateByUrl('/', { skipLocationChange: true }).then(() => {
          this.router.navigate(['/app/key-management', this.key?.id]);
        });
      },
      error: (err) => {
        this.notificationService.showError(err.error?.message || 'Failed to update key.');
        this.isLoading = false;
      }
    });
  }

  /**
   * Schedules the key for deletion after a specified number of days.
   * @param daysValue The number of days after which the key should be deleted.
   */
  deleteKey(daysValue: string): void {
    const scheduleDays = parseInt(daysValue, 10);
    if (!this.key || isNaN(scheduleDays) || scheduleDays <= 0) {
      this.notificationService.showError('Please provide a valid deletion period.');
      return;
    }

    if (this.key.cloud_provider === 'aws' && (scheduleDays < 7 || scheduleDays > 30)) {
      this.notificationService.showError('For AWS, the deletion period must be between 7 and 30 days.');
      return;
    }

    const dialogRef = this.dialog.open(this.deleteKeyDialog, {
      panelClass: 'warn-dialog-outline',
      backdropClass: 'dialog-backdrop-blur'
    });

    dialogRef.afterClosed().subscribe(result => {
      if (result === true) {
        this.isLoading = true;
        this.keyService.deleteKey(this.key!.cloud_provider, this.key!.key_id, scheduleDays).subscribe({
          next: () => {
            // **ADDED**: Success notification when deletion is scheduled.
            this.notificationService.showSuccess('Key has been scheduled for deletion.');
            this.router.navigate(['/app/key-management']);
          },
          error: (err) => {
            this.notificationService.showError(err.error?.message || 'Failed to schedule key for deletion.');
            this.isLoading = false;
          }
        });
      }
    });
  }

  /**
   * Reverts any changes made in the form to the key's original state.
   */
  cancelChanges(): void {
    if (this.key) {
      this.initializeForm(this.key);
      // **ADDED**: Notify user that changes were discarded.
      this.notificationService.showSuccess('Changes have been discarded.');
    }
  }

  /**
   * Formats a record of labels into a single display string.
   * @param labels A record of string key-value pairs.
   * @returns A comma-separated string of "key: value".
   */
  formatLabels(labels: Record<string, string>): string {
    if (!labels || Object.keys(labels).length === 0) { return 'None'; }
    return Object.entries(labels).map(([key, value]) => `${key}: ${value}`).join(', ');
  }

  /**
   * Navigates to the previous page in the browser's history.
   */
  goBack(): void {
    this.location.back();
  }
}