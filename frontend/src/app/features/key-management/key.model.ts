// src/app/key-management/key.model.ts

export interface Key {
  id: number;
  algorithm: 'SYMMETRIC_DEFAULT' | string;
  cloud_provider: 'aws' | 'azure' | 'gcp';
  created_at: string; // ISO 8601 date string
  description: string;
  is_primary: boolean;
  key_arn: string;
  key_id: string;
  labels: Record<string, string>;
  last_update_source: 'API' | 'UI' | 'SYSTEM';
  last_updated_by: string;
  origin: 'AWS_KMS' | 'AZURE_KEY_VAULT' | 'GCP_KMS' | string;
  protection_level: 'SOFTWARE' | 'HSM';
  region: string;
  rotation_days: number | null;
  rotation_enabled: boolean;
  status: string;
  usage: 'ENCRYPT_DECRYPT' | 'SIGN_VERIFY';
  version: number | null;
}