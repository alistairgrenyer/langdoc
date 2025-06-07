"""Git repository service implementation."""

import subprocess
from pathlib import Path
from typing import Dict, Optional

import rich.console
from langdoc.domain.interfaces import GitRepository


class GitRepositoryService(GitRepository):
    """Implementation of Git repository operations."""

    def __init__(self, console: Optional[rich.console.Console] = None):
        """Initialize the Git repository service.
        
        Args:
            console: Optional Rich console for output
        """
        self.console = console or rich.console.Console()

    def extract_project_info(self, repo_path: Path) -> Dict[str, str]:
        """Extract information from a Git repository.

        Args:
            repo_path: Path to the Git repository

        Returns:
            Dictionary containing repository information
        """
        info = {}
        
        # Check if the path is a Git repository
        if not (repo_path / ".git").exists():
            self.console.print("[yellow]Not a Git repository. Limited information available.[/yellow]")
            return {"is_git_repo": "false"}
            
        info["is_git_repo"] = "true"
        
        try:
            # Get remote URL
            remote_url = self._run_git_command(
                ["git", "config", "--get", "remote.origin.url"], 
                repo_path
            )
            if remote_url:
                info["remote_url"] = remote_url
                
                # Extract repository name and owner from URL
                if "github.com" in remote_url:
                    parts = remote_url.strip().split("/")
                    if len(parts) >= 2:
                        repo_name = parts[-1].replace(".git", "")
                        owner = parts[-2].split(":")[-1]
                        info["repo_name"] = repo_name
                        info["repo_owner"] = owner
            
            # Get default branch
            default_branch = self._run_git_command(
                ["git", "symbolic-ref", "--short", "HEAD"], 
                repo_path
            )
            if default_branch:
                info["default_branch"] = default_branch
                
            # Get last commit info
            last_commit = self._run_git_command(
                ["git", "log", "-1", "--pretty=format:%h|%an|%ae|%s"], 
                repo_path
            )
            if last_commit:
                parts = last_commit.split("|")
                if len(parts) >= 4:
                    info["last_commit_hash"] = parts[0]
                    info["last_commit_author"] = parts[1]
                    info["last_commit_email"] = parts[2]
                    info["last_commit_subject"] = parts[3]
                    
            # Check for tags
            tags = self._run_git_command(
                ["git", "tag", "--sort=-creatordate"], 
                repo_path
            )
            if tags:
                info["latest_tag"] = tags.splitlines()[0]
                info["has_tags"] = "true"
            else:
                info["has_tags"] = "false"
                
        except Exception as e:
            self.console.print(f"[yellow]Error extracting Git information:[/yellow] {str(e)}")
            
        return info
        
    def _run_git_command(self, command: list, cwd: Path) -> str:
        """Run a Git command and return its output.
        
        Args:
            command: Git command to run
            cwd: Working directory
            
        Returns:
            Command output as string
            
        Raises:
            subprocess.SubprocessError: If command fails
        """
        try:
            result = subprocess.run(
                command,
                cwd=str(cwd),
                capture_output=True,
                text=True,
                check=True
            )
            return result.stdout.strip()
        except subprocess.SubprocessError:
            return ""
