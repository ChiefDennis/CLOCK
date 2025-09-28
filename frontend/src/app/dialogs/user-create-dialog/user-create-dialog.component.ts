import { Component } from '@angular/core';
import { AbstractControl, FormBuilder, FormGroup, ValidationErrors, Validators, ReactiveFormsModule } from '@angular/forms';
import { MatDialogRef } from '@angular/material/dialog';
import { CommonModule } from '@angular/common';

// Import necessary Material Modules
import { MatDialogModule } from '@angular/material/dialog';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatSelectModule } from '@angular/material/select';
import { MatButtonModule } from '@angular/material/button';

export function passwordsMatchValidator(control: AbstractControl): ValidationErrors | null {
  const password = control.get('password');
  const repeatPassword = control.get('repeatPassword');

  if (!password || !repeatPassword || password.value === repeatPassword.value) {
    if (repeatPassword?.hasError('passwordsMismatch')) {
        repeatPassword.setErrors(null);
    }
    return null;
  }
  
  repeatPassword?.setErrors({ passwordsMismatch: true });
  return { passwordsMismatch: true };
};

@Component({
  selector: 'app-user-create-dialog',
  standalone: true,
  imports: [
    CommonModule, ReactiveFormsModule, MatDialogModule, MatFormFieldModule,
    MatInputModule, MatSelectModule, MatButtonModule
  ],
  template: `
    <h2 mat-dialog-title>Create New User</h2>
    <mat-dialog-content>
      <form [formGroup]="userForm" class="dialog-form">
        <mat-form-field appearance="outline">
          <mat-label>Username</mat-label>
          <input matInput formControlName="username" required>
        </mat-form-field>

        <mat-form-field appearance="outline">
          <mat-label>Password</mat-label>
          <input matInput formControlName="password" type="password" required>
          <mat-error *ngIf="userForm.get('password')?.hasError('minlength')">
            Password must be at least 8 characters long.
          </mat-error>
        </mat-form-field>

        <mat-form-field appearance="outline">
          <mat-label>Repeat Password</mat-label>
          <input matInput formControlName="repeatPassword" type="password" required>
          <mat-error *ngIf="userForm.get('repeatPassword')?.hasError('passwordsMismatch')">
            Passwords do not match.
          </mat-error>
        </mat-form-field>

        <mat-form-field appearance="outline">
          <mat-label>Role</mat-label>
          <mat-select formControlName="role" required>
            <mat-option value="user">User</mat-option>
            <mat-option value="admin">Admin</mat-option>
          </mat-select>
        </mat-form-field>
      </form>
    </mat-dialog-content>
    <mat-dialog-actions align="end">
      <button mat-button (click)="onCancel()">Cancel</button>
      <button mat-raised-button color="primary" [disabled]="userForm.invalid" (click)="onCreate()">Create</button>
    </mat-dialog-actions>
  `,
  styles: [`.dialog-form { display: flex; flex-direction: column; gap: 0.8rem; padding-top: 0.5rem; }`]
})
export class UserCreateDialogComponent {
  userForm: FormGroup;

  constructor(
    private fb: FormBuilder,
    public dialogRef: MatDialogRef<UserCreateDialogComponent>
  ) {
    this.userForm = this.fb.group({
      username: ['', Validators.required],
      // 2. Add the minLength validator to the password control
      password: ['', [Validators.required, Validators.minLength(8)]],
      repeatPassword: ['', Validators.required],
      role: ['user', Validators.required]
    }, { 
      validators: passwordsMatchValidator 
    });
  }

  onCancel(): void {
    this.dialogRef.close();
  }

  onCreate(): void {
    if (this.userForm.valid) {
      const { repeatPassword, ...userPayload } = this.userForm.value;
      this.dialogRef.close(userPayload);
    }
  }
}