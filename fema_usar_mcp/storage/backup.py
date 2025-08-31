"""Backup and disaster recovery module for FEMA USAR MCP.

Provides automated backup, encryption, and disaster recovery capabilities
for critical USAR operational data.
"""

import asyncio
import gzip
import json
import logging
import os
import shutil
import tempfile
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass
import hashlib
import secrets

import boto3
from botocore.exceptions import ClientError, NoCredentialsError
from cryptography.fernet import Fernet
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import psutil

logger = logging.getLogger(__name__)


class BackupType:
    """Backup type constants."""
    FULL = "full"
    INCREMENTAL = "incremental"
    DIFFERENTIAL = "differential"
    TRANSACTION_LOG = "transaction_log"


class BackupStatus:
    """Backup status constants."""
    PENDING = "pending"
    RUNNING = "running"  
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class BackupConfiguration:
    """Backup configuration settings."""
    database_url: str
    backup_directory: str
    encryption_key: bytes
    s3_bucket: Optional[str] = None
    s3_region: Optional[str] = "us-east-1"
    retention_days: int = 30
    compression_enabled: bool = True
    encryption_enabled: bool = True
    verify_backups: bool = True
    max_backup_size_gb: int = 100
    backup_timeout_minutes: int = 60
    notification_emails: List[str] = None


class BackupMetadata:
    """Backup metadata model."""
    
    def __init__(
        self,
        backup_id: str,
        backup_type: str,
        database_name: str,
        backup_size: int,
        compressed_size: int,
        checksum: str,
        created_at: datetime,
        completed_at: Optional[datetime] = None,
        status: str = BackupStatus.PENDING,
        error_message: Optional[str] = None,
        file_path: Optional[str] = None,
        s3_key: Optional[str] = None
    ):
        self.backup_id = backup_id
        self.backup_type = backup_type
        self.database_name = database_name
        self.backup_size = backup_size
        self.compressed_size = compressed_size
        self.checksum = checksum
        self.created_at = created_at
        self.completed_at = completed_at
        self.status = status
        self.error_message = error_message
        self.file_path = file_path
        self.s3_key = s3_key
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "backup_id": self.backup_id,
            "backup_type": self.backup_type,
            "database_name": self.database_name,
            "backup_size": self.backup_size,
            "compressed_size": self.compressed_size,
            "checksum": self.checksum,
            "created_at": self.created_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "status": self.status,
            "error_message": self.error_message,
            "file_path": self.file_path,
            "s3_key": self.s3_key
        }


class EncryptionManager:
    """Encryption manager for backup data."""
    
    def __init__(self, encryption_key: bytes):
        """Initialize encryption manager.
        
        Args:
            encryption_key: Fernet encryption key
        """
        self.fernet = Fernet(encryption_key)
        
    def encrypt_file(self, input_path: str, output_path: str) -> None:
        """Encrypt file.
        
        Args:
            input_path: Path to input file
            output_path: Path to encrypted output file
        """
        with open(input_path, 'rb') as infile:
            with open(output_path, 'wb') as outfile:
                # Process file in chunks for large files
                chunk_size = 64 * 1024  # 64KB chunks
                while True:
                    chunk = infile.read(chunk_size)
                    if not chunk:
                        break
                    encrypted_chunk = self.fernet.encrypt(chunk)
                    outfile.write(encrypted_chunk)
                    
    def decrypt_file(self, input_path: str, output_path: str) -> None:
        """Decrypt file.
        
        Args:
            input_path: Path to encrypted input file
            output_path: Path to decrypted output file
        """
        with open(input_path, 'rb') as infile:
            with open(output_path, 'wb') as outfile:
                # Process file in chunks
                chunk_size = 64 * 1024
                while True:
                    encrypted_chunk = infile.read(chunk_size)
                    if not encrypted_chunk:
                        break
                    chunk = self.fernet.decrypt(encrypted_chunk)
                    outfile.write(chunk)
                    
    def calculate_checksum(self, file_path: str) -> str:
        """Calculate SHA-256 checksum of file.
        
        Args:
            file_path: Path to file
            
        Returns:
            SHA-256 checksum
        """
        hash_sha256 = hashlib.sha256()
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_sha256.update(chunk)
        return hash_sha256.hexdigest()


class S3BackupStorage:
    """S3 storage backend for backups."""
    
    def __init__(self, bucket_name: str, region: str = "us-east-1"):
        """Initialize S3 storage.
        
        Args:
            bucket_name: S3 bucket name
            region: AWS region
        """
        self.bucket_name = bucket_name
        self.region = region
        self.s3_client = boto3.client('s3', region_name=region)
        
    def upload_backup(self, local_path: str, s3_key: str) -> bool:
        """Upload backup to S3.
        
        Args:
            local_path: Local file path
            s3_key: S3 object key
            
        Returns:
            True if upload successful
        """
        try:
            # Upload with server-side encryption
            self.s3_client.upload_file(
                local_path,
                self.bucket_name,
                s3_key,
                ExtraArgs={
                    'ServerSideEncryption': 'AES256',
                    'StorageClass': 'STANDARD_IA',  # Infrequent Access
                    'Metadata': {
                        'source': 'fema-usar-mcp',
                        'upload_time': datetime.now(timezone.utc).isoformat()
                    }
                }
            )
            
            logger.info(f"Uploaded backup to S3: {s3_key}")
            return True
            
        except (ClientError, NoCredentialsError) as e:
            logger.error(f"Failed to upload backup to S3: {str(e)}")
            return False
            
    def download_backup(self, s3_key: str, local_path: str) -> bool:
        """Download backup from S3.
        
        Args:
            s3_key: S3 object key
            local_path: Local file path
            
        Returns:
            True if download successful
        """
        try:
            self.s3_client.download_file(self.bucket_name, s3_key, local_path)
            logger.info(f"Downloaded backup from S3: {s3_key}")
            return True
            
        except ClientError as e:
            logger.error(f"Failed to download backup from S3: {str(e)}")
            return False
            
    def list_backups(self, prefix: str = "") -> List[Dict[str, Any]]:
        """List backups in S3.
        
        Args:
            prefix: Object key prefix filter
            
        Returns:
            List of backup objects
        """
        try:
            response = self.s3_client.list_objects_v2(
                Bucket=self.bucket_name,
                Prefix=prefix
            )
            
            objects = []
            for obj in response.get('Contents', []):
                objects.append({
                    'key': obj['Key'],
                    'size': obj['Size'],
                    'last_modified': obj['LastModified'],
                    'storage_class': obj.get('StorageClass', 'STANDARD')
                })
                
            return objects
            
        except ClientError as e:
            logger.error(f"Failed to list S3 backups: {str(e)}")
            return []
            
    def delete_backup(self, s3_key: str) -> bool:
        """Delete backup from S3.
        
        Args:
            s3_key: S3 object key
            
        Returns:
            True if deletion successful
        """
        try:
            self.s3_client.delete_object(Bucket=self.bucket_name, Key=s3_key)
            logger.info(f"Deleted backup from S3: {s3_key}")
            return True
            
        except ClientError as e:
            logger.error(f"Failed to delete S3 backup: {str(e)}")
            return False


class DatabaseBackupEngine:
    """Database backup engine."""
    
    def __init__(self, config: BackupConfiguration):
        """Initialize backup engine.
        
        Args:
            config: Backup configuration
        """
        self.config = config
        self.encryption_mgr = EncryptionManager(config.encryption_key)
        self.s3_storage = S3BackupStorage(config.s3_bucket, config.s3_region) if config.s3_bucket else None
        
    def create_full_backup(self) -> BackupMetadata:
        """Create full database backup.
        
        Returns:
            Backup metadata
        """
        backup_id = f"full_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}_{secrets.token_hex(4)}"
        
        metadata = BackupMetadata(
            backup_id=backup_id,
            backup_type=BackupType.FULL,
            database_name=self._extract_db_name(self.config.database_url),
            backup_size=0,
            compressed_size=0,
            checksum="",
            created_at=datetime.now(timezone.utc),
            status=BackupStatus.RUNNING
        )
        
        try:
            # Create backup directory
            backup_dir = Path(self.config.backup_directory) / backup_id
            backup_dir.mkdir(parents=True, exist_ok=True)
            
            # Create database dump
            dump_file = backup_dir / "database.sql"
            self._create_pg_dump(str(dump_file))
            
            # Get original size
            metadata.backup_size = dump_file.stat().st_size
            
            # Compress if enabled
            if self.config.compression_enabled:
                compressed_file = backup_dir / "database.sql.gz"
                self._compress_file(str(dump_file), str(compressed_file))
                dump_file.unlink()  # Remove uncompressed file
                dump_file = compressed_file
                
            metadata.compressed_size = dump_file.stat().st_size
            
            # Encrypt if enabled
            if self.config.encryption_enabled:
                encrypted_file = backup_dir / "database.sql.gz.enc"
                self.encryption_mgr.encrypt_file(str(dump_file), str(encrypted_file))
                dump_file.unlink()  # Remove unencrypted file
                dump_file = encrypted_file
                
            metadata.file_path = str(dump_file)
            metadata.checksum = self.encryption_mgr.calculate_checksum(str(dump_file))
            
            # Upload to S3 if configured
            if self.s3_storage:
                s3_key = f"backups/{backup_id}/{dump_file.name}"
                if self.s3_storage.upload_backup(str(dump_file), s3_key):
                    metadata.s3_key = s3_key
                    
            # Backup additional data
            self._backup_configuration(backup_dir)
            self._backup_logs(backup_dir)
            
            metadata.status = BackupStatus.COMPLETED
            metadata.completed_at = datetime.now(timezone.utc)
            
            # Verify backup if enabled
            if self.config.verify_backups:
                if not self._verify_backup(metadata):
                    raise Exception("Backup verification failed")
                    
            logger.info(f"Full backup completed: {backup_id}")
            return metadata
            
        except Exception as e:
            metadata.status = BackupStatus.FAILED
            metadata.error_message = str(e)
            logger.error(f"Full backup failed: {str(e)}")
            return metadata
            
    def create_incremental_backup(self, last_backup_time: datetime) -> BackupMetadata:
        """Create incremental backup.
        
        Args:
            last_backup_time: Time of last backup
            
        Returns:
            Backup metadata
        """
        backup_id = f"incr_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}_{secrets.token_hex(4)}"
        
        metadata = BackupMetadata(
            backup_id=backup_id,
            backup_type=BackupType.INCREMENTAL,
            database_name=self._extract_db_name(self.config.database_url),
            backup_size=0,
            compressed_size=0,
            checksum="",
            created_at=datetime.now(timezone.utc),
            status=BackupStatus.RUNNING
        )
        
        try:
            # Create backup directory
            backup_dir = Path(self.config.backup_directory) / backup_id
            backup_dir.mkdir(parents=True, exist_ok=True)
            
            # Export changed data since last backup
            changes_file = backup_dir / "changes.sql"
            self._export_incremental_changes(last_backup_time, str(changes_file))
            
            if changes_file.stat().st_size == 0:
                logger.info("No changes since last backup")
                metadata.status = BackupStatus.COMPLETED
                metadata.completed_at = datetime.now(timezone.utc)
                return metadata
                
            # Process file same as full backup
            metadata = self._process_backup_file(changes_file, metadata, backup_dir)
            
            logger.info(f"Incremental backup completed: {backup_id}")
            return metadata
            
        except Exception as e:
            metadata.status = BackupStatus.FAILED
            metadata.error_message = str(e)
            logger.error(f"Incremental backup failed: {str(e)}")
            return metadata
            
    def restore_backup(self, backup_metadata: BackupMetadata, target_db_url: Optional[str] = None) -> bool:
        """Restore database from backup.
        
        Args:
            backup_metadata: Backup to restore
            target_db_url: Target database URL (defaults to source)
            
        Returns:
            True if restore successful
        """
        try:
            target_url = target_db_url or self.config.database_url
            
            # Download from S3 if needed
            local_file = backup_metadata.file_path
            if backup_metadata.s3_key and not os.path.exists(local_file):
                temp_file = tempfile.NamedTemporaryFile(delete=False)
                if not self.s3_storage.download_backup(backup_metadata.s3_key, temp_file.name):
                    raise Exception("Failed to download backup from S3")
                local_file = temp_file.name
                
            # Verify checksum
            if self.encryption_mgr.calculate_checksum(local_file) != backup_metadata.checksum:
                raise Exception("Backup file checksum verification failed")
                
            # Process restore file
            restore_file = self._prepare_restore_file(local_file, backup_metadata)
            
            # Restore database
            if backup_metadata.backup_type == BackupType.FULL:
                self._restore_full_backup(restore_file, target_url)
            else:
                self._restore_incremental_backup(restore_file, target_url)
                
            logger.info(f"Database restore completed: {backup_metadata.backup_id}")
            return True
            
        except Exception as e:
            logger.error(f"Database restore failed: {str(e)}")
            return False
            
    def _create_pg_dump(self, output_file: str) -> None:
        """Create PostgreSQL dump."""
        import subprocess
        
        # Parse database URL for pg_dump
        from urllib.parse import urlparse
        parsed = urlparse(self.config.database_url)
        
        cmd = [
            'pg_dump',
            f'--host={parsed.hostname}',
            f'--port={parsed.port or 5432}',
            f'--username={parsed.username}',
            f'--dbname={parsed.path[1:]}',  # Remove leading slash
            '--format=custom',
            '--compress=9',
            '--no-owner',
            '--no-privileges',
            f'--file={output_file}'
        ]
        
        env = os.environ.copy()
        env['PGPASSWORD'] = parsed.password
        
        result = subprocess.run(cmd, env=env, capture_output=True, text=True)
        
        if result.returncode != 0:
            raise Exception(f"pg_dump failed: {result.stderr}")
            
    def _compress_file(self, input_file: str, output_file: str) -> None:
        """Compress file using gzip."""
        with open(input_file, 'rb') as f_in:
            with gzip.open(output_file, 'wb') as f_out:
                shutil.copyfileobj(f_in, f_out)
                
    def _decompress_file(self, input_file: str, output_file: str) -> None:
        """Decompress gzip file."""
        with gzip.open(input_file, 'rb') as f_in:
            with open(output_file, 'wb') as f_out:
                shutil.copyfileobj(f_in, f_out)
                
    def _backup_configuration(self, backup_dir: Path) -> None:
        """Backup configuration files."""
        config_dir = backup_dir / "config"
        config_dir.mkdir(exist_ok=True)
        
        # Backup environment configuration
        config_data = {
            "backup_time": datetime.now(timezone.utc).isoformat(),
            "database_url": self.config.database_url,  # Remove sensitive parts in production
            "retention_days": self.config.retention_days,
            "compression_enabled": self.config.compression_enabled,
            "encryption_enabled": self.config.encryption_enabled
        }
        
        with open(config_dir / "backup_config.json", 'w') as f:
            json.dump(config_data, f, indent=2)
            
    def _backup_logs(self, backup_dir: Path) -> None:
        """Backup recent log files."""
        logs_dir = backup_dir / "logs"
        logs_dir.mkdir(exist_ok=True)
        
        # Copy recent application logs if they exist
        log_paths = [
            "/app/logs/application.log",
            "/var/log/fema-usar-mcp/application.log"
        ]
        
        for log_path in log_paths:
            if os.path.exists(log_path):
                shutil.copy2(log_path, logs_dir / Path(log_path).name)
                
    def _export_incremental_changes(self, since_time: datetime, output_file: str) -> None:
        """Export incremental database changes."""
        # This is a simplified implementation
        # In production, you'd use WAL files or change tracking
        
        engine = create_engine(self.config.database_url)
        with engine.connect() as conn:
            # Export changes since last backup time
            tables_to_export = [
                'task_forces', 'deployments', 'personnel', 
                'equipment', 'operations', 'reports', 'audit_logs'
            ]
            
            with open(output_file, 'w') as f:
                f.write("-- Incremental backup changes\n")
                f.write(f"-- Since: {since_time.isoformat()}\n\n")
                
                for table in tables_to_export:
                    try:
                        # Get updated records
                        result = conn.execute(text(f"""
                            SELECT * FROM {table} 
                            WHERE updated_at > :since_time 
                            OR created_at > :since_time
                        """), {"since_time": since_time})
                        
                        records = result.fetchall()
                        if records:
                            f.write(f"-- Changes in {table}\n")
                            for record in records:
                                # Simple INSERT statement (production would handle UPSERTs)
                                f.write(f"-- Record: {dict(record)}\n")
                                
                    except Exception as e:
                        logger.warning(f"Could not export changes for {table}: {str(e)}")
                        
    def _process_backup_file(self, file_path: Path, metadata: BackupMetadata, backup_dir: Path) -> BackupMetadata:
        """Process backup file with compression and encryption."""
        current_file = file_path
        metadata.backup_size = current_file.stat().st_size
        
        # Compress if enabled
        if self.config.compression_enabled:
            compressed_file = backup_dir / f"{current_file.stem}.gz"
            self._compress_file(str(current_file), str(compressed_file))
            current_file.unlink()
            current_file = compressed_file
            
        metadata.compressed_size = current_file.stat().st_size
        
        # Encrypt if enabled
        if self.config.encryption_enabled:
            encrypted_file = backup_dir / f"{current_file.name}.enc"
            self.encryption_mgr.encrypt_file(str(current_file), str(encrypted_file))
            current_file.unlink()
            current_file = encrypted_file
            
        metadata.file_path = str(current_file)
        metadata.checksum = self.encryption_mgr.calculate_checksum(str(current_file))
        
        # Upload to S3 if configured
        if self.s3_storage:
            s3_key = f"backups/{metadata.backup_id}/{current_file.name}"
            if self.s3_storage.upload_backup(str(current_file), s3_key):
                metadata.s3_key = s3_key
                
        metadata.status = BackupStatus.COMPLETED
        metadata.completed_at = datetime.now(timezone.utc)
        
        return metadata
        
    def _prepare_restore_file(self, backup_file: str, metadata: BackupMetadata) -> str:
        """Prepare backup file for restore."""
        current_file = backup_file
        
        # Decrypt if needed
        if self.config.encryption_enabled and current_file.endswith('.enc'):
            decrypted_file = current_file[:-4]  # Remove .enc extension
            self.encryption_mgr.decrypt_file(current_file, decrypted_file)
            current_file = decrypted_file
            
        # Decompress if needed
        if self.config.compression_enabled and current_file.endswith('.gz'):
            decompressed_file = current_file[:-3]  # Remove .gz extension
            self._decompress_file(current_file, decompressed_file)
            current_file = decompressed_file
            
        return current_file
        
    def _restore_full_backup(self, backup_file: str, target_db_url: str) -> None:
        """Restore full backup."""
        import subprocess
        from urllib.parse import urlparse
        
        parsed = urlparse(target_db_url)
        
        cmd = [
            'pg_restore',
            f'--host={parsed.hostname}',
            f'--port={parsed.port or 5432}',
            f'--username={parsed.username}',
            f'--dbname={parsed.path[1:]}',
            '--clean',
            '--no-owner',
            '--no-privileges',
            backup_file
        ]
        
        env = os.environ.copy()
        env['PGPASSWORD'] = parsed.password
        
        result = subprocess.run(cmd, env=env, capture_output=True, text=True)
        
        if result.returncode != 0:
            raise Exception(f"pg_restore failed: {result.stderr}")
            
    def _restore_incremental_backup(self, backup_file: str, target_db_url: str) -> None:
        """Restore incremental backup."""
        # Apply incremental changes
        engine = create_engine(target_db_url)
        with engine.connect() as conn:
            with open(backup_file, 'r') as f:
                sql_content = f.read()
                # Execute SQL statements (simplified)
                conn.execute(text(sql_content))
                conn.commit()
                
    def _verify_backup(self, metadata: BackupMetadata) -> bool:
        """Verify backup integrity."""
        try:
            # Check file exists and matches checksum
            if not os.path.exists(metadata.file_path):
                return False
                
            current_checksum = self.encryption_mgr.calculate_checksum(metadata.file_path)
            if current_checksum != metadata.checksum:
                return False
                
            # Check file size is reasonable
            file_size = os.path.getsize(metadata.file_path)
            if file_size != metadata.compressed_size:
                return False
                
            return True
            
        except Exception as e:
            logger.error(f"Backup verification failed: {str(e)}")
            return False
            
    def _extract_db_name(self, database_url: str) -> str:
        """Extract database name from URL."""
        from urllib.parse import urlparse
        parsed = urlparse(database_url)
        return parsed.path[1:] if parsed.path.startswith('/') else parsed.path


class BackupScheduler:
    """Automated backup scheduler."""
    
    def __init__(self, config: BackupConfiguration):
        """Initialize backup scheduler.
        
        Args:
            config: Backup configuration
        """
        self.config = config
        self.backup_engine = DatabaseBackupEngine(config)
        self.backup_history: List[BackupMetadata] = []
        
    async def schedule_backups(self):
        """Start automated backup scheduling."""
        logger.info("Starting automated backup scheduler")
        
        while True:
            try:
                # Full backup daily at 2 AM
                now = datetime.now(timezone.utc)
                if now.hour == 2 and now.minute == 0:
                    await self._run_full_backup()
                    
                # Incremental backup every 4 hours
                elif now.hour % 4 == 0 and now.minute == 0:
                    await self._run_incremental_backup()
                    
                # Cleanup old backups
                elif now.hour == 1 and now.minute == 0:
                    await self._cleanup_old_backups()
                    
                await asyncio.sleep(60)  # Check every minute
                
            except Exception as e:
                logger.error(f"Backup scheduler error: {str(e)}")
                await asyncio.sleep(300)  # Wait 5 minutes on error
                
    async def _run_full_backup(self):
        """Run full backup."""
        logger.info("Starting scheduled full backup")
        metadata = self.backup_engine.create_full_backup()
        self.backup_history.append(metadata)
        self._save_backup_metadata(metadata)
        
    async def _run_incremental_backup(self):
        """Run incremental backup."""
        if not self.backup_history:
            logger.info("No previous backups, running full backup instead")
            await self._run_full_backup()
            return
            
        last_backup = max(self.backup_history, key=lambda x: x.created_at)
        logger.info("Starting scheduled incremental backup")
        metadata = self.backup_engine.create_incremental_backup(last_backup.created_at)
        self.backup_history.append(metadata)
        self._save_backup_metadata(metadata)
        
    async def _cleanup_old_backups(self):
        """Clean up old backups."""
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=self.config.retention_days)
        
        expired_backups = [
            backup for backup in self.backup_history 
            if backup.created_at < cutoff_date
        ]
        
        for backup in expired_backups:
            try:
                # Delete local file
                if backup.file_path and os.path.exists(backup.file_path):
                    os.remove(backup.file_path)
                    
                # Delete from S3
                if backup.s3_key and self.backup_engine.s3_storage:
                    self.backup_engine.s3_storage.delete_backup(backup.s3_key)
                    
                self.backup_history.remove(backup)
                logger.info(f"Cleaned up expired backup: {backup.backup_id}")
                
            except Exception as e:
                logger.error(f"Failed to cleanup backup {backup.backup_id}: {str(e)}")
                
    def _save_backup_metadata(self, metadata: BackupMetadata):
        """Save backup metadata to file."""
        metadata_dir = Path(self.config.backup_directory) / "metadata"
        metadata_dir.mkdir(parents=True, exist_ok=True)
        
        metadata_file = metadata_dir / f"{metadata.backup_id}.json"
        with open(metadata_file, 'w') as f:
            json.dump(metadata.to_dict(), f, indent=2)