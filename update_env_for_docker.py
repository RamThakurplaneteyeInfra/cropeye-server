#!/usr/bin/env python
"""
Update .env file for Docker database configuration
"""

import os
from pathlib import Path
from dotenv import load_dotenv

def update_env_for_docker():
    """Update .env file with Docker database settings"""
    
    env_path = Path('.env')
    
    if not env_path.exists():
        print("[ERROR] .env file does not exist!")
        return False
    
    # Read current .env
    with open(env_path, 'r') as f:
        content = f.read()
    
    # Update database configuration for Docker
    # Docker container uses: localhost:5432 with postgres/admin credentials
    
    lines = content.split('\n')
    updated_lines = []
    
    for line in lines:
        if line.startswith('DB_HOST='):
            updated_lines.append('DB_HOST=localhost  # Docker container')
        elif line.startswith('DB_PORT='):
            updated_lines.append('DB_PORT=5432  # Docker container port')
        elif line.startswith('DB_NAME='):
            updated_lines.append('DB_NAME=neoce  # Docker database')
        elif line.startswith('DB_USER='):
            updated_lines.append('DB_USER=postgres  # Docker user')
        elif line.startswith('DB_PASSWORD='):
            # Check if it's a comment line
            if 'DB_PASSWORD=' in line and not line.strip().startswith('#'):
                updated_lines.append('DB_PASSWORD=admin  # Docker password (from docker-compose.yml)')
            else:
                updated_lines.append(line)
        else:
            updated_lines.append(line)
    
    # Write updated content
    updated_content = '\n'.join(updated_lines)
    
    # Backup original
    backup_path = Path('.env.docker-backup')
    if not backup_path.exists():
        with open(backup_path, 'w') as f:
            f.write(content)
        print(f"[INFO] Backed up original .env to .env.docker-backup")
    
    # Write updated file
    with open(env_path, 'w') as f:
        f.write(updated_content)
    
    print("[OK] Updated .env file for Docker database configuration")
    print("")
    print("Database settings:")
    print("  DB_HOST=localhost")
    print("  DB_PORT=5432")
    print("  DB_NAME=neoce")
    print("  DB_USER=postgres")
    print("  DB_PASSWORD=admin")
    
    return True

if __name__ == '__main__':
    print("Updating .env file for Docker database...")
    print("")
    if update_env_for_docker():
        print("")
        print("[SUCCESS] .env file updated!")
    else:
        print("")
        print("[ERROR] Failed to update .env file")

