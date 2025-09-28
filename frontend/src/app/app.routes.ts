// src/app/app.routes.ts

import { Routes } from '@angular/router';
import { ShellComponent } from './layout/shell.component';
import { authGuard } from './core/auth.guard';

export const APP_ROUTES: Routes = [
  { path: '', pathMatch: 'full', redirectTo: 'login' },
  { path: 'login', loadComponent: () => import('./features/auth/login.component').then(m => m.LoginComponent) },
  {
    path: 'app',
    component: ShellComponent,
    canActivate: [authGuard],
    children: [
      { path: '', pathMatch: 'full', redirectTo: 'dashboard' },

      {
        path: 'dashboard',
        loadComponent: () => import('./features/dashboard/dashboard.component').then(m => m.DashboardComponent),
        title: 'Dashboard'
      },
      {
        path: 'key-management',
        children: [
          {
            path: '',
            pathMatch: 'full',
            loadComponent: () => import('./features/key-management/key-list/key-list.component').then(m => m.KeyListComponent),
            title: 'Key Management'
          },
          {
            path: 'create',
            loadComponent: () => import('./features/key-management/key-create/key-create.component').then(m => m.KeyCreateComponent),
            title: 'Create New Key'
          },
          {
            path: ':id',
            loadComponent: () => import('./features/key-management/key-detail/key-detail.component').then(m => m.KeyDetailComponent),
            title: 'Key Details'
          }
        ]
      },
      {
        path: 'crypto-tools',
        loadComponent: () => import('./features/crypto-tools/crypto-tools.component').then(m => m.CryptoToolsComponent),
        title: 'Crypto Tools'
      },
      {
        path: 'pending-actions',
        loadComponent: () => import('./features/pending-actions/pending-actions.component').then(m => m.PendingActionsComponent),
        title: 'Pending Approvals'
      },
      {
        path: 'logs', // Returned to top level
        loadComponent: () => import('./features/logs/logs.component').then(m => m.LogsComponent),
        title: 'Logs'
      },
      {
        path: 'alerts', // Returned to top level
        loadComponent: () => import('./features/alerts/alerts.component').then(m => m.AlertsComponent),
        title: 'Alerts'
      },
      {
        path: 'users',
        loadComponent: () => import('./features/users/users.component').then(m => m.UsersComponent),
        title: 'User Management'
      },
      {
        path: 'modules',
        loadComponent: () => import('./features/modules/modules.component').then(m => m.ModulesComponent),
        title: 'Modules & Sync'
      },
      {
        path: 'reports',
        loadComponent: () => import('./features/reports/reports.component').then(m => m.ReportsComponent),
        title: 'Reports'
      }
    ]
  },
  { path: '**', redirectTo: 'login' }
];