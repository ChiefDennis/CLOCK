from services import metadata_service
from models import User, PendingAction
from app import create_app
from extensions import db

def sync_all_providers():
    """
    A scheduled job that iterates through all cloud providers and
    triggers the synchronization logic for each one.
    """

    # Create an app context to be able to use the database and other extensions
    app = create_app()
    with app.app_context():
        providers = ["aws", "azure", "gcp"]
        print(f"[Scheduler] Starting daily synchronization for providers: {providers}")

        for provider in providers:
            try:
                print(f"[Scheduler] Synchronizing {provider}...")
                summary = metadata_service.synchronize_provider_keys(provider)
                print(f"[Scheduler] Synchronization for {provider} complete. Summary: {summary}")
            except Exception as e:
                # Log errors but continue to the next provider
                print(f"[Scheduler] ERROR: Synchronization failed for {provider}. Reason: {str(e)}")
        
        print("[Scheduler] Daily synchronization finished.")

def execute_pending_actions():
    """
    A scheduled job to execute approved sensitive actions.
    """

    app = create_app()
    with app.app_context():
        # Find actions that were approved but not yet executed
        actions_to_run = PendingAction.query.filter_by(status='APPROVED').all()
        if not actions_to_run:
            return # Nothing to do

        print(f"[Executor] Found {len(actions_to_run)} approved action(s) to execute.")

        for action in actions_to_run:
            try:
                if action.action_type == 'DELETE_USER':
                    user_id = int(action.resource_identifier)
                    user = User.query.get(user_id)
                    if user:
                        db.session.delete(user)
                        print(f"[Executor] Executed DELETE_USER for user ID {user_id}")
                                
                action.status = 'EXECUTED'
                db.session.commit()
            
            except Exception as e:
                print(f"[Executor] ERROR: Failed to execute action {action.id}. Reason: {str(e)}")
                action.status = 'FAILED_EXECUTION' # Mark as failed
                db.session.commit()