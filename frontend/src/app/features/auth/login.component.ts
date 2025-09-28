// login.component.ts

import { Component } from '@angular/core';
import { AuthService } from '../../core/auth.service';
import { FormsModule } from '@angular/forms';
import { MatIconModule } from '@angular/material/icon';
import { MatButtonModule } from '@angular/material/button';
import { CommonModule } from '@angular/common';

@Component({
  standalone: true,
  selector: 'app-login',
  templateUrl: './login.component.html',
  styleUrl: './login.component.scss',  
  imports: [
    FormsModule, // Enables ngModel
    MatIconModule,
    MatButtonModule,
    CommonModule
  ]
})
export class LoginComponent {
  // Properties to hold the form data
  username = '';
  password = '';
  errorMessage = ''; // To display login errors

  passwordType = "password";

  // Inject the AuthService
  constructor(private auth: AuthService) {}

  onLoginClick() {
    console.log(`Attempting to log in user: ${this.username}`);
    this.errorMessage = ''; // Reset error message

    // Call the service, passing the username and password
    this.auth.login(this.username, this.password).subscribe({
      next: (response) => {
        // Handle successful login (the service will likely navigate)
        console.log('Login successful!', response);
      },
      error: (err) => {
        // Handle login failure
        console.error('Login failed:', err);
        this.errorMessage = 'Invalid username or password.';
      }
    });
  }

  togglePassword() {
    this.passwordType = this.passwordType === "password" ? "text" : "password";
  }
}