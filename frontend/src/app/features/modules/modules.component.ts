// Import necessary modules from Angular's core and common libraries
import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';

// Import RxJS operators for handling asynchronous data streams
import { Observable, BehaviorSubject, switchMap, map } from 'rxjs';

// Import the dedicated service and its data models for this feature
import { ModulesService, ModuleStatus } from './modules.service';
import { NotificationService } from '../../core/notification.service';

// Import all the required Angular Material modules for the template
import { MatSlideToggleModule, MatSlideToggleChange } from '@angular/material/slide-toggle';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { MatDividerModule } from '@angular/material/divider';

/**
 * ModulesComponent manages enabling/disabling cloud provider modules
 * and triggering manual data synchronization for them.
 */
@Component({
  selector: 'app-modules',
  standalone: true,
  imports: [
    CommonModule, MatSlideToggleModule, MatButtonModule, MatIconModule,
    MatProgressSpinnerModule, MatDividerModule
  ],
  templateUrl: './modules.component.html',
  styleUrls: ['./modules.component.scss']
})
export class ModulesComponent implements OnInit {
  // An observable that will hold the sorted list of modules for the template
  modules$!: Observable<ModuleStatus[]>;
  // A BehaviorSubject that acts as a trigger to refetch the module list
  private refreshModules = new BehaviorSubject<void>(undefined);
  // An object to track the loading state of the sync button for each provider individually
  syncing: { [key: string]: boolean } = {};

  constructor(
    private modulesService: ModulesService, // Injected service for module/sync API calls
    private notificationService: NotificationService // Injected service for showing snackbars
  ) {}

  /**
   * On component initialization, set up the observable pipeline to fetch and sort modules.
   */
  ngOnInit(): void {
    // A static array to define the desired display order of the modules
    const providerOrder = ['aws', 'azure', 'gcp'];

    this.modules$ = this.refreshModules.pipe(
      // When refreshModules emits a new value, switch to a new getModulesStatus() call
      switchMap(() => this.modulesService.getModulesStatus()),
      // After fetching, sort the modules array into the predefined order
      map(modules => modules.sort((a, b) => {
        return providerOrder.indexOf(a.provider_name) - providerOrder.indexOf(b.provider_name);
      }))
    );
  }

  /**
   * Handles the (change) event from the mat-slide-toggle for a module.
   * @param event The slide toggle change event.
   * @param module The module object associated with the toggle.
   */
  onToggleModule(event: MatSlideToggleChange, module: ModuleStatus): void {
    const { checked } = event; // `checked` is true if the toggle is now on
    this.modulesService.setModuleStatus(module.provider_name, checked).subscribe({
      next: () => {
        // On success, show a success snackbar and trigger a refresh of the module list
        this.notificationService.showSuccess(`Module '${module.provider_name.toUpperCase()}' has been ${checked ? 'enabled' : 'disabled'}.`);
        this.refreshModules.next();
      },
      error: (err) => {
        // On failure, show an error snackbar
        this.notificationService.showError(`Failed to update module: ${err.error?.message || 'Unknown error'}`);
        // IMPORTANT: Revert the toggle back to its original state since the API call failed
        event.source.checked = !checked;
      }
    });
  }

  /**
   * Handles the (click) event from the "Sync Now" button.
   * @param provider The provider name (e.g., 'aws') to synchronize.
   */
  onSync(provider: string): void {
    // Set the syncing state for this specific provider to true to show the spinner
    this.syncing[provider] = true;
    this.modulesService.syncProvider(provider).subscribe({
      next: (res) => {
        const { added, updated, removed } = res.summary;
        // On success, show a success snackbar with the summary
        this.notificationService.showSuccess(`Sync for ${provider.toUpperCase()} successful! Added: ${added}, Updated: ${updated}, Removed: ${removed}.`);
        // Reset the syncing state for this provider
        this.syncing[provider] = false;
      },
      error: (err) => {
        // On failure, show an error snackbar
        this.notificationService.showError(`Sync failed: ${err.error?.message || 'Unknown error'}`);
        // Reset the syncing state for this provider
        this.syncing[provider] = false;
      }
    });
  }
}