import { bootstrapApplication } from '@angular/platform-browser';
import { provideHttpClient, withInterceptors } from '@angular/common/http';
import { provideRouter, withComponentInputBinding } from '@angular/router';
import { provideAnimations } from '@angular/platform-browser/animations';

import { AppComponent } from './app/app.component';
import { APP_ROUTES } from './app/app.routes';
import { authInterceptor } from './app/core/auth.interceptor';
// 1. Import the new error interceptor
import { errorInterceptor } from './app/core/error.interceptor'; 

bootstrapApplication(AppComponent, {
  providers: [
    provideHttpClient(withInterceptors([
      authInterceptor, 
      errorInterceptor
    ])),
    
    provideRouter(APP_ROUTES, withComponentInputBinding()),
    provideAnimations()
  ]
}).catch(err => console.error(err));