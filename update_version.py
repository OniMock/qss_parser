import sys
import re
import tomlkit
from pathlib import Path
from typing import Optional

def validate_version(version: str) -> None:
    """Validates that the version follows MAJOR.MINOR.PATCH format."""
    if not re.match(r'^\d+\.\d+\.\d+$', version):
        raise ValueError("Version must be in MAJOR.MINOR.PATCH format (e.g., 0.1.0)")

def update_pyproject_version(filepath: Path, new_version: str) -> None:
    """Updates the version in the pyproject.toml file."""
    filepath = Path(filepath)
    if not filepath.exists():
        raise FileNotFoundError(f"File not found: {filepath}")

    with filepath.open('r', encoding='utf-8') as f:
        data = tomlkit.parse(f.read())
    
    if 'project' not in data or 'version' not in data['project']:
        raise KeyError("Invalid pyproject.toml: missing 'project.version' field")
    
    data['project']['version'] = new_version
    
    with filepath.open('w', encoding='utf-8') as f:
        f.write(tomlkit.dumps(data))
    print(f"Updated {filepath} to version {new_version}")

def update_init_version(filepath: Path, new_version: str) -> None:
    """Updates the version in the __init__.py file."""
    filepath = Path(filepath)
    if not filepath.exists():
        raise FileNotFoundError(f"File not found: {filepath}")

    with filepath.open('r', encoding='utf-8') as f:
        content = f.read()
    
    pattern = r'__version__ = ["\'].*?["\']'
    if not re.search(pattern, content):
        raise ValueError(f"No __version__ found in {filepath}")
    
    new_content = re.sub(pattern, f'__version__ = "{new_version}"', content)
    
    with filepath.open('w', encoding='utf-8') as f:
        f.write(new_content)
    print(f"Updated {filepath} to version {new_version}")

def get_current_version(filepath: Path) -> Optional[str]:
    """Reads the current version from pyproject.toml."""
    filepath = Path(filepath)
    if not filepath.exists():
        return None
    with filepath.open('r', encoding='utf-8') as f:
        data = tomlkit.parse(f.read())
    return data.get('project', {}).get('version')

def main() -> None:
    """Main function to update version in pyproject.toml and __init__.py."""
    if len(sys.argv) != 2:
        print("Usage: python update_version.py <new_version>")
        sys.exit(1)
    
    new_version = sys.argv[1]
    
    try:
        validate_version(new_version)
        
        pyproject_file = Path('pyproject.toml')
        init_file = Path('src/qss_parser/__init__.py')
        
        # Check if current version matches the new version
        current_version = get_current_version(pyproject_file)
        if current_version == new_version:
            print(f"Version {new_version} already set in pyproject.toml, skipping update")
            return
        
        # Update files
        update_pyproject_version(pyproject_file, new_version)
        update_init_version(init_file, new_version)
        
    except (ValueError, FileNotFoundError, KeyError) as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()