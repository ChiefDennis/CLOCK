import { inject } from '@angular/core';
import {
  HttpEvent,
  HttpHandlerFn,
  HttpRequest,
  HttpErrorResponse,
  HttpInterceptorFn
} from '@angular/common/http';
import { Observable, throwError } from 'rxjs';
import { catchError } from 'rxjs/operators';
import { NotificationService } from './notification.service';

export const errorInterceptor: HttpInterceptorFn = (req: HttpRequest<any>, next: HttpHandlerFn): Observable<HttpEvent<any>> => {
  
  const notificationService = inject(NotificationService);

  return next(req).pipe(
    catchError((error: HttpErrorResponse) => {
      if (error.status >= 400 && error.status < 500) {
        // UPDATED: Now checks for 'error.error.msg' as a fallback before the default message.
        const errorMessage = error.error?.message || error.error?.msg || 'An unexpected error occurred.';
        notificationService.showError(errorMessage);
      }
      
      return throwError(() => error);
    })
  );
};